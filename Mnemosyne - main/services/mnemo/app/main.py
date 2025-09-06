"""
MnemosyneOS - Memory Service for Lucian Voss
FastAPI application serving as the interface to the memory system.
"""
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, HttpUrl

from app.config import settings
from app import logging_setup
from app.memory import (
    semantic, episodic, procedural, reflective, 
    affective, identity, meta
)
from app.ingest import rss, fs
from app.store import chroma

# Initialize logger
logger = logging_setup.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="MnemosyneOS Memory Service",
    description="Memory system for Lucian Voss with 7 memory layers",
    version="2.0.0"
)

# Models for API requests/responses
class MemoryItem(BaseModel):
    content: str
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ReflectionRequest(BaseModel):
    query: Optional[str] = None
    time_range: Optional[str] = None
    tags: Optional[List[str]] = None

class RecallRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
    memory_type: Optional[str] = None
    time_range: Optional[str] = None

class IngestRequest(BaseModel):
    path: str
    recursive: Optional[bool] = False
    file_types: Optional[List[str]] = None

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
    collection: Optional[str] = None

class AffectTagRequest(BaseModel):
    content: str
    tags: List[str]
    valence: Optional[float] = 0.0

class RssAddRequest(BaseModel):
    url: HttpUrl
    name: Optional[str] = None
    category: Optional[str] = None
    update_frequency: Optional[int] = 3600  # in seconds, default 1 hour

