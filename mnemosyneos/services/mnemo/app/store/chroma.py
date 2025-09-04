"""
ChromaDB Store for MnemosyneOS.

This module provides a single interface for interacting with ChromaDB,
ensuring consistent connection handling and configuration across memory layers.
"""
import os
import time
import chromadb
from chromadb.config import Settings
from typing import Optional, Dict, Any, List

from app import logging_setup
from app.config import settings

# Initialize logger
logger = logging_setup.get_logger()

# Global client instance
_client = None

def get_client():
    """
    Get or create a ChromaDB client instance.
    
    Returns:
        ChromaDB client instance
    """
    global _client
    
    if _client is None:
        # Ensure the Chroma directory exists
        os.makedirs(settings.CHROMA_DIR, exist_ok=True)
        
        try:
            # Create the client with persistent storage
            _client = chromadb.PersistentClient(
                path=settings.CHROMA_DIR,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            logger.info(f"Created ChromaDB client with persistent storage at {settings.CHROMA_DIR}")
            
        except Exception as e:
            logger.error(f"Error creating ChromaDB client: {str(e)}")
            raise
            
    return _client

def reset_client():
    """
    Reset the global client instance.
    Useful for testing or when connection issues occur.
    
    Returns:
        New ChromaDB client instance
    """
    global _client
    
    # Close the existing client if possible
    if _client is not None:
        try:
            # Some ChromaDB versions don't have a close method
            if hasattr(_client, "close") and callable(_client.close):
                _client.close()
        except Exception as e:
            logger.warning(f"Error closing ChromaDB client: {str(e)}")
            
    # Reset the client
    _client = None
    
    # Create a new client
    return get_client()

def check_health():
    """
    Check if ChromaDB is healthy.
    
    Returns:
        Dictionary with health status
    """
    try:
        client = get_client()
        
        # Check if we can list collections
        collections = client.list_collections()
        
        return {
            "status": "healthy",
            "collection_count": len(collections),
            "collections": [c.name for c in collections]
        }
        
    except Exception as e:
        logger.error(f"ChromaDB health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

def create_collection(name: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Create a new collection or get an existing one.
    
    Args:
        name: Name of the collection
        metadata: Optional metadata for the collection
        
    Returns:
        ChromaDB collection
    """
    try:
        client = get_client()
        
        # Get or create the collection
        collection = client.get_or_create_collection(
            name=name,
            metadata=metadata
        )
        
        logger.info(f"Created or got collection: {name}")
        return collection
        
    except Exception as e:
        logger.error(f"Error creating collection {name}: {str(e)}")
        raise

def delete_collection(name: str):
    """
    Delete a collection.
    
    Args:
        name: Name of the collection to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        
        # Check if collection exists
        collections = client.list_collections()
        if name not in [c.name for c in collections]:
            logger.warning(f"Collection {name} not found for deletion")
            return False
            
        # Delete the collection
        client.delete_collection(name)
        
        logger.info(f"Deleted collection: {name}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting collection {name}: {str(e)}")
        return False

def get_collection_by_memory_type(memory_type: str):
    """
    Get a collection by memory type.
    
    Args:
        memory_type: Type of memory (e.g., "semantic", "episodic")
        
    Returns:
        ChromaDB collection
    """
    try:
        client = get_client()
        
        # Construct collection name
        collection_name = f"{memory_type}_memory"
        
        # Get the collection
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"description": f"{memory_type.capitalize()} memory collection"}
        )
        
        return collection
        
    except Exception as e:
        logger.error(f"Error getting collection for {memory_type} memory: {str(e)}")
        raise

def get_or_create_embedding_function(provider: Optional[str] = None):
    """
    Get or create an embedding function based on the configured provider.
    
    Args:
        provider: Provider name (defaults to settings.LVC_PROVIDER)
        
    Returns:
        Embedding function compatible with ChromaDB
    """
    try:
        # Use default provider if not specified
        if provider is None:
            provider = settings.LVC_PROVIDER
            
        # OpenAI embeddings
        if provider == "openai":
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
            
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key not set")
                
            return OpenAIEmbeddingFunction(
                api_key=settings.OPENAI_API_KEY,
                model_name="text-embedding-ada-002"
            )
            
        # If provider is not recognized or not implemented, use default
        # which is usually the all-MiniLM-L6-v2 model from sentence_transformers
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        return DefaultEmbeddingFunction()
        
    except Exception as e:
        logger.error(f"Error creating embedding function: {str(e)}")
        # Fall back to default embedding function
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        return DefaultEmbeddingFunction()

def batch_add_to_collection(
    collection_name: str,
    documents: List[str],
    metadatas: List[Dict[str, Any]],
    ids: Optional[List[str]] = None,
    batch_size: int = 100
):
    """
    Add documents to a collection in batches to avoid memory issues.
    
    Args:
        collection_name: Name of the collection
        documents: List of document contents
        metadatas: List of metadata dictionaries
        ids: List of document IDs (if None, UUIDs will be generated)
        batch_size: Number of documents to add in each batch
        
    Returns:
        List of document IDs
    """
    try:
        client = get_client()
        
        # Get the collection
        collection = client.get_or_create_collection(name=collection_name)
        
        # Generate IDs if not provided
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in range(len(documents))]
            
        # Add documents in batches
        for i in range(0, len(documents), batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_documents = documents[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            
            collection.add(
                ids=batch_ids,
                documents=batch_documents,
                metadatas=batch_metadatas
            )
            
            logger.info(f"Added batch of {len(batch_ids)} documents to {collection_name}")
            
            # Small delay to avoid overwhelming the database
            time.sleep(0.1)
            
        return ids
        
    except Exception as e:
        logger.error(f"Error batch adding to collection {collection_name}: {str(e)}")
        raise

def query_similar_documents(
    collection_name: str,
    query_texts: List[str],
    n_results: int = 10,
    where_filter: Optional[Dict[str, Any]] = None
):
    """
    Query for similar documents across collections.
    
    Args:
        collection_name: Name of the collection to query
        query_texts: List of query texts
        n_results: Number of results to return per query
        where_filter: Optional filter to apply to the query
        
    Returns:
        Query results
    """
    try:
        client = get_client()
        
        # Get the collection
        collection = client.get_collection(name=collection_name)
        
        # Query the collection
        results = collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error querying collection {collection_name}: {str(e)}")
        raise

def backup_collections(backup_dir: Optional[str] = None):
    """
    Backup all collections to a specified directory.
    
    Args:
        backup_dir: Directory to store backups (defaults to settings.STATE_DIR/backups)
        
    Returns:
        Dictionary with backup results
    """
    try:
        import shutil
        import datetime
        
        # Use default backup directory if not specified
        if backup_dir is None:
            backup_dir = os.path.join(settings.STATE_DIR, "backups")
            
        # Ensure backup directory exists
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create a timestamped backup directory
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"chroma_backup_{timestamp}")
        
        # Create the backup directory
        os.makedirs(backup_path, exist_ok=True)
        
        # Copy the ChromaDB directory to the backup directory
        shutil.copytree(
            settings.CHROMA_DIR,
            os.path.join(backup_path, "chroma"),
            dirs_exist_ok=True
        )
        
        logger.info(f"Backed up ChromaDB to {backup_path}")
        
        return {
            "status": "success",
            "backup_path": backup_path,
            "timestamp": timestamp
        }
        
    except Exception as e:
        logger.error(f"Error backing up ChromaDB: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

def restore_from_backup(backup_path: str):
    """
    Restore collections from a backup.
    
    Args:
        backup_path: Path to the backup directory
        
    Returns:
        Dictionary with restoration results
    """
    try:
        import shutil
        
        # Check if backup exists
        chroma_backup = os.path.join(backup_path, "chroma")
        if not os.path.exists(chroma_backup):
            error_msg = f"Backup not found at {chroma_backup}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
            
        # Reset the client
        reset_client()
        
        # Remove existing ChromaDB directory
        if os.path.exists(settings.CHROMA_DIR):
            shutil.rmtree(settings.CHROMA_DIR)
            
        # Copy the backup to the ChromaDB directory
        shutil.copytree(
            chroma_backup,
            settings.CHROMA_DIR,
            dirs_exist_ok=True
        )
        
        # Get a new client
        client = get_client()
        
        # List collections to verify restoration
        collections = client.list_collections()
        
        logger.info(f"Restored ChromaDB from {backup_path}")
        
        return {
            "status": "success",
            "collection_count": len(collections),
            "collections": [c.name for c in collections]
        }
        
    except Exception as e:
        logger.error(f"Error restoring ChromaDB from backup: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }
