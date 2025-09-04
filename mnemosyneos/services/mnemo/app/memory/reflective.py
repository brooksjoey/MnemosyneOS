"""
Reflective Memory Layer for MnemosyneOS.

This module handles generation and retrieval of reflections,
which are higher-level insights derived from analyzing other memories.
"""
import os
import uuid
import datetime
import json
from typing import List, Dict, Any, Optional, Tuple, Union

from app import logging_setup
from app.config import settings
from app.store import chroma
from app.memory import episodic, semantic, procedural
from app.llm import provider

# Initialize logger
logger = logging_setup.get_logger()

# Collection name for reflective memory
COLLECTION_NAME = "reflective_memory"

def initialize():
    """Initialize the reflective memory collection"""
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Reflective memory for insights and lessons learned"}
        )
        logger.info(f"Initialized reflective memory collection with {collection.count()} documents")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize reflective memory: {str(e)}")
        return False

def store_reflection(
    content: str,
    source_memories: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None
) -> str:
    """
    Store a reflection.
    
    Args:
        content: The reflection content
        source_memories: List of memory IDs that were used to generate this reflection
        metadata: Additional metadata about the reflection
        tags: List of tags to categorize the reflection
        
    Returns:
        ID of the stored reflection
    """
    try:
        # Generate unique ID
        reflection_id = str(uuid.uuid4())
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add standard metadata
        timestamp = datetime.datetime.now().isoformat()
        metadata.update({
            "memory_type": "reflective",
            "created_at": timestamp,
            "updated_at": timestamp,
        })
        
        # Add source memories if provided
        if source_memories:
            metadata["source_memories"] = json.dumps(source_memories)
            
        # Add tags if provided
        if tags:
            metadata["tags"] = ", ".join(tags)
            
        # Get collection
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Add to collection
        collection.add(
            ids=[reflection_id],
            documents=[content],
            metadatas=[metadata]
        )
        
        logger.info(f"Stored reflection: {reflection_id[:8]}...")
        return reflection_id
        
    except Exception as e:
        logger.error(f"Error storing reflection: {str(e)}")
        raise

