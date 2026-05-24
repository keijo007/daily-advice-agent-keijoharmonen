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
)
from app.services.normalize import normalize_items
from app.services.deduplicate import deduplicate_items, get_hashes_from_items
from app.services.storage import StorageService
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
            print(f"✓ Loaded goals and recent diary\n")
            
            # STEP 6-8: Run agents
            print("STEP 6: RUNNING ANALYSIS AGENTS")
            print("-" * 40)
            
            # Create input for agents
            agent_input = AgentInput(
                new_items=new_items,
                goals=goals,
                recent_diary=recent_diary,
        previous_insights=None,
            )
            # Reflection Agent: analyze patterns
            print("  [2/3] Reflection Agent...")
            reflection_output = self.reflection_agent.think(agent_input)
            
            # Coach Agent: synthesize advice
            print("  [3/3] Coach Agent...")
            coach_output = self.coach_agent.think(agent_input)
            
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


# Convenience function for manual execution
def run_daily_pipeline() -> Optional[DailyInsight]:
    """
    Run the complete daily pipeline.
    
    Returns:
        DailyInsight or None
    """
    pipeline = DailyPipeline()
    return pipeline.run()
