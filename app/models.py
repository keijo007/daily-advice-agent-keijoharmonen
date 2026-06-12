"""
Data models for Daily Insight Agent.

WHY THIS FILE EXISTS:
- Defines the universal data structure that ALL sources are normalized into
- Makes it easy for agents to work with data without knowing the original source
- Uses Python dataclasses + Pydantic for type safety

HOW IT RELATES TO AGENT THINKING:
- Agents need a predictable interface to data
- This schema is the "contract" between collectors and agents
- Enables agents to focus on analysis, not data parsing

HOW TO EXTEND:
- Add new fields to ContentItem if you track new metadata
- Create new enums for new source types (e.g., LINKEDIN, PODCAST)
- Add validation logic (e.g., min content length)
"""

from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
import hashlib
import json


class SourceType(str, Enum):
    """All possible data sources."""
    DIARY = "diary"
    WHATSAPP = "whatsapp"
    RSS = "rss"
    GOALS = "goals"
    PERSONAL = "personal"
    YOUTUBE = "youtube"
    TELEGRAM = "telegram"
    LINKEDIN = "linkedin"
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    # Extension points for future sources:
    # PODCAST = "podcast"
    # EMAIL = "email"


class SourceBias(str, Enum):
    """Classification of source bias/interest."""
    OPERATOR = "operator"  # Founder/CEO - useful for early signals, commercial bias
    INVESTOR = "investor"  # VC/investor - useful for trends, financial bias
    JOURNALIST = "journalist"  # News - useful for broad scanning, may be shallow
    RESEARCH = "research"  # Academic/research - strong for verification
    OFFICIAL = "official"  # Official statements - authoritative but narrow
    COMMUNITY = "community"  # Social/community - useful for weak signals, high noise
    PERSONAL = "personal"  # Diary/goals - subjective, for reflection only
    UNKNOWN = "unknown"  # Unknown source


class SignalType(str, Enum):
    """Classification of items by importance/actionability."""
    SIGNAL = "signal"  # Top 5 items for brief
    WEAK_SIGNAL = "weak_signal"  # May matter if repeated
    OPPORTUNITY = "opportunity"  # Has deadline or action items
    VERIFY = "verify"  # Important claim needing verification
    NOISE = "noise"  # Low priority, likely distractions


class EvidenceLevel(str, Enum):
    """Strength of evidence for claims."""
    ANECDOTE = "anecdote"  # Personal story, no data
    DATA = "data"  # Numbers or metrics
    RESEARCH = "research"  # Peer-reviewed or rigorous study
    OFFICIAL = "official"  # From official source
    UNKNOWN = "unknown"  # Cannot assess


@dataclass
class NormalizedItem:
    """Canonical normalized record used by Signal OS processing."""

    id: str
    source: str
    source_type: str
    title: Optional[str]
    author: Optional[str]
    text: str
    url: Optional[str]
    published_at: Optional[datetime]
    captured_at: datetime
    topics: List[str]
    people: List[str]
    places: List[str]
    claims: List[str]
    deadline: Optional[datetime]
    raw: Dict[str, Any]

    def to_dict(self) -> dict:
        """Convert to JSON-safe dict."""
        return {
            "id": self.id,
            "source": self.source,
            "source_type": self.source_type,
            "title": self.title,
            "author": self.author,
            "text": self.text,
            "url": self.url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "captured_at": self.captured_at.isoformat(),
            "topics": self.topics,
            "people": self.people,
            "places": self.places,
            "claims": self.claims,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "raw": self.raw,
        }


