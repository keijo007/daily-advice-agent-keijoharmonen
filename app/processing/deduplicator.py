"""
Signal OS deduplicator.

Deduplication rules:
- same URL
- similar title
- similar normalized text beginning
- same source + same published_at + same title
- known content hash already stored
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Iterable, List, Set

from app.models import ContentItem


def deduplicate_items(items: List[ContentItem], existing_hashes: Set[str]) -> List[ContentItem]:
    """Deduplicate by hash, URL, title similarity and source/timestamp combos."""
    deduped: List[ContentItem] = []

    seen_hashes = set(existing_hashes)
    seen_urls = set()
    seen_keys = set()

    for item in items:
        item_hash = item.compute_hash()
        if item_hash in seen_hashes:
            continue

        if item.url:
            clean_url = item.url.strip().lower()
            if clean_url in seen_urls:
                continue

        key = _stable_key(item)
        if key in seen_keys:
            continue

        if _is_similar_to_any(item, deduped):
            continue

        deduped.append(item)
        seen_hashes.add(item_hash)
        seen_keys.add(key)
        if item.url:
            seen_urls.add(item.url.strip().lower())

    return deduped


def _stable_key(item: ContentItem) -> str:
    ts = item.timestamp.strftime("%Y-%m-%d")
    return f"{item.source.value}|{ts}|{_normalize(item.title)}"


def _normalize(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def _prefix(text: str, n: int = 140) -> str:
    return _normalize(text)[:n]


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _is_similar_to_any(item: ContentItem, existing: Iterable[ContentItem]) -> bool:
    candidate_title = _normalize(item.title)
    candidate_prefix = _prefix(item.content)

    for other in existing:
        title_ratio = _similarity(candidate_title, _normalize(other.title))
        if title_ratio >= 0.94:
            return True

        prefix_ratio = _similarity(candidate_prefix, _prefix(other.content))
        if prefix_ratio >= 0.92:
            return True

    return False
