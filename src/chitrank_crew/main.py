#!/usr/bin/env python
import sys
import warnings

from datetime import datetime
import uuid

from chitrank_crew.crew import ChitrankCrew


warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information


def new_session_id() -> str:
    return uuid.uuid4().hex

def run():
    """
    Run the crew.
    """
    inputs = {
        "session": new_session_id(),
        "project_name": "AwesomeApp",
        "feature_spec": "User can reset password via email magic link with token expiry",
        "repo_url": "https://github.com/org/awesomeapp",
        "service_name": "auth-service",
        "environment": "staging",
        "test_scope": "unit, integration, e2e",
        "rag_namespace": "auth-feature",
        "rag_agent_scope": "shared",
        "docs_dir": "/Users/chitrankdixit/Documents/personal_projects/prabhu-ai/chitrank_crew/src/knowledge/docs/shared",
    }
    
    try:
        ChitrankCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "session": new_session_id(),
        "project_name": "AwesomeApp",
        "feature_spec": "User can reset password via email magic link with token expiry",
        "repo_url": "https://github.com/org/awesomeapp",
        "service_name": "auth-service",
        "environment": "staging",
        "test_scope": "unit, integration, e2e",
        "rag_namespace": "auth-feature",
        "rag_agent_scope": "shared",
        "docs_dir": "/Users/chitrankdixit/Documents/personal_projects/prabhu-ai/chitrank_crew/src/knowledge/docs/shared",
    }

    
    try:
        ChitrankCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        ChitrankCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "session": new_session_id(),
        "project_name": "AwesomeApp",
        "feature_spec": "User can reset password via email magic link with token expiry",
        "repo_url": "https://github.com/org/awesomeapp",
        "service_name": "auth-service",
        "environment": "staging",
        "test_scope": "unit, integration, e2e",
        "rag_namespace": "auth-feature",
        "rag_agent_scope": "shared",
        "docs_dir": "/Users/chitrankdixit/Documents/personal_projects/prabhu-ai/chitrank_crew/src/knowledge/docs/shared",
    }   
    
    try:
        ChitrankCrew().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "session": new_session_id(),
        "project_name": "AwesomeApp",
        "feature_spec": "User can reset password via email magic link with token expiry",
        "repo_url": "https://github.com/org/awesomeapp",
        "service_name": "auth-service",
        "environment": "staging",
        "test_scope": "unit, integration, e2e",
        "rag_namespace": "auth-feature",
        "rag_agent_scope": "shared",
        "docs_dir": "/Users/chitrankdixit/Documents/personal_projects/prabhu-ai/chitrank_crew/src/knowledge/docs/shared",
    }
    try:
        result = ChitrankCrew().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
