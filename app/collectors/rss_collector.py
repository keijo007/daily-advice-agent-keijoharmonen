"""
RSS Collector - fetches articles from RSS feeds.

WHY THIS FILE EXISTS:
- RSS feeds are structured, machine-readable sources
- Allows automatic collection of news, blogs, podcasts
- Reader Agent uses these as the primary \"new external input\"

HOW IT WORKS:
- Reads feed URLs from data/rss_sources.txt (one URL per line)
- Fetches latest entries from each feed
- Converts entries to ContentItem
- Handles errors gracefully (one bad feed doesn't break everything)

AGENT RELEVANCE:
- Reader Agent: PRIMARY USER - summarizes these articles
- Reflection Agent: Skips these (external content only)
- Coach Agent: Uses Reader's summary to inform advice

FEED FORMAT:
data/rss_sources.txt contains:
```
https://example.com/feed
https://news.ycombinator.com/rss
# Comments are allowed
```

EXTENSION IDEAS:
- Filter by keywords in title
- Track which articles you've already seen
- Sentiment analysis of headlines
- Category-based organization
- Add podcast feeds (RSS with audio)
"""

import feedparser
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from app.collectors.base_collector import BaseCollector
from app.models import ContentItem, SourceType
from app.config import config


class RSSCollector(BaseCollector):
    """Fetches articles from RSS feeds."""
    
    def __init__(self, sources_file: Path = None):
        """
        Initialize RSS collector.
        
        Args:
            sources_file: Path to file with RSS URLs (one per line)
        """
        super().__init__(SourceType.RSS)
        self.sources_file = sources_file or config.RSS_SOURCES_FILE
    
    def collect(self) -> List[ContentItem]:
        """
        Fetch articles from all configured RSS feeds.
        
        Returns:
            List of ContentItem objects from all feeds
        """
        items = []
        
        if not self.sources_file.exists():
            print(f"ℹ️  RSS sources file not found: {self.sources_file}")
            print(f"   Create {self.sources_file} with one RSS URL per line")
            return items
        
        # Read feed URLs
        feeds = self._load_feed_urls()
        print(f"📰 Found {len(feeds)} RSS feeds to fetch")
        
        for feed_url in feeds:
            try:
                feed_items = self._fetch_feed(feed_url)
                items.extend(feed_items)
                print(f"  ✓ Fetched: {feed_url}")
            except Exception as e:
                print(f"  ✗ Error fetching {feed_url}: {e}")
        
        return items
    
    def _load_feed_urls(self) -> List[str]:
        """Load RSS feed URLs from sources file (skip comments)."""
        urls = []
        try:
            content = self.sources_file.read_text(encoding="utf-8")
            for line in content.strip().split("\n"):
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    urls.append(line)
        except Exception as e:
            print(f"✗ Error reading RSS sources: {e}")
        
        return urls
    
    def _fetch_feed(self, feed_url: str) -> List[ContentItem]:
        """
        Fetch recent entries from one RSS feed.
        
        Args:
            feed_url: URL to RSS feed
        
        Returns:
            List of ContentItem objects from this feed
        """
        items = []
        
        try:
            feed = feedparser.parse(feed_url)
            
            # Check for fetch errors
            if feed.bozo:
                print(f"    ⚠️  Feed parsing warning: {feed.bozo_exception}")
            
            # Get feed title
            feed_title = feed.feed.get("title", "Unknown Feed")
            
            # Process entries (usually 10-20 recent entries)
            for entry in feed.entries[:10]:
                try:
                    # Extract data
                    title = entry.get("title", "No Title")
                    link = entry.get("link", "")
                    summary = entry.get("summary", "")
                    author = entry.get("author", feed_title)
                    
                    # Parse timestamp
                    timestamp = self._parse_timestamp(entry)
                    
                    # Create ContentItem
                    content = f"{summary}\n\n[Read more: {link}]"
                    
                    item = self._create_item(
                        title=title,
                        content=content,
                        author=author,
                        timestamp=timestamp,
                        url=link,
                    )
                    items.append(item)
                    
                except Exception as e:
                    print(f"    ⚠️  Error parsing entry: {e}")
        
        except Exception as e:
            raise Exception(f"Failed to fetch RSS feed {feed_url}: {e}")
        
        return items
    
    def _parse_timestamp(self, entry: dict) -> datetime:
        """Extract and parse timestamp from RSS entry."""
        try:
            # Try published date first
            if "published_parsed" in entry:
                import time
                return datetime.fromtimestamp(time.mktime(entry.published_parsed))
            # Fall back to updated
            elif "updated_parsed" in entry:
                import time
                return datetime.fromtimestamp(time.mktime(entry.updated_parsed))
        except:
            pass
        
        # Default to now if parsing fails
        return datetime.now()
