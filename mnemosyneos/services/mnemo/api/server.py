from fastapi import FastAPI, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.openapi.utils import get_openapi

app = FastAPI()

# Define API Key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Custom OpenAPI schema with security
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="MnemosyneOS",
        version="1.0.0",
        description="Your MnemosyneOS API with API Key authentication",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"APIKeyHeader": []}])
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi