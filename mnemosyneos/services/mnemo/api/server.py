try:
    from fastapi import FastAPI
    import uvicorn
except Exception:
    FastAPI = None
    uvicorn = None

def run():
    if FastAPI is None:
        print("FastAPI/uvicorn not installed; install deps before running.")
        return
    app = FastAPI()

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    uvicorn.run(app, host="0.0.0.0", port=int(__import__("os").environ.get("APP_PORT", "8208")))
