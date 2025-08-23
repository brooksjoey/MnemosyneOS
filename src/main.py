src/main.py
from fastapi import FastAPI
from .utils.logging import configure_logging
from .utils.settings import settings
from .db.automigrate import run_migrations
from .db.session import SessionLocal
from .db.vector_index import ensure_indexes
from .api.routes_memory import router as memory_router
from .api.routes_ops import router as ops_router
from .api.routes_health import router as health_router
from .core.healing import self_heal_on_boot

# Optional: simple OTel setup if endpoint provided
try:
    if settings.otel_exporter_otlp_endpoint:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        provider = TracerProvider(resource=Resource.create({"service.name": "hippocampus"}))
        provider.add_span_processor(BatchSpanProcessor(
            OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        ))
        trace.set_tracer_provider(provider)
except Exception:
    # keep app boot resilient even if OTel wiring fails
    pass

def create_app():
    log = configure_logging()
    app = FastAPI(title="Hippocampus", version="0.2.0")

    # Migrations + index + healing
    run_migrations()
    with SessionLocal() as db:
        ensure_indexes(db.connection())
        self_heal_on_boot(db)

    app.include_router(health_router)
    app.include_router(memory_router)
    app.include_router(ops_router)
    return app

# Export app for non-factory runners (e.g., uvicorn src.main:app)
app = create_app()