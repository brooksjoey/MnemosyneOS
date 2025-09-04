"""
Meta Memory Layer for MnemosyneOS.

This module handles meta-operations across all memory layers,
including statistics, compaction, reindexing, and system-wide operations.
"""
import os
import datetime
import json
from typing import List, Dict, Any, Optional, Set, Tuple

from app import logging_setup
from app.config import settings
from app.store import chroma
from app.memory import (
    semantic, episodic, procedural, reflective, 
    affective, identity
)

# Initialize logger
logger = logging_setup.get_logger()

# Collection name for meta memory
COLLECTION_NAME = "meta_memory"

# Memory types and their modules
MEMORY_MODULES = {
    "semantic": semantic,
    "episodic": episodic,
    "procedural": procedural,
    "reflective": reflective,
    "affective": affective,
    "identity": identity
}

def initialize():
    """Initialize the meta memory collection"""
    try:
        client = chroma.get_client()
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Meta memory for system statistics and operations"}
        )
        logger.info(f"Initialized meta memory collection with {collection.count()} documents")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize meta memory: {str(e)}")
        return False

def get_stats():
    """
    Get statistics across all memory layers.
    
    Returns:
        Dictionary with combined statistics
    """
    try:
        stats = {
            "timestamp": datetime.datetime.now().isoformat(),
            "memory_layers": {}
        }
        
        total_count = 0
        
        # Get stats from each memory module
        for memory_type, module in MEMORY_MODULES.items():
            try:
                memory_stats = module.get_stats()
                stats["memory_layers"][memory_type] = memory_stats
                total_count += memory_stats.get("count", 0)
            except Exception as e:
                logger.error(f"Error getting stats for {memory_type} memory: {str(e)}")
                stats["memory_layers"][memory_type] = {"error": str(e), "count": 0}
        
        # Add total count
        stats["total_memory_count"] = total_count
        
        # Add system stats
        stats["system"] = _get_system_stats()
        
        logger.info(f"Retrieved stats across all memory layers: {total_count} total memories")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting combined stats: {str(e)}")
        return {"error": str(e), "timestamp": datetime.datetime.now().isoformat()}

