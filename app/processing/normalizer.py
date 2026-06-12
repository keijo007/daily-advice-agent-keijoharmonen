"""
Signal OS normalizer.

Enriches collected ContentItem records with lightweight structured metadata
(topics, claims, people, places, deadlines) and creates NormalizedItem output.
"""

from __future__ import annotations

from datetime import datetime
import re
from typing import List, Optional

from app.models import ContentItem, NormalizedItem, SourceBias, SourceType


TOPIC_KEYWORDS = {
    "ai": ["ai", "llm", "model", "openai", "agent", "machine learning", "ml"],
    "startup": ["startup", "founder", "seed", "mvp", "product-market fit"],
    "funding": ["funding", "grant", "investor", "vc", "capital", "raise"],
    "career": ["job", "hiring", "internship", "position", "career"],
    "education": ["university", "scholarship", "course", "study", "degree"],
    "community": ["meetup", "community", "event", "conference", "hackathon"],
}

PLACE_HINTS = [
    "helsinki", "espoo", "tampere", "turku", "finland", "estonia", "sweden",
    "berlin", "london", "new york", "san francisco", "remote",
]


def map_source_bias(source_hint: Optional[str]) -> SourceBias:
    """Map source hint text to SourceBias enum."""
    if not source_hint:
        return SourceBias.UNKNOWN

    hint = source_hint.strip().lower()
    if hint in {"founder", "operator"}:
        return SourceBias.OPERATOR
    if hint == "investor":
        return SourceBias.INVESTOR
    if hint == "journalist":
        return SourceBias.JOURNALIST
    if hint == "research":
        return SourceBias.RESEARCH
    if hint == "official":
        return SourceBias.OFFICIAL
    if hint == "community":
        return SourceBias.COMMUNITY
    if hint == "personal":
        return SourceBias.PERSONAL

    # Fallback from known SourceType labels
    if hint in {SourceType.DIARY.value, SourceType.GOALS.value, SourceType.PERSONAL.value}:
        return SourceBias.PERSONAL
    if hint in {SourceType.RSS.value, SourceType.YOUTUBE.value, SourceType.TELEGRAM.value}:
        return SourceBias.COMMUNITY

    return SourceBias.UNKNOWN


def enrich_content_item(
    item: ContentItem,
    source_bias: Optional[SourceBias] = None,
    configured_topics: Optional[List[str]] = None,
) -> ContentItem:
    """Fill missing structured fields on ContentItem with heuristics."""
    text = f"{item.title} {item.content}".lower()

    if item.source_bias == SourceBias.UNKNOWN:
        item.source_bias = source_bias or map_source_bias(item.source.value)

    if not item.topics:
        topics = []
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                topics.append(topic)
        if configured_topics:
            for topic in configured_topics:
                if topic and topic.lower() in text and topic.lower() not in topics:
                    topics.append(topic.lower())
        item.topics = topics

    if not item.people:
        # Naive person extraction: 2-word capitalized names.
        people = re.findall(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b", f"{item.title} {item.content}")
        item.people = list(dict.fromkeys(people))[:8]

    if not item.places:
        places = [place for place in PLACE_HINTS if place in text]
        item.places = list(dict.fromkeys(places))

    if not item.claims:
        item.claims = _extract_claims(item.content)

    if not item.deadline:
        item.deadline = _extract_deadline(item.content) or _extract_deadline(item.title)

    if item.actionability_score <= 0:
        item.actionability_score = _estimate_actionability(text)

    return item


def to_normalized_item(item: ContentItem) -> NormalizedItem:
    """Convert ContentItem to NormalizedItem schema."""
    return NormalizedItem(
        id=item.compute_hash(),
        source=item.author or item.source.value,
        source_type=item.source_bias.value,
        title=item.title or None,
        author=item.author or None,
        text=item.content,
        url=item.url,
        published_at=item.timestamp,
        captured_at=datetime.now(),
        topics=item.topics,
        people=item.people,
        places=item.places,
        claims=item.claims,
        deadline=item.deadline,
        raw=item.to_dict(),
    )


def normalize_for_signal_os(
    items: List[ContentItem],
    source_bias: Optional[SourceBias] = None,
    configured_topics: Optional[List[str]] = None,
) -> List[NormalizedItem]:
    """Enrich items and convert to NormalizedItem list."""
    normalized = []
    for item in items:
        enrich_content_item(item, source_bias=source_bias, configured_topics=configured_topics)
        normalized.append(to_normalized_item(item))
    return normalized


def _extract_claims(content: str) -> List[str]:
    claims = []
    sentences = [s.strip() for s in re.split(r"[.!?]", content) if s.strip()]
    for sentence in sentences:
        lowered = sentence.lower()
        if len(sentence) < 25:
            continue
        if any(
            marker in lowered
            for marker in ["according to", "study", "data", "shows", "reported", "will", "is", "are"]
        ):
            claims.append(sentence)
        if len(claims) >= 6:
            break
    return claims


def _extract_deadline(text: str) -> Optional[datetime]:
    # YYYY-MM-DD
    iso_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    if iso_match:
        try:
            return datetime.fromisoformat(iso_match.group(1))
        except ValueError:
            pass

    # DD/MM/YYYY
    slash_match = re.search(r"\b(\d{1,2}/\d{1,2}/20\d{2})\b", text)
    if slash_match:
        try:
            return datetime.strptime(slash_match.group(1), "%d/%m/%Y")
        except ValueError:
            pass

    return None


def _estimate_actionability(text: str) -> float:
    score = 0.0
    action_terms = [
        "apply", "register", "join", "contact", "submit", "deadline", "hiring", "event", "job",
    ]
    if any(term in text for term in action_terms):
        score += 0.6
    if "http" in text or "www." in text:
        score += 0.2
    if any(token in text for token in ["today", "tomorrow", "this week", "by "]):
        score += 0.2
    return min(score, 1.0)
