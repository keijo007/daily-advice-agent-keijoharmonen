"""
Storage service for Daily Insight Agent.

WHY THIS LAYER EXISTS:
- Manages database interactions (SQLite)
- Prevents duplicate entries using content hashing
- Provides clean interface for querying stored data

HOW IT RELATES TO AGENT THINKING:
- Agents query: "What have I learned recently?"
- Storage service returns clean, deduplicated data
- Agents don't need to know about database schema

HOW TO EXTEND:
- Add new query methods (e.g., search_by_date_range)
- Migrate to PostgreSQL for cloud deployment
- Add vector embeddings for semantic search (future)

DATABASE SCHEMA:
- content_items: Raw collected data (diary, WhatsApp, RSS, etc.)
- daily_insights: Final agent outputs (one per day)
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import json

from app.models import ContentItem, DailyInsight, SourceType


class StorageService:
    """
    Manage all data persistence.
    
    DEDUPLICATION STRATEGY:
    - Hash every ContentItem on creation
    - Check if hash exists before saving
    - Prevents same diary entry/RSS article from being stored twice
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Content items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS content_items (
                    id INTEGER PRIMARY KEY,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    author TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    url TEXT,
                    raw_path TEXT,
                    hash TEXT UNIQUE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Daily insights table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_insights (
                    id INTEGER PRIMARY KEY,
                    date TEXT UNIQUE NOT NULL,
                    main_insight TEXT NOT NULL,
                    source_summary TEXT NOT NULL,
                    self_reflection TEXT NOT NULL,
                    thinking_biases_detected TEXT NOT NULL,
                    practical_tip TEXT NOT NULL,
                    one_day_action TEXT NOT NULL,
                    possible_project_idea TEXT,
                    important_quotes TEXT NOT NULL,
                    uncertainties TEXT NOT NULL,
                    sources_used TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_timestamp 
                ON content_items(timestamp DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_hash 
                ON content_items(hash)
            """)

            conn.commit()

    def save_content_item(self, item: ContentItem) -> bool:
        """
        Save a content item if it doesn't already exist (by hash).
        
        Returns: True if saved, False if duplicate.
        """
        item_hash = item.compute_hash()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT INTO content_items 
                    (source, title, content, author, timestamp, url, raw_path, hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.source.value,
                    item.title,
                    item.content,
                    item.author,
                    item.timestamp.isoformat(),
                    item.url,
                    item.raw_path,
                    item_hash,
                ))
                conn.commit()
                return True

            except sqlite3.IntegrityError:
                # Duplicate hash - this item already exists
                return False

    def get_items_since(self, lookback_days: int = 1) -> List[ContentItem]:
        """
        Get all content items from the last N days.
        
        Used by agents to load "today's" data for analysis.
        """
        cutoff_date = datetime.now() - timedelta(days=lookback_days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT source, title, content, author, timestamp, url, raw_path
                FROM content_items
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """, (cutoff_date.isoformat(),))

            items = []
            for row in cursor.fetchall():
                item = ContentItem(
                    source=SourceType(row[0]),
                    title=row[1],
                    content=row[2],
                    author=row[3],
                    timestamp=datetime.fromisoformat(row[4]),
                    url=row[5],
                    raw_path=row[6],
                )
                items.append(item)

            return items

    def save_daily_insight(self, insight: DailyInsight) -> bool:
        """
        Save a daily insight (final agent output).
        
        Returns: True if saved, False if already exists for this date.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT INTO daily_insights 
                    (date, main_insight, source_summary, self_reflection,
                     thinking_biases_detected, practical_tip, one_day_action,
                     possible_project_idea, important_quotes, uncertainties, sources_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    insight.date,
                    insight.main_insight,
                    insight.source_summary,
                    insight.self_reflection,
                    json.dumps(insight.thinking_biases_detected),
                    insight.practical_tip,
                    insight.one_day_action,
                    insight.possible_project_idea,
                    json.dumps(insight.important_quotes),
                    json.dumps(insight.uncertainties),
                    json.dumps(insight.sources_used),
                ))
                conn.commit()
                return True

            except sqlite3.IntegrityError:
                # Already exists for this date
                return False

    def get_daily_insight(self, date: str) -> Optional[DailyInsight]:
        """
        Get insight for a specific date (YYYY-MM-DD format).
        
        Used by web endpoint to display today's (or past) insights.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM daily_insights WHERE date = ?
            """, (date,))

            row = cursor.fetchone()
            if not row:
                return None

            return DailyInsight(
                date=row[1],
                main_insight=row[2],
                source_summary=row[3],
                self_reflection=row[4],
                thinking_biases_detected=json.loads(row[5]),
                practical_tip=row[6],
                one_day_action=row[7],
                possible_project_idea=row[8],
                important_quotes=json.loads(row[9]),
                uncertainties=json.loads(row[10]),
                sources_used=json.loads(row[11]),
            )

    def get_latest_insight(self) -> Optional[DailyInsight]:
        """Get the most recent insight (typically today's)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM daily_insights
                ORDER BY date DESC
                LIMIT 1
            """)

            row = cursor.fetchone()
            if not row:
                return None

            return DailyInsight(
                date=row[1],
                main_insight=row[2],
                source_summary=row[3],
                self_reflection=row[4],
                thinking_biases_detected=json.loads(row[5]),
                practical_tip=row[6],
                one_day_action=row[7],
                possible_project_idea=row[8],
                important_quotes=json.loads(row[9]),
                uncertainties=json.loads(row[10]),
                sources_used=json.loads(row[11]),
            )

    def get_all_insights(self, limit: int = 30) -> List[DailyInsight]:
        """Get recent insights for history view."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM daily_insights
                ORDER BY date DESC
                LIMIT ?
            """, (limit,))

            insights = []
            for row in cursor.fetchall():
                insight = DailyInsight(
                    date=row[1],
                    main_insight=row[2],
                    source_summary=row[3],
                    self_reflection=row[4],
                    thinking_biases_detected=json.loads(row[5]),
                    practical_tip=row[6],
                    one_day_action=row[7],
                    possible_project_idea=row[8],
                    important_quotes=json.loads(row[9]),
                    uncertainties=json.loads(row[10]),
                    sources_used=json.loads(row[11]),
                )
                insights.append(insight)

            return insights
