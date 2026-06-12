"""
Brief Synthesizer Agent for Personal Signal OS.

Combines outputs from:
- Signal Summary Agent (top signals)
- Opportunity Agent (opportunities)
- Claim Checker Agent (claims to verify)
- Reflection Agent (thinking mirror)

Produces final DailyBrief with recommended action and noise filtering.
"""

from typing import List, Optional
from app.models import DailyBrief, ScoredItem, Signal, Opportunity, Claim, WeakSignal, ThinkingMirror, SignalType
from app.services.openai_client import OpenAIClient


class BriefSynthesizer:
    """Synthesize all signal OS agents into final DailyBrief."""
    
    def __init__(self, openai_client: Optional[OpenAIClient] = None):
        """Initialize with optional OpenAI client for generating recommended action."""
        self.openai_client = openai_client
    
    def synthesize(
        self,
        date: str,
        scored_items: List[ScoredItem],
        signals: List[Signal],
        opportunities: List[Opportunity],
        claims: List[Claim],
        weak_signals: List[WeakSignal],
        thinking_mirror: Optional[ThinkingMirror],
        goals: Optional[str] = None,
        current_state: Optional[str] = None,
    ) -> DailyBrief:
        """
        Synthesize all components into final DailyBrief.
        
        Args:
            date: YYYY-MM-DD
            scored_items: All scored items from today
            signals: Top 5 signals
            opportunities: Extracted opportunities
            claims: Claims to verify
            weak_signals: Weak signals
            thinking_mirror: Personal reflection
            goals: Goals file content (for context)
            current_state: Current state YAML (for context)
        
        Returns:
            DailyBrief with all 7 sections
        """
        # Filter to top opportunities and claims
        top_opportunities = opportunities[:5]
        top_claims = claims[:5]
        top_weak_signals = weak_signals[:5]
        
        # Filter noise (items classified as NOISE)
        noise_items = [si for si in scored_items if si.signal_type == SignalType.NOISE]
        low_priority_noise = [
            {
                "title": si.item.title,
                "reason": si.reasoning,
                "source": si.item.author or si.item.source.value,
            }
            for si in noise_items[:10]
        ]
        
        # Generate recommended action
        recommended_action = self._generate_recommended_action(
            signals, opportunities, thinking_mirror, goals, current_state
        )
        
        # Collect sources used
        sources_used = self._collect_sources(scored_items)
        
        # Create brief
        brief = DailyBrief(
            date=date,
            top_signals=signals,
            opportunities=top_opportunities,
            claims_to_verify=top_claims,
            weak_signals=top_weak_signals,
            thinking_mirror=thinking_mirror,
            recommended_action_today=recommended_action,
            low_priority_noise=low_priority_noise,
            sources_used=sources_used,
            collected_items_count=len(scored_items),
            scored_items_count=len(scored_items),
        )
        
        return brief
    
    def _generate_recommended_action(
        self,
        signals: List[Signal],
        opportunities: List[Opportunity],
        thinking_mirror: Optional[ThinkingMirror],
        goals: Optional[str],
        current_state: Optional[str],
    ) -> str:
        """
        Generate one recommended action for today.
        
        Considers: top signals, opportunities with deadlines, thinking mirror insights.
        """
        # Default: if opportunities have urgent deadlines, suggest action on them
        today_actions = [
            opp for opp in opportunities
            if opp.deadline and self._is_urgent(opp.deadline)
        ]
        
        if today_actions:
            opp = today_actions[0]
            return f"Today: Focus on this opportunity - {opp.title}. {opp.next_action}"
        
        # Second priority: Act on top signal
        if signals:
            signal = signals[0]
            return f"Today: Review this key signal - {signal.title}. {signal.suggested_action}"
        
        # Third priority: Use thinking mirror suggestion
        if thinking_mirror and thinking_mirror.suggested_adjustment:
            return f"Today: {thinking_mirror.suggested_adjustment}"
        
        # Default
        return "Today: Review the signals above and take one concrete action toward your goals."
    
    @staticmethod
    def _is_urgent(deadline) -> bool:
        """Check if deadline is within 7 days."""
        from datetime import datetime, timedelta
        today = datetime.now()
        days_until = (deadline - today).days
        return 0 <= days_until <= 7
    
    @staticmethod
    def _collect_sources(scored_items: List[ScoredItem]) -> List[str]:
        """Collect unique sources from scored items."""
        sources = set()
        for si in scored_items:
            if si.item.author:
                sources.add(si.item.author)
            else:
                sources.add(si.item.source.value)
        
        return sorted(list(sources))
