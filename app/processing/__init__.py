"""Processing module for Personal Signal OS."""

from app.processing.claim_extractor import ClaimExtractor
from app.processing.deduplicator import deduplicate_items
from app.processing.normalizer import (
	enrich_content_item,
	map_source_bias,
	normalize_for_signal_os,
	to_normalized_item,
)
from app.processing.opportunity_extractor import OpportunityExtractor
from app.processing.signal_scorer import SignalScorer

__all__ = [
	"ClaimExtractor",
	"OpportunityExtractor",
	"SignalScorer",
	"deduplicate_items",
	"enrich_content_item",
	"map_source_bias",
	"normalize_for_signal_os",
	"to_normalized_item",
]