@dataclass
class ContentItem:
    """
    Universal data structure for all content sources.
    
    EXTENDED for Personal Signal OS:
    - Added: topics, people, places, claims, deadline, actionability_score
    - These fields enable signal scoring without LLM (heuristic-based)
    """
    
    source: SourceType
    title: str
    content: str
    author: str
    timestamp: datetime
    url: Optional[str] = None
    raw_path: Optional[str] = None
    
    # Signal OS extensions
    source_bias: SourceBias = SourceBias.UNKNOWN  # Classify source type for bias weighting
    topics: List[str] = None  # ["AI", "startup", "funding"] - for relevance matching
    people: List[str] = None  # People mentioned
    places: List[str] = None  # Geographic locations mentioned
    claims: List[str] = None  # Factual claims to verify
    deadline: Optional[datetime] = None  # If item has urgency date
    actionability_score: float = 0.0  # 0-1: how actionable is this?
    
    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.topics is None:
            self.topics = []
        if self.people is None:
            self.people = []
        if self.places is None:
            self.places = []
        if self.claims is None:
            self.claims = []
    
    def compute_hash(self) -> str:
        """
        Compute unique hash to detect duplicates.
        
        DEDUPLICATION LOGIC:
        - Hash based on content + timestamp (not exact content match)
        - Prevents same diary entry from being stored twice
        - Used by deduplicate.py service
        """
        hash_input = f"{self.source}:{self.content}:{self.author}:{self.timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["source"] = self.source.value
        data["source_bias"] = self.source_bias.value
        data["timestamp"] = self.timestamp.isoformat()
        if data.get("deadline"):
            data["deadline"] = data["deadline"].isoformat()
        data["hash"] = self.compute_hash()
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class DailyInsight:
    """
    The final output structure from the daily pipeline.
    
    This is what gets displayed to the user.
    Generated by coach_agent.py, stored in SQLite, rendered as HTML.
    
    DEPRECATED: Kept for backward compatibility. Use DailyBrief for new Signal OS.
    """
    
    date: str  # YYYY-MM-DD
    main_insight: str  # High-level summary of the day's learnings
    source_summary: str  # What did Reader Agent learn?
    self_reflection: str  # What did Reflection Agent observe about you?
    thinking_biases_detected: List[Dict[str, Any]]  # Specific cognitive biases noticed (objects with name/evidence)
    practical_tip: str  # Concrete, actionable advice
    one_day_action: str  # Something you can do TODAY
    possible_project_idea: Optional[str]  # Optional innovation/project idea
    important_quotes: List[dict]  # [{"quote": "...", "source": "..."}]
    uncertainties: List[str]  # What we're not sure about
    sources_used: List[str]  # Which sources contributed
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON/database storage."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class ScoredItem:
    """ContentItem with signal scoring metadata."""
    item: ContentItem
    signal_score: float  # 0-10 scale
    signal_type: SignalType  # SIGNAL, WEAK_SIGNAL, NOISE, OPPORTUNITY, VERIFY
    reasoning: str  # Why this score?
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "item": self.item.to_dict(),
            "signal_score": self.signal_score,
            "signal_type": self.signal_type.value,
            "reasoning": self.reasoning,
        }


@dataclass
class Signal:
    """Top signal for daily brief."""
    title: str
    content: str
    source: str
    source_type: SourceType
    score: float  # 0-10
    why_matters: str  # LLM-generated explanation
    suggested_action: str  # What to do about it
    url: Optional[str] = None
    topics: List[str] = None
    
    def __post_init__(self):
        if self.topics is None:
            self.topics = []
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "source_type": self.source_type.value,
            "score": self.score,
            "why_matters": self.why_matters,
            "suggested_action": self.suggested_action,
            "url": self.url,
            "topics": self.topics,
        }


@dataclass
class Opportunity:
    """Deadline or action-oriented item."""
    title: str
    description: str
    why_relevant: str  # Why does this matter to you?
    deadline: Optional[datetime] = None
    next_action: str = ""  # First step to take
    source: str = ""
    url: Optional[str] = None
    opportunity_type: str = ""  # event, application, job, grant, hackathon, etc.
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "why_relevant": self.why_relevant,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "next_action": self.next_action,
            "source": self.source,
            "url": self.url,
            "opportunity_type": self.opportunity_type,
        }


@dataclass
class Claim:
    """Factual claim extracted from content."""
    claim_text: str
    source: str
    source_bias: SourceBias
    evidence_level: EvidenceLevel
    possible_bias: str  # Why this source might be biased
    how_to_verify: str  # Suggested verification method
    recommended_action: str  # ignore | follow | verify | act


@dataclass
class WeakSignal:
    """Item that's not clearly important yet but may become important."""
    title: str
    content: str
    source: str
    why_weak: str  # Why we're tracking this
    url: Optional[str] = None


