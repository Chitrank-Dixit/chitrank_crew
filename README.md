# ChitrankCrew Crew

Welcome to the ChitrankCrew Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

```bash
uv sync
```

This will install all dependencies and make the project scripts available.
### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# LLM Configuration
MODEL=your-model-name  # e.g., "llama3" for Ollama
API_BASE=http://localhost:11434  # Ollama API base URL (or your LLM API endpoint)

# Optional: OpenAI API Key (if using OpenAI models)
OPENAI_API_KEY=your-api-key-here
```

### Customizing

- Modify `src/chitrank_crew/config/agents.yaml` to define your agents
- Modify `src/chitrank_crew/config/tasks.yaml` to define your tasks
- Modify `src/chitrank_crew/crew.py` to add your own logic, tools and specific args
- Modify `src/chitrank_crew/main.py` to add custom inputs for your agents and tasks

## Running the Project

### 1. Setup RAG (Vector Store)

Before running the crew, you need to ingest documents into the vector store. Run this once (or whenever documents are added/updated):

```bash
uv run setup_rag
```

**⏱️ First Run Timing:**
- **First time**: ~1-2 minutes (downloads ~90MB embedding model, loads into memory, then ingests documents)
- **Subsequent runs**: ~10-30 seconds (only ingests documents, model is cached)

This will ingest documents from:
- `src/knowledge/docs/shared/` - Shared documents for all agents
- `src/knowledge/docs/software_engineer/` - Software engineer specific docs
- `src/knowledge/docs/qa_engineer/` - QA engineer specific docs
- `src/knowledge/docs/devops_engineer/` - DevOps engineer specific docs
- `src/knowledge/docs/manager/` - Manager specific docs

### 2. Run the Crew

To kickstart your crew of AI agents and begin task execution:

```bash
uv run run_crew
```

Or using the crewai CLI:

```bash
crewai run
```

This command initializes the ChitrankCrew, assembling the agents and assigning them tasks as defined in your configuration.

### 3. Run the MCP Server (Optional)

The MCP server exposes memory and RAG tools via the Model Context Protocol. To run it:

```bash
uv run mcp_server
```

**Note**: This runs continuously until you stop it (Ctrl+C). The server communicates via stdin/stdout, so keep it running in a separate terminal if you want to use it with MCP clients.

#### Connecting to Claude Desktop

To use the MCP server with Claude Desktop, add this to your Claude Desktop configuration file (typically `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "crew-memory": {
      "command": "uv",
      "args": [
        "run",
        "mcp_server"
      ],
      "cwd": "/Users/chitrankdixit/Documents/personal_projects/prabhu-ai/chitrank_crew"
    }
  }
}
```

Replace the `cwd` path with your actual project path. Restart Claude Desktop to see the `crew-memory` tools available.

#### Available MCP Tools

- **st_store**: Store a short-term message in SQLite for a session
- **st_fetch**: Fetch recent short-term messages from SQLite for a session
- **vector_recall**: Semantic search in long-term vector memory for an agent
- **rag_query**: Query the RAG vector store filtered by agent_scope/namespace

### 4. Other Commands

```bash
# Train the crew
uv run train <n_iterations> <filename>

# Test the crew
uv run test <n_iterations> <eval_llm>

# Replay from a specific task
uv run replay <task_id>

# Run with trigger payload
uv run run_with_trigger <json_payload>
```

## Understanding Your Crew

The chitrank-crew Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the ChitrankCrew Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.

## Project Structure

```
chitrank_crew/
├── src/
│   ├── chitrank_crew/
│   │   ├── config/          # Agent and task configurations
│   │   ├── tools/           # Custom tools (memory, RAG)
│   │   ├── crew.py          # Crew definition
│   │   ├── main.py          # Main entry points
│   │   └── setup_rag.py     # RAG ingestion script
│   ├── mcp_servers/         # MCP server for external tools
│   └── knowledge/           # Vector stores and documents
│       ├── docs/            # Documents to ingest
│       ├── vector_store/    # ChromaDB vector store
│       └── short_term.sqlite # SQLite for short-term memory
└── pyproject.toml           # Project configuration
```

## Memory & RAG System

This project includes a sophisticated memory system:

- **Short-term Memory (SQLite)**: Session-based conversation history
- **Long-term Memory (ChromaDB)**: Agent-specific semantic memories
- **RAG (Retrieval Augmented Generation)**: Document-based knowledge retrieval with agent scoping

Documents are organized by agent scope, allowing each agent to access relevant knowledge while maintaining separation of concerns.

## Performance Notes

### First Run (Cold Start)

The **first time** you run the crew with RAG/memory tools, expect delays:

1. **Embedding Model Download**: ~30-60 seconds
   - Downloads `sentence-transformers/all-MiniLM-L6-v2` (~90MB)
   - Stored in `~/.cache/huggingface/` (cached for future runs)

2. **Model Loading**: ~5-10 seconds
   - Loads the model into memory
   - Subsequent runs: ~1-2 seconds (model cached)

3. **Database Initialization**: ~1-2 seconds
   - Creates ChromaDB and SQLite databases/tables

**Total first run**: ~1-2 minutes before agent execution starts

### Subsequent Runs

After the first run:
- **Model loading**: ~1-2 seconds (cached)
- **Database access**: Instant (already created)
- **Crew execution**: Depends on your LLM and task complexity

### Optimization Tips for Crew Execution

1. **Pre-warm embedding model**: The `run_crew` command now automatically pre-warms the embedding model to avoid delays on first tool use
2. **Run `setup_rag` first**: Ensures documents are ingested and model is cached
3. **LLM Performance**: Crew execution speed depends heavily on your LLM:
   - **Local Ollama**: Faster models (e.g., `llama3.2`, `mistral`) will execute faster than larger models
   - **Remote API**: Network latency adds overhead; consider using faster/cheaper models for development
4. **Reduce verbose mode**: Set `verbose=False` in `crew.py` for faster execution (currently `verbose=True` for debugging)
5. **Tool count**: Each agent has 8 tools - more tools mean more decision overhead for the LLM. Consider removing unused tools if speed is critical
6. **Keep MCP server running**: If using MCP, keep it running to reuse the loaded embedding model across sessions
7. **Task dependencies**: Sequential processing is necessary but slow - tasks run one after another based on dependencies

### Expected Crew Execution Times

- **With fast local LLM (Ollama)**: 2-5 minutes for a full crew run
- **With remote API (OpenAI/Anthropic)**: 3-10 minutes (depends on network and model speed)
- **Agent thinking + tool calls**: Each agent decision can take 5-30 seconds depending on LLM speed

The main bottleneck is typically **LLM inference time**, not the tools themselves.