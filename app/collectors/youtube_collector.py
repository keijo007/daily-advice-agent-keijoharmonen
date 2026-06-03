"""
YouTube Collector - fetches transcripts from recent channel videos.

Prefers existing captions; optionally uses Whisper when enabled.
"""

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional
import feedparser
from app.collectors.base_collector import BaseCollector
from app.models import ContentItem, SourceType
from app.config import config


PENDING_FILE = Path(__file__).parent.parent.parent / "data" / "youtube_pending.json"


class YouTubeCollector(BaseCollector):
    """YouTube video transcript collector."""

    def __init__(self):
        super().__init__(SourceType.YOUTUBE)

    def collect(self) -> List[ContentItem]:
        channels = self._parse_channels(config.YOUTUBE_CHANNEL_URLS)
        if not channels:
            print("ℹ️  No YouTube channels configured")
            return []

        since = datetime.now(timezone.utc) - timedelta(days=config.YOUTUBE_LOOKBACK_DAYS)
        pending = self._load_pending()
        items: List[ContentItem] = []

        for channel_url in channels:
            channel_id = self._resolve_channel_id(channel_url)
            if not channel_id:
                print(f"⚠️  Could not resolve channel: {channel_url}")
                continue

            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            feed = feedparser.parse(feed_url)

            for entry in feed.entries:
                published = self._parse_datetime(entry.get("published"))
                if not published or published < since:
                    continue

                video_id = entry.get("yt_videoid") or entry.get("id", "").split(":")[-1]
                if not video_id:
                    continue

                transcript = self._get_transcript(video_id)
                if not transcript:
                    pending[video_id] = {
                        "url": entry.get("link"),
                        "title": entry.get("title"),
                        "added_at": datetime.now(timezone.utc).isoformat(),
                    }
                    continue

                items.append(self._build_item(entry, transcript, published))

        # Re-check pending videos for captions
        items.extend(self._check_pending(pending))
        self._save_pending(pending)

        if items:
            print(f"▶️  Loaded {len(items)} YouTube items")
        return items

    def _check_pending(self, pending: dict) -> List[ContentItem]:
        items: List[ContentItem] = []
        max_age = datetime.now(timezone.utc) - timedelta(days=config.YOUTUBE_LOOKBACK_DAYS)

        for video_id, info in list(pending.items()):
            added_at = self._parse_datetime(info.get("added_at")) or datetime.now(timezone.utc)
            if added_at < max_age:
                pending.pop(video_id, None)
                continue

            transcript = self._get_transcript(video_id)
            if not transcript:
                continue

            title = info.get("title") or "YouTube video"
            item = self._create_item(
                title=f"YouTube: {title}",
                content=transcript,
                author="YouTube",
                timestamp=datetime.now(),
                url=info.get("url"),
                raw_path=f"youtube:{video_id}",
            )
            items.append(item)
            pending.pop(video_id, None)

        return items

    def _get_transcript(self, video_id: str) -> Optional[str]:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled

            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)

            transcript = None
            for lang in ["fi", "en"]:
                try:
                    transcript = transcripts.find_manually_created_transcript([lang])
                    break
                except Exception:
                    continue

            if not transcript:
                for lang in ["fi", "en"]:
                    try:
                        transcript = transcripts.find_generated_transcript([lang])
                        break
                    except Exception:
                        continue

            if transcript:
                parts = transcript.fetch()
                return " ".join(p["text"] for p in parts)

        except (NoTranscriptFound, TranscriptsDisabled):
            pass
        except Exception:
            pass

        if config.YOUTUBE_WHISPER_ENABLED:
            return self._transcribe_with_whisper(video_id)

        return None

    def _transcribe_with_whisper(self, video_id: str) -> Optional[str]:
        try:
            from yt_dlp import YoutubeDL
            from openai import OpenAI
        except Exception:
            return None

        tmp_dir = Path(__file__).parent.parent.parent / "data" / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        audio_path = tmp_dir / f"{video_id}.m4a"

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(audio_path),
            "quiet": True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            duration = info.get("duration") or 0
            max_seconds = config.YOUTUBE_WHISPER_MAX_MINUTES * 60
            if duration and duration > max_seconds:
                return None

            if not audio_path.exists():
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

        if not audio_path.exists():
            return None

        client = OpenAI(api_key=config.OPENAI_API_KEY)
        with open(audio_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
            )
        return response.text

    @staticmethod
    def _parse_channels(raw: str) -> List[str]:
        if not raw:
            return []
        return [v.strip() for v in raw.split(",") if v.strip()]

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    @staticmethod
    def _extract_channel_id(html: str) -> Optional[str]:
        match = re.search(r"channelId\":\"(UC[\w-]{20,})\"", html)
        return match.group(1) if match else None

    def _resolve_channel_id(self, channel_url: str) -> Optional[str]:
        if "channel/" in channel_url:
            return channel_url.split("channel/")[-1].split("/")[0]

        try:
            import requests
            response = requests.get(channel_url, timeout=10)
            if response.status_code != 200:
                return None
            return self._extract_channel_id(response.text)
        except Exception:
            return None

    @staticmethod
    def _build_item(entry: dict, transcript: str, published: datetime) -> ContentItem:
        title = entry.get("title", "YouTube video")
        return ContentItem(
            source=SourceType.YOUTUBE,
            title=f"YouTube: {title}",
            content=transcript,
            author=entry.get("author", "YouTube"),
            timestamp=published,
            url=entry.get("link"),
            raw_path=entry.get("id"),
        )

    @staticmethod
    def _load_pending() -> dict:
        if not PENDING_FILE.exists():
            return {}
        try:
            return json.loads(PENDING_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}

    @staticmethod
    def _save_pending(pending: dict) -> None:
        PENDING_FILE.write_text(json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8")
