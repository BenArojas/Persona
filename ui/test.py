from src.ingestion_local import process_local_files

# Mock file for testing
from io import BytesIO
test_file = BytesIO(b"This is a test document.")
test_file.name = "test.txt"
test_file.type = "text/plain"

# Test the function
PERSONAS_DIR = "./personas"
CHROMA_DIR = "chroma"
result = process_local_files("test_persona", [test_file])
print(f"Result: {result}")