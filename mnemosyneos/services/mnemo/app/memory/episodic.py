"""
Episodic Memory Layer for MnemosyneOS.

This module handles storage and retrieval of episodic memories,
focusing on events, experiences, and temporal sequences.
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

# Collection name for episodic memory
COLLECTION_NAME = "episodic_memory"

def initialize():
    """Initialize the episodic memory collection"""
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Episodic memory for events and experiences"}
        )
        logger.info(f"Initialized episodic memory collection with {collection.count()} documents")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize episodic memory: {str(e)}")
        return False

def store_memory(
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    source: Optional[str] = None
) -> str:
    """
    Store an episodic memory item.
    
    Args:
        content: The content to store (event description)
        metadata: Additional metadata about the event
        tags: List of tags to categorize the event
        source: Source of the event (e.g., user input, system event)
        
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
            "memory_type": "episodic",
            "created_at": timestamp,
            "updated_at": timestamp,
            "event_time": metadata.get("event_time", timestamp)
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
        
        logger.info(f"Stored episodic memory: {memory_id[:8]}...")
        return memory_id
        
    except Exception as e:
        logger.error(f"Error storing episodic memory: {str(e)}")
        raise

def retrieve_memories(
    query: str,
    limit: int = 10,
    time_range: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve episodic memories based on a query.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        time_range: Optional time range filter (e.g., "1d", "7d", "30d")
        
    Returns:
        List of matching memories with their metadata
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Prepare time filter if specified
        where_filter = None
        if time_range:
            now = datetime.datetime.now()
            
            if time_range.endswith("d"):
                days = int(time_range[:-1])
                start_date = (now - datetime.timedelta(days=days)).isoformat()
            elif time_range.endswith("h"):
                hours = int(time_range[:-1])
                start_date = (now - datetime.timedelta(hours=hours)).isoformat()
            else:
                # Default to 30 days if format is unknown
                start_date = (now - datetime.timedelta(days=30)).isoformat()
                
            where_filter = {"event_time": {"$gte": start_date}}
        
        # Query collection
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter,
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
        
        logger.info(f"Retrieved {len(memories)} episodic memories for query: {query}")
        return memories
        
    except Exception as e:
        logger.error(f"Error retrieving episodic memories: {str(e)}")
        raise

def retrieve_by_timeframe(
    start_date: str,
    end_date: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Retrieve episodic memories within a specific timeframe.
    
    Args:
        start_date: Start date in ISO format
        end_date: End date in ISO format (defaults to now)
        limit: Maximum number of results to return
        
    Returns:
        List of memories within the timeframe, sorted chronologically
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Set end date to now if not provided
        if not end_date:
            end_date = datetime.datetime.now().isoformat()
            
        # Create time filter
        where_filter = {
            "event_time": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        
        # Get memories within timeframe
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
                memories.append(memory)
        
        # Sort by event_time
        memories.sort(key=lambda x: x["metadata"].get("event_time", ""))
        
        logger.info(f"Retrieved {len(memories)} episodic memories for timeframe {start_date} to {end_date}")
        return memories
        
    except Exception as e:
        logger.error(f"Error retrieving episodic memories by timeframe: {str(e)}")
        raise

def create_session(
    session_name: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a new session to group related episodic memories.
    
    Args:
        session_name: Name of the session
        metadata: Additional metadata about the session
        
    Returns:
        Session ID
    """
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
            
        # Add standard metadata
        timestamp = datetime.datetime.now().isoformat()
        metadata.update({
            "memory_type": "episodic",
            "created_at": timestamp,
            "updated_at": timestamp,
            "event_time": timestamp,
            "is_session": True,
            "session_name": session_name,
            "session_id": session_id,
            "tags": metadata.get("tags", "") + ", session"
        })
        
        # Store in collection
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Add session marker to collection
        collection.add(
            ids=[session_id],
            documents=[f"Session: {session_name}"],
            metadatas=[metadata]
        )
        
        logger.info(f"Created session '{session_name}' with ID {session_id[:8]}...")
        return session_id
        
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise

def add_memory_to_session(
    session_id: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None
) -> str:
    """
    Add a memory to an existing session.
    
    Args:
        session_id: ID of the session to add the memory to
        content: The content to store
        metadata: Additional metadata about the memory
        tags: List of tags to categorize the memory
        
    Returns:
        ID of the stored memory
    """
    try:
        # Verify session exists
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        session = collection.get(ids=[session_id], include=["metadatas"])
        
        if not session["ids"]:
            raise ValueError(f"Session not found: {session_id}")
            
        session_metadata = session["metadatas"][0]
        session_name = session_metadata.get("session_name", "Unknown Session")
        
        # Prepare memory metadata
        if metadata is None:
            metadata = {}
            
        if tags is None:
            tags = []
            
        # Add session info to metadata
        metadata.update({
            "session_id": session_id,
            "session_name": session_name,
        })
        
        # Add session tag if not already present
        if "session" not in tags:
            tags.append("session")
            
        # Store the memory
        memory_id = store_memory(
            content=content,
            metadata=metadata,
            tags=tags,
            source=f"Session: {session_name}"
        )
        
        logger.info(f"Added memory {memory_id[:8]}... to session {session_id[:8]}...")
        return memory_id
        
    except Exception as e:
        logger.error(f"Error adding memory to session: {str(e)}")
        raise

def get_session_memories(
    session_id: str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get all memories associated with a session.
    
    Args:
        session_id: ID of the session
        limit: Maximum number of memories to retrieve
        
    Returns:
        List of memories in the session, sorted chronologically
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Create session filter
        where_filter = {"session_id": session_id}
        
        # Get memories in session
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
                memories.append(memory)
        
        # Sort by event_time
        memories.sort(key=lambda x: x["metadata"].get("event_time", ""))
        
        logger.info(f"Retrieved {len(memories)} memories for session {session_id[:8]}...")
        return memories
        
    except Exception as e:
        logger.error(f"Error retrieving session memories: {str(e)}")
        raise

def update_memory(
    memory_id: str,
    content: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Update an existing episodic memory.
    
    Args:
        memory_id: ID of the memory to update
        content: New content (if None, only metadata is updated)
        metadata: New or updated metadata
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Get existing memory
        result = collection.get(
            ids=[memory_id],
            include=["documents", "metadatas"]
        )
        
        if not result["ids"]:
            logger.warning(f"Memory not found for update: {memory_id}")
            return False
            
        existing_content = result["documents"][0]
        existing_metadata = result["metadatas"][0]
        
        # Update content if provided
        if content is not None:
            updated_content = content
        else:
            updated_content = existing_content
            
        # Update metadata
        if metadata:
            existing_metadata.update(metadata)
        
        # Always update the updated_at timestamp
        existing_metadata["updated_at"] = datetime.datetime.now().isoformat()
        
        # Update in collection
        collection.update(
            ids=[memory_id],
            documents=[updated_content],
            metadatas=[existing_metadata]
        )
        
        logger.info(f"Updated episodic memory: {memory_id[:8]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error updating episodic memory: {str(e)}")
        return False

def delete_memory(memory_id: str) -> bool:
    """
    Delete an episodic memory.
    
    Args:
        memory_id: ID of the memory to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        collection.delete(ids=[memory_id])
        
        logger.info(f"Deleted episodic memory: {memory_id[:8]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting episodic memory: {str(e)}")
        return False

def delete_session(session_id: str, delete_memories: bool = False) -> bool:
    """
    Delete a session and optionally all memories in the session.
    
    Args:
        session_id: ID of the session to delete
        delete_memories: If True, also delete all memories in the session
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Delete session memories if requested
        if delete_memories:
            # Create session filter
            where_filter = {"session_id": session_id}
            
            # Get memories in session
            results = collection.get(
                where=where_filter,
                include=["ids"]
            )
            
            if results["ids"]:
                collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} memories from session {session_id[:8]}...")
        
        # Delete the session itself
        collection.delete(ids=[session_id])
        
        logger.info(f"Deleted session: {session_id[:8]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        return False

def get_stats() -> Dict[str, Any]:
    """
    Get statistics about the episodic memory collection.
    
    Returns:
        Dictionary with statistics
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        count = collection.count()
        
        # Get sessions count
        where_filter = {"is_session": True}
        sessions = collection.get(
            where=where_filter,
            include=["ids"]
        )
        session_count = len(sessions["ids"]) if sessions["ids"] else 0
        
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
        
        return {
            "count": count,
            "session_count": session_count,
            "oldest": oldest,
            "newest": newest,
            "tags": tags
        }
        
    except Exception as e:
        logger.error(f"Error getting episodic memory stats: {str(e)}")
        return {"error": str(e), "count": 0, "session_count": 0}
