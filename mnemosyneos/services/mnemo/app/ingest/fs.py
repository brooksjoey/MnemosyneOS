"""
Filesystem Ingest Module for MnemosyneOS.

This module handles ingestion of documents from the filesystem,
including text extraction, chunking, and storage in memory layers.
"""
import os
import re
import datetime
import mimetypes
from typing import List, Dict, Any, Optional, Tuple, Set

from app import logging_setup
from app.config import settings
from app.memory import semantic
from app.store import chroma

# Initialize logger
logger = logging_setup.get_logger()

# Default file types to ingest
DEFAULT_FILE_TYPES = [
    ".md", ".txt", ".py", ".js", ".html", ".css", ".json", ".yaml", ".yml",
    ".sh", ".bash", ".rst", ".csv", ".ini", ".toml", ".xml", ".cfg"
]

# Define chunk size and overlap for text splitting
CHUNK_SIZE = 1000  # characters
CHUNK_OVERLAP = 200  # characters

def ingest_documents(
    path: str,
    recursive: bool = False,
    file_types: Optional[List[str]] = None,
    max_file_size: int = 1024 * 1024,  # 1MB
    memory_type: str = "semantic"
) -> Dict[str, Any]:
    """
    Ingest documents from a filesystem path.
    
    Args:
        path: Path to file or directory
        recursive: Whether to recursively traverse directories
        file_types: List of file extensions to ingest (None for defaults)
        max_file_size: Maximum file size in bytes to ingest
        memory_type: Memory type to store documents in (defaults to semantic)
        
    Returns:
        Dictionary with ingestion results
    """
    try:
        # Normalize and expand path
        path = os.path.abspath(os.path.expanduser(path))
        
        if not os.path.exists(path):
            error_msg = f"Path does not exist: {path}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
            
        # Use default file types if not specified
        if file_types is None:
            file_types = DEFAULT_FILE_TYPES
            
        # Ensure file types start with a dot
        file_types = [ft if ft.startswith(".") else f".{ft}" for ft in file_types]
        
        # Collect files to ingest
        files_to_ingest = []
        
        if os.path.isfile(path):
            # Single file
            file_ext = os.path.splitext(path)[1].lower()
            if file_ext in file_types or not file_types:
                files_to_ingest.append(path)
        else:
            # Directory
            for root, dirs, files in os.walk(path):
                if not recursive and root != path:
                    continue
                    
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()
                    
                    if file_ext in file_types or not file_types:
                        if os.path.getsize(file_path) <= max_file_size:
                            files_to_ingest.append(file_path)
        
        # Process and ingest files
        ingestion_results = []
        
        for file_path in files_to_ingest:
            try:
                result = ingest_file(file_path, memory_type)
                ingestion_results.append({
                    "file": file_path,
                    "status": "success",
                    "chunks": result.get("chunks", 0),
                    "ids": result.get("ids", [])
                })
                logger.info(f"Ingested {file_path}: {result.get('chunks', 0)} chunks")
            except Exception as e:
                logger.error(f"Error ingesting {file_path}: {str(e)}")
                ingestion_results.append({
                    "file": file_path,
                    "status": "error",
                    "error": str(e)
                })
                
        # Summarize results
        successful = sum(1 for r in ingestion_results if r["status"] == "success")
        failed = sum(1 for r in ingestion_results if r["status"] == "error")
        total_chunks = sum(r.get("chunks", 0) for r in ingestion_results if r["status"] == "success")
        
        return {
            "status": "completed",
            "timestamp": datetime.datetime.now().isoformat(),
            "path": path,
            "recursive": recursive,
            "file_types": file_types,
            "files_processed": len(files_to_ingest),
            "files_successful": successful,
            "files_failed": failed,
            "total_chunks": total_chunks,
            "results": ingestion_results
        }
        
    except Exception as e:
        logger.error(f"Error ingesting documents from {path}: {str(e)}")
        return {"status": "error", "message": str(e)}