def _get_system_stats():
    """
    Get system-level statistics.
    
    Returns:
        Dictionary with system statistics
    """
    try:
        stats = {}
        
        # Get ChromaDB statistics
        try:
            client = chroma.get_client()
            collections = client.list_collections()
            
            collection_stats = []
            total_embeddings = 0
            
            for collection in collections:
                try:
                    count = collection.count()
                    total_embeddings += count
                    collection_stats.append({
                        "name": collection.name,
                        "count": count
                    })
                except Exception as e:
                    logger.error(f"Error getting stats for collection {collection.name}: {str(e)}")
            
            stats["chroma"] = {
                "collections": collection_stats,
                "total_embeddings": total_embeddings
            }
            
        except Exception as e:
            logger.error(f"Error getting ChromaDB stats: {str(e)}")
            stats["chroma"] = {"error": str(e)}
        
        # Get disk usage statistics
        try:
            chroma_dir_size = _get_directory_size(settings.CHROMA_DIR)
            state_dir_size = _get_directory_size(settings.STATE_DIR)
            log_dir_size = _get_directory_size(settings.LOG_DIR)
            
            stats["disk_usage"] = {
                "chroma_dir_mb": chroma_dir_size / (1024 * 1024),
                "state_dir_mb": state_dir_size / (1024 * 1024),
                "log_dir_mb": log_dir_size / (1024 * 1024),
                "total_mb": (chroma_dir_size + state_dir_size + log_dir_size) / (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"Error getting disk usage stats: {str(e)}")
            stats["disk_usage"] = {"error": str(e)}
            
        return stats
        
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        return {"error": str(e)}

def _get_directory_size(path):
    """
    Calculate the total size of a directory in bytes.
    
    Args:
        path: Directory path
        
    Returns:
        Size in bytes
    """
    total_size = 0
    
    if not os.path.exists(path):
        return 0
        
    if os.path.isfile(path):
        return os.path.getsize(path)
        
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if os.path.exists(file_path):
                total_size += os.path.getsize(file_path)
                
    return total_size

def compact_memory(memory_type: Optional[str] = None):
    """
    Compact and optimize memory collections.
    
    Args:
        memory_type: Specific memory type to compact (None for all)
        
    Returns:
        Dictionary with results of compaction
    """
    try:
        results = {}
        
        # Determine which memory types to compact
        memory_types = [memory_type] if memory_type else MEMORY_MODULES.keys()
        
        for mem_type in memory_types:
            if mem_type not in MEMORY_MODULES:
                logger.warning(f"Unknown memory type for compaction: {mem_type}")
                results[mem_type] = {"status": "error", "message": f"Unknown memory type: {mem_type}"}
                continue
                
            try:
                # Get the collection for this memory type
                client = chroma.get_client()
                collection_name = f"{mem_type}_memory"
                
                if collection_name in [c.name for c in client.list_collections()]:
                    collection = client.get_collection(collection_name)
                    
                    # Store the count before compaction
                    count_before = collection.count()
                    
                    # Perform compaction (implementation varies by ChromaDB version)
                    try:
                        # Try collection-level compact method if available
                        if hasattr(collection, "compact") and callable(collection.compact):
                            collection.compact()
                        else:
                            # Fall back to client-level compact
                            if hasattr(client, "compact") and callable(client.compact):
                                client.compact(collection_name)
                    except AttributeError:
                        logger.warning(f"Compaction not supported for {mem_type} memory")
                        
                    # Check count after compaction
                    count_after = collection.count()
                    
                    results[mem_type] = {
                        "status": "success",
                        "count_before": count_before,
                        "count_after": count_after
                    }
                    
                    logger.info(f"Compacted {mem_type} memory: {count_before} -> {count_after} items")
                else:
                    logger.warning(f"Collection not found for compaction: {collection_name}")
                    results[mem_type] = {"status": "error", "message": f"Collection not found: {collection_name}"}
                    
            except Exception as e:
                logger.error(f"Error compacting {mem_type} memory: {str(e)}")
                results[mem_type] = {"status": "error", "message": str(e)}
        
        return {
            "status": "completed",
            "timestamp": datetime.datetime.now().isoformat(),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error during memory compaction: {str(e)}")
        return {"status": "error", "message": str(e)}

def reindex_memory(memory_type: Optional[str] = None):
    """
    Reindex memory collections to rebuild embeddings and indexes.
    
    Args:
        memory_type: Specific memory type to reindex (None for all)
        
    Returns:
        Dictionary with results of reindexing
    """
    try:
        results = {}
        
        # Determine which memory types to reindex
        memory_types = [memory_type] if memory_type else MEMORY_MODULES.keys()
        
        for mem_type in memory_types:
            if mem_type not in MEMORY_MODULES:
                logger.warning(f"Unknown memory type for reindexing: {mem_type}")
                results[mem_type] = {"status": "error", "message": f"Unknown memory type: {mem_type}"}
                continue
                
            try:
                # Get the collection for this memory type
                client = chroma.get_client()
                collection_name = f"{mem_type}_memory"
                
                if collection_name in [c.name for c in client.list_collections()]:
                    collection = client.get_collection(collection_name)
                    
                    # Store the count before reindexing
                    count_before = collection.count()
                    
                    # Perform reindexing
                    # This is a simplified approach - in a real implementation,
                    # you might need to extract all data, delete the collection,
                    # and recreate it with the same data
                    
                    # Get all data
                    batch_size = 1000
                    all_data = []
                    
                    for offset in range(0, count_before, batch_size):
                        batch = collection.get(
                            limit=batch_size,
                            offset=offset,
                            include=["embeddings", "documents", "metadatas"]
                        )
                        
                        for i in range(len(batch["ids"])):
                            all_data.append({
                                "id": batch["ids"][i],
                                "document": batch["documents"][i],
                                "metadata": batch["metadatas"][i],
                                "embedding": batch["embeddings"][i] if batch["embeddings"] else None
                            })
                    
                    # Delete and recreate collection
                    try:
                        client.delete_collection(collection_name)
                        collection = client.create_collection(
                            name=collection_name,
                            metadata={"description": f"{mem_type} memory collection (reindexed)"}
                        )
                        
                        # Reinsert all data
                        for i in range(0, len(all_data), batch_size):
                            batch = all_data[i:i+batch_size]
                            
                            ids = [item["id"] for item in batch]
                            documents = [item["document"] for item in batch]
                            metadatas = [item["metadata"] for item in batch]
                            embeddings = [item["embedding"] for item in batch] if all(item["embedding"] is not None for item in batch) else None
                            
                            collection.add(
                                ids=ids,
                                documents=documents,
                                metadatas=metadatas,
                                embeddings=embeddings
                            )
                        
                        # Check count after reindexing
                        count_after = collection.count()
                        
                        results[mem_type] = {
                            "status": "success",
                            "count_before": count_before,
                            "count_after": count_after
                        }
                        
                        logger.info(f"Reindexed {mem_type} memory: {count_before} -> {count_after} items")
                        
                    except Exception as e:
                        logger.error(f"Error during collection recreation for {mem_type}: {str(e)}")
                        results[mem_type] = {"status": "error", "message": f"Collection recreation failed: {str(e)}"}
                        
                else:
                    logger.warning(f"Collection not found for reindexing: {collection_name}")
                    results[mem_type] = {"status": "error", "message": f"Collection not found: {collection_name}"}
                    
            except Exception as e:
                logger.error(f"Error reindexing {mem_type} memory: {str(e)}")
                results[mem_type] = {"status": "error", "message": str(e)}
        
        return {
            "status": "completed",
            "timestamp": datetime.datetime.now().isoformat(),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error during memory reindexing: {str(e)}")
        return {"status": "error", "message": str(e)}

def prune_old_memories(
    memory_type: Optional[str] = None,
    days_to_keep: int = 365,
    dry_run: bool = True
):
    """
    Prune memories older than a specified number of days.
    
    Args:
        memory_type: Specific memory type to prune (None for all)
        days_to_keep: Number of days of memories to keep
        dry_run: If True, only report what would be deleted without actually deleting
        
    Returns:
        Dictionary with results of pruning
    """
    try:
        results = {}
        
        # Calculate cutoff date
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days_to_keep)).isoformat()
        
        # Determine which memory types to prune
        memory_types = [memory_type] if memory_type else MEMORY_MODULES.keys()
        
        for mem_type in memory_types:
            if mem_type not in MEMORY_MODULES:
                logger.warning(f"Unknown memory type for pruning: {mem_type}")
                results[mem_type] = {"status": "error", "message": f"Unknown memory type: {mem_type}"}
                continue
                
            try:
                # Get the collection for this memory type
                client = chroma.get_client()
                collection_name = f"{mem_type}_memory"
                
                if collection_name in [c.name for c in client.list_collections()]:
                    collection = client.get_collection(collection_name)
                    
                    # Store the count before pruning
                    count_before = collection.count()
                    
                    # Find memories older than the cutoff date
                    where_filter = {"created_at": {"$lt": cutoff_date}}
                    
                    old_memories = collection.get(
                        where=where_filter,
                        include=["metadatas"]
                    )
                    
                    old_count = len(old_memories["ids"]) if old_memories["ids"] else 0
                    
                    if not dry_run and old_count > 0:
                        # Actually delete old memories
                        collection.delete(ids=old_memories["ids"])
                        
                        # Check count after pruning
                        count_after = collection.count()
                        
                        results[mem_type] = {
                            "status": "success",
                            "count_before": count_before,
                            "count_after": count_after,
                            "memories_deleted": old_count
                        }
                        
                        logger.info(f"Pruned {old_count} old {mem_type} memories")
                    else:
                        # Dry run, just report
                        results[mem_type] = {
                            "status": "dry_run",
                            "count": count_before,
                            "memories_to_delete": old_count
                        }
                        
                        logger.info(f"Dry run: Would prune {old_count} old {mem_type} memories")
                        
                else:
                    logger.warning(f"Collection not found for pruning: {collection_name}")
                    results[mem_type] = {"status": "error", "message": f"Collection not found: {collection_name}"}
                    
            except Exception as e:
                logger.error(f"Error pruning {mem_type} memory: {str(e)}")
                results[mem_type] = {"status": "error", "message": str(e)}
        
        return {
            "status": "completed",
            "timestamp": datetime.datetime.now().isoformat(),
            "dry_run": dry_run,
            "cutoff_date": cutoff_date,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error during memory pruning: {str(e)}")
        return {"status": "error", "message": str(e)}

def generate_memory_graph(memory_types: Optional[List[str]] = None, max_items: int = 1000):
    """
    Generate a graph representation of the memory system.
    
    Args:
        memory_types: Specific memory types to include (None for all)
        max_items: Maximum number of items to include per memory type
        
    Returns:
        Dictionary with graph representation
    """
    try:
        graph = {
            "nodes": [],
            "edges": []
        }
        
        # Assign type-specific properties
        type_properties = {
            "semantic": {"color": "#3498db", "shape": "circle"},
            "episodic": {"color": "#2ecc71", "shape": "square"},
            "procedural": {"color": "#e74c3c", "shape": "triangle"},
            "reflective": {"color": "#9b59b6", "shape": "diamond"},
            "affective": {"color": "#f39c12", "shape": "star"},
            "identity": {"color": "#1abc9c", "shape": "hexagon"}
        }
        
        # Track node IDs to avoid duplicates
        node_ids = set()
        
        # Track edges to avoid duplicates
        edge_set = set()
        
        # Determine which memory types to include
        mem_types = memory_types if memory_types else MEMORY_MODULES.keys()
        
        # First, collect all nodes
        for mem_type in mem_types:
            if mem_type not in MEMORY_MODULES:
                logger.warning(f"Unknown memory type for graph: {mem_type}")
                continue
                
            try:
                # Get the collection for this memory type
                client = chroma.get_client()
                collection_name = f"{mem_type}_memory"
                
                if collection_name in [c.name for c in client.list_collections()]:
                    collection = client.get_collection(collection_name)
                    
                    # Get memories
                    memories = collection.get(
                        limit=max_items,
                        include=["metadatas"]
                    )
                    
                    if memories["ids"]:
                        for i in range(len(memories["ids"])):
                            memory_id = memories["ids"][i]
                            metadata = memories["metadatas"][i]
                            
                            # Skip if node already exists
                            if memory_id in node_ids:
                                continue
                                
                            # Add node to graph
                            node = {
                                "id": memory_id,
                                "label": metadata.get("title", f"{mem_type[:3]}-{memory_id[:8]}"),
                                "type": mem_type,
                                "created_at": metadata.get("created_at", ""),
                                "properties": type_properties.get(mem_type, {"color": "#95a5a6", "shape": "dot"})
                            }
                            
                            graph["nodes"].append(node)
                            node_ids.add(memory_id)
                            
            except Exception as e:
                logger.error(f"Error collecting nodes for {mem_type} memory: {str(e)}")
        
        # Now, collect edges between nodes
        for mem_type in mem_types:
            if mem_type != "reflective":
                continue  # For simplicity, only look for edges in reflective memory
                
            try:
                # Get the collection for reflective memory
                client = chroma.get_client()
                collection_name = "reflective_memory"
                
                if collection_name in [c.name for c in client.list_collections()]:
                    collection = client.get_collection(collection_name)
                    
                    # Get reflections
                    reflections = collection.get(
                        limit=max_items,
                        include=["metadatas"]
                    )
                    
                    if reflections["ids"]:
                        for i in range(len(reflections["ids"])):
                            reflection_id = reflections["ids"][i]
                            metadata = reflections["metadatas"][i]
                            
                            # Get source memory IDs if present
                            if "source_memories" in metadata:
                                try:
                                    source_memories = json.loads(metadata["source_memories"])
                                    
                                    # Add edges from source memories to this reflection
                                    for source_id in source_memories:
                                        # Only add edge if both nodes exist
                                        if source_id in node_ids and reflection_id in node_ids:
                                            edge_key = (source_id, reflection_id)
                                            
                                            # Skip if edge already exists
                                            if edge_key in edge_set:
                                                continue
                                                
                                            # Add edge to graph
                                            edge = {
                                                "source": source_id,
                                                "target": reflection_id,
                                                "type": "source_of"
                                            }
                                            
                                            graph["edges"].append(edge)
                                            edge_set.add(edge_key)
                                    
                                except (json.JSONDecodeError, TypeError):
                                    pass
                                
            except Exception as e:
                logger.error(f"Error collecting edges for {mem_type} memory: {str(e)}")
        
        logger.info(f"Generated memory graph with {len(graph['nodes'])} nodes and {len(graph['edges'])} edges")
        return graph
        
    except Exception as e:
        logger.error(f"Error generating memory graph: {str(e)}")
        return {"error": str(e)}

def export_memories(
    memory_type: Optional[str] = None,
    output_format: str = "json",
    max_items: int = 1000
):
    """
    Export memories to a specified format.
    
    Args:
        memory_type: Specific memory type to export (None for all)
        output_format: Format to export to ("json" or "csv")
        max_items: Maximum number of items to export per memory type
        
    Returns:
        Dictionary with export results
    """
    try:
        export_data = {}
        
        # Determine which memory types to export
        memory_types = [memory_type] if memory_type else MEMORY_MODULES.keys()
        
        for mem_type in memory_types:
            if mem_type not in MEMORY_MODULES:
                logger.warning(f"Unknown memory type for export: {mem_type}")
                continue
                
            try:
                # Get the collection for this memory type
                client = chroma.get_client()
                collection_name = f"{mem_type}_memory"
                
                if collection_name in [c.name for c in client.list_collections()]:
                    collection = client.get_collection(collection_name)
                    
                    # Get memories
                    memories = collection.get(
                        limit=max_items,
                        include=["documents", "metadatas"]
                    )
                    
                    if memories["ids"]:
                        memory_data = []
                        
                        for i in range(len(memories["ids"])):
                            memory_item = {
                                "id": memories["ids"][i],
                                "content": memories["documents"][i],
                                "metadata": memories["metadatas"][i]
                            }
                            
                            memory_data.append(memory_item)
                            
                        export_data[mem_type] = memory_data
                        logger.info(f"Exported {len(memory_data)} {mem_type} memories")
                    else:
                        export_data[mem_type] = []
                        logger.info(f"No {mem_type} memories to export")
                        
                else:
                    logger.warning(f"Collection not found for export: {collection_name}")
                    
            except Exception as e:
                logger.error(f"Error exporting {mem_type} memory: {str(e)}")
                export_data[mem_type] = {"error": str(e)}
        
        # Generate export result
        export_result = {
            "status": "completed",
            "timestamp": datetime.datetime.now().isoformat(),
            "format": output_format,
            "memory_types": list(export_data.keys()),
            "total_memories": sum(len(memories) for memories in export_data.values() if isinstance(memories, list))
        }
        
        # Add the actual export data
        if output_format == "json":
            export_result["data"] = export_data
        else:
            # CSV not directly supported in the return value
            # In a real implementation, you might write to a file instead
            export_result["message"] = "CSV format not supported for direct return"
            
        return export_result
        
    except Exception as e:
        logger.error(f"Error exporting memories: {str(e)}")
        return {"status": "error", "message": str(e)}
