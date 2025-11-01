#!/usr/bin/env python
"""
RAG Setup Script

This script ingests documents into the vector store for all agents.
Run this separately when documents are added or updated.
"""
from chitrank_crew.tools.custom_tool import AgentScopedRAGIngestTool, AgentScopedRAGQueryTool, RAGIngestTool, RAGQueryTool
import json

def ingest_shared():
    """Ingest shared documents into RAG vector store"""
    print("📚 Ingesting shared documents...")
    ingest_tool = RAGIngestTool()
    ingest_result = ingest_tool.run({
        "directory": "/Users/chitrankdixit/Documents/personal_projects/prabhu-ai/chitrank_crew/src/knowledge/docs/shared",
        "agent_scope": "shared",
        "namespace": "auth-feature",
        "patterns": "*.pdf,*.txt",
        "max_words": 300,
        "overlap_words": 50
    })
    result = json.loads(ingest_result)
    print(f"   ✓ Ingested {result.get('files', 0)} files, {result.get('chunks_added', 0)} chunks added")
    
    # Test query
    print("   🔍 Testing query...")
    query_tool = RAGQueryTool()
    query_result = query_tool.run({
        "query": "password reset token expiry and security considerations",
        "top_k": 8,
        "agent_scope": "shared",
        "namespace": "auth-feature"
    })
    results = json.loads(query_result)
    print(f"   ✓ Query returned {len(results)} results")


def ingest_se():
    """Ingest software engineer documents"""
    print("\n👨‍💻 Ingesting software_engineer documents...")
    ingest_tool = AgentScopedRAGIngestTool("software_engineer")
    result = ingest_tool.run({
        "directory": "/Users/chitrankdixit/Documents/personal_projects/prabhu-ai/chitrank_crew/src/knowledge/docs/software_engineer",
        "namespace": "se-auth-feature",
        "patterns": "*.pdf,*.txt"
    })
    parsed = json.loads(result)
    print(f"   ✓ Ingested {parsed.get('files', 0)} files, {parsed.get('chunks_added', 0)} chunks added")
    
    query_tool = AgentScopedRAGQueryTool("software_engineer")
    query_result = query_tool.run({
        "query": "password reset token expiry and security considerations",
        "top_k": 8,
        "namespace": "se-auth-feature"
    })
    results = json.loads(query_result)
    print(f"   ✓ Query returned {len(results)} results")

def ingest_qa():
    """Ingest QA engineer documents"""
    print("\n🧪 Ingesting qa_engineer documents...")
    ingest_tool = AgentScopedRAGIngestTool("qa_engineer")
    result = ingest_tool.run({
        "directory": "/Users/chitrankdixit/Documents/personal_projects/prabhu-ai/chitrank_crew/src/knowledge/docs/qa_engineer",
        "namespace": "qa-auth-feature",
        "patterns": "*.pdf,*.txt"
    })
    parsed = json.loads(result)
    print(f"   ✓ Ingested {parsed.get('files', 0)} files, {parsed.get('chunks_added', 0)} chunks added")
    
    query_tool = AgentScopedRAGQueryTool("qa_engineer")
    query_result = query_tool.run({
        "query": "password reset token expiry and security considerations",
        "top_k": 8,
        "namespace": "qa-auth-feature"
    })
    results = json.loads(query_result)
    print(f"   ✓ Query returned {len(results)} results")

def ingest_devops():
    """Ingest DevOps engineer documents"""
    print("\n⚙️  Ingesting devops_engineer documents...")
    ingest_tool = AgentScopedRAGIngestTool("devops_engineer")
    result = ingest_tool.run({
        "directory": "/Users/chitrankdixit/Documents/personal_projects/prabhu-ai/chitrank_crew/src/knowledge/docs/devops_engineer",
        "namespace": "devops-auth-feature",
        "patterns": "*.pdf,*.txt"
    })
    parsed = json.loads(result)
    print(f"   ✓ Ingested {parsed.get('files', 0)} files, {parsed.get('chunks_added', 0)} chunks added")
    
    query_tool = AgentScopedRAGQueryTool("devops_engineer")
    query_result = query_tool.run({
        "query": "password reset token expiry and security considerations",
        "top_k": 8,
        "namespace": "devops-auth-feature"
    })
    results = json.loads(query_result)
    print(f"   ✓ Query returned {len(results)} results")

def ingest_manager():
    """Ingest manager documents"""
    print("\n👔 Ingesting manager documents...")
    ingest_tool = AgentScopedRAGIngestTool("manager")
    result = ingest_tool.run({
        "directory": "/Users/chitrankdixit/Documents/personal_projects/prabhu-ai/chitrank_crew/src/knowledge/docs/manager",
        "namespace": "manager-auth-feature",
        "patterns": "*.pdf,*.txt"
    })
    parsed = json.loads(result)
    print(f"   ✓ Ingested {parsed.get('files', 0)} files, {parsed.get('chunks_added', 0)} chunks added")
    
    query_tool = AgentScopedRAGQueryTool("manager")
    query_result = query_tool.run({
        "query": "password reset token expiry and security considerations",
        "top_k": 8,
        "namespace": "manager-auth-feature"
    })
    results = json.loads(query_result)
    print(f"   ✓ Query returned {len(results)} results")

def initialize_rag():
    """Initialize RAG by ingesting all agent documents"""
    print("🚀 Starting RAG initialization...\n")
    try:
        ingest_shared()
        ingest_se()
        ingest_qa()
        ingest_devops()
        ingest_manager()
        print("\n✅ RAG initialization complete!")
    except Exception as e:
        print(f"\n❌ Error during RAG initialization: {e}")
        raise


if __name__ == "__main__":
    initialize_rag()