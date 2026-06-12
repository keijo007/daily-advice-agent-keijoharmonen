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

from app.models import ContentItem, DailyInsight, SourceType, DailyBrief, ScoredItem


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
        self.conn = None
        self._init_db()

    def connect(self):
        """Open a persistent SQLite connection for storage operations."""
        self.disconnect()
        self.conn = sqlite3.connect(self.db_path)
        self._init_db()

    def disconnect(self):
        """Close the persistent SQLite connection if it is open."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

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

            # Daily insights table (DEPRECATED: kept for backward compatibility)
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

            # Scored items table (NEW: for Signal OS)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scored_items (
                    id INTEGER PRIMARY KEY,
                    item_hash TEXT UNIQUE NOT NULL,
                    signal_score REAL NOT NULL,
                    signal_type TEXT NOT NULL,
                    reasoning TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Daily briefs table (NEW: for Signal OS)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_briefs (
                    id INTEGER PRIMARY KEY,
                    date TEXT UNIQUE NOT NULL,
                    brief_json TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Feedback table (NEW: for future scoring tuning)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY,
                    feedback_date TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    rating TEXT NOT NULL,
                    note TEXT,
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
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_scored_items_hash
                ON scored_items(item_hash)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_daily_briefs_date
                ON daily_briefs(date)
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

    def get_existing_hashes(self):
        """Return the set of hashes already stored for content items."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT hash FROM content_items")
            return {row[0] for row in cursor.fetchall()}

    def save_items(self, items: List[ContentItem]) -> int:
        """Save a batch of content items and return how many were newly stored."""
        saved_count = 0
        for item in items:
            if self.save_content_item(item):
                saved_count += 1
        return saved_count

    def save_insight(self, insight: DailyInsight) -> bool:
        """Save a DailyInsight using the current storage contract."""
        return self.save_daily_insight(insight)

    # ==================== NEW: Signal OS Methods ====================
    
    def save_daily_brief(self, brief: DailyBrief) -> bool:
        """
        Save a DailyBrief (Signal OS output).
        
        Returns: True if saved, False if already exists for this date.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO daily_briefs (date, brief_json)
                    VALUES (?, ?)
                """, (brief.date, brief.to_json()))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Already exists for this date
                return False
    
    def get_daily_brief(self, date: str) -> Optional[DailyBrief]:
        """Get a DailyBrief for a specific date."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT brief_json FROM daily_briefs WHERE date = ?
            """, (date,))
            row = cursor.fetchone()
            if not row:
                return None
            
            # Parse and reconstruct DailyBrief from JSON
            data = json.loads(row[0])
            return self._dict_to_daily_brief(data)
    
    def get_latest_brief(self) -> Optional[DailyBrief]:
        """Get the most recent DailyBrief."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT brief_json FROM daily_briefs
                ORDER BY date DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if not row:
                return None
            
            data = json.loads(row[0])
            return self._dict_to_daily_brief(data)

    def get_recent_briefs(self, limit: int = 7) -> List[DailyBrief]:
        """Get recent DailyBriefs (latest first)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT brief_json FROM daily_briefs
                ORDER BY date DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            briefs: List[DailyBrief] = []
            for row in rows:
                data = json.loads(row[0])
                briefs.append(self._dict_to_daily_brief(data))
            return briefs
    
    @staticmethod
    def _dict_to_daily_brief(data: dict) -> DailyBrief:
        """Helper to reconstruct DailyBrief from dict."""
        from app.models import Signal, Opportunity, Claim, WeakSignal, ThinkingMirror, EvidenceLevel, SourceBias, SourceType
        
        brief = DailyBrief(date=data.get("date", ""))
        
        # Reconstruct signals
        brief.top_signals = [
            Signal(
                item_id=s.get("item_id", None),
                title=s["title"],
                content=s["content"],
                source=s["source"],
                source_type=SourceType(s["source_type"]),
                score=s["score"],
                why_matters=s["why_matters"],
                suggested_action=s["suggested_action"],
                url=s.get("url"),
                topics=s.get("topics", []),
            )
            for s in data.get("top_signals", [])
        ]
        
        # Reconstruct opportunities
        brief.opportunities = [
            Opportunity(
                title=o["title"],
                description=o["description"],
                why_relevant=o["why_relevant"],
                deadline=datetime.fromisoformat(o["deadline"]) if o.get("deadline") else None,
                next_action=o.get("next_action", ""),
                source=o.get("source", ""),
                url=o.get("url"),
                opportunity_type=o.get("opportunity_type", ""),
            )
            for o in data.get("opportunities", [])
        ]
        
        # Reconstruct claims
        brief.claims_to_verify = [
            Claim(
                claim_text=c["claim_text"],
                source=c["source"],
                source_bias=SourceBias(c["source_bias"]),
                evidence_level=EvidenceLevel(c["evidence_level"]),
                possible_bias=c["possible_bias"],
                how_to_verify=c["how_to_verify"],
                recommended_action=c["recommended_action"],
            )
            for c in data.get("claims_to_verify", [])
        ]
        
        # Reconstruct weak signals
        brief.weak_signals = [
            WeakSignal(
                title=w["title"],
                content=w["content"],
                source=w["source"],
                why_weak=w["why_weak"],
                url=w.get("url"),
            )
            for w in data.get("weak_signals", [])
        ]
        
        # Reconstruct thinking mirror
        if data.get("thinking_mirror"):
            tm = data["thinking_mirror"]
            brief.thinking_mirror = ThinkingMirror(
                repeated_focus=tm.get("repeated_focus", ""),
                possible_blind_spot=tm.get("possible_blind_spot", ""),
                possible_bias=tm.get("possible_bias", ""),
                one_question=tm.get("one_question", ""),
                suggested_adjustment=tm.get("suggested_adjustment"),
            )
        
        brief.recommended_action_today = data.get("recommended_action_today", "")
        brief.low_priority_noise = data.get("low_priority_noise", [])
        brief.sources_used = data.get("sources_used", [])
        brief.collected_items_count = data.get("collected_items_count", 0)
        brief.scored_items_count = data.get("scored_items_count", 0)
        
        return brief
    
    def save_scored_item(self, scored_item: ScoredItem) -> bool:
        """
        Save a scored item.
        
        Returns: True if saved, False if already exists.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO scored_items (item_hash, signal_score, signal_type, reasoning)
                    VALUES (?, ?, ?, ?)
                """, (
                    scored_item.item.compute_hash(),
                    scored_item.signal_score,
                    scored_item.signal_type.value,
                    scored_item.reasoning,
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_scored_items_by_type(self, signal_type: str, limit: int = 10):
        """Get scored items of a specific type."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT item_hash, signal_score, signal_type, reasoning
                FROM scored_items
                WHERE signal_type = ?
                ORDER BY signal_score DESC
                LIMIT ?
            """, (signal_type, limit))
            
            return cursor.fetchall()
    
    def save_feedback(self, feedback: 'Feedback') -> bool:
        """
        Save user feedback on an item.
        
        Returns: True if saved.
        """
        from app.models import Feedback
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO feedback (feedback_date, item_id, rating, note)
                VALUES (?, ?, ?, ?)
            """, (feedback.date, feedback.item_id, feedback.rating, feedback.note))
            conn.commit()
            return True
    
    def get_feedback_for_item(self, item_id: str) -> list:
        """Get all feedback for a specific item."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT feedback_date, rating, note FROM feedback
                WHERE item_id = ?
                ORDER BY feedback_date DESC
            """, (item_id,))
            return cursor.fetchall()