def ingest_file(file_path: str, memory_type: str = "semantic") -> Dict[str, Any]:
    """
    Ingest a single file.
    
    Args:
        file_path: Path to the file
        memory_type: Memory type to store documents in
        
    Returns:
        Dictionary with ingestion results
    """
    try:
        # Extract text from file
        text, metadata = extract_text_from_file(file_path)
        
        if not text:
            return {"status": "error", "message": "No text extracted"}
            
        # Split text into chunks
        chunks = split_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        
        # Create metadata for each chunk
        chunk_metadatas = []
        chunk_ids = []
        
        for i, chunk in enumerate(chunks):
            # Create a copy of the metadata for this chunk
            chunk_metadata = metadata.copy()
            
            # Add chunk-specific metadata
            chunk_metadata.update({
                "chunk_index": i,
                "chunk_total": len(chunks),
                "chunk_size": len(chunk)
            })
            
            chunk_metadatas.append(chunk_metadata)
            
        # Store chunks in memory
        if memory_type == "semantic":
            ids = []
            for i, (chunk, chunk_metadata) in enumerate(zip(chunks, chunk_metadatas)):
                # Add chunk index to tags
                tags = chunk_metadata.get("tags", [])
                if not isinstance(tags, list):
                    tags = [tags]
                    
                tags.extend(["document", "filesystem"])
                
                # Store in semantic memory
                chunk_id = semantic.store_memory(
                    content=chunk,
                    metadata=chunk_metadata,
                    tags=tags,
                    source=file_path
                )
                
                ids.append(chunk_id)
                
            return {
                "status": "success",
                "chunks": len(chunks),
                "ids": ids
            }
        else:
            # Other memory types not yet implemented
            return {"status": "error", "message": f"Memory type not supported: {memory_type}"}
            
    except Exception as e:
        logger.error(f"Error ingesting file {file_path}: {str(e)}")
        raise

def extract_text_from_file(file_path: str) -> Tuple[str, Dict[str, Any]]:
    """
    Extract text and metadata from a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (text, metadata)
    """
    try:
        # Get file info
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()
        file_size = os.path.getsize(file_path)
        file_mtime = os.path.getmtime(file_path)
        file_mtime_str = datetime.datetime.fromtimestamp(file_mtime).isoformat()
        
        # Get mime type
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = "application/octet-stream"
            
        # Prepare metadata
        metadata = {
            "source": file_path,
            "file_name": file_name,
            "file_extension": file_ext,
            "file_size": file_size,
            "file_modified": file_mtime_str,
            "mime_type": mime_type,
            "tags": ["document", "filesystem"]
        }
        
        # Extract text based on file type
        text = ""
        
        # Plain text files
        if file_ext in [".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".yaml", ".yml", 
                        ".sh", ".bash", ".rst", ".csv", ".ini", ".toml", ".xml", ".cfg"]:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
                
            # Add language tag based on extension
            if file_ext == ".py":
                metadata["tags"].append("python")
            elif file_ext in [".js", ".ts"]:
                metadata["tags"].append("javascript")
            elif file_ext in [".html", ".htm"]:
                metadata["tags"].append("html")
            elif file_ext == ".md":
                metadata["tags"].append("markdown")
            elif file_ext in [".yaml", ".yml"]:
                metadata["tags"].append("yaml")
            elif file_ext == ".json":
                metadata["tags"].append("json")
            elif file_ext in [".sh", ".bash"]:
                metadata["tags"].append("shell")
            elif file_ext == ".css":
                metadata["tags"].append("css")
                
        # PDF files
        elif file_ext == ".pdf":
            try:
                import fitz  # PyMuPDF
                
                doc = fitz.open(file_path)
                for page in doc:
                    text += page.get_text()
                    
                # Add metadata
                metadata["page_count"] = len(doc)
                metadata["tags"].append("pdf")
                
            except ImportError:
                logger.warning("PyMuPDF not installed, skipping PDF text extraction")
                text = f"[PDF: {file_name}] - Install PyMuPDF for text extraction"
                
        # DOCX files
        elif file_ext == ".docx":
            try:
                import docx
                
                doc = docx.Document(file_path)
                for para in doc.paragraphs:
                    text += para.text + "\n"
                    
                # Add metadata
                metadata["tags"].append("docx")
                
            except ImportError:
                logger.warning("python-docx not installed, skipping DOCX text extraction")
                text = f"[DOCX: {file_name}] - Install python-docx for text extraction"
                
        # Unsupported file types
        else:
            text = f"[Unsupported file type: {file_ext}] {file_name}"
            
        return text, metadata
        
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        return f"[Error extracting text: {str(e)}]", {"source": file_path, "error": str(e)}