# API Routes
@app.get("/health")
async def health_check():
    """Check if the service is healthy"""
    try:
        # Check if ChromaDB is accessible
        chroma_status = chroma.check_health()
        return {
            "status": "healthy", 
            "version": app.version,
            "chroma_status": chroma_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/config")
async def get_config():
    """Get the current configuration (safe values only)"""
    safe_config = {
        "version": app.version,
        "chroma_dir": settings.CHROMA_DIR,
        "log_dir": settings.LOG_DIR,
        "state_dir": settings.STATE_DIR,
        "provider": settings.LVC_PROVIDER,
        # Do not include API keys or sensitive data
    }
    return safe_config

# Memory endpoints
@app.post("/memory/remember")
async def remember(memory: MemoryItem):
    """Store a new memory item"""
    try:
        # Determine the appropriate memory type based on content/tags
        # Default to episodic if not specified
        memory_type = "episodic"
        if memory.tags and "procedural" in memory.tags:
            memory_type = "procedural"
        elif memory.tags and "semantic" in memory.tags:
            memory_type = "semantic"
        
        result = None
        if memory_type == "episodic":
            result = episodic.store_memory(memory.content, memory.metadata, memory.tags, memory.source)
        elif memory_type == "procedural":
            result = procedural.store_memory(memory.content, memory.metadata, memory.tags, memory.source)
        elif memory_type == "semantic":
            result = semantic.store_memory(memory.content, memory.metadata, memory.tags, memory.source)
        
        return {"status": "success", "id": result, "memory_type": memory_type}
    except Exception as e:
        logger.error(f"Error storing memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error storing memory: {str(e)}")

@app.post("/memory/reflect")
async def reflect(request: ReflectionRequest = Body(...), background_tasks: BackgroundTasks = None):
    """Generate reflections on existing memories"""
    try:
        # Start a reflection process in the background
        if background_tasks:
            background_tasks.add_task(
                reflective.generate_reflections,
                query=request.query,
                time_range=request.time_range,
                tags=request.tags
            )
            return {"status": "reflection_started"}
        else:
            # Synchronous reflection if no background_tasks
            result = reflective.generate_reflections(
                query=request.query,
                time_range=request.time_range,
                tags=request.tags
            )
            return {"status": "success", "reflections": result}
    except Exception as e:
        logger.error(f"Error during reflection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during reflection: {str(e)}")

@app.get("/memory/recall")
async def recall(query: str, limit: int = 10, memory_type: Optional[str] = None):
    """Retrieve memories based on query"""
    try:
        results = []
        if memory_type == "episodic" or memory_type is None:
            episodic_results = episodic.retrieve_memories(query, limit)
            results.extend([{**r, "memory_type": "episodic"} for r in episodic_results])
        
        if memory_type == "semantic" or memory_type is None:
            semantic_results = semantic.retrieve_memories(query, limit)
            results.extend([{**r, "memory_type": "semantic"} for r in semantic_results])
        
        if memory_type == "procedural" or memory_type is None:
            procedural_results = procedural.retrieve_memories(query, limit)
            results.extend([{**r, "memory_type": "procedural"} for r in procedural_results])
        
        if memory_type == "reflective" or memory_type is None:
            reflective_results = reflective.retrieve_reflections(query, limit)
            results.extend([{**r, "memory_type": "reflective"} for r in reflective_results])
        
        # Sort combined results by relevance
        results = sorted(results, key=lambda x: x.get("relevance", 0), reverse=True)[:limit]
        
        return {"status": "success", "results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Error recalling memories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error recalling memories: {str(e)}")

# Knowledge base endpoints
@app.post("/kb/ingest")
async def ingest_knowledge(request: IngestRequest, background_tasks: BackgroundTasks):
    """Ingest documents into the knowledge base"""
    try:
        # Start ingestion in background
        background_tasks.add_task(
            fs.ingest_documents,
            path=request.path,
            recursive=request.recursive,
            file_types=request.file_types
        )
        return {"status": "ingestion_started", "path": request.path}
    except Exception as e:
        logger.error(f"Error ingesting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ingesting documents: {str(e)}")

@app.get("/kb/search")
async def search_knowledge(query: str, limit: int = 10):
    """Search the knowledge base"""
    try:
        results = semantic.search_knowledge(query, limit)
        return {"status": "success", "results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching knowledge base: {str(e)}")

# Affect endpoints
@app.post("/affect/tag")
async def tag_affect(request: AffectTagRequest):
    """Tag content with affect information"""
    try:
        result = affective.tag_content(
            content=request.content,
            tags=request.tags,
            valence=request.valence
        )
        return {"status": "success", "id": result}
    except Exception as e:
        logger.error(f"Error tagging affect: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error tagging affect: {str(e)}")

@app.get("/affect/feed")
async def get_affect_feed(tag: Optional[str] = None, valence_range: Optional[str] = None):
    """Get an affect-filtered feed"""
    try:
        results = affective.get_affect_feed(tag=tag, valence_range=valence_range)
        return {"status": "success", "results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Error getting affect feed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting affect feed: {str(e)}")

# RSS endpoints
@app.post("/rss/add")
async def add_rss_feed(request: RssAddRequest):
    """Add a new RSS feed to monitor"""
    try:
        feed_id = rss.add_feed(
            url=str(request.url),
            name=request.name,
            category=request.category,
            update_frequency=request.update_frequency
        )
        return {"status": "success", "feed_id": feed_id}
    except Exception as e:
        logger.error(f"Error adding RSS feed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding RSS feed: {str(e)}")

@app.get("/rss/list")
async def list_rss_feeds(category: Optional[str] = None):
    """List all RSS feeds being monitored"""
    try:
        feeds = rss.list_feeds(category=category)
        return {"status": "success", "feeds": feeds, "count": len(feeds)}
    except Exception as e:
        logger.error(f"Error listing RSS feeds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing RSS feeds: {str(e)}")

@app.post("/rss/pull-now")
async def pull_rss_feeds(background_tasks: BackgroundTasks, feed_id: Optional[str] = None):
    """Pull RSS feeds immediately"""
    try:
        background_tasks.add_task(rss.pull_feeds, feed_id=feed_id)
        return {"status": "rss_pull_started"}
    except Exception as e:
        logger.error(f"Error pulling RSS feeds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error pulling RSS feeds: {str(e)}")

# Identity endpoint
@app.post("/identity/update")
async def update_identity(identity_data: Dict[str, Any]):
    """Update the identity information"""
    try:
        result = identity.update_identity(identity_data)
        return {"status": "success", "id": result}
    except Exception as e:
        logger.error(f"Error updating identity: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating identity: {str(e)}")

# Meta operations
@app.post("/meta/compact")
async def compact_memory(background_tasks: BackgroundTasks, memory_type: Optional[str] = None):
    """Compact the memory collections"""
    try:
        background_tasks.add_task(meta.compact_memory, memory_type=memory_type)
        return {"status": "compaction_started"}
    except Exception as e:
        logger.error(f"Error compacting memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error compacting memory: {str(e)}")

@app.get("/meta/stats")
async def get_stats():
    """Get memory system statistics"""
    try:
        stats = meta.get_stats()
        return {"status": "success", "stats": stats}
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")
