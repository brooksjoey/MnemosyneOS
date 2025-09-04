"""
Procedural Memory Layer for MnemosyneOS.

This module handles storage and retrieval of procedural knowledge,
focusing on how-to guides, instructions, and step-by-step processes.
"""
import os
import uuid
import datetime
import json
from typing import List, Dict, Any, Optional

from app import logging_setup
from app.config import settings
from app.store import chroma

# Initialize logger
logger = logging_setup.get_logger()

# Collection name for procedural memory
COLLECTION_NAME = "procedural_memory"

def initialize():
    """Initialize the procedural memory collection"""
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Procedural memory for how-to knowledge and procedures"}
        )
        logger.info(f"Initialized procedural memory collection with {collection.count()} documents")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize procedural memory: {str(e)}")
        return False

def store_memory(
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    source: Optional[str] = None
) -> str:
    """
    Store a procedural memory item.
    
    Args:
        content: The content to store (procedure description)
        metadata: Additional metadata about the procedure
        tags: List of tags to categorize the procedure
        source: Source of the procedure
        
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
            "memory_type": "procedural",
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
        
        logger.info(f"Stored procedural memory: {memory_id[:8]}...")
        return memory_id
        
    except Exception as e:
        logger.error(f"Error storing procedural memory: {str(e)}")
        raise

def store_procedure(
    title: str,
    steps: List[str],
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    requirements: Optional[List[str]] = None,
    source: Optional[str] = None
) -> str:
    """
    Store a structured procedure with steps.
    
    Args:
        title: Title of the procedure
        steps: List of steps in the procedure
        description: Optional description of the procedure
        tags: List of tags to categorize the procedure
        requirements: List of requirements for the procedure
        source: Source of the procedure
        
    Returns:
        ID of the stored procedure
    """
    try:
        # Format the procedure content
        procedure = {
            "title": title,
            "description": description or "",
            "steps": steps,
            "requirements": requirements or []
        }
        
        # Convert to string (will be converted back when retrieving)
        content = json.dumps(procedure)
        
        # Prepare metadata
        metadata = {
            "title": title,
            "is_structured": True,
            "step_count": len(steps)
        }
        
        # Add tags if not provided
        if tags is None:
            tags = []
        
        # Always add procedural tag
        if "procedural" not in tags:
            tags.append("procedural")
            
        # Add how-to tag
        if "how-to" not in tags:
            tags.append("how-to")
            
        # Store the procedure
        memory_id = store_memory(
            content=content,
            metadata=metadata,
            tags=tags,
            source=source
        )
        
        return memory_id
        
    except Exception as e:
        logger.error(f"Error storing structured procedure: {str(e)}")
        raise

def retrieve_memories(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve procedural memories based on a query.
    
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
                
                # Parse structured procedures
                if memory["metadata"].get("is_structured", False):
                    try:
                        procedure = json.loads(memory["content"])
                        memory["procedure"] = procedure
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse structured procedure: {memory['id']}")
                
                memories.append(memory)
        
        logger.info(f"Retrieved {len(memories)} procedural memories for query: {query}")
        return memories
        
    except Exception as e:
        logger.error(f"Error retrieving procedural memories: {str(e)}")
        raise

def retrieve_by_tags(tags: List[str], limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve procedural memories by tags.
    
    Args:
        tags: List of tags to filter by
        limit: Maximum number of results to return
        
    Returns:
        List of matching memories with their metadata
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Prepare where clause for tag filtering
        where_filter = None
        if tags:
            # For each tag, check if it's in the tags metadata field
            # This is a simplified approach - a more robust solution would use
            # a database with better tag querying capabilities
            where_filter = {}
            for tag in tags:
                where_filter[f"tags"] = {"$contains": tag}
        
        # Get memories with matching tags
        results = collection.get(
            where=where_filter,
            limit=limit,
            include=["documents", "metadatas"]
        )
        
        # Format results
        memories = []
        if results["ids"]:
            for i in range(len(results["ids"])):
                memory = {
                    "id": results["ids"][i],
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i]
                }
                
                # Parse structured procedures
                if memory["metadata"].get("is_structured", False):
                    try:
                        procedure = json.loads(memory["content"])
                        memory["procedure"] = procedure
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse structured procedure: {memory['id']}")
                
                memories.append(memory)
        
        logger.info(f"Retrieved {len(memories)} procedural memories for tags: {tags}")
        return memories
        
    except Exception as e:
        logger.error(f"Error retrieving procedural memories by tags: {str(e)}")
        raise

def update_procedure(
    memory_id: str,
    title: Optional[str] = None,
    steps: Optional[List[str]] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    requirements: Optional[List[str]] = None
) -> bool:
    """
    Update an existing structured procedure.
    
    Args:
        memory_id: ID of the procedure to update
        title: New title (if None, keep existing)
        steps: New steps (if None, keep existing)
        description: New description (if None, keep existing)
        tags: New tags (if None, keep existing)
        requirements: New requirements (if None, keep existing)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Get existing procedure
        result = collection.get(
            ids=[memory_id],
            include=["documents", "metadatas"]
        )
        
        if not result["ids"]:
            logger.warning(f"Procedure not found for update: {memory_id}")
            return False
            
        existing_content = result["documents"][0]
        existing_metadata = result["metadatas"][0]
        
        # Parse existing procedure
        try:
            procedure = json.loads(existing_content)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse existing procedure: {memory_id}")
            return False
        
        # Update procedure fields
        if title is not None:
            procedure["title"] = title
            existing_metadata["title"] = title
            
        if description is not None:
            procedure["description"] = description
            
        if steps is not None:
            procedure["steps"] = steps
            existing_metadata["step_count"] = len(steps)
            
        if requirements is not None:
            procedure["requirements"] = requirements
        
        # Convert back to string
        updated_content = json.dumps(procedure)
        
        # Update tags if provided
        if tags is not None:
            existing_metadata["tags"] = ", ".join(tags)
        
        # Always update the updated_at timestamp
        existing_metadata["updated_at"] = datetime.datetime.now().isoformat()
        
        # Update in collection
        collection.update(
            ids=[memory_id],
            documents=[updated_content],
            metadatas=[existing_metadata]
        )
        
        logger.info(f"Updated procedural memory: {memory_id[:8]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error updating procedural memory: {str(e)}")
        return False

