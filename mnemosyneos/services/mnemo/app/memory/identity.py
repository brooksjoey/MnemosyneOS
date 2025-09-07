"""
Identity Memory Layer for MnemosyneOS.

This module handles storage and retrieval of identity-related information,
focusing on self-model, values, rules, and personality aspects of Lucian Voss.
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

# Collection name for identity memory
COLLECTION_NAME = "identity_memory"

# Identity aspects/categories
IDENTITY_ASPECTS = [
    "core_values",
    "personality_traits",
    "preferences",
    "rules_of_conduct",
    "self_description",
    "relationships",
    "capabilities",
    "limitations",
    "background",
    "goals"
]

def initialize():
    """Initialize the identity memory collection"""
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Identity memory for Lucian's self-model and values"}
        )
        logger.info(f"Initialized identity memory collection with {collection.count()} documents")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize identity memory: {str(e)}")
        return False

def store_identity_item(
    aspect: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None
) -> str:
    """
    Store an identity item.
    
    Args:
        aspect: Identity aspect/category (e.g., "core_values", "personality_traits")
        content: The content to store
        metadata: Additional metadata about the identity item
        tags: List of tags to categorize the identity item
        
    Returns:
        ID of the stored identity item
    """
    try:
        # Generate unique ID
        identity_id = str(uuid.uuid4())
        
        # Validate aspect
        if aspect not in IDENTITY_ASPECTS:
            logger.warning(f"Unknown identity aspect: {aspect}, using 'other'")
            aspect = "other"
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add standard metadata
        timestamp = datetime.datetime.now().isoformat()
        metadata.update({
            "memory_type": "identity",
            "created_at": timestamp,
            "updated_at": timestamp,
            "aspect": aspect
        })
        
        # Add tags if provided
        if tags:
            metadata["tags"] = ", ".join(tags)
            
        # Get collection
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Add to collection
        collection.add(
            ids=[identity_id],
            documents=[content],
            metadatas=[metadata]
        )
        
        logger.info(f"Stored identity item for aspect '{aspect}': {identity_id[:8]}...")
        return identity_id
        
    except Exception as e:
        logger.error(f"Error storing identity item: {str(e)}")
        raise

def retrieve_by_aspect(
    aspect: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Retrieve identity items by aspect.
    
    Args:
        aspect: Identity aspect to retrieve
        limit: Maximum number of results to return
        
    Returns:
        List of matching identity items with their metadata
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Prepare where clause for aspect filtering
        where_filter = {"aspect": aspect}
        
        # Get items with matching aspect
        results = collection.get(
            where=where_filter,
            limit=limit,
            include=["documents", "metadatas"]
        )
        
        # Format results
        items = []
        if results["ids"]:
            for i in range(len(results["ids"])):
                item = {
                    "id": results["ids"][i],
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i],
                    "aspect": aspect
                }
                items.append(item)
        
        logger.info(f"Retrieved {len(items)} identity items for aspect: {aspect}")
        return items
        
    except Exception as e:
        logger.error(f"Error retrieving identity items by aspect: {str(e)}")
        raise

def retrieve_identity_profile() -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieve the complete identity profile across all aspects.
    
    Returns:
        Dictionary mapping aspects to lists of identity items
    """
    try:
        profile = {}
        
        for aspect in IDENTITY_ASPECTS:
            items = retrieve_by_aspect(aspect)
            profile[aspect] = items
        
        logger.info(f"Retrieved complete identity profile with {sum(len(items) for items in profile.values())} items")
        return profile
        
    except Exception as e:
        logger.error(f"Error retrieving identity profile: {str(e)}")
        raise

