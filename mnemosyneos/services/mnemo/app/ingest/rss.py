"""
RSS Ingest Module for MnemosyneOS.

This module handles ingestion of RSS feeds, including feed management,
periodic pulling, and storage in memory layers.
"""
import os
import uuid
import json
import datetime
import time
import feedparser
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app import logging_setup
from app.config import settings
from app.memory import semantic, episodic
from app.store import chroma

# Initialize logger
logger = logging_setup.get_logger()

# Path to store RSS feed information
RSS_FEEDS_FILE = os.path.join(settings.STATE_DIR, "rss", "feeds.json")

def initialize():
    """Initialize the RSS ingest module"""
    try:
        # Ensure RSS directory exists
        os.makedirs(os.path.dirname(RSS_FEEDS_FILE), exist_ok=True)
        
        # Create feeds file if it doesn't exist
        if not os.path.exists(RSS_FEEDS_FILE):
            with open(RSS_FEEDS_FILE, 'w') as f:
                json.dump([], f)
                
        logger.info("Initialized RSS ingest module")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize RSS ingest module: {str(e)}")
        return False

def add_feed(
    url: str,
    name: Optional[str] = None,
    category: Optional[str] = None,
    update_frequency: int = 3600  # 1 hour default
) -> str:
    """
    Add a new RSS feed to monitor.
    
    Args:
        url: URL of the RSS feed
        name: Name of the feed (if None, will be extracted from the feed)
        category: Category for the feed
        update_frequency: Update frequency in seconds
        
    Returns:
        ID of the added feed
    """
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid URL: {url}")
            
        # Generate feed ID
        feed_id = str(uuid.uuid4())
        
        # If name not provided, try to get it from the feed
        if name is None:
            try:
                feed_data = feedparser.parse(url)
                name = feed_data.feed.get('title', url)
            except Exception as e:
                logger.warning(f"Couldn't get feed title from {url}: {str(e)}")
                name = url
                
        # Prepare feed data
        feed = {
            "id": feed_id,
            "url": url,
            "name": name,
            "category": category,
            "update_frequency": update_frequency,
            "added_at": datetime.datetime.now().isoformat(),
            "last_update": None,
            "last_update_status": None,
            "items_count": 0
        }
        
        # Load existing feeds
        feeds = _load_feeds()
        
        # Check if feed URL already exists
        for existing_feed in feeds:
            if existing_feed["url"] == url:
                logger.warning(f"Feed URL already exists: {url}")
                return existing_feed["id"]
                
        # Add new feed
        feeds.append(feed)
        
        # Save feeds
        _save_feeds(feeds)
        
        logger.info(f"Added RSS feed: {name} ({url})")
        return feed_id
        
    except Exception as e:
        logger.error(f"Error adding RSS feed {url}: {str(e)}")
        raise

