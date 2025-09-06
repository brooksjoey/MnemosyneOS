"""
Affective Memory Layer for MnemosyneOS.

This module handles storage and retrieval of affective memories,
focusing on emotional valence, sentiment, and feeling associated with memories.
"""
import os
import uuid
import datetime
import json
from typing import List, Dict, Any, Optional, Tuple, Union

from app import logging_setup
from app.config import settings
from app.store import chroma
from app.llm import provider

# Initialize logger
logger = logging_setup.get_logger()

# Collection name for affective memory
COLLECTION_NAME = "affective_memory"

def initialize():
    """Initialize the affective memory collection"""
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Affective memory for emotional content and valence"}
        )
        logger.info(f"Initialized affective memory collection with {collection.count()} documents")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize affective memory: {str(e)}")
        return False

def tag_content(
    content: str,
    tags: List[str],
    valence: float = 0.0,
    metadata: Optional[Dict[str, Any]] = None,
    source: Optional[str] = None
) -> str:
    """
    Tag content with affect information.
    
    Args:
        content: The content to tag
        tags: List of emotional tags (e.g., "joy", "anger", "fear")
        valence: Emotional valence score (-1.0 to 1.0, where -1 is negative, 0 is neutral, 1 is positive)
        metadata: Additional metadata about the content
        source: Source of the content
        
    Returns:
        ID of the stored affect item
    """
    try:
        # Generate unique ID
        affect_id = str(uuid.uuid4())
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add standard metadata
        timestamp = datetime.datetime.now().isoformat()
        metadata.update({
            "memory_type": "affective",
            "created_at": timestamp,
            "updated_at": timestamp,
            "valence": float(valence)  # Ensure valence is stored as float
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
            ids=[affect_id],
            documents=[content],
            metadatas=[metadata]
        )
        
        logger.info(f"Tagged content with affect: {affect_id[:8]}...")
        return affect_id
        
    except Exception as e:
        logger.error(f"Error tagging content with affect: {str(e)}")
        raise

def analyze_content(content: str) -> Dict[str, Any]:
    """
    Analyze content to extract emotional information using LLM.
    
    Args:
        content: The content to analyze
        
    Returns:
        Dictionary with emotional analysis
    """
    try:
        llm = provider.get_llm()
        
        prompt = f"""
Analyze the emotional content of the following text. Identify the emotions present, 
the overall emotional valence (positive, negative, or neutral), and the intensity 
of emotions (on a scale of 1-10). Format your response as JSON with these keys:
- emotions: array of emotion labels (e.g., "joy", "anger", "sadness", "fear", "surprise")
- valence: float between -1.0 (very negative) and 1.0 (very positive)
- intensity: integer between 1 (low intensity) and 10 (high intensity)
- summary: brief description of the emotional content

Here's the text to analyze:

{content}

JSON response:
"""
        
        response = llm.generate_text(prompt)
        
        # Parse JSON from response
        try:
            result = json.loads(response)
            
            # Validate and sanitize the result
            if "emotions" not in result or not isinstance(result["emotions"], list):
                result["emotions"] = []
                
            if "valence" not in result or not isinstance(result["valence"], (int, float)):
                result["valence"] = 0.0
            else:
                # Ensure valence is between -1.0 and 1.0
                result["valence"] = max(-1.0, min(1.0, float(result["valence"])))
                
            if "intensity" not in result or not isinstance(result["intensity"], (int, float)):
                result["intensity"] = 5
            else:
                # Ensure intensity is between 1 and 10
                result["intensity"] = max(1, min(10, int(result["intensity"])))
                
            if "summary" not in result or not isinstance(result["summary"], str):
                result["summary"] = "No emotional summary available."
                
            logger.info(f"Analyzed content emotion: {result['emotions']}, valence: {result['valence']}")
            return result
            
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse LLM response as JSON: {response[:100]}...")
            return {
                "emotions": [],
                "valence": 0.0,
                "intensity": 5,
                "summary": "Failed to analyze emotional content."
            }
            
    except Exception as e:
        logger.error(f"Error analyzing content emotion: {str(e)}")
        return {
            "emotions": [],
            "valence": 0.0,
            "intensity": 5,
            "summary": f"Error in emotional analysis: {str(e)}"
        }

def tag_content_auto(
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    source: Optional[str] = None
) -> Dict[str, Any]:
    """
    Automatically analyze and tag content with emotional information.
    
    Args:
        content: The content to analyze and tag
        metadata: Additional metadata about the content
        source: Source of the content
        
    Returns:
        Dictionary with the affect ID and analysis results
    """
    try:
        # Analyze the content
        analysis = analyze_content(content)
        
        # Extract tags and valence
        tags = analysis.get("emotions", [])
        valence = analysis.get("valence", 0.0)
        
        # Add analysis to metadata
        if metadata is None:
            metadata = {}
            
        metadata.update({
            "emotional_analysis": json.dumps(analysis),
            "intensity": analysis.get("intensity", 5)
        })
        
        # Tag the content
        affect_id = tag_content(
            content=content,
            tags=tags,
            valence=valence,
            metadata=metadata,
            source=source
        )
        
        # Return the results
        return {
            "id": affect_id,
            "analysis": analysis,
            "tags": tags,
            "valence": valence
        }
        
    except Exception as e:
        logger.error(f"Error auto-tagging content: {str(e)}")
        raise

def retrieve_by_emotion(
    emotion: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Retrieve content by specific emotion tag.
    
    Args:
        emotion: Emotion tag to search for
        limit: Maximum number of results to return
        
    Returns:
        List of matching affect items with their metadata
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Prepare where clause for emotion filtering
        where_filter = {"tags": {"$contains": emotion}}
        
        # Get items with matching emotion
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
                    "metadata": results["metadatas"][i]
                }
                
                # Extract valence
                valence = item["metadata"].get("valence", 0.0)
                item["valence"] = float(valence)
                
                # Parse emotional analysis if present
                if "emotional_analysis" in item["metadata"]:
                    try:
                        analysis = json.loads(item["metadata"]["emotional_analysis"])
                        item["analysis"] = analysis
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse emotional analysis for item: {item['id']}")
                
                items.append(item)
        
        logger.info(f"Retrieved {len(items)} affect items for emotion: {emotion}")
        return items
        
    except Exception as e:
        logger.error(f"Error retrieving affect items by emotion: {str(e)}")
        raise

def retrieve_by_valence(
    min_valence: float,
    max_valence: float = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Retrieve content by valence range.
    
    Args:
        min_valence: Minimum valence value
        max_valence: Maximum valence value (if None, equal to min_valence)
        limit: Maximum number of results to return
        
    Returns:
        List of matching affect items with their metadata
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # If max_valence not provided, set equal to min_valence for exact match
        if max_valence is None:
            max_valence = min_valence
            
        # Ensure values are within valid range
        min_valence = max(-1.0, min(1.0, min_valence))
        max_valence = max(-1.0, min(1.0, max_valence))
        
        # Prepare where clause for valence filtering
        where_filter = {"valence": {"$gte": min_valence, "$lte": max_valence}}
        
        # Get items with matching valence
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
                    "metadata": results["metadatas"][i]
                }
                
                # Extract valence
                valence = item["metadata"].get("valence", 0.0)
                item["valence"] = float(valence)
                
                # Parse emotional analysis if present
                if "emotional_analysis" in item["metadata"]:
                    try:
                        analysis = json.loads(item["metadata"]["emotional_analysis"])
                        item["analysis"] = analysis
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse emotional analysis for item: {item['id']}")
                
                items.append(item)
        
        logger.info(f"Retrieved {len(items)} affect items for valence range: {min_valence} to {max_valence}")
        return items
        
    except Exception as e:
        logger.error(f"Error retrieving affect items by valence: {str(e)}")
        raise

def search_affect(
    query: str,
    limit: int = 10,
    min_valence: Optional[float] = None,
    max_valence: Optional[float] = None,
    emotions: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Search affect items by content and optional filters.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        min_valence: Minimum valence value
        max_valence: Maximum valence value
        emotions: List of emotions to filter by
        
    Returns:
        List of matching affect items with their metadata
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Prepare where clause for filtering
        where_filter = None
        
        # Add valence filter if provided
        if min_valence is not None or max_valence is not None:
            where_filter = where_filter or {}
            where_filter["valence"] = {}
            
            if min_valence is not None:
                where_filter["valence"]["$gte"] = max(-1.0, min(1.0, min_valence))
                
            if max_valence is not None:
                where_filter["valence"]["$lte"] = max(-1.0, min(1.0, max_valence))
        
        # Add emotion filter if provided
        if emotions and len(emotions) > 0:
            # We can only filter by one emotion at a time with Chroma's simple query language
            # So we'll post-filter for multiple emotions
            where_filter = where_filter or {}
            where_filter["tags"] = {"$contains": emotions[0]}
        
        # Query collection
        results = collection.query(
            query_texts=[query],
            n_results=limit * 2 if emotions and len(emotions) > 1 else limit,  # Get extra results for post-filtering
            where=where_filter,
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
                    "relevance": 1.0 - min(results["distances"][0][i], 1.0)  # Convert distance to relevance
                }
                
                # Extract valence
                valence = item["metadata"].get("valence", 0.0)
                item["valence"] = float(valence)
                
                # Parse emotional analysis if present
                if "emotional_analysis" in item["metadata"]:
                    try:
                        analysis = json.loads(item["metadata"]["emotional_analysis"])
                        item["analysis"] = analysis
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse emotional analysis for item: {item['id']}")
                
                # Post-filter for multiple emotions if needed
                if emotions and len(emotions) > 1:
                    tags = item["metadata"].get("tags", "").split(", ")
                    if all(emotion in tags for emotion in emotions):
                        items.append(item)
                else:
                    items.append(item)
        
        # Limit results after post-filtering
        items = items[:limit]
        
        logger.info(f"Retrieved {len(items)} affect items for query: {query}")
        return items
        
    except Exception as e:
        logger.error(f"Error searching affect items: {str(e)}")
        raise

def get_affect_feed(
    tag: Optional[str] = None,
    valence_range: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Get a feed of affect-filtered content.
    
    Args:
        tag: Optional emotion tag to filter by
        valence_range: Optional valence range in format "min:max" (e.g., "-0.5:0.8")
        limit: Maximum number of results to return
        
    Returns:
        List of affect items matching the filters
    """
    try:
        # Parse valence range if provided
        min_valence = None
        max_valence = None
        
        if valence_range:
            try:
                parts = valence_range.split(":")
                if len(parts) == 2:
                    min_valence = float(parts[0])
                    max_valence = float(parts[1])
                elif len(parts) == 1:
                    # If only one value, use it as both min and max
                    min_valence = max_valence = float(parts[0])
            except ValueError:
                logger.warning(f"Invalid valence range format: {valence_range}")
        
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Prepare where clause for filtering
        where_filter = {}
        
        # Add tag filter if provided
        if tag:
            where_filter["tags"] = {"$contains": tag}
            
        # Add valence filter if provided
        if min_valence is not None and max_valence is not None:
            where_filter["valence"] = {
                "$gte": max(-1.0, min(1.0, min_valence)),
                "$lte": max(-1.0, min(1.0, max_valence))
            }
        
        # Get items with matching filters
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
                    "metadata": results["metadatas"][i]
                }
                
                # Extract valence
                valence = item["metadata"].get("valence", 0.0)
                item["valence"] = float(valence)
                
                # Parse emotional analysis if present
                if "emotional_analysis" in item["metadata"]:
                    try:
                        analysis = json.loads(item["metadata"]["emotional_analysis"])
                        item["analysis"] = analysis
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse emotional analysis for item: {item['id']}")
                
                items.append(item)
        
        # Sort by created_at if available
        items.sort(
            key=lambda x: x["metadata"].get("created_at", ""),
            reverse=True  # Most recent first
        )
        
        logger.info(f"Retrieved {len(items)} items for affect feed")
        return items
        
    except Exception as e:
        logger.error(f"Error getting affect feed: {str(e)}")
        raise

def get_emotion_stats() -> Dict[str, Any]:
    """
    Get statistics about emotions in the affect memory.
    
    Returns:
        Dictionary with emotion statistics
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        count = collection.count()
        if count == 0:
            return {"count": 0, "emotions": {}, "valence_distribution": {}}
        
        # Get all metadatas
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
        
        # Get emotion distribution
        emotions = {}
        for metadata in all_metadatas:
            if "tags" in metadata:
                for tag in metadata["tags"].split(", "):
                    if tag:  # Skip empty tags
                        emotions[tag] = emotions.get(tag, 0) + 1
        
        # Get valence distribution
        valence_bins = {
            "very_negative": 0,  # -1.0 to -0.6
            "negative": 0,       # -0.6 to -0.2
            "slightly_negative": 0,  # -0.2 to -0.0
            "neutral": 0,        # 0.0
            "slightly_positive": 0,  # 0.0 to 0.2
            "positive": 0,       # 0.2 to 0.6
            "very_positive": 0   # 0.6 to 1.0
        }
        
        for metadata in all_metadatas:
            valence = float(metadata.get("valence", 0.0))
            
            if valence < -0.6:
                valence_bins["very_negative"] += 1
            elif valence < -0.2:
                valence_bins["negative"] += 1
            elif valence < 0.0:
                valence_bins["slightly_negative"] += 1
            elif valence == 0.0:
                valence_bins["neutral"] += 1
            elif valence <= 0.2:
                valence_bins["slightly_positive"] += 1
            elif valence <= 0.6:
                valence_bins["positive"] += 1
            else:
                valence_bins["very_positive"] += 1
        
        return {
            "count": count,
            "emotions": emotions,
            "valence_distribution": valence_bins
        }
        
    except Exception as e:
        logger.error(f"Error getting emotion stats: {str(e)}")
        return {"error": str(e), "count": 0}

def delete_affect(affect_id: str) -> bool:
    """
    Delete an affect item.
    
    Args:
        affect_id: ID of the affect item to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        collection.delete(ids=[affect_id])
        
        logger.info(f"Deleted affect item: {affect_id[:8]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting affect item: {str(e)}")
        return False

def update_affect(
    affect_id: str,
    content: Optional[str] = None,
    tags: Optional[List[str]] = None,
    valence: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Update an existing affect item.
    
    Args:
        affect_id: ID of the affect item to update
        content: New content (if None, keep existing)
        tags: New emotion tags (if None, keep existing)
        valence: New valence value (if None, keep existing)
        metadata: New or updated metadata (if None, keep existing)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Get existing affect item
        result = collection.get(
            ids=[affect_id],
            include=["documents", "metadatas"]
        )
        
        if not result["ids"]:
            logger.warning(f"Affect item not found for update: {affect_id}")
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
            
        if valence is not None:
            existing_metadata["valence"] = max(-1.0, min(1.0, float(valence)))
        
        # Always update the updated_at timestamp
        existing_metadata["updated_at"] = datetime.datetime.now().isoformat()
        
        # Update in collection
        collection.update(
            ids=[affect_id],
            documents=[updated_content],
            metadatas=[existing_metadata]
        )
        
        logger.info(f"Updated affect item: {affect_id[:8]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error updating affect item: {str(e)}")
        return False

def get_stats() -> Dict[str, Any]:
    """
    Get statistics about the affective memory collection.
    
    Returns:
        Dictionary with statistics
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        count = collection.count()
        
        # Get emotion stats
        emotion_stats = get_emotion_stats()
        
        # Get oldest and newest affect items
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
        
        # Calculate average valence
        valences = [float(m.get("valence", 0.0)) for m in all_metadatas]
        avg_valence = sum(valences) / len(valences) if valences else 0.0
        
        return {
            "count": count,
            "oldest": oldest,
            "newest": newest,
            "avg_valence": avg_valence,
            "emotions": emotion_stats.get("emotions", {}),
            "valence_distribution": emotion_stats.get("valence_distribution", {})
        }
        
    except Exception as e:
        logger.error(f"Error getting affective memory stats: {str(e)}")
        return {"error": str(e), "count": 0}
