from vertexai.preview import reasoning_engines

# Initialize with your project and location
import vertexai
vertexai.init(project="YOUR_PROJECT_ID", location="YOUR_LOCATION")

# List your engines to find the ID
engines = reasoning_engines.ReasoningEngine.list()
for engine in engines:
    print(f"Display Name: {engine.display_name}")
    print(f"Resource Name: {engine.resource_name}") # This is the unique path