def search_identity(
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search identity items by content.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        List of matching identity items with their metadata
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Query collection
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        items = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                item = {
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "aspect": results["metadatas"][0][i].get("aspect", "unknown"),
                    "relevance": 1.0 - min(results["distances"][0][i], 1.0)  # Convert distance to relevance
                }
                items.append(item)
        
        logger.info(f"Retrieved {len(items)} identity items for query: {query}")
        return items
        
    except Exception as e:
        logger.error(f"Error searching identity items: {str(e)}")
        raise

def update_identity_item(
    item_id: str,
    content: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None
) -> bool:
    """
    Update an existing identity item.
    
    Args:
        item_id: ID of the identity item to update
        content: New content (if None, keep existing)
        metadata: New or updated metadata (if None, keep existing)
        tags: New tags (if None, keep existing)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Get existing identity item
        result = collection.get(
            ids=[item_id],
            include=["documents", "metadatas"]
        )
        
        if not result["ids"]:
            logger.warning(f"Identity item not found for update: {item_id}")
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
            
        if tags is not None:
            existing_metadata["tags"] = ", ".join(tags)
        
        # Always update the updated_at timestamp
        existing_metadata["updated_at"] = datetime.datetime.now().isoformat()
        
        # Update in collection
        collection.update(
            ids=[item_id],
            documents=[updated_content],
            metadatas=[existing_metadata]
        )
        
        logger.info(f"Updated identity item: {item_id[:8]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error updating identity item: {str(e)}")
        return False

def delete_identity_item(item_id: str) -> bool:
    """
    Delete an identity item.
    
    Args:
        item_id: ID of the identity item to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        collection.delete(ids=[item_id])
        
        logger.info(f"Deleted identity item: {item_id[:8]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting identity item: {str(e)}")
        return False

def update_identity(identity_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Update identity with multiple items at once.
    
    Args:
        identity_data: Dictionary mapping aspects to lists of identity items
        
    Returns:
        Dictionary mapping aspects to lists of created/updated item IDs
    """
    try:
        result_ids = {}
        
        for aspect, items in identity_data.items():
            if aspect not in IDENTITY_ASPECTS:
                logger.warning(f"Unknown identity aspect: {aspect}, skipping")
                continue
                
            # Convert single item to list for uniform processing
            if not isinstance(items, list):
                items = [items]
                
            aspect_ids = []
            
            for item in items:
                # If item is a string, treat it as content
                if isinstance(item, str):
                    content = item
                    metadata = None
                    tags = None
                # If item is a dictionary, extract content, metadata, tags
                elif isinstance(item, dict):
                    content = item.get("content", "")
                    metadata = item.get("metadata")
                    tags = item.get("tags")
                else:
                    logger.warning(f"Invalid identity item format for aspect {aspect}, skipping")
                    continue
                    
                # Store the identity item
                item_id = store_identity_item(
                    aspect=aspect,
                    content=content,
                    metadata=metadata,
                    tags=tags
                )
                
                aspect_ids.append(item_id)
                
            result_ids[aspect] = aspect_ids
            
        logger.info(f"Updated identity with {sum(len(ids) for ids in result_ids.values())} items")
        return result_ids
        
    except Exception as e:
        logger.error(f"Error updating identity: {str(e)}")
        raise

def get_identity_json() -> Dict[str, Any]:
    """
    Get a JSON representation of the identity profile.
    
    Returns:
        Dictionary with the identity profile
    """
    try:
        profile = retrieve_identity_profile()
        
        # Convert to simplified JSON format
        json_profile = {}
        
        for aspect, items in profile.items():
            json_profile[aspect] = [item["content"] for item in items]
            
        return json_profile
        
    except Exception as e:
        logger.error(f"Error getting identity JSON: {str(e)}")
        raise

def get_stats() -> Dict[str, Any]:
    """
    Get statistics about the identity memory collection.
    
    Returns:
        Dictionary with statistics
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        count = collection.count()
        
        # Get counts by aspect
        aspect_counts = {}
        for aspect in IDENTITY_ASPECTS:
            where_filter = {"aspect": aspect}
            results = collection.get(
                where=where_filter,
                include=["ids"]
            )
            aspect_counts[aspect] = len(results["ids"]) if results["ids"] else 0
        
        # Get oldest and newest identity items
        all_metadatas = []
        
        # Get items in batches to avoid loading everything at once
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
            "oldest": oldest,
            "newest": newest,
            "aspect_counts": aspect_counts,
            "tags": tags
        }
        
    except Exception as e:
        logger.error(f"Error getting identity memory stats: {str(e)}")
        return {"error": str(e), "count": 0}
