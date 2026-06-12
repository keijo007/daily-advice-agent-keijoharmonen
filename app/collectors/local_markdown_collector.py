"""
Local markdown collector for Personal Signal OS.

Reads:
- data/personal/goals.md
- data/personal/current_state.yaml
- data/personal/diary/*.md

All items are marked as personal source bias.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from app.collectors.base_collector import BaseCollector
from app.config import config
from app.models import ContentItem, SourceBias, SourceType

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


class LocalMarkdownCollector(BaseCollector):
    """Collect personal local markdown/yaml context files."""

    def __init__(self, sources_path: Optional[Path] = None):
        super().__init__(SourceType.PERSONAL)
        self.sources_path = sources_path or (config.PROJECT_ROOT / "config" / "sources.yaml")

    def collect(self) -> List[ContentItem]:
        diary_dir, goals_file, current_state_file = self._resolve_paths()

        items: List[ContentItem] = []
        if goals_file.exists():
            items.append(self._read_file_item(goals_file, "Goals"))

        if current_state_file.exists():
            items.append(self._read_file_item(current_state_file, "Current State"))

        if diary_dir.exists():
            diary_files = sorted(diary_dir.glob("*.md"))[-7:]
            for path in diary_files:
                items.append(self._read_file_item(path, f"Diary: {path.stem}"))

        return items

    def _resolve_paths(self) -> Tuple[Path, Path, Path]:
        default_diary = config.PROJECT_ROOT / "data" / "personal" / "diary"
        default_goals = config.PROJECT_ROOT / "data" / "personal" / "goals.md"
        default_state = config.PROJECT_ROOT / "data" / "personal" / "current_state.yaml"

        if yaml is not None and self.sources_path.exists():
            try:
                payload = yaml.safe_load(self.sources_path.read_text(encoding="utf-8")) or {}
                local_cfg = payload.get("local_markdown", {})
                diary = config.PROJECT_ROOT / local_cfg.get("diary_dir", str(default_diary.relative_to(config.PROJECT_ROOT)))
                goals = config.PROJECT_ROOT / local_cfg.get("goals_file", str(default_goals.relative_to(config.PROJECT_ROOT)))
                state = config.PROJECT_ROOT / local_cfg.get("current_state_file", str(default_state.relative_to(config.PROJECT_ROOT)))
                return diary, goals, state
            except Exception:
                pass

        return default_diary, default_goals, default_state

    def _read_file_item(self, path: Path, title: str) -> ContentItem:
        content = path.read_text(encoding="utf-8")
        ts = datetime.fromtimestamp(path.stat().st_mtime)
        return self._create_item(
            title=title,
            content=content,
            author="personal",
            timestamp=ts,
            raw_path=str(path),
            source_bias=SourceBias.PERSONAL,
        )
