"""
Daily Pipeline - orchestrates the entire agent workflow.

WHY THIS FILE EXISTS:
- Coordinates all data collection, processing, and analysis
- Implements the sequence: Collect → Normalize → Deduplicate → Store → Analyze
- Single entry point for running the full daily analysis
- Makes it easy to schedule or trigger manually

HOW IT WORKS:
1. Collect new items from all sources
2. Normalize to ContentItem format
3. Load goals and recent diary
4. Check for duplicates
5. Save new items to database
6. Run Reader Agent on new items
7. Run Reflection Agent on goals + diary
8. Run Coach Agent to synthesize insight
9. Save insight to database
10. Return final DailyInsight

FLOW DIAGRAM:
```
Collectors:
  - Diary
  - WhatsApp
  - RSS
  - Goals
         ↓
     Normalize
         ↓
    Deduplicate
         ↓
      Storage
         ↓
  ReaderAgent → Reader Output
  ReflectionAgent → Reflection Output
  CoachAgent → Final Insight
         ↓
   Save Insight
         ↓
   DailyInsight (JSON) → HTML view
```

AGENT ARCHITECTURE CONCEPT:
- This is the ORCHESTRATOR layer
- It knows the sequence but doesn't do the actual thinking
- Agents do the thinking, pipeline coordinates them
- Pipeline is glue that connects modules

ERROR HANDLING:
- If one source fails, continue with others
- If OpenAI call fails, return partial results
- Log errors but don't crash

EXTENSION IDEAS:
- Add background scheduling (APScheduler)
- Add caching to avoid re-processing
- Add performance metrics/timing
- Add rollback capability
- Support multiple pipeline strategies (async, batch, etc.)
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from app.collectors import (
    DiaryCollector,
    WhatsAppCollector,
    RSSCollector,
    GoalsCollector,
    YouTubeCollector,
    TelegramCollector,
    LinkedInExportCollector,
)
from app.services.normalize import normalize_items
from app.services.deduplicate import deduplicate_items, get_hashes_from_items
from app.services.storage import StorageService
from app.services.onedrive_client import OneDriveClient
from app.agents.reader_agent import ReaderAgent
from app.agents.reflection_agent import ReflectionAgent
from app.agents.coach_agent import CoachAgent
from app.models import AgentInput, DailyInsight, ContentItem
from app.config import config


class DailyPipeline:
    """Orchestrates daily analysis workflow."""
    
    def __init__(self):
        """Initialize pipeline with all components."""
        self.storage = StorageService(config.DB_PATH)
        self.storage.connect()
        
        # Initialize collectors
        self.collectors = [
            DiaryCollector(),
            GoalsCollector(),
            WhatsAppCollector(),
            LinkedInExportCollector(),
            RSSCollector(),
            YouTubeCollector(),
            TelegramCollector(),
        ]
        
        # Initialize agents
        self.reader_agent = ReaderAgent()
        self.reflection_agent = ReflectionAgent()
        self.coach_agent = CoachAgent()
    
    def run(self) -> Optional[DailyInsight]:
        """
        Run complete daily pipeline.
        
        Returns:
            DailyInsight object or None if error
        """
        
        print("\n" + "="*60)
        print("📅 DAILY INSIGHT AGENT - STARTING PIPELINE")
        print("="*60 + "\n")
        
        try:
            # STEP 1: Collect
            print("STEP 1: COLLECTING DATA FROM ALL SOURCES")
            print("-" * 40)
            all_items = self._collect_all()
            print(f"✓ Collected {len(all_items)} total items\n")
            
            # STEP 2: Normalize
            print("STEP 2: NORMALIZING DATA")
            print("-" * 40)
            normalized_items = normalize_items(all_items)
            print(f"✓ Normalized {len(normalized_items)} items\n")
            
            # STEP 3: Deduplicate
            print("STEP 3: DEDUPLICATING")
            print("-" * 40)
            existing_hashes = self.storage.get_existing_hashes()
            new_items = deduplicate_items(normalized_items, existing_hashes)
            print(f"✓ Found {len(new_items)} new items\n")
            
            # STEP 4: Store
            print("STEP 4: STORING NEW ITEMS")
            print("-" * 40)
            saved_count = self.storage.save_items(new_items)
            print(f"✓ Saved {saved_count} items to database\n")
            
            # STEP 5: Load context for agents
            print("STEP 5: LOADING CONTEXT")
            print("-" * 40)
            goals = self._load_goals()
            recent_diary = self._load_recent_diary()
            previous_insights, previous_insight_summaries = self._load_previous_insights()
            print(f"✓ Loaded goals, recent diary, and prior insights\n")
            
            # STEP 6-8: Run agents
            print("STEP 6: RUNNING ANALYSIS AGENTS")
            print("-" * 40)
            
            # Create input for agents
            agent_input = AgentInput(
                new_items=new_items,
                goals=goals,
                recent_diary=recent_diary,
                previous_insights=previous_insights,
                previous_insight_summaries=previous_insight_summaries,
            )
            
            # Reader Agent: summarize new content
            print("\n  [1/3] Reader Agent...")
            try:
                reader_output = self.reader_agent.think(agent_input)
            except Exception as e:
                print(f"  ✗ Error in Reader Agent: {e}")
                reader_output = {
                    "summary": "Error analyzing content",
                    "key_topics": [],
                    "important_quotes": [],
                    "facts_vs_opinions": {"facts": [], "opinions": [], "interpretations": []},
                    "sources_used": [],
                }
            
            # Reflection Agent: analyze patterns
            print("  [2/3] Reflection Agent...")
            try:
                reflection_output = self.reflection_agent.think(agent_input)
            except Exception as e:
                print(f"  ✗ Error in Reflection Agent: {e}")
                reflection_output = {
                    "key_observations": [],
                    "thinking_biases_detected": [],
                    "alignment_with_goals": {"aligned": [], "misaligned": [], "unclear": []},
                    "patterns_noticed": [],
                    "blind_spots": [],
                    "hypothesis": "Unable to complete analysis",
                    "uncertainties": [],
                }
            
            # Coach Agent: synthesize advice
            print("  [3/3] Coach Agent...")
            try:
                coach_output = self.coach_agent.think(agent_input)
            except Exception as e:
                print(f"  ✗ Error in Coach Agent: {e}")
                coach_output = {
                    "practical_tip": "Unable to generate advice due to error",
                    "one_day_action": "",
                    "possible_project_idea": None,
                    "warnings": [],
                    "confidence": 0.0,
                }
            
            print("✓ Analysis complete\n")
            
            # STEP 9: Create final insight
            print("STEP 7: CREATING FINAL INSIGHT")
            print("-" * 40)
            
            sources_used = list(set(item.source.value for item in new_items))
            daily_insight = self.coach_agent.create_daily_insight(
                reader_output,
                reflection_output,
                coach_output,
                sources_used,
            )
            
            # STEP 10: Save insight
            print("STEP 8: SAVING INSIGHT")
            print("-" * 40)
            
            saved = self.storage.save_insight(daily_insight)
            if saved:
                print(f"✓ Saved insight for {daily_insight.date}\n")
            else:
                print("⚠️  Could not save insight\n")
            
            # SUCCESS
            print("="*60)
            print("✅ PIPELINE COMPLETE")
            print("="*60 + "\n")
            
            return daily_insight
        
        except Exception as e:
            print(f"\n❌ PIPELINE ERROR: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        finally:
            self.storage.disconnect()
    
    def _collect_all(self) -> List:
        """
        Collect items from all sources.
        
        Returns:
            List of collected items (mixed types)
        """
        all_items = []
        
        for collector in self.collectors:
            try:
                items = collector.collect()
                all_items.extend(items)
            except Exception as e:
                print(f"⚠️  {collector.name} collector failed: {e}")
        
        return all_items
    
    def _load_goals(self) -> Optional[str]:
        """Load goals file content."""
        try:
            goals_path = Path(config.GOALS_FILE_PATH)
            if goals_path.exists():
                return goals_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"⚠️  Could not load goals: {e}")
        
        return None
    
    def _load_recent_diary(self) -> Optional[str]:
        """Load recent diary entries."""
        try:
            items = self.storage.get_items_since(config.DIARY_LOOKBACK_DAYS)
            
            if not items:
                return None
            
            # Format diary items
            diary_text = "# Recent Diary Entries\n\n"
            for item in items:
                if item.source.value == "diary":
                    diary_text += f"## {item.title}\n{item.content}\n\n"
            
            return diary_text if diary_text != "# Recent Diary Entries\n\n" else None
        
        except Exception as e:
            print(f"⚠️  Could not load diary: {e}")
            return None

    def _load_previous_insights(self):
        """Load past insights from storage and optionally from OneDrive."""
        previous_insights = []
        previous_insight_summaries = []

        try:
            previous_insights = self.storage.get_all_insights(limit=config.PREVIOUS_INSIGHTS_LIMIT)
            if previous_insights:
                print(f"✓ Loaded {len(previous_insights)} previous insights from local storage")
            else:
                print("ℹ️  No prior local insights found")
        except Exception as e:
            print(f"⚠️  Could not load prior insights from local storage: {e}")
            previous_insights = []

        if config.ONEDRIVE_DAILY_INSIGHTS_PATH or config.ONEDRIVE_DAILY_INSIGHTS_SHARE_URL:
            client = OneDriveClient()
            if client.enabled:
                try:
                    summaries = client.read_previous_insight_summaries(
                        folder_path=config.ONEDRIVE_DAILY_INSIGHTS_PATH,
                        share_url=config.ONEDRIVE_DAILY_INSIGHTS_SHARE_URL,
                        limit=config.PREVIOUS_INSIGHTS_LIMIT,
                    )
                    if summaries:
                        previous_insight_summaries.extend(summaries)
                        print(f"✓ Loaded {len(summaries)} previous insight summaries from OneDrive")
                    else:
                        print("ℹ️  No prior insight summaries found in OneDrive")
                except Exception as e:
                    print(f"⚠️  Error loading insight summaries from OneDrive: {e}")
            else:
                print("ℹ️  OneDrive client not configured or enabled")

        return previous_insights, previous_insight_summaries


# Convenience function for manual execution
def run_daily_pipeline() -> Optional[DailyInsight]:
    """
    Run the complete daily pipeline.
    
    Returns:
        DailyInsight or None
    """
    pipeline = DailyPipeline()
    return pipeline.run()
