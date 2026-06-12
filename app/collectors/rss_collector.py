"""
RSS collector for Personal Signal OS.

Supports source definitions from:
- config/sources.yaml
- data/sources.yaml

Fallback:
- data/rss_sources.txt (legacy one-url-per-line format)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List

import feedparser

from app.collectors.base_collector import BaseCollector
from app.config import config
from app.models import ContentItem, SourceBias, SourceType
from app.processing.normalizer import map_source_bias

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


class RSSCollector(BaseCollector):
    """Collect RSS items from configured feeds."""

    def __init__(self, config_paths: List[Path] = None):
        super().__init__(SourceType.RSS)
        root = config.PROJECT_ROOT
        self.config_paths = config_paths or [
            root / "config" / "sources.yaml",
            root / "data" / "sources.yaml",
        ]
        self.legacy_sources_file = config.RSS_SOURCES_FILE

    def collect(self) -> List[ContentItem]:
        feeds = self._load_feeds()
        if not feeds:
            print("ℹ️  No RSS feeds configured")
            return []

        items: List[ContentItem] = []
        for feed in feeds:
            feed_items = self._fetch_feed(feed)
            items.extend(feed_items)

        return items

    def _load_feeds(self) -> List[Dict[str, object]]:
        if yaml is not None:
            for path in self.config_paths:
                if path.exists():
                    try:
                        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                        rss = payload.get("rss", [])
                        parsed = []
                        for entry in rss:
                            url = (entry or {}).get("url")
                            if not url:
                                continue
                            parsed.append(
                                {
                                    "name": (entry or {}).get("name", "RSS Feed"),
                                    "url": url,
                                    "source_type": (entry or {}).get("source_type", "unknown"),
                                    "topics": (entry or {}).get("topics", []),
                                }
                            )
                        if parsed:
                            print(f"📰 RSS sources loaded from {path}")
                            return parsed
                    except Exception as exc:
                        print(f"⚠️  Failed to parse {path}: {exc}")

        # Legacy fallback
        if self.legacy_sources_file.exists():
            feeds = []
            for raw in self.legacy_sources_file.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if line and not line.startswith("#"):
                    feeds.append(
                        {
                            "name": "Legacy RSS",
                            "url": line,
                            "source_type": "journalist",
                            "topics": [],
                        }
                    )
            if feeds:
                print(f"📰 RSS sources loaded from {self.legacy_sources_file}")
            return feeds

        return []

    def _fetch_feed(self, feed_cfg: Dict[str, object]) -> List[ContentItem]:
        url = str(feed_cfg.get("url"))
        feed_name = str(feed_cfg.get("name") or "RSS Feed")
        topics = list(feed_cfg.get("topics") or [])
        source_bias = map_source_bias(str(feed_cfg.get("source_type", "unknown")))

        try:
            feed = feedparser.parse(url)
        except Exception as exc:
            print(f"⚠️  RSS fetch failed for {url}: {exc}")
            return []

        if getattr(feed, "bozo", False):
            bozo_exception = getattr(feed, "bozo_exception", None)
            if bozo_exception:
                print(f"⚠️  RSS parse warning for {url}: {bozo_exception}")

        items: List[ContentItem] = []
        for entry in getattr(feed, "entries", [])[:15]:
            title = entry.get("title", "Untitled RSS item")
            summary = entry.get("summary") or entry.get("description") or ""
            link = entry.get("link")
            author = entry.get("author") or feed_name
            timestamp = self._parse_timestamp(entry)

            item = self._create_item(
                title=title,
                content=summary,
                author=author,
                timestamp=timestamp,
                url=link,
                raw_path=url,
                source_bias=source_bias,
                topics=[str(topic).lower() for topic in topics],
            )
            items.append(item)

        print(f"  ✓ {feed_name}: {len(items)} items")
        return items

    @staticmethod
    def _parse_timestamp(entry: dict) -> datetime:
        for key in ("published_parsed", "updated_parsed"):
            parsed = entry.get(key)
            if parsed:
                try:
                    import time

                    return datetime.fromtimestamp(time.mktime(parsed))
                except Exception:
                    pass
        return datetime.now()
