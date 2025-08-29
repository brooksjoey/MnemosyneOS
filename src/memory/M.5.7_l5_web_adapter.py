"""
M.5.7 — L5 Web Adapter Module
PURPOSE: Provide a simple web API for the memory system, enabling HTTP-based interaction for ingest, recall, diagnostics, etc.
INPUTS: HTTP requests (action, params)
ACTIONS:
  1. Expose endpoints for ingest, recall, sitrep, backup, restore.
  2. Route requests to memory_api and return JSON responses.
OUTPUT/STATE: HTTP API responses
ROLLBACK: N/A (stateless interface)
QUICKTEST: python -m memory.M.5.7_l5_web_adapter --test
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .M.5.4_l5_api_adapter import memory_api

app = FastAPI(title="Mnemosyne Memory Web API")

@app.post("/ingest")
async def ingest(request: Request):
    data = await request.json()
    result = memory_api("ingest", data)
    return JSONResponse(result)

@app.get("/recall")
async def recall(query: str, limit: int = 10):
    result = memory_api("recall", {"query": query, "limit": limit})
    return JSONResponse(result)

@app.get("/sitrep")
async def sitrep():
    result = memory_api("sitrep", {})
    return JSONResponse(result)

@app.post("/backup")
async def backup(request: Request):
    data = await request.json()
    result = memory_api("backup", data)
    return JSONResponse(result)

@app.post("/restore")
async def restore(request: Request):
    data = await request.json()
    result = memory_api("restore", data)
    return JSONResponse(result)

# Quicktest is not implemented for web adapter (requires ASGI test client)
if __name__ == "__main__":
    print("Run with: uvicorn memory.M.5.7_l5_web_adapter:app --reload")
