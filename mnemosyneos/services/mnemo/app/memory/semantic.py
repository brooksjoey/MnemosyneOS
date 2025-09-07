"""
Semantic Memory Layer for MnemosyneOS.

This module handles storage and retrieval of semantic knowledge,
focusing on factual information, concepts, and general knowledge.
"""
import os
import uuid
import datetime
from typing import List, Dict, Any, Optional

from app import logging_setup
from app.config import settings
from app.store import chroma

# Initialize logger
logger = logging_setup.get_logger()

# Collection name for semantic memory
COLLECTION_NAME = "semantic_memory"

def initialize():
    """Initialize the semantic memory collection"""
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Semantic memory for factual knowledge"}
        )
        logger.info(f"Initialized semantic memory collection with {collection.count()} documents")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize semantic memory: {str(e)}")
        return False

def store_memory(
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    source: Optional[str] = None
) -> str:
    """
    Store a semantic memory item.
    
    Args:
        content: The content to store
        metadata: Additional metadata about the content
        tags: List of tags to categorize the content
        source: Source of the information
        
    Returns:
        ID of the stored memory
    """
    try:
        # Generate unique ID
        memory_id = str(uuid.uuid4())
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add standard metadata
        timestamp = datetime.datetime.now().isoformat()
        metadata.update({
            "memory_type": "semantic",
            "created_at": timestamp,
            "updated_at": timestamp,
        })
        
        # Add tags if provided
        if tags:
            metadata["tags"] = ", ".join(tags)
            
        # Add source if provided
        if source:
            metadata["source"] = source
            
        # Get collection
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Add to collection
        collection.add(
            ids=[memory_id],
            documents=[content],
            metadatas=[metadata]
        )
        
        logger.info(f"Stored semantic memory: {memory_id[:8]}...")
        return memory_id
        
    except Exception as e:
        logger.error(f"Error storing semantic memory: {str(e)}")
        raise

def retrieve_memories(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve semantic memories based on a query.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        List of matching memories with their metadata
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        memories = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                memory = {
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "relevance": 1.0 - min(results["distances"][0][i], 1.0)  # Convert distance to relevance
                }
                memories.append(memory)
        
        logger.info(f"Retrieved {len(memories)} semantic memories for query: {query}")
        return memories
        
    except Exception as e:
        logger.error(f"Error retrieving semantic memories: {str(e)}")
        raise

def search_knowledge(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search through the knowledge base using semantic search.
    This is an alias for retrieve_memories but may be extended
    with additional knowledge sources in the future.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        List of matching knowledge items
    """
    return retrieve_memories(query, limit)

def update_memory(memory_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Update an existing semantic memory.
    
    Args:
        memory_id: ID of the memory to update
        content: New content
        metadata: New or updated metadata
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Get existing metadata
        result = collection.get(ids=[memory_id], include=["metadatas"])
        
        if not result["ids"]:
            logger.warning(f"Memory not found for update: {memory_id}")
            return False
            
        existing_metadata = result["metadatas"][0]
        
        # Update metadata
        if metadata:
            existing_metadata.update(metadata)
        
        # Always update the updated_at timestamp
        existing_metadata["updated_at"] = datetime.datetime.now().isoformat()
        
        # Update in collection
        collection.update(
            ids=[memory_id],
            documents=[content],
            metadatas=[existing_metadata]
        )
        
        logger.info(f"Updated semantic memory: {memory_id[:8]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error updating semantic memory: {str(e)}")
        return False

def delete_memory(memory_id: str) -> bool:
    """
    Delete a semantic memory.
    
    Args:
        memory_id: ID of the memory to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        collection.delete(ids=[memory_id])
        
        logger.info(f"Deleted semantic memory: {memory_id[:8]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting semantic memory: {str(e)}")
        return False

def get_stats() -> Dict[str, Any]:
    """
    Get statistics about the semantic memory collection.
    
    Returns:
        Dictionary with statistics
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        count = collection.count()
        
        # Get oldest and newest memories
        all_metadatas = []
        
        # Get memories in batches to avoid loading everything at once
        batch_size = 100
        for offset in range(0, count, batch_size):
            batch = collection.get(
                limit=batch_size,
                offset=offset,
                include=["metadatas"]
            )
            all_metadatas.extend(batch["metadatas"])
            
        # Get creation timestamps
        timestamps = [
            datetime.datetime.fromisoformat(m.get("created_at", "2023-01-01T00:00:00"))
            for m in all_metadatas if "created_at" in m
        ]
        
        oldest = min(timestamps).isoformat() if timestamps else None
        newest = max(timestamps).isoformat() if timestamps else None
        
        # Get tag distribution
        tags = {}
        for metadata in all_metadatas:
            if "tags" in metadata:
                for tag in metadata["tags"].split(", "):
                    tags[tag] = tags.get(tag, 0) + 1
        
        return {
            "count": count,
            "oldest": oldest,
            "newest": newest,
            "tags": tags
        }
        
    except Exception as e:
        logger.error(f"Error getting semantic memory stats: {str(e)}")
        return {"error": str(e), "count": 0}
