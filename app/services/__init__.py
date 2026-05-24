"""
Services package - data processing and external API integration.

This layer handles:
- normalize: Convert all data to ContentItem
- deduplicate: Remove duplicates by hash
- storage: SQLite persistence
- openai_client: API calls
- quote_preserving_summary: Extract key quotes while summarizing
- daily_pipeline: Orchestrate all services

AGENT ARCHITECTURE PATTERN:
Raw Data → Collectors → Normalize → Deduplicate → Store → Agents
"""

from app.services.normalize import normalize_item, normalize_items, validate_item
from app.services.deduplicate import deduplicate_items, get_hashes_from_items
from app.services.storage import StorageService
from app.services.openai_client import OpenAIClient, call_openai, call_openai_json
from app.services.quote_preserving_summary import (
    extract_key_quotes,
    summarize_preserving_quotes,
    create_briefing,
)

__all__ = [
    "normalize_item",
    "normalize_items",
    "validate_item",
    "deduplicate_items",
    "get_hashes_from_items",
    "StorageService",
    "OpenAIClient",
    "call_openai",
    "call_openai_json",
    "extract_key_quotes",
    "summarize_preserving_quotes",
    "create_briefing",
]
