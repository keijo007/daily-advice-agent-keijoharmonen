"""
Reflection Agent V2 for Personal Signal OS.

Adapted from original Reflection Agent.
Produces ThinkingMirror output (personal reflection) instead of bias list.

Looks at:
- Diary entries (latest)
- Goals and current state
- Signals collected today

Outputs:
- Repeated focus (what you're focusing on)
- Possible blind spot (what you might be missing)
- Possible bias (how you might be biased)
- One question (for you to consider)
"""

from typing import List, Optional
from app.models import ThinkingMirror, ContentItem, ScoredItem, SignalType
from app.services.openai_client import OpenAIClient


class ReflectionAgentV2:
    """Generate personal reflection (ThinkingMirror) from diary and signals."""
    
    def __init__(self, openai_client: Optional[OpenAIClient] = None, allow_external_llm_for_diary: bool = False):
        """
        Initialize reflection agent.
        
        Args:
            openai_client: Optional OpenAI client
            allow_external_llm_for_diary: If False, diary data not sent to LLM
        """
        self.openai_client = openai_client
        self.allow_external_llm_for_diary = allow_external_llm_for_diary
    
    def process(
        self,
        scored_items: List[ScoredItem],
        recent_diary: Optional[str],
        goals: Optional[str],
        current_state: Optional[str],
    ) -> Optional[ThinkingMirror]:
        """
        Generate ThinkingMirror reflection.
        
        Args:
            scored_items: All scored items from today
            recent_diary: Recent diary entries
            goals: Goals file content
            current_state: Current state YAML
        
        Returns:
            ThinkingMirror object
        """
        # Extract focus areas from diary/goals/signals
        repeated_focus = self._extract_repeated_focus(scored_items, goals, current_state)
        
        # Generate reflection using LLM or heuristics
        if self.openai_client and self.allow_external_llm_for_diary:
            reflection = self._generate_with_llm(
                repeated_focus, recent_diary, goals, scored_items
            )
        else:
            # Heuristic-only (doesn't send diary to external API)
            reflection = self._generate_heuristic(
                repeated_focus, goals, scored_items
            )
        
        return reflection
    
    def _extract_repeated_focus(
        self,
        scored_items: List[ScoredItem],
        goals: Optional[str],
        current_state: Optional[str],
    ) -> str:
        """Extract what you seem to be focusing on based on signals and goals."""
        # Count topic mentions
        topic_counts = {}
        for si in scored_items:
            for topic in si.item.topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Most repeated topics
        if topic_counts:
            top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            return "You seem to be focusing on: " + ", ".join(t[0] for t in top_topics)
        
        # Fallback to goals
        if goals:
            lines = goals.split("\n")
            focus_lines = [line.strip() for line in lines if "focus" in line.lower()]
            if focus_lines:
                return focus_lines[0]
        
        return "Your focus areas are not yet clear from today's signals"
    
    def _generate_with_llm(
        self,
        repeated_focus: str,
        recent_diary: Optional[str],
        goals: Optional[str],
        scored_items: List[ScoredItem],
    ) -> ThinkingMirror:
        """Generate reflection using LLM."""
        try:
            user_message = f"""
Based on the person's signals, diary, and goals today:

REPEATED FOCUS: {repeated_focus}

DIARY EXCERPT: {recent_diary[:500] if recent_diary else "(no diary entries)"}

GOALS: {goals[:500] if goals else "(no goals defined)"}

TOP SIGNALS TODAY: {'; '.join(si.item.title for si in scored_items[:5])}

Generate a personal reflection with:
1. BLIND_SPOT: One thing they might be missing or overlooking (1-2 sentences)
2. BIAS: One possible bias in their thinking based on today's signals (1-2 sentences)
3. QUESTION: One useful question for them to consider (1 sentence)
4. ADJUSTMENT: One small adjustment they could make (optional, 1 sentence)

Format:
BLIND_SPOT: [answer]
BIAS: [answer]
QUESTION: [answer]
ADJUSTMENT: [answer or omit]
"""

            response = self.openai_client.call_with_prompt(
                system_prompt=(
                    "You are a practical reflection coach. "
                    "Avoid diagnosis, keep outputs concise and actionable."
                ),
                user_message=user_message,
                max_tokens=350,
            )
            if not response:
                return self._generate_heuristic(repeated_focus, goals, scored_items)
            
            # Parse response
            blind_spot = self._extract_field(response, "BLIND_SPOT")
            bias = self._extract_field(response, "BIAS")
            question = self._extract_field(response, "QUESTION")
            adjustment = self._extract_field(response, "ADJUSTMENT")
            
            return ThinkingMirror(
                repeated_focus=repeated_focus,
                possible_blind_spot=blind_spot or "Consider what information you might be missing",
                possible_bias=bias or "Reflect on your assumptions",
                one_question=question or "What would change if your main assumption were wrong?",
                suggested_adjustment=adjustment,
            )
        
        except Exception as e:
            print(f"Error generating LLM reflection: {e}")
            return self._generate_heuristic(repeated_focus, "", scored_items)
    
    def _generate_heuristic(
        self,
        repeated_focus: str,
        goals: Optional[str],
        scored_items: List[ScoredItem],
    ) -> ThinkingMirror:
        """Generate reflection using heuristics (no external LLM)."""
        # Heuristic blind spot: check for missing source types
        source_types = set(si.item.source for si in scored_items)
        if len(source_types) < 5:
            missing = "You might be over-relying on certain source types. Consider seeking diverse perspectives."
        else:
            missing = "What information are you not receiving that could be important?"
        
        # Heuristic bias: check for signal recency bias
        if scored_items:
            recent_scores = [si.signal_score for si in scored_items[:5]]
            old_scores = [si.signal_score for si in scored_items[5:]]
            
            if recent_scores and old_scores:
                avg_recent = sum(recent_scores) / len(recent_scores)
                avg_old = sum(old_scores) / len(old_scores) if old_scores else 0
                
                if avg_recent > avg_old * 1.2:
                    bias = "You may be weighting recent signals too heavily. Consider older context too."
                else:
                    bias = "Are you considering the full context or just focusing on what's convenient?"
            else:
                bias = "Reflect on what assumptions are driving your focus today"
        else:
            bias = "Without signals, consider what you might be assuming"
        
        return ThinkingMirror(
            repeated_focus=repeated_focus,
            possible_blind_spot=missing,
            possible_bias=bias,
            one_question="What would change if one of your key assumptions were wrong?",
            suggested_adjustment=None,
        )
    
    @staticmethod
    def _extract_field(response: str, field_name: str) -> str:
        """Extract a field from LLM response."""
        for line in response.split("\n"):
            if line.startswith(field_name + ":"):
                return line.replace(field_name + ":", "").strip()
        return ""
