import os, json, sqlite3
from typing import Optional, Dict, List
from mcp.server.fastmcp import FastMCP

# Paths align with your project
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
VEC_DIR = os.path.join(ROOT, "knowledge", "vector_store")
ST_DB = os.path.join(ROOT, "knowledge", "short_term.sqlite")

app = FastMCP("crew-memory")

# ---------- SQLite short-term memory ----------
def _ensure_sqlite():
    conn = sqlite3.connect(ST_DB)
    cur = conn.cursor()
    cur.execute("""
      CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session TEXT NOT NULL,
        agent TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        ts REAL NOT NULL
      );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_ts ON messages(session, ts);")
    conn.commit()
    return conn

@app.tool()
def st_fetch(session: str, limit: int = 10) -> str:
    """
    Fetch recent short-term messages from SQLite for a session (JSON).
    """
    conn = _ensure_sqlite()
    rows = conn.execute(
        "SELECT agent, role, content, ts FROM messages WHERE session=? ORDER BY ts DESC LIMIT ?",
        (session, limit)
    ).fetchall()
    conn.close()
    return json.dumps([{"agent": a, "role": r, "content": c, "ts": t} for a, r, c, t in rows])

@app.tool()
def st_store(session: str, agent: str, role: str, content: str) -> str:
    """
    Store a short-term message in SQLite for this session.
    """
    import time
    conn = _ensure_sqlite()
    conn.execute(
        "INSERT INTO messages(session, agent, role, content, ts) VALUES (?,?,?,?,?)",
        (session, agent, role, content, time.time())
    )
    conn.commit()
    conn.close()
    return "stored"

# ---------- Chroma vector memory / RAG ----------
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
        _collection = _chroma.get_or_create_collection("agent_long_term")
    return _collection, _embedder

@app.tool()
def vector_recall(agent: str, query: str, top_k: int = 5) -> str:
    """
    Semantic search in long-term vector memory for an agent. Returns JSON with text, tags, score.
    """
    col, emb = _ensure_vector_store()
    qv = emb.encode([query]).tolist()[0]
    res = col.query(query_embeddings=[qv], n_results=top_k, where={"agent": agent})
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    out = []
    for d, m, s in zip(docs, metas, dists):
        # Parse tags from JSON string (ChromaDB doesn't support lists in metadata)
        tags_str = m.get("tags", "[]")
        try:
            tags_list = json.loads(tags_str) if isinstance(tags_str, str) else (tags_str or [])
        except (json.JSONDecodeError, TypeError):
            tags_list = []
        out.append({"text": d, "agent": m.get("agent"), "tags": tags_list, "score": float(s)})
    return json.dumps(out)

@app.tool()
def rag_query(query: str, top_k: int = 5, agent_scope: Optional[str] = None, namespace: Optional[str] = None) -> str:
    """
    Query the RAG vector store (PDF/TXT ingested) filtered by agent_scope/namespace. Returns JSON.
    """
    col, emb = _ensure_vector_store()
    where: Dict[str, str] = {}
    if agent_scope:
        where["agent_scope"] = agent_scope
    if namespace:
        where["namespace"] = namespace
    qv = emb.encode([query]).tolist()[0]
    res = col.query(query_embeddings=[qv], n_results=top_k, where=where or None)
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    out = []
    for d, m, s in zip(docs, metas, dists):
        out.append({
            "text": d,
            "path": m.get("path"),
            "agent_scope": m.get("agent_scope"),
            "namespace": m.get("namespace"),
            "score": float(s)
        })
    return json.dumps(out)

def run():
    """Run the MCP server (blocks until interrupted)"""
    # Run as stdio MCP server
    app.run()

if __name__ == "__main__":
    # Run as stdio MCP server
    run()