from crewai.tools import BaseTool
from typing import Type, List
from pydantic import BaseModel, Field
import os, json, time, sqlite3

# ---------- Paths ----------
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MEM_DIR = os.path.join(ROOT_DIR, "knowledge", "memory")
VEC_DIR = os.path.join(ROOT_DIR, "knowledge", "vector_store")
ST_DB = os.path.join(ROOT_DIR, "knowledge", "short_term.sqlite")
os.makedirs(MEM_DIR, exist_ok=True)
os.makedirs(VEC_DIR, exist_ok=True)

# ---------- Long-term Vector Memory (Chroma) ----------
# Lazy imports to avoid import cost if unused
_chroma = None
_embedder = None
_collection = None

def _ensure_vector_store():
    global _chroma, _embedder, _collection
    if _chroma is None:
        import chromadb
        from chromadb.config import Settings
        _chroma = chromadb.PersistentClient(path=VEC_DIR, settings=Settings(anonymized_telemetry=False))
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    if _collection is None:
        _collection = _chroma.get_or_create_collection(name="agent_long_term")
    return _collection, _embedder

class VRememberInput(BaseModel):
    agent: str = Field(..., description="Agent id, e.g. 'manager', 'software_engineer'")
    text: str = Field(..., description="Text to store")
    tags: List[str] = Field(default_factory=list, description="Optional tags")

class VRecallInput(BaseModel):
    agent: str = Field(..., description="Agent id")
    query: str = Field(..., description="Search query")
    top_k: int = Field(5, description="Max results")

class VectorRememberTool(BaseTool):
    name: str = "vector_remember"
    description: str = "Persist a note to long-term vector memory for an agent"
    args_schema: Type[BaseModel] = VRememberInput

    def _run(self, agent: str, text: str, tags: List[str] = None) -> str:
        col, emb = _ensure_vector_store()
        doc_id = f"{agent}:{int(time.time()*1000)}"
        meta = {"agent": agent, "tags": tags or []}
        vec = emb.encode([text]).tolist()[0]
        col.add(ids=[doc_id], documents=[text], metadatas=[meta], embeddings=[vec])
        return "saved"

class VectorRecallTool(BaseTool):
    name: str = "vector_recall"
    description: str = "Search long-term vector memory for an agent and return the most relevant notes (JSON)"
    args_schema: Type[BaseModel] = VRecallInput

    def _run(self, agent: str, query: str, top_k: int = 5) -> str:
        col, emb = _ensure_vector_store()
        qv = emb.encode([query]).tolist()[0]
        res = col.query(query_embeddings=[qv], n_results=top_k, where={"agent": agent})
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        scores = (res.get("distances") or [[]])[0]  # lower is better in Chroma 0.5 by default
        out = []
        for d, m, s in zip(docs, metas, scores):
            out.append({"text": d, "agent": m.get("agent"), "tags": m.get("tags", []), "score": float(s)})
        return json.dumps(out)

