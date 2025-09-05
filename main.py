from fastapi import FastAPI
from config import settings

app = FastAPI(debug=settings.DEBUG)

def get_data_path(filename: str) -> str:
    return f"{settings.DATA_DIR}/{filename}"

def get_vector_path(filename: str) -> str:
    return f"{settings.VECTOR_DIR}/{filename}"

# Example usage:
# with open(get_data_path("my_data.json"), "r") as f:
#     data = f.read()
# with open(get_vector_path("my_vectors.vec"), "r") as f:
#     vectors = f.read()