"""MVP tests for Personal Signal OS."""

from datetime import datetime, timedelta

from app.models import (
    Claim,
    ContentItem,
    DailyBrief,
    EvidenceLevel,
    Signal,
    SourceBias,
    SourceType,
    ThinkingMirror,
)
from app.processing.claim_extractor import ClaimExtractor
from app.processing.deduplicator import deduplicate_items
from app.processing.normalizer import normalize_for_signal_os
from app.processing.opportunity_extractor import OpportunityExtractor
from app.processing.signal_scorer import SignalScorer
from app.brief.markdown_renderer import MarkdownRenderer


def test_rss_item_normalization():
    item = ContentItem(
        source=SourceType.RSS,
        title="AI grant deadline announced",
        content="Apply by 2026-07-01 for startup grant in Helsinki.",
        author="Tech Feed",
        timestamp=datetime.now(),
        url="https://example.com/post/1",
        source_bias=SourceBias.JOURNALIST,
    )

    normalized = normalize_for_signal_os([item])[0]

    assert normalized.source_type in {"journalist", "community", "unknown"}
    assert normalized.id
    assert normalized.text
    assert isinstance(normalized.topics, list)


def test_signal_scoring_classification():
    scorer = SignalScorer(
        goals="current_focus:\n- startup\n- ai\n",
        current_state="decision_deadlines:\n  - date: '2026-07-02'\n    description: 'application result'\n",
    )
    item = ContentItem(
        source=SourceType.RSS,
        title="Startup internship application deadline",
        content="Apply now. Deadline 2026-06-12. Hiring AI intern.",
        author="Jobs Feed",
        timestamp=datetime.now(),
        source_bias=SourceBias.JOURNALIST,
    )

    scored = scorer.score_item(item)

    assert scored.signal_score >= 3.0
    assert scored.signal_type.value in {"signal", "opportunity", "verify", "weak_signal"}


def test_opportunity_detection():
    extractor = OpportunityExtractor()
    item = ContentItem(
        source=SourceType.RSS,
        title="Hackathon applications open",
        content="Join the hackathon. Application deadline is 2026-06-20.",
        author="Community",
        timestamp=datetime.now(),
    )

    opp = extractor.extract_from_item(item)

    assert opp is not None
    assert opp.opportunity_type in {"hackathon", "application", "event"}


def test_claim_card_creation():
    extractor = ClaimExtractor()
    item = ContentItem(
        source=SourceType.RSS,
        title="Study claims 40% productivity increase",
        content="A new study shows teams improved productivity by 40% after adopting tooling.",
        author="News",
        timestamp=datetime.now(),
        source_bias=SourceBias.JOURNALIST,
    )

    claims = extractor.extract_from_item(item)

    assert len(claims) >= 1
    claim = claims[0]
    assert isinstance(claim, Claim)
    assert claim.evidence_level in {
        EvidenceLevel.DATA,
        EvidenceLevel.RESEARCH,
        EvidenceLevel.UNKNOWN,
        EvidenceLevel.ANECDOTE,
        EvidenceLevel.OFFICIAL,
    }


def test_markdown_brief_rendering():
    brief = DailyBrief(
        date="2026-06-10",
        top_signals=[
            Signal(
                title="Important signal",
                content="Signal body",
                source="Feed",
                source_type=SourceType.RSS,
                score=7.4,
                why_matters="Can affect near-term decision",
                suggested_action="Review details and decide by evening",
                url="https://example.com",
            )
        ],
        thinking_mirror=ThinkingMirror(
            repeated_focus="AI and opportunities",
            possible_blind_spot="Official sources missing",
            possible_bias="Recency bias",
            one_question="What if this assumption is wrong?",
        ),
        recommended_action_today="Send one concrete application.",
        sources_used=["Feed"],
        collected_items_count=3,
        scored_items_count=3,
    )

    md = MarkdownRenderer().render(brief)

    assert "## 1. Top Signals" in md
    assert "## 5. Thinking Mirror" in md
    assert "## 6. Recommended Action Today" in md


def test_deduplication_rules_same_url_and_similar_title():
    base_time = datetime.now()
    item_a = ContentItem(
        source=SourceType.RSS,
        title="AI startup raises funding",
        content="Same article beginning text... details follow",
        author="Feed A",
        timestamp=base_time,
        url="https://example.com/a",
    )
    item_b = ContentItem(
        source=SourceType.RSS,
        title="AI startup raises funding!",
        content="Same article beginning text... different ending",
        author="Feed B",
        timestamp=base_time + timedelta(minutes=1),
        url="https://example.com/a",
    )

    deduped = deduplicate_items([item_a, item_b], existing_hashes=set())

    assert len(deduped) == 1