@dataclass
class ThinkingMirror:
    """Personal reflection based on diary and signals."""
    repeated_focus: str  # What you seem to be focusing on
    possible_blind_spot: str  # What might you be missing?
    possible_bias: str  # How might you be biased in your thinking?
    one_question: str  # One useful question for you to consider
    suggested_adjustment: Optional[str] = None  # Optional suggestion


@dataclass
class DailyBrief:
    """
    NEW OUTPUT FORMAT for Personal Signal OS.
    
    Contains all 7 sections of the daily brief:
    1. Top Signals
    2. Opportunities
    3. Claims to Verify
    4. Weak Signals
    5. Thinking Mirror
    6. Recommended Action Today
    7. Low Priority / Noise
    """
    date: str  # YYYY-MM-DD
    
    # Section 1: Top Signals
    top_signals: List[Signal] = None  # 5 items
    
    # Section 2: Opportunities
    opportunities: List[Opportunity] = None  # 5 items
    
    # Section 3: Claims to Verify
    claims_to_verify: List[Claim] = None  # 5 items
    
    # Section 4: Weak Signals
    weak_signals: List[WeakSignal] = None  # Items may matter if repeated
    
    # Section 5: Thinking Mirror
    thinking_mirror: Optional[ThinkingMirror] = None
    
    # Section 6: Recommended Action
    recommended_action_today: str = ""  # One concrete action
    
    # Section 7: Low Priority
    low_priority_noise: List[Dict[str, str]] = None  # title, reason, source
    
    # Metadata
    sources_used: List[str] = None
    collected_items_count: int = 0
    scored_items_count: int = 0
    
    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.top_signals is None:
            self.top_signals = []
        if self.opportunities is None:
            self.opportunities = []
        if self.claims_to_verify is None:
            self.claims_to_verify = []
        if self.weak_signals is None:
            self.weak_signals = []
        if self.low_priority_noise is None:
            self.low_priority_noise = []
        if self.sources_used is None:
            self.sources_used = []
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "date": self.date,
            "top_signals": [s.to_dict() for s in self.top_signals],
            "opportunities": [o.to_dict() for o in self.opportunities],
            "claims_to_verify": [
                {
                    "claim_text": c.claim_text,
                    "source": c.source,
                    "source_bias": c.source_bias.value,
                    "evidence_level": c.evidence_level.value,
                    "possible_bias": c.possible_bias,
                    "how_to_verify": c.how_to_verify,
                    "recommended_action": c.recommended_action,
                }
                for c in self.claims_to_verify
            ],
            "weak_signals": [
                {
                    "title": w.title,
                    "content": w.content,
                    "source": w.source,
                    "why_weak": w.why_weak,
                    "url": w.url,
                }
                for w in self.weak_signals
            ],
            "thinking_mirror": {
                "repeated_focus": self.thinking_mirror.repeated_focus,
                "possible_blind_spot": self.thinking_mirror.possible_blind_spot,
                "possible_bias": self.thinking_mirror.possible_bias,
                "one_question": self.thinking_mirror.one_question,
                "suggested_adjustment": self.thinking_mirror.suggested_adjustment,
            } if self.thinking_mirror else None,
            "recommended_action_today": self.recommended_action_today,
            "low_priority_noise": self.low_priority_noise,
            "sources_used": self.sources_used,
            "collected_items_count": self.collected_items_count,
            "scored_items_count": self.scored_items_count,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class Feedback:
    """User feedback on items (for future scoring tuning)."""
    date: str  # YYYY-MM-DD when feedback was given
    item_id: str  # Hash or ID of the item
    rating: str  # "+", "-", "?", "!"
    note: Optional[str] = None  # Optional explanation


@dataclass
class AgentInput:
    """Input data structure passed to each agent."""
    
    new_items: List[ContentItem]  # Items collected today
    goals: Optional[str]  # Goals file content
    recent_diary: Optional[str]  # Recent diary entries
    previous_insights: Optional[List[DailyInsight]]  # For context (deprecated)
    previous_insight_summaries: Optional[List[str]] = None  # Remote or historical summaries
    current_state: Optional[str] = None  # Current state YAML content (for Signal OS)
    scored_items: List['ScoredItem'] = None  # Scored items (for Signal OS agents)
    
    def __post_init__(self):
        if self.scored_items is None:
            self.scored_items = []
