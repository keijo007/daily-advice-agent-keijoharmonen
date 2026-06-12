"""
Personal Signal OS pipeline.

Flow:
1. Source collectors
2. Normalization
3. Deduplication
4. Storage
5. Signal scoring
6. Agent analysis
7. Daily Markdown brief generation
8. Feedback-ready outputs
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.agents.brief_synthesizer import BriefSynthesizer
from app.agents.claim_checker_agent import ClaimCheckerAgent
from app.agents.opportunity_agent import OpportunityAgent
from app.agents.reflection_agent_v2 import ReflectionAgentV2
from app.agents.signal_summary_agent import SignalSummaryAgent
from app.brief.markdown_renderer import MarkdownRenderer
from app.collectors import (
    CalendarCollectorStub,
    GmailCollectorStub,
    LocalMarkdownCollector,
    OutlookCollectorStub,
    RSSCollector,
    TelegramCollectorStub,
    YouTubeCollectorStub,
    GmailCollector,
    OutlookCollector,
    TelegramCollector,
    YouTubeCollector,
    LinkedInExportCollector,
    WhatsAppCollector,
)
from app.config import config
from app.models import ContentItem, DailyBrief, SignalType, WeakSignal
from app.processing.claim_extractor import ClaimExtractor
from app.processing.deduplicator import deduplicate_items
from app.processing.normalizer import enrich_content_item, normalize_for_signal_os
from app.processing.signal_scorer import SignalScorer
from app.services.normalize import normalize_items
from app.services.openai_client import OpenAIClient
from app.services.storage import StorageService

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


class DailyPipeline:
    """Main orchestrator for Personal Signal OS."""

    def __init__(self, sources_path: Optional[Path] = None, settings_path: Optional[Path] = None):
        self.project_root = config.PROJECT_ROOT
        self.data_dir = self.project_root / "data"
        self.outputs_dir = self.project_root / "outputs" / "daily_briefs"

        self.sources_path = sources_path or self._resolve_first_existing(
            [
                self.project_root / "config" / "sources.yaml",
                self.project_root / "data" / "sources.yaml",
                self.project_root / "config" / "sources.example.yaml",
                self.project_root / "config" / "sources.yaml.example",
            ]
        )
        self.settings_path = settings_path or self._resolve_first_existing(
            [
                self.project_root / "config" / "settings.yaml",
                self.project_root / "config" / "settings.example.yaml",
                self.project_root / "config" / "settings.yaml.example",
            ]
        )

        self.settings = self._load_yaml(self.settings_path)
        self.storage = StorageService(config.DB_PATH)
        self.storage.connect()

        self.openai_client = self._build_openai_client()
        self.collectors = self._build_collectors()

    # ---------------- Public API ----------------

    def collect(self) -> List[ContentItem]:
        """Collect raw items from configured sources."""
        collected: List[ContentItem] = []
        for collector in self.collectors:
            try:
                items = collector.collect()
                collected.extend(items)
                print(f"✓ {collector.__class__.__name__}: {len(items)} items")
            except Exception as exc:
                print(f"⚠️  Collector failed ({collector.__class__.__name__}): {exc}")

        self._append_jsonl(self.data_dir / "raw_items.jsonl", [item.to_dict() for item in collected])
        return collected

    def normalize_and_store(self, items: List[ContentItem]) -> List[ContentItem]:
        """Normalize, enrich, deduplicate and persist items."""
        normalized = normalize_items(items)
        for item in normalized:
            enrich_content_item(item)

        existing_hashes = self.storage.get_existing_hashes()
        deduped = deduplicate_items(normalized, existing_hashes)

        self.storage.save_items(deduped)

        normalized_records = normalize_for_signal_os(deduped)
        self._append_jsonl(self.data_dir / "normalized_items.jsonl", [row.to_dict() for row in normalized_records])

        return deduped

    def score(self, items: List[ContentItem], goals: Optional[str], current_state: Optional[str]):
        """Score normalized items and persist scored output."""
        scorer = SignalScorer(goals=goals, current_state=current_state)
        scored_items = scorer.score_items(items)

        for scored in scored_items:
            self.storage.save_scored_item(scored)

        self._append_jsonl(self.data_dir / "scored_items.jsonl", [s.to_dict() for s in scored_items])
        return scored_items

    def generate_brief(
        self,
        scored_items,
        goals: Optional[str],
        current_state: Optional[str],
        recent_diary: Optional[str],
    ) -> Tuple[DailyBrief, Path]:
        """Run agent modules and render daily Markdown brief."""
        brief_cfg = (self.settings.get("brief") or {})
        max_signals = int(brief_cfg.get("max_top_signals", 5))
        max_weak = int(brief_cfg.get("max_weak_signals", 5))

        sorted_scored = sorted(scored_items, key=lambda s: s.signal_score, reverse=True)
        signal_candidates = [s for s in sorted_scored if s.signal_type != SignalType.NOISE][:max_signals]
        weak_candidates = [s for s in sorted_scored if s.signal_type == SignalType.WEAK_SIGNAL][:max_weak]

        signal_agent = SignalSummaryAgent(openai_client=self.openai_client)
        signals = signal_agent.process(signal_candidates)

        # Preserve source voice by appending direct quote excerpt from each source item.
        for signal, source_item in zip(signals, signal_candidates):
            excerpt = self._source_voice_excerpt(source_item.item.content)
            if excerpt:
                signal.content = excerpt

        all_items = [s.item for s in scored_items]
        opportunities = OpportunityAgent().process(OpportunityExtractor().extract_opportunities(all_items))
        claims = ClaimCheckerAgent().process(ClaimExtractor().extract_claims(all_items))

        weak_signals = [
            WeakSignal(
                title=s.item.title,
                content=s.item.content[:240],
                source=s.item.author or s.item.source.value,
                why_weak=s.reasoning,
                url=s.item.url,
            )
            for s in weak_candidates
        ]

        privacy_cfg = (self.settings.get("privacy") or {})
        allow_diary_llm = bool(privacy_cfg.get("allow_external_llm_for_diary", False))
        reflection = ReflectionAgentV2(
            openai_client=self.openai_client if allow_diary_llm else None,
            allow_external_llm_for_diary=allow_diary_llm,
        )
        previous_context = self._recent_brief_context(recent_briefs)
        context_with_history = current_state or ""
        if previous_context:
            context_with_history = (
                f"{context_with_history}\n\nprevious_brief_context:\n{previous_context}".strip()
            )

        thinking_mirror = reflection.process(
            scored_items,
            recent_diary,
            goals,
            context_with_history,
        )

        recent_briefs = self.storage.get_recent_briefs(limit=7)
        feedback_counts = self._build_feedback_map()

        # Boost/deprioritize scored items based on historical feedback memory.
        for scored in scored_items:
            item_id = scored.item.compute_hash()
            fb = feedback_counts.get(item_id, {"+": 0, "-": 0, "!": 0})
            scored.signal_score += 0.3 * fb.get("+", 0)
            scored.signal_score += 0.6 * fb.get("!", 0)
            scored.signal_score -= 0.4 * fb.get("-", 0)
            scored.signal_score = max(0.0, min(10.0, scored.signal_score))

        synthesizer = BriefSynthesizer(openai_client=self.openai_client)
        brief = synthesizer.synthesize(
            date=datetime.now().strftime("%Y-%m-%d"),
            scored_items=scored_items,
            signals=signals,
            opportunities=opportunities,
            claims=claims,
            weak_signals=weak_signals,
            thinking_mirror=thinking_mirror,
            goals=goals,
            current_state=current_state,
        )

        # Add continuity note from previous days.
        if recent_briefs:
            continuity_note = self._build_continuity_note(recent_briefs)
            if continuity_note:
                brief.low_priority_noise.insert(
                    0,
                    {
                        "title": "Continuity note",
                        "reason": continuity_note,
                        "source": "memory",
                    },
                )

        self.storage.save_daily_brief(brief)

        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.outputs_dir / f"{brief.date}.md"
        MarkdownRenderer().save_to_file(brief, str(output_path))

        return brief, output_path

    def run(self) -> Optional[DailyBrief]:
        """Run full daily flow and return generated brief."""
        return self.run_daily()

    def run_daily(self) -> Optional[DailyBrief]:
        """Collect -> normalize -> score -> brief."""
        print("\n" + "=" * 68)
        print("PERSONAL SIGNAL OS - DAILY INTELLIGENCE BRIEF")
        print("=" * 68)

        raw_items = self.collect()
        if not raw_items:
            print("ℹ️  No items collected. Creating empty brief context.")

        normalized_items = self.normalize_and_store(raw_items)
        goals, current_state, recent_diary = self._load_personal_context()
        scored_items = self.score(normalized_items, goals, current_state)

        brief, output_path = self.generate_brief(scored_items, goals, current_state, recent_diary)
        print(f"✓ Daily brief saved: {output_path}")

        return brief

    # ---------------- Internal helpers ----------------

    def _build_collectors(self):
        collectors = [
            RSSCollector(),
            LocalMarkdownCollector(self.sources_path),
        ]

        sources_cfg = self._load_yaml(self.sources_path)
        settings_sources = self.settings.get("sources") or {}

        include_email = bool((sources_cfg.get("email") or {}).get("enabled")) or bool(
            settings_sources.get("include_email")
        )
        include_social = bool((sources_cfg.get("social") or {}).get("enabled")) or bool(
            settings_sources.get("include_social_media")
        )
        include_calendar = bool((sources_cfg.get("calendar") or {}).get("enabled")) or bool(
            settings_sources.get("include_calendar")
        )

        # Email (Gmail / Outlook)
        if include_email:
            if config.GMAIL_CLIENT_ID and config.GMAIL_CLIENT_SECRET and config.GMAIL_REFRESH_TOKEN:
                collectors.append(GmailCollector())
            else:
                collectors.append(GmailCollectorStub())

            if config.OUTLOOK_CLIENT_ID and (config.OUTLOOK_CLIENT_SECRET or config.OUTLOOK_REFRESH_TOKEN):
                collectors.append(OutlookCollector())
            else:
                collectors.append(OutlookCollectorStub())

        # Social (Telegram / YouTube)
        if include_social:
            if config.TELEGRAM_API_ID and config.TELEGRAM_API_HASH and config.TELEGRAM_SESSION_STRING:
                collectors.append(TelegramCollector())
            else:
                collectors.append(TelegramCollectorStub())

            if config.YOUTUBE_CHANNEL_URLS:
                collectors.append(YouTubeCollector())
            else:
                collectors.append(YouTubeCollectorStub())

        # Calendar (stub only for now)
        if include_calendar:
            collectors.append(CalendarCollectorStub())

        # OneDrive export-based collectors (auto-enable if paths configured)
        if config.ONEDRIVE_LINKEDIN_EXPORT_PATH:
            collectors.append(LinkedInExportCollector())
        if config.ONEDRIVE_WHATSAPP_EXPORT_PATH:
            collectors.append(WhatsAppCollector())

        return collectors

    def _build_openai_client(self) -> Optional[OpenAIClient]:
        if not config.OPENAI_API_KEY:
            return None

        llm_cfg = self.settings.get("llm") or {}
        model = llm_cfg.get("model") or config.OPENAI_MODEL
        return OpenAIClient(api_key=config.OPENAI_API_KEY, model=model)

    def _load_personal_context(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        goals_file = self.project_root / "data" / "personal" / "goals.md"
        state_file = self.project_root / "data" / "personal" / "current_state.yaml"
        diary_dir = self.project_root / "data" / "personal" / "diary"

        goals = goals_file.read_text(encoding="utf-8") if goals_file.exists() else None
        current_state = state_file.read_text(encoding="utf-8") if state_file.exists() else None

        recent_diary = None
        if diary_dir.exists():
            entries = sorted(diary_dir.glob("*.md"))[-7:]
            if entries:
                recent_diary = "\n\n".join(path.read_text(encoding="utf-8") for path in entries)

        return goals, current_state, recent_diary

    @staticmethod
    def _resolve_first_existing(paths: List[Path]) -> Path:
        for path in paths:
            if path.exists():
                return path
        return paths[0]

    @staticmethod
    def _load_yaml(path: Path) -> Dict[str, object]:
        if yaml is None or not path.exists():
            return {}
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            return {}

    @staticmethod
    def _append_jsonl(path: Path, rows: List[dict]):
        if not rows:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _build_feedback_map(self) -> Dict[str, Dict[str, int]]:
        """Load feedback counts grouped by item_id and rating."""
        counts: Dict[str, Dict[str, int]] = {}

        # JSONL source
        feedback_path = self.data_dir / "feedback.jsonl"
        if feedback_path.exists():
            try:
                for line in feedback_path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    item_id = row.get("item_id")
                    rating = row.get("rating")
                    if not item_id or rating not in {"+", "-", "?", "!"}:
                        continue
                    counts.setdefault(item_id, {"+": 0, "-": 0, "?": 0, "!": 0})
                    counts[item_id][rating] += 1
            except Exception:
                pass

        # SQLite source
        try:
            import sqlite3

            with sqlite3.connect(self.storage.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT item_id, rating FROM feedback")
                for item_id, rating in cursor.fetchall():
                    if not item_id or rating not in {"+", "-", "?", "!"}:
                        continue
                    counts.setdefault(item_id, {"+": 0, "-": 0, "?": 0, "!": 0})
                    counts[item_id][rating] += 1
        except Exception:
            pass

        return counts

    @staticmethod
    def _source_voice_excerpt(text: str) -> str:
        """Keep source voice by extracting a direct short excerpt."""
        if not text:
            return ""
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
        if not sentences:
            return text[:200]
        excerpt = sentences[0][:220]
        return f'"{excerpt}"'

    @staticmethod
    def _build_continuity_note(recent_briefs: List[DailyBrief]) -> str:
        """Summarize continuity from recent days for memory effect."""
        if not recent_briefs:
            return ""
        repeated_titles: Dict[str, int] = {}
        for brief in recent_briefs:
            for signal in brief.top_signals[:5]:
                title = (signal.title or "").strip().lower()
                if title:
                    repeated_titles[title] = repeated_titles.get(title, 0) + 1
        recurring = [title for title, n in repeated_titles.items() if n >= 2]
        if not recurring:
            return "No repeating top signals from recent days."
        top = "; ".join(recurring[:3])
        return f"Recurring signals from previous days: {top}."

    @staticmethod
    def _recent_brief_context(recent_briefs: List[DailyBrief], limit: int = 3) -> str:
        """Compact context string from recent generated briefs."""
        if not recent_briefs:
            return ""
        parts: List[str] = []
        for brief in recent_briefs[:limit]:
            top_titles = ", ".join(signal.title for signal in brief.top_signals[:3])
            action = brief.recommended_action_today or ""
            parts.append(f"{brief.date}: top=[{top_titles}] action=[{action}]")
        return " | ".join(parts)


# Lazy import to avoid circular dependency at module import time.
from app.processing.opportunity_extractor import OpportunityExtractor  # noqa: E402


def run_daily_pipeline() -> Optional[DailyBrief]:
    """Backward-compatible helper for legacy callers."""
    return DailyPipeline().run_daily()
