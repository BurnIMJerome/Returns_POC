import os
from dotenv import load_dotenv
import vertexai
from vertexai import Client
from vertexai.preview import reasoning_engines

# Load .env into local process first
load_dotenv()

from email_intake_poc.agent import root_agent

PROJECT_ID = "agentic-ai-poc-486504"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://ira-intelligent-returns-agent-bucket"
ENGINE_NAME = "projects/agentic-ai-poc-486504/locations/us-central1/reasoningEngines/3025557482232610816"

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)

client = Client(
    project=PROJECT_ID,
    location=LOCATION,
)

app = reasoning_engines.AdkApp(agent=root_agent)

updated_engine = client.agent_engines.update(
    name=ENGINE_NAME,
    agent=app,
    config={
        "staging_bucket": STAGING_BUCKET,
        "display_name": "intelligent-returns-agent",
        "requirements": [
            "google-cloud-aiplatform[adk,agent_engines]",
            "google-adk",
            "google-generativeai",
            "msal",
            "requests",
            "python-dotenv",
            "pydantic",
            "absl-py",
        ],
        "extra_packages": ["./email_intake_poc"],
        "env_vars": {
            # KEEP this (not reserved)
            "GOOGLE_GENAI_USE_VERTEXAI": os.getenv("GOOGLE_GENAI_USE_VERTEXAI", ""),

            # Azure
            "AZURE_TENANT_ID": os.getenv("AZURE_TENANT_ID", ""),
            "AZURE_CLIENT_ID": os.getenv("AZURE_CLIENT_ID", ""),
            "AZURE_CLIENT_SECRET": os.getenv("AZURE_CLIENT_SECRET", ""),
            "MAILBOX_UPN": os.getenv("MAILBOX_UPN", ""),

            # ServiceNow
            "SNOW_INSTANCE_NAME": os.getenv("SNOW_INSTANCE_NAME", ""),
            "SNOW_USERNAME": os.getenv("SNOW_USERNAME", ""),
            "SNOW_PASSWORD": os.getenv("SNOW_PASSWORD", ""),
            "SNOW_DEFAULT_TABLE": os.getenv("SNOW_DEFAULT_TABLE", ""),
            "SNOW_VERIFY_TLS": os.getenv("SNOW_VERIFY_TLS", ""),
            "SNOW_TIMEOUT_SECONDS": os.getenv("SNOW_TIMEOUT_SECONDS", ""),

            # BigQuery (optional — only if your code explicitly reads env)
            "BIGQUERY_PROJECT": os.getenv("BIGQUERY_PROJECT", ""),
            "BIGQUERY_DATASET": os.getenv("BIGQUERY_DATASET", ""),
            "BIGQUERY_TABLE": os.getenv("BIGQUERY_TABLE", ""),

            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",
        },
    },
)

print("Redeployment finished!")
print(updated_engine)