def update_memory(memory_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Update an existing procedural memory.
    
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
        
        logger.info(f"Updated procedural memory: {memory_id[:8]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error updating procedural memory: {str(e)}")
        return False

def delete_memory(memory_id: str) -> bool:
    """
    Delete a procedural memory.
    
    Args:
        memory_id: ID of the memory to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        collection.delete(ids=[memory_id])
        
        logger.info(f"Deleted procedural memory: {memory_id[:8]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting procedural memory: {str(e)}")
        return False

def get_stats() -> Dict[str, Any]:
    """
    Get statistics about the procedural memory collection.
    
    Returns:
        Dictionary with statistics
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        count = collection.count()
        
        # Get structured procedures count
        where_filter = {"is_structured": True}
        structured = collection.get(
            where=where_filter,
            include=["ids"]
        )
        structured_count = len(structured["ids"]) if structured["ids"] else 0
        
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
                    if tag:  # Skip empty tags
                        tags[tag] = tags.get(tag, 0) + 1
        
        # Get average steps per procedure
        step_counts = [
            m.get("step_count", 0) for m in all_metadatas 
            if m.get("is_structured", False)
        ]
        avg_steps = sum(step_counts) / len(step_counts) if step_counts else 0
        
        return {
            "count": count,
            "structured_count": structured_count,
            "oldest": oldest,
            "newest": newest,
            "tags": tags,
            "avg_steps": avg_steps
        }
        
    except Exception as e:
        logger.error(f"Error getting procedural memory stats: {str(e)}")
        return {"error": str(e), "count": 0, "structured_count": 0}
