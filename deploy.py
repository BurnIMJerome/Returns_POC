import os
import vertexai
from vertexai import agent_engines
from vertexai.preview import reasoning_engines
from email_intake_poc.agent import root_agent

PROJECT_ID = "agentic-ai-poc-486504"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://ira-intelligent-returns-agent-bucket"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)

app = reasoning_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

remote_app = agent_engines.create(
    agent_engine=app,
    display_name="intelligent-returns-agent",
    requirements=[
        "google-cloud-aiplatform[adk,agent_engines]",
        "google-adk",
        "google-generativeai",
        "msal",
        "requests",
        "python-dotenv",
        "pydantic",
        "absl-py",
    ],
    extra_packages=["./email_intake_poc"],
)

print("Deployment finished!")
print(f"Resource Name: {remote_app.resource_name}")