def list_feeds(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all RSS feeds.
    
    Args:
        category: Optional category to filter by
        
    Returns:
        List of feed information dictionaries
    """
    try:
        feeds = _load_feeds()
        
        # Filter by category if specified
        if category:
            feeds = [feed for feed in feeds if feed.get("category") == category]
            
        logger.info(f"Listed {len(feeds)} RSS feeds" + (f" in category {category}" if category else ""))
        return feeds
        
    except Exception as e:
        logger.error(f"Error listing RSS feeds: {str(e)}")
        return []

def update_feed(feed_id: str, **kwargs) -> bool:
    """
    Update an existing RSS feed.
    
    Args:
        feed_id: ID of the feed to update
        **kwargs: Feed properties to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        feeds = _load_feeds()
        
        # Find the feed
        for i, feed in enumerate(feeds):
            if feed["id"] == feed_id:
                # Update feed properties
                for key, value in kwargs.items():
                    if key in feed:
                        feed[key] = value
                        
                # Save feeds
                _save_feeds(feeds)
                
                logger.info(f"Updated RSS feed: {feed['name']} ({feed['url']})")
                return True
                
        logger.warning(f"RSS feed not found for update: {feed_id}")
        return False
        
    except Exception as e:
        logger.error(f"Error updating RSS feed {feed_id}: {str(e)}")
        return False

def delete_feed(feed_id: str) -> bool:
    """
    Delete an RSS feed.
    
    Args:
        feed_id: ID of the feed to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        feeds = _load_feeds()
        
        # Find the feed
        for i, feed in enumerate(feeds):
            if feed["id"] == feed_id:
                # Remove the feed
                del feeds[i]
                
                # Save feeds
                _save_feeds(feeds)
                
                logger.info(f"Deleted RSS feed: {feed_id}")
                return True
                
        logger.warning(f"RSS feed not found for deletion: {feed_id}")
        return False
        
    except Exception as e:
        logger.error(f"Error deleting RSS feed {feed_id}: {str(e)}")
        return False

def pull_feeds(feed_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Pull and process RSS feeds.
    
    Args:
        feed_id: Optional ID of a specific feed to pull (None for all)
        
    Returns:
        Dictionary with pull results
    """
    try:
        feeds = _load_feeds()
        
        # Filter feeds if specific ID provided
        if feed_id:
            feeds = [feed for feed in feeds if feed["id"] == feed_id]
            if not feeds:
                return {"status": "error", "message": f"Feed not found: {feed_id}"}
                
        results = []
        
        # Process each feed
        for feed in feeds:
            try:
                feed_result = _process_feed(feed)
                results.append(feed_result)
            except Exception as e:
                logger.error(f"Error processing feed {feed['name']}: {str(e)}")
                results.append({
                    "id": feed["id"],
                    "name": feed["name"],
                    "status": "error",
                    "error": str(e)
                })
                
        # Update the feeds file with last update time
        _save_feeds(feeds)
        
        return {
            "status": "completed",
            "timestamp": datetime.datetime.now().isoformat(),
            "feeds_processed": len(feeds),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error pulling RSS feeds: {str(e)}")
        return {"status": "error", "message": str(e)}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def _fetch_feed(url: str) -> Dict[str, Any]:
    """
    Fetch an RSS feed with retry logic.
    
    Args:
        url: URL of the feed
        
    Returns:
        Parsed feed data
    """
    try:
        # Use httpx for better timeout handling
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            content = response.text
            
        # Parse the feed content
        feed_data = feedparser.parse(content)
        
        return feed_data
        
    except Exception as e:
        logger.error(f"Error fetching feed {url}: {str(e)}")
        raise

def _process_feed(feed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single RSS feed and store new items.
    
    Args:
        feed: Feed information dictionary
        
    Returns:
        Dictionary with processing results
    """
    try:
        feed_id = feed["id"]
        url = feed["url"]
        
        # Get feed data
        feed_data = _fetch_feed(url)
        
        # Get previously processed items
        processed_items = _get_processed_items(feed_id)
        
        # Process new items
        new_items = []
        
        for entry in feed_data.entries:
            # Get unique ID for entry
            entry_id = entry.get('id', entry.get('link', None))
            if not entry_id:
                # Generate an ID if none exists
                entry_id = str(uuid.uuid4())
                
            # Skip if already processed
            if entry_id in processed_items:
                continue
                
            # Get entry details
            title = entry.get('title', 'Untitled')
            link = entry.get('link', '')
            summary = entry.get('summary', '')
            content = entry.get('content', [{'value': ''}])[0]['value'] if 'content' in entry else ''
            published = entry.get('published', '')
            
            # Try to parse published date
            try:
                if published:
                    published_date = datetime.datetime(*entry.published_parsed[:6]).isoformat()
                else:
                    published_date = datetime.datetime.now().isoformat()
            except (AttributeError, TypeError):
                published_date = datetime.datetime.now().isoformat()
                
            # Combine summary and content
            if not content:
                content = summary
                
            # Prepare full content
            full_content = f"Title: {title}\n\nSource: {feed['name']}\nURL: {link}\nPublished: {published}\n\n{content}"
            
            # Store in semantic memory
            metadata = {
                "title": title,
                "feed_id": feed_id,
                "feed_name": feed["name"],
                "url": link,
                "published": published_date,
                "source_type": "rss"
            }
            
            # Add category if present
            if feed.get("category"):
                metadata["category"] = feed["category"]
                
            # Store in memory
            memory_id = semantic.store_memory(
                content=full_content,
                metadata=metadata,
                tags=["rss", "external", feed.get("category", "news")],
                source=feed["name"]
            )
            
            # Also store as an episodic memory (as an event)
            event_content = f"RSS update from {feed['name']}: {title}\n\n{summary}"
            
            episodic.store_memory(
                content=event_content,
                metadata={
                    "event_type": "rss_update",
                    "feed_id": feed_id,
                    "feed_name": feed["name"],
                    "url": link,
                    "title": title,
                    "memory_id": memory_id
                },
                tags=["rss", "external", feed.get("category", "news")],
                source="rss_ingest"
            )
            
            # Add to new items
            new_items.append({
                "id": entry_id,
                "title": title,
                "link": link,
                "memory_id": memory_id,
                "published": published_date
            })
            
            # Add to processed items
            processed_items[entry_id] = {
                "processed_at": datetime.datetime.now().isoformat(),
                "memory_id": memory_id
            }
            
        # Save processed items
        _save_processed_items(feed_id, processed_items)
        
        # Update feed information
        feed["last_update"] = datetime.datetime.now().isoformat()
        feed["last_update_status"] = "success"
        feed["items_count"] = len(processed_items)
        
        logger.info(f"Processed feed {feed['name']}: {len(new_items)} new items")
        
        return {
            "id": feed_id,
            "name": feed["name"],
            "status": "success",
            "new_items": len(new_items),
            "total_items": len(processed_items),
            "items": new_items
        }
        
    except Exception as e:
        # Update feed with error status
        feed["last_update"] = datetime.datetime.now().isoformat()
        feed["last_update_status"] = f"error: {str(e)}"
        
        logger.error(f"Error processing feed {feed.get('name', 'unknown')}: {str(e)}")
        return {
            "id": feed.get("id", "unknown"),
            "name": feed.get("name", "unknown"),
            "status": "error",
            "error": str(e)
        }

def _load_feeds() -> List[Dict[str, Any]]:
    """
    Load RSS feeds from file.
    
    Returns:
        List of feed information dictionaries
    """
    try:
        if not os.path.exists(RSS_FEEDS_FILE):
            # Create empty feeds file
            with open(RSS_FEEDS_FILE, 'w') as f:
                json.dump([], f)
            return []
            
        with open(RSS_FEEDS_FILE, 'r') as f:
            feeds = json.load(f)
            
        return feeds
        
    except Exception as e:
        logger.error(f"Error loading RSS feeds: {str(e)}")
        return []

def _save_feeds(feeds: List[Dict[str, Any]]):
    """
    Save RSS feeds to file.
    
    Args:
        feeds: List of feed information dictionaries
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(RSS_FEEDS_FILE), exist_ok=True)
        
        with open(RSS_FEEDS_FILE, 'w') as f:
            json.dump(feeds, f, indent=2)
            
    except Exception as e:
        logger.error(f"Error saving RSS feeds: {str(e)}")

def _get_processed_items(feed_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Get processed items for a feed.
    
    Args:
        feed_id: ID of the feed
        
    Returns:
        Dictionary mapping item IDs to processing information
    """
    try:
        items_file = os.path.join(settings.STATE_DIR, "rss", f"{feed_id}_items.json")
        
        if not os.path.exists(items_file):
            return {}
            
        with open(items_file, 'r') as f:
            items = json.load(f)
            
        return items
        
    except Exception as e:
        logger.error(f"Error loading processed items for feed {feed_id}: {str(e)}")
        return {}

def _save_processed_items(feed_id: str, items: Dict[str, Dict[str, Any]]):
    """
    Save processed items for a feed.
    
    Args:
        feed_id: ID of the feed
        items: Dictionary mapping item IDs to processing information
    """
    try:
        items_file = os.path.join(settings.STATE_DIR, "rss", f"{feed_id}_items.json")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(items_file), exist_ok=True)
        
        with open(items_file, 'w') as f:
            json.dump(items, f, indent=2)
            
    except Exception as e:
        logger.error(f"Error saving processed items for feed {feed_id}: {str(e)}")

def prune_old_items(days_to_keep: int = 30) -> Dict[str, Any]:
    """
    Prune old processed items.
    
    Args:
        days_to_keep: Number of days of items to keep
        
    Returns:
        Dictionary with pruning results
    """
    try:
        feeds = _load_feeds()
        results = []
        
        for feed in feeds:
            feed_id = feed["id"]
            
            try:
                items = _get_processed_items(feed_id)
                
                # Calculate cutoff date
                cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days_to_keep)).isoformat()
                
                # Find old items
                old_items = {}
                keep_items = {}
                
                for item_id, item_info in items.items():
                    processed_at = item_info.get("processed_at", "")
                    
                    if processed_at < cutoff_date:
                        old_items[item_id] = item_info
                    else:
                        keep_items[item_id] = item_info
                        
                # Save pruned items
                _save_processed_items(feed_id, keep_items)
                
                # Update feed count
                feed["items_count"] = len(keep_items)
                
                results.append({
                    "id": feed_id,
                    "name": feed["name"],
                    "pruned_items": len(old_items),
                    "remaining_items": len(keep_items)
                })
                
                logger.info(f"Pruned {len(old_items)} old items from feed {feed['name']}")
                
            except Exception as e:
                logger.error(f"Error pruning items for feed {feed.get('name', 'unknown')}: {str(e)}")
                results.append({
                    "id": feed_id,
                    "name": feed["name"],
                    "status": "error",
                    "error": str(e)
                })
                
        # Save updated feeds
        _save_feeds(feeds)
        
        return {
            "status": "completed",
            "timestamp": datetime.datetime.now().isoformat(),
            "feeds_processed": len(feeds),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error pruning old RSS items: {str(e)}")
        return {"status": "error", "message": str(e)}

def setup_default_feeds() -> Dict[str, Any]:
    """
    Set up some default RSS feeds.
    
    Returns:
        Dictionary with setup results
    """
    try:
        default_feeds = [
            {
                "url": "https://news.ycombinator.com/rss",
                "name": "Hacker News",
                "category": "tech"
            },
            {
                "url": "https://www.theverge.com/rss/index.xml",
                "name": "The Verge",
                "category": "tech"
            },
            {
                "url": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
                "name": "NY Times Technology",
                "category": "tech"
            }
        ]
        
        results = []
        
        for feed_info in default_feeds:
            try:
                feed_id = add_feed(
                    url=feed_info["url"],
                    name=feed_info["name"],
                    category=feed_info["category"]
                )
                
                results.append({
                    "url": feed_info["url"],
                    "name": feed_info["name"],
                    "status": "success",
                    "id": feed_id
                })
                
            except Exception as e:
                logger.error(f"Error adding default feed {feed_info['name']}: {str(e)}")
                results.append({
                    "url": feed_info["url"],
                    "name": feed_info["name"],
                    "status": "error",
                    "error": str(e)
                })
                
        return {
            "status": "completed",
            "feeds_added": sum(1 for r in results if r["status"] == "success"),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error setting up default feeds: {str(e)}")
        return {"status": "error", "message": str(e)}

def search_feed_items(
    query: str,
    category: Optional[str] = None,
    feed_id: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search RSS feed items.
    
    Args:
        query: Search query
        category: Optional category to filter by
        feed_id: Optional feed ID to filter by
        limit: Maximum number of results to return
        
    Returns:
        List of matching items
    """
    try:
        # Build search filters
        where_filter = {"source_type": "rss"}
        
        if category:
            where_filter["category"] = category
            
        if feed_id:
            where_filter["feed_id"] = feed_id
            
        # Search in semantic memory
        client = chroma.get_client()
        collection = client.get_or_create_collection(name="semantic_memory")
        
        results = collection.query(
            query_texts=[query],
            n_results=limit,
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
                items.append(item)
                
        logger.info(f"Found {len(items)} RSS items for query: {query}")
        return items
        
    except Exception as e:
        logger.error(f"Error searching RSS items: {str(e)}")
        return []

def get_feed_stats() -> Dict[str, Any]:
    """
    Get statistics about RSS feeds.
    
    Returns:
        Dictionary with feed statistics
    """
    try:
        feeds = _load_feeds()
        
        # Calculate basic stats
        feed_count = len(feeds)
        item_count = sum(feed.get("items_count", 0) for feed in feeds)
        
        # Count by category
        categories = {}
        for feed in feeds:
            category = feed.get("category", "uncategorized")
            categories[category] = categories.get(category, 0) + 1
            
        # Get latest update
        latest_update = None
        for feed in feeds:
            last_update = feed.get("last_update")
            if last_update:
                if latest_update is None or last_update > latest_update:
                    latest_update = last_update
                    
        return {
            "feed_count": feed_count,
            "item_count": item_count,
            "categories": categories,
            "latest_update": latest_update
        }
        
    except Exception as e:
        logger.error(f"Error getting feed stats: {str(e)}")
        return {"error": str(e)}