def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into chunks of approximately equal size.
    
    Args:
        text: Text to split
        chunk_size: Target size of each chunk in characters
        chunk_overlap: Overlap between chunks in characters
        
    Returns:
        List of text chunks
    """
    # If text is shorter than chunk size, return as is
    if len(text) <= chunk_size:
        return [text]
        
    # Split text into paragraphs
    paragraphs = text.split("\n")
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed chunk size
        if len(current_chunk) + len(paragraph) > chunk_size:
            # If current chunk is not empty, add it to chunks
            if current_chunk:
                chunks.append(current_chunk)
                
                # Start new chunk with overlap
                if chunk_overlap > 0:
                    # Get the last part of the previous chunk for overlap
                    overlap_text = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else current_chunk
                    current_chunk = overlap_text
                else:
                    current_chunk = ""
                    
        # Add paragraph to current chunk
        if current_chunk and not current_chunk.endswith("\n"):
            current_chunk += "\n"
            
        current_chunk += paragraph
        
    # Add the last chunk if not empty
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def get_documents_stats() -> Dict[str, Any]:
    """
    Get statistics about ingested documents.
    
    Returns:
        Dictionary with document statistics
    """
    try:
        # Get semantic memory stats
        stats = semantic.get_stats()
        
        # Filter for documents
        document_count = 0
        file_extensions = {}
        sources = {}
        
        # Query semantic memory for documents
        client = chroma.get_client()
        collection = client.get_or_create_collection(name="semantic_memory")
        
        # Get document items
        where_filter = {"tags": {"$contains": "document"}}
        results = collection.get(
            where=where_filter,
            include=["metadatas"]
        )
        
        if results["ids"]:
            document_count = len(results["ids"])
            
            # Process metadata
            for metadata in results["metadatas"]:
                # Count file extensions
                if "file_extension" in metadata:
                    ext = metadata["file_extension"]
                    file_extensions[ext] = file_extensions.get(ext, 0) + 1
                    
                # Count sources
                if "source" in metadata:
                    source = metadata["source"]
                    sources[source] = sources.get(source, 0) + 1
        
        return {
            "document_count": document_count,
            "file_extensions": file_extensions,
            "sources": sources
        }
        
    except Exception as e:
        logger.error(f"Error getting document stats: {str(e)}")
        return {"error": str(e)}

def ingest_directory_documents(
    directory: str,
    recursive: bool = True,
    file_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Ingest all documents from a directory.
    Convenience wrapper around ingest_documents.
    
    Args:
        directory: Directory path
        recursive: Whether to recursively traverse directories
        file_types: List of file extensions to ingest
        
    Returns:
        Dictionary with ingestion results
    """
    return ingest_documents(
        path=directory,
        recursive=recursive,
        file_types=file_types
    )

def ingest_project_documentation(
    project_dir: str,
    doc_dirs: List[str] = ["docs", "documentation", "README.md"],
    file_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Ingest documentation from a project directory.
    
    Args:
        project_dir: Project directory path
        doc_dirs: List of documentation directories or files to look for
        file_types: List of file extensions to ingest
        
    Returns:
        Dictionary with ingestion results
    """
    try:
        # Normalize project directory
        project_dir = os.path.abspath(os.path.expanduser(project_dir))
        
        if not os.path.exists(project_dir):
            error_msg = f"Project directory does not exist: {project_dir}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
            
        # Use default file types if not specified
        if file_types is None:
            file_types = [".md", ".rst", ".txt", ".html"]
            
        # Find documentation directories and files
        docs_to_ingest = []
        
        for doc_path in doc_dirs:
            full_path = os.path.join(project_dir, doc_path)
            if os.path.exists(full_path):
                docs_to_ingest.append(full_path)
                
        # Ingest each documentation directory/file
        results = []
        
        for doc_path in docs_to_ingest:
            try:
                if os.path.isdir(doc_path):
                    # Directory
                    result = ingest_documents(
                        path=doc_path,
                        recursive=True,
                        file_types=file_types
                    )
                else:
                    # Single file
                    result = ingest_documents(
                        path=doc_path,
                        recursive=False,
                        file_types=file_types
                    )
                    
                results.append({
                    "path": doc_path,
                    "status": result.get("status", "unknown"),
                    "files_processed": result.get("files_processed", 0),
                    "total_chunks": result.get("total_chunks", 0)
                })
                
            except Exception as e:
                logger.error(f"Error ingesting documentation at {doc_path}: {str(e)}")
                results.append({
                    "path": doc_path,
                    "status": "error",
                    "error": str(e)
                })
                
        # Summarize results
        successful = sum(1 for r in results if r["status"] == "completed")
        failed = sum(1 for r in results if r["status"] == "error")
        total_files = sum(r.get("files_processed", 0) for r in results if r["status"] == "completed")
        total_chunks = sum(r.get("total_chunks", 0) for r in results if r["status"] == "completed")
        
        return {
            "status": "completed",
            "timestamp": datetime.datetime.now().isoformat(),
            "project_dir": project_dir,
            "docs_found": len(docs_to_ingest),
            "docs_successful": successful,
            "docs_failed": failed,
            "total_files": total_files,
            "total_chunks": total_chunks,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error ingesting project documentation from {project_dir}: {str(e)}")
        return {"status": "error", "message": str(e)}