def retrieve_reflections(
    query: str,
    limit: int = 10,
    time_range: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve reflections based on a query.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        time_range: Optional time range filter (e.g., "1d", "7d", "30d")
        
    Returns:
        List of matching reflections with their metadata
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
                
            where_filter = {"created_at": {"$gte": start_date}}
        
        # Query collection
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        reflections = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                reflection = {
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "relevance": 1.0 - min(results["distances"][0][i], 1.0)  # Convert distance to relevance
                }
                
                # Parse source memories if present
                if "source_memories" in reflection["metadata"]:
                    try:
                        source_memories = json.loads(reflection["metadata"]["source_memories"])
                        reflection["source_memories"] = source_memories
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse source memories for reflection: {reflection['id']}")
                
                reflections.append(reflection)
        
        logger.info(f"Retrieved {len(reflections)} reflections for query: {query}")
        return reflections
        
    except Exception as e:
        logger.error(f"Error retrieving reflections: {str(e)}")
        raise

def retrieve_by_tags(
    tags: List[str],
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Retrieve reflections by tags.
    
    Args:
        tags: List of tags to filter by
        limit: Maximum number of results to return
        
    Returns:
        List of matching reflections with their metadata
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Prepare where clause for tag filtering
        where_filter = None
        if tags:
            # For each tag, check if it's in the tags metadata field
            where_filter = {}
            for tag in tags:
                where_filter[f"tags"] = {"$contains": tag}
        
        # Get reflections with matching tags
        results = collection.get(
            where=where_filter,
            limit=limit,
            include=["documents", "metadatas"]
        )
        
        # Format results
        reflections = []
        if results["ids"]:
            for i in range(len(results["ids"])):
                reflection = {
                    "id": results["ids"][i],
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i]
                }
                
                # Parse source memories if present
                if "source_memories" in reflection["metadata"]:
                    try:
                        source_memories = json.loads(reflection["metadata"]["source_memories"])
                        reflection["source_memories"] = source_memories
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse source memories for reflection: {reflection['id']}")
                
                reflections.append(reflection)
        
        logger.info(f"Retrieved {len(reflections)} reflections for tags: {tags}")
        return reflections
        
    except Exception as e:
        logger.error(f"Error retrieving reflections by tags: {str(e)}")
        raise

def generate_reflections(
    query: Optional[str] = None,
    time_range: Optional[str] = None,
    tags: Optional[List[str]] = None,
    max_source_memories: int = 10
) -> List[Dict[str, Any]]:
    """
    Generate new reflections by analyzing existing memories.
    
    Args:
        query: Optional query to filter memories to reflect on
        time_range: Optional time range to filter memories (e.g., "1d", "7d", "30d")
        tags: Optional list of tags to filter memories
        max_source_memories: Maximum number of source memories to consider
        
    Returns:
        List of generated reflections
    """
    try:
        # Step 1: Retrieve relevant memories to reflect on
        source_memories = _get_memories_for_reflection(query, time_range, tags, max_source_memories)
        
        if not source_memories:
            logger.warning("No memories found to generate reflections")
            return []
            
        logger.info(f"Found {len(source_memories)} memories for reflection generation")
        
        # Step 2: Generate reflections using LLM
        reflection_results = _generate_reflections_with_llm(source_memories)
        
        # Step 3: Store the generated reflections
        stored_reflections = []
        for reflection in reflection_results:
            reflection_id = store_reflection(
                content=reflection["content"],
                source_memories=reflection["source_memory_ids"],
                metadata={"query": query} if query else {},
                tags=reflection.get("tags", []) + (tags or [])
            )
            
            reflection["id"] = reflection_id
            stored_reflections.append(reflection)
            
        logger.info(f"Generated and stored {len(stored_reflections)} reflections")
        return stored_reflections
        
    except Exception as e:
        logger.error(f"Error generating reflections: {str(e)}")
        raise

def _get_memories_for_reflection(
    query: Optional[str],
    time_range: Optional[str],
    tags: Optional[List[str]],
    max_memories: int
) -> List[Dict[str, Any]]:
    """
    Get memories to use as sources for reflection generation.
    
    Args:
        query: Optional query to filter memories
        time_range: Optional time range to filter memories
        tags: Optional list of tags to filter memories
        max_memories: Maximum number of memories to retrieve
        
    Returns:
        List of memories to reflect on
    """
    all_memories = []
    
    # If query is provided, use it to retrieve memories
    if query:
        # Get episodic memories
        episodic_results = episodic.retrieve_memories(query, max_memories // 3, time_range)
        for memory in episodic_results:
            memory["memory_type"] = "episodic"
            all_memories.append(memory)
            
        # Get semantic memories
        semantic_results = semantic.retrieve_memories(query, max_memories // 3)
        for memory in semantic_results:
            memory["memory_type"] = "semantic"
            all_memories.append(memory)
            
        # Get procedural memories
        procedural_results = procedural.retrieve_memories(query, max_memories // 3)
        for memory in procedural_results:
            memory["memory_type"] = "procedural"
            all_memories.append(memory)
    
    # If tags are provided but no query, filter by tags
    elif tags:
        # Filter episodic memories by tags
        # This is a simplified approach, as each memory layer might have different tag filtering capabilities
        # For a more robust solution, each memory layer would need a retrieve_by_tags method
        client = chroma.get_client()
        
        # For each memory type, get memories with the specified tags
        for memory_type, collection_name in [
            ("episodic", "episodic_memory"),
            ("semantic", "semantic_memory"),
            ("procedural", "procedural_memory")
        ]:
            collection = client.get_or_create_collection(name=collection_name)
            
            # Prepare where clause for tag filtering
            where_filter = {}
            for tag in tags:
                where_filter["tags"] = {"$contains": tag}
                
            # Add time range filter if specified
            if time_range:
                now = datetime.datetime.now()
                
                if time_range.endswith("d"):
                    days = int(time_range[:-1])
                    start_date = (now - datetime.timedelta(days=days)).isoformat()
                elif time_range.endswith("h"):
                    hours = int(time_range[:-1])
                    start_date = (now - datetime.timedelta(hours=hours)).isoformat()
                else:
                    start_date = (now - datetime.timedelta(days=30)).isoformat()
                    
                if memory_type == "episodic":
                    where_filter["event_time"] = {"$gte": start_date}
                else:
                    where_filter["created_at"] = {"$gte": start_date}
            
            # Get memories with matching tags
            results = collection.get(
                where=where_filter,
                limit=max_memories // 3,
                include=["ids", "documents", "metadatas"]
            )
            
            # Format results
            if results["ids"]:
                for i in range(len(results["ids"])):
                    memory = {
                        "id": results["ids"][i],
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i],
                        "memory_type": memory_type
                    }
                    all_memories.append(memory)
    
    # If neither query nor tags, get recent memories
    else:
        # Get recent episodic memories
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=7)  # Last week by default
        
        episodic_results = episodic.retrieve_by_timeframe(
            start_date=start_date.isoformat(),
            limit=max_memories // 2
        )
        
        for memory in episodic_results:
            memory["memory_type"] = "episodic"
            all_memories.append(memory)
            
        # Get some random semantic and procedural memories
        # This is a simplified approach - a more robust solution would
        # have a way to get recent or important memories from each layer
        client = chroma.get_client()
        
        for memory_type, collection_name in [
            ("semantic", "semantic_memory"),
            ("procedural", "procedural_memory")
        ]:
            collection = client.get_or_create_collection(name=collection_name)
            
            # Get a sample of memories
            results = collection.get(
                limit=max_memories // 4,
                include=["ids", "documents", "metadatas"]
            )
            
            # Format results
            if results["ids"]:
                for i in range(len(results["ids"])):
                    memory = {
                        "id": results["ids"][i],
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i],
                        "memory_type": memory_type
                    }
                    all_memories.append(memory)
    
    # Sort and limit the results
    # For now, we'll just take the first max_memories, but a more
    # sophisticated approach would prioritize based on relevance, recency, etc.
    return all_memories[:max_memories]

def _generate_reflections_with_llm(
    source_memories: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Generate reflections using the LLM provider.
    
    Args:
        source_memories: List of memories to generate reflections from
        
    Returns:
        List of generated reflections with metadata
    """
    # Group memories by type for easier processing
    memories_by_type = {}
    for memory in source_memories:
        memory_type = memory.get("memory_type", "unknown")
        if memory_type not in memories_by_type:
            memories_by_type[memory_type] = []
        memories_by_type[memory_type].append(memory)
    
    # Create a context summary for the LLM
    context_summary = "I'll analyze the following memories and generate insightful reflections:\n\n"
    
    memory_texts = []
    memory_ids = []
    
    for memory_type, memories in memories_by_type.items():
        context_summary += f"## {memory_type.capitalize()} Memories ({len(memories)}):\n"
        
        for i, memory in enumerate(memories):
            context_summary += f"{i+1}. "
            if memory_type == "episodic":
                event_time = memory["metadata"].get("event_time", "Unknown time")
                context_summary += f"[{event_time}] {memory['content'][:200]}...\n"
            elif memory_type == "procedural":
                title = memory["metadata"].get("title", "Unnamed procedure")
                context_summary += f"Procedure: {title} - {memory['content'][:200]}...\n"
            else:
                context_summary += f"{memory['content'][:200]}...\n"
            
            memory_texts.append(memory["content"])
            memory_ids.append(memory["id"])
    
    # Create the prompt for reflection generation
    prompt = f"""
You are the reflection system for MnemosyneOS, tasked with generating valuable insights
from memory patterns. Analyze the provided memories and generate 1-3 thoughtful reflections.

{context_summary}

For each reflection, provide:
1. A clear, insightful observation that connects multiple memories or identifies patterns
2. Supporting evidence from the specific memories
3. Implications or lessons learned
4. Relevant tags (2-5 tags that categorize this reflection)

Format each reflection as follows:
REFLECTION:
[Your reflection text here - be thoughtful, insightful, and connect ideas across memories]

EVIDENCE:
[Cite specific evidence from the memories that supports this reflection]

IMPLICATIONS:
[Describe the implications or lessons learned from this reflection]

TAGS:
[List 2-5 relevant tags, separated by commas]

---
"""

    # Call the LLM provider to generate reflections
    try:
        llm = provider.get_llm()
        response = llm.generate_text(prompt)
        
        # Parse the response into individual reflections
        reflections = _parse_reflection_response(response, memory_ids)
        
        logger.info(f"Generated {len(reflections)} reflections from LLM")
        return reflections
        
    except Exception as e:
        logger.error(f"Error generating reflections with LLM: {str(e)}")
        # Return a simple reflection about the error
        return [{
            "content": f"Error generating reflections: {str(e)}",
            "source_memory_ids": memory_ids,
            "tags": ["error", "reflection_generation"]
        }]

def _parse_reflection_response(
    response: str,
    memory_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Parse the LLM response into structured reflections.
    
    Args:
        response: The raw LLM response text
        memory_ids: List of memory IDs that were used as sources
        
    Returns:
        List of parsed reflections
    """
    reflections = []
    
    # Split the response into individual reflections (separated by ---)
    raw_reflections = response.split("---")
    
    for raw_reflection in raw_reflections:
        if not raw_reflection.strip():
            continue
            
        # Extract the main sections
        sections = {}
        current_section = None
        current_content = []
        
        for line in raw_reflection.split("\n"):
            line = line.strip()
            
            if not line:
                continue
                
            if line in ["REFLECTION:", "EVIDENCE:", "IMPLICATIONS:", "TAGS:"]:
                # If we were already in a section, save its content
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                    
                # Start new section
                current_section = line.replace(":", "").lower()
                current_content = []
            elif current_section:
                current_content.append(line)
                
        # Save the last section
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content)
            
        # Skip if no reflection content
        if "reflection" not in sections:
            continue
            
        # Format the reflection content
        content = sections.get("reflection", "")
        
        if "evidence" in sections:
            content += f"\n\nEvidence:\n{sections['evidence']}"
            
        if "implications" in sections:
            content += f"\n\nImplications:\n{sections['implications']}"
            
        # Extract tags
        tags = []
        if "tags" in sections:
            tags_text = sections["tags"]
            tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
            
        # Add to reflections
        reflections.append({
            "content": content,
            "source_memory_ids": memory_ids,
            "tags": tags
        })
    
    # If no reflections were parsed successfully, create a default one
    if not reflections:
        reflections.append({
            "content": "Reflection generated from analyzing recent memories. No specific patterns identified.",
            "source_memory_ids": memory_ids,
            "tags": ["general", "reflection"]
        })
        
    return reflections

def update_reflection(
    reflection_id: str,
    content: Optional[str] = None,
    source_memories: Optional[List[str]] = None,
    tags: Optional[List[str]] = None
) -> bool:
    """
    Update an existing reflection.
    
    Args:
        reflection_id: ID of the reflection to update
        content: New content (if None, keep existing)
        source_memories: New source memory IDs (if None, keep existing)
        tags: New tags (if None, keep existing)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Get existing reflection
        result = collection.get(
            ids=[reflection_id],
            include=["documents", "metadatas"]
        )
        
        if not result["ids"]:
            logger.warning(f"Reflection not found for update: {reflection_id}")
            return False
            
        existing_content = result["documents"][0]
        existing_metadata = result["metadatas"][0]
        
        # Update content if provided
        if content is not None:
            updated_content = content
        else:
            updated_content = existing_content
            
        # Update metadata
        if source_memories is not None:
            existing_metadata["source_memories"] = json.dumps(source_memories)
            
        if tags is not None:
            existing_metadata["tags"] = ", ".join(tags)
        
        # Always update the updated_at timestamp
        existing_metadata["updated_at"] = datetime.datetime.now().isoformat()
        
        # Update in collection
        collection.update(
            ids=[reflection_id],
            documents=[updated_content],
            metadatas=[existing_metadata]
        )
        
        logger.info(f"Updated reflection: {reflection_id[:8]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error updating reflection: {str(e)}")
        return False

def delete_reflection(reflection_id: str) -> bool:
    """
    Delete a reflection.
    
    Args:
        reflection_id: ID of the reflection to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        collection.delete(ids=[reflection_id])
        
        logger.info(f"Deleted reflection: {reflection_id[:8]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting reflection: {str(e)}")
        return False

def get_stats() -> Dict[str, Any]:
    """
    Get statistics about the reflective memory collection.
    
    Returns:
        Dictionary with statistics
    """
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        count = collection.count()
        
        # Get oldest and newest reflections
        all_metadatas = []
        
        # Get reflections in batches to avoid loading everything at once
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
        
        # Get source memory types
        source_types = {"episodic": 0, "semantic": 0, "procedural": 0}
        
        for metadata in all_metadatas:
            if "source_memories" in metadata:
                try:
                    source_memories = json.loads(metadata["source_memories"])
                    for memory_id in source_memories:
                        # Extract memory type from ID (if available)
                        # This is a simplified approach and may not be accurate
                        # A more robust solution would track source types directly
                        if memory_id.startswith("ep_"):
                            source_types["episodic"] += 1
                        elif memory_id.startswith("sem_"):
                            source_types["semantic"] += 1
                        elif memory_id.startswith("proc_"):
                            source_types["procedural"] += 1
                except json.JSONDecodeError:
                    pass
        
        return {
            "count": count,
            "oldest": oldest,
            "newest": newest,
            "tags": tags,
            "source_types": source_types
        }
        
    except Exception as e:
        logger.error(f"Error getting reflective memory stats: {str(e)}")
        return {"error": str(e), "count": 0}
