import os
from chitrank_crew.tools.custom_tool import VectorRememberTool, VectorRecallTool, STStoreTool, STFetchTool, RAGIngestTool, RAGQueryTool, AgentScopedRAGIngestTool, AgentScopedRAGQueryTool
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from crewai import LLM
from dotenv import load_dotenv
load_dotenv()
model = os.getenv("MODEL")
base_url = os.getenv("API_BASE")

ollama_llm = LLM(
    model=model,
    base_url=base_url
)

# RAG Ingest Directory
ingest_tool = RAGIngestTool()
ingest_result = ingest_tool.run({
  "directory": "/Users/chitrankdixit/Documents/personal_projects/prabhu-ai/chitrank_crew/src/knowledge/docs/shared",
  "agent_scope": "shared",
  "namespace": "auth-feature",
  "patterns": "*.pdf,*.txt",
  "max_words": 300,
  "overlap_words": 50
})

query_tool = RAGQueryTool()
query_result = query_tool.run({
  "query": "password reset token expiry and security considerations",
  "top_k": 8,
  "agent_scope": "shared",
  "namespace": "auth-feature"
})

# RAG Ingest Directory for software_engineer

@CrewBase
class ChitrankCrew():
    """ChitrankCrew crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    def _debug_print_configs(self):
        print("Loaded agent keys:", list(self.agents_config.keys()))
        print("Loaded task keys:", list(self.tasks_config.keys()))

    @agent
    def manager(self) -> Agent:
        
        return Agent(
            config=self.agents_config['manager'],  # type: ignore[index]
            verbose=True,
            llm=ollama_llm,
            tools=[VectorRememberTool(), VectorRecallTool(), STStoreTool(), STFetchTool(), RAGIngestTool(), RAGQueryTool(),
            AgentScopedRAGIngestTool(default_agent_scope="manager"),
            AgentScopedRAGQueryTool(default_agent_scope="manager"),]
        )

    @agent
    def software_engineer(self) -> Agent:
        
        return Agent(
            config=self.agents_config['software_engineer'],  # type: ignore[index]
            verbose=True,
            llm=ollama_llm,
            tools=[VectorRememberTool(), VectorRecallTool(), STStoreTool(), STFetchTool(), RAGIngestTool(), RAGQueryTool(),
            AgentScopedRAGIngestTool(default_agent_scope="software_engineer"),
            AgentScopedRAGQueryTool(default_agent_scope="software_engineer"),]
        )

    @agent
    def devops_engineer(self) -> Agent:
        
        return Agent(
            config=self.agents_config['devops_engineer'],  # type: ignore[index]
            verbose=True,
            llm=ollama_llm,
            tools=[VectorRememberTool(), VectorRecallTool(), STStoreTool(), STFetchTool(), RAGIngestTool(), RAGQueryTool(),
            AgentScopedRAGIngestTool(default_agent_scope="devops_engineer"),
            AgentScopedRAGQueryTool(default_agent_scope="devops_engineer"),]
        )

    @agent
    def qa_engineer(self) -> Agent:
        
        return Agent(
            config=self.agents_config['qa_engineer'],  # type: ignore[index]
            verbose=True,
            llm=ollama_llm,
            tools=[VectorRememberTool(), VectorRecallTool(), STStoreTool(), STFetchTool(), RAGIngestTool(), RAGQueryTool(),
            AgentScopedRAGIngestTool(default_agent_scope="qa_engineer"),
            AgentScopedRAGQueryTool(default_agent_scope="qa_engineer"),]
        )

    @task
    def plan_project(self) -> Task:
        return Task(
            config=self.tasks_config['plan_project'],  # type: ignore[index]
        )

    @task
    def implement_feature(self) -> Task:
        return Task(
            config=self.tasks_config['implement_feature'],  # type: ignore[index]
            context=[self.plan_project()],
        )

    @task
    def setup_ci_cd(self) -> Task:
        return Task(
            config=self.tasks_config['setup_ci_cd'],  # type: ignore[index]
            context=[self.plan_project(), self.implement_feature()],
        )

    @task
    def write_tests(self) -> Task:
        return Task(
            config=self.tasks_config['write_tests'],  # type: ignore[index]
            context=[self.plan_project(), self.implement_feature()],
        )

    @task
    def final_review(self) -> Task:
        return Task(
            config=self.tasks_config['final_review'],  # type: ignore[index]
            context=[self.plan_project(), self.implement_feature(), self.setup_ci_cd(), self.write_tests()],
            output_file='report.md'
        )
    
    @task
    def ingest_docs(self) -> Task:
        return Task(config=self.tasks_config['ingest_docs'])

    @crew
    def crew(self) -> Crew:
        """Creates the ChitrankCrew crew"""
        #self._debug_print_configs()
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            manager=self.manager(),
            verbose=True,
        )