# ---------- Short-term Memory (SQLite) ----------
def _ensure_sqlite():
    conn = sqlite3.connect(ST_DB)
    cur = conn.cursor()
    cur.execute("""
      CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session TEXT NOT NULL,
        agent TEXT NOT NULL,
        role TEXT NOT NULL,       -- 'user' | 'assistant' | 'system' | 'note'
        content TEXT NOT NULL,
        ts REAL NOT NULL
      );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_ts ON messages(session, ts);")
    conn.commit()
    return conn

class STStoreInput(BaseModel):
    session: str = Field(..., description="Conversation/session id")
    agent: str = Field(..., description="Agent id")
    role: str = Field("note", description="Role label")
    content: str = Field(..., description="Message content")

class STFetchInput(BaseModel):
    session: str = Field(..., description="Conversation/session id")
    limit: int = Field(10, description="Max items to fetch, newest first")

class STStoreTool(BaseTool):
    name: str = "st_store"
    description: str = "Store a short-term message in SQLite for this session"
    args_schema: Type[BaseModel] = STStoreInput

    def _run(self, session: str, agent: str, role: str, content: str) -> str:
        conn = _ensure_sqlite()
        cur = conn.cursor()
        cur.execute("INSERT INTO messages(session, agent, role, content, ts) VALUES (?, ?, ?, ?, ?)",
                    (session, agent, role, content, time.time()))
        conn.commit()
        conn.close()
        return "stored"

class STFetchTool(BaseTool):
    name: str = "st_fetch"
    description: str = "Fetch recent short-term messages from SQLite for a session (JSON)"
    args_schema: Type[BaseModel] = STFetchInput

    def _run(self, session: str, limit: int = 10) -> str:
        conn = _ensure_sqlite()
        cur = conn.cursor()
        cur.execute("SELECT agent, role, content, ts FROM messages WHERE session=? ORDER BY ts DESC LIMIT ?", (session, limit))
        rows = cur.fetchall()
        conn.close()
        out = [{"agent": a, "role": r, "content": c, "ts": t} for (a, r, c, t) in rows]
        return json.dumps(out)

# ---------- RAG: Ingest PDFs and TXT into Chroma, and query ----------

from typing import Optional, Dict
import re
from pydantic import BaseModel, Field
from pypdf import PdfReader

def _read_pdf(path: str) -> str:
    reader = PdfReader(path)
    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(texts)

def _read_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def _chunk_text(text: str, max_words: int = 300, overlap_words: int = 50):
    words = re.findall(r"\S+", text)
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i+max_words]
        chunks.append(" ".join(chunk))
        if i + max_words >= len(words):
            break
        i += max_words - overlap_words
    return chunks

class IngestInput(BaseModel):
    directory: str = Field(..., description="Directory containing files to ingest")
    agent_scope: str = Field("shared", description="Agent scope tag, e.g. 'software_engineer' or 'shared'")
    namespace: str = Field("default", description="Logical namespace/project")
    patterns: str = Field("*.pdf,*.txt", description="Comma-separated glob patterns")
    max_words: int = Field(300, description="Chunk size in words")
    overlap_words: int = Field(50, description="Chunk overlap in words")

class RAGIngestTool(BaseTool):
    name: str = "rag_ingest"
    description: str = "Ingest PDFs/TXT from a directory into vector store with metadata (agent_scope, namespace)"
    args_schema: Type[BaseModel] = IngestInput

    def _run(self, directory: str = None, agent_scope: str = "shared", namespace: str = "default",
             patterns: str = "*.pdf,*.txt", max_words: int = 300, overlap_words: int = 50, **kwargs) -> str:
        import glob, os, json, time
        # Handle case where arguments are passed as a dict (CrewAI BaseTool behavior)
        if isinstance(directory, dict):
            kwargs = directory
            directory = kwargs.get("directory")
            agent_scope = kwargs.get("agent_scope", "shared")
            namespace = kwargs.get("namespace", "default")
            patterns = kwargs.get("patterns", "*.pdf,*.txt")
            max_words = kwargs.get("max_words", 300)
            overlap_words = kwargs.get("overlap_words", 50)
        elif kwargs:
            # If kwargs are provided separately, use them to override defaults
            directory = kwargs.get("directory", directory)
            agent_scope = kwargs.get("agent_scope", agent_scope)
            namespace = kwargs.get("namespace", namespace)
            patterns = kwargs.get("patterns", patterns)
            max_words = kwargs.get("max_words", max_words)
            overlap_words = kwargs.get("overlap_words", overlap_words)
        
        if not directory:
            return json.dumps({"error": "directory parameter is required"})
        
        col, emb = _ensure_vector_store()
        pats = [p.strip() for p in patterns.split(",") if p.strip()]
        files = []
        for p in pats:
            files.extend(glob.glob(os.path.join(directory, p), recursive=True))

        added = 0
        for path in files:
            try:
                ext = os.path.splitext(path)[1].lower()
                if ext == ".pdf":
                    text = _read_pdf(path)
                elif ext == ".txt":
                    text = _read_txt(path)
                else:
                    continue
                if not text.strip():
                    continue
                chunks = _chunk_text(text, max_words=max_words, overlap_words=overlap_words)
                if not chunks:
                    continue
                embeds = emb.encode(chunks).tolist()
                ids = [f"{path}:{i}:{int(time.time()*1000)}" for i in range(len(chunks))]
                metas = [{"path": path, "agent_scope": agent_scope, "namespace": namespace, "chunk": i} for i in range(len(chunks))]
                col.add(ids=ids, documents=chunks, metadatas=metas, embeddings=embeds)
                added += len(chunks)
            except Exception:
                continue
        return json.dumps({"files": len(set(files)), "chunks_added": added})

class RAGQueryInput(BaseModel):
    query: str = Field(..., description="Search query")
    top_k: int = Field(5, description="Max results")
    agent_scope: Optional[str] = Field(None, description="Filter by agent_scope")
    namespace: Optional[str] = Field(None, description="Filter by namespace")

class RAGQueryTool(BaseTool):
    name: str = "rag_query"
    description: str = "Query the vector store for relevant chunks; returns JSON array with text, path, score."
    args_schema: Type[BaseModel] = RAGQueryInput

    def _run(self, query: str = None, top_k: int = 5, agent_scope: Optional[str] = None, namespace: Optional[str] = None, **kwargs) -> str:
        import json
        # Handle case where arguments are passed as a dict (CrewAI BaseTool behavior)
        if isinstance(query, dict):
            kwargs = query
            query = kwargs.get("query")
            top_k = kwargs.get("top_k", 5)
            agent_scope = kwargs.get("agent_scope")
            namespace = kwargs.get("namespace")
        elif kwargs:
            # If kwargs are provided separately, use them to override defaults
            query = kwargs.get("query", query)
            top_k = kwargs.get("top_k", top_k)
            agent_scope = kwargs.get("agent_scope", agent_scope)
            namespace = kwargs.get("namespace", namespace)
        
        if not query:
            return json.dumps({"error": "query parameter is required"})
        
        col, emb = _ensure_vector_store()
        # Build where filter: ChromaDB requires $and operator for multiple conditions
        where = None
        conditions = []
        if agent_scope:
            conditions.append({"agent_scope": agent_scope})
        if namespace:
            conditions.append({"namespace": namespace})
        
        if len(conditions) == 1:
            where = conditions[0]
        elif len(conditions) > 1:
            where = {"$and": conditions}
        
        qv = emb.encode([query]).tolist()[0]
        res = col.query(query_embeddings=[qv], n_results=top_k, where=where)
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        scores = (res.get("distances") or [[]])[0]
        out = []
        for d, m, s in zip(docs, metas, scores):
            out.append({
                "text": d,
                "path": m.get("path"),
                "agent_scope": m.get("agent_scope"),
                "namespace": m.get("namespace"),
                "score": float(s)
            })
        return json.dumps(out)

class AgentScopedRAGIngestTool(RAGIngestTool):
    def __init__(self, default_agent_scope: str):
        super().__init__()
        # Use object.__setattr__ to bypass Pydantic validation for custom attributes
        object.__setattr__(self, 'default_agent_scope', default_agent_scope)

    def _run(self, directory: str = None, agent_scope: str = None, namespace: str = "default",
             patterns: str = "*.pdf,*.txt", max_words: int = 300, overlap_words: int = 50, **kwargs) -> str:
        # Get default_agent_scope using object.__getattribute__ or direct access (should work after __setattr__)
        default_scope = getattr(self, 'default_agent_scope', None)
        agent_scope = agent_scope or default_scope
        return super()._run(directory=directory, agent_scope=agent_scope, namespace=namespace,
                            patterns=patterns, max_words=max_words, overlap_words=overlap_words, **kwargs)

class AgentScopedRAGQueryTool(RAGQueryTool):
    def __init__(self, default_agent_scope: str):
        super().__init__()
        # Use object.__setattr__ to bypass Pydantic validation for custom attributes
        object.__setattr__(self, 'default_agent_scope', default_agent_scope)

    def _run(self, query: str = None, top_k: int = 5, agent_scope: str = None, namespace: str = None, **kwargs) -> str:
        # Get default_agent_scope using getattr
        default_scope = getattr(self, 'default_agent_scope', None)
        agent_scope = agent_scope or default_scope
        return super()._run(query=query, top_k=top_k, agent_scope=agent_scope, namespace=namespace, **kwargs)