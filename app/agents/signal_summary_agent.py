"""
Signal Summary Agent for Personal Signal OS.

Adapted from Reader Agent.
Summarizes top signals with LLM-generated:
- Why it matters
- Suggested action
"""

from typing import List, Optional
from app.models import Signal, ScoredItem, SignalType
from app.services.openai_client import OpenAIClient


class SignalSummaryAgent:
    """Summarize top signals."""
    
    def __init__(self, openai_client: Optional[OpenAIClient] = None):
        """Initialize with optional OpenAI client."""
        self.openai_client = openai_client
    
    def process(self, top_scored_items: List[ScoredItem]) -> List[Signal]:
        """
        Convert top scored items to Signal cards with LLM-generated explanations.
        
        Args:
            top_scored_items: Top 5 ScoredItem objects (SIGNAL type)
        
        Returns:
            List of Signal objects
        """
        signals = []
        
        for scored_item in top_scored_items[:5]:
            item = scored_item.item
            
            # Use LLM to generate why_matters and suggested_action if available
            if self.openai_client:
                why_matters, suggested_action = self._generate_explanations(item, scored_item.reasoning)
            else:
                # Fallback: heuristic explanations
                why_matters = self._heuristic_why_matters(item)
                suggested_action = self._heuristic_action(item)
            
            signal = Signal(
                item_id=item.compute_hash(),
                title=item.title,
                content=item.content[:200],  # Truncate for signal card
                source=item.author or item.source.value,
                source_type=item.source,
                score=scored_item.signal_score,
                why_matters=why_matters,
                suggested_action=suggested_action,
                url=item.url,
                topics=item.topics,
            )
            
            signals.append(signal)
        
        return signals
    
    def _generate_explanations(self, item, reasoning: str) -> tuple:
        """Use LLM to generate why_matters and suggested_action."""
        try:
            user_message = f"""
Given this signal:
Title: {item.title}
Content: {item.content[:300]}
Scoring: {reasoning}

Generate:
1. In 1-2 sentences: Why does this matter to someone interested in {', '.join(item.topics[:3]) or 'this topic'}?
2. In 1-2 sentences: One concrete action to take based on this signal.

Format:
WHY_MATTERS: [your answer]
ACTION: [your answer]
"""

            response = self.openai_client.call_with_prompt(
                system_prompt=(
                    "You are a concise signal-analysis assistant. "
                    "Return short practical output exactly in requested keys."
                ),
                user_message=user_message,
                max_tokens=250,
            )
            if not response:
                return self._heuristic_why_matters(item), self._heuristic_action(item)
            
            # Parse response
            lines = response.split("\n")
            why_matters = ""
            action = ""
            
            for line in lines:
                if line.startswith("WHY_MATTERS:"):
                    why_matters = line.replace("WHY_MATTERS:", "").strip()
                elif line.startswith("ACTION:"):
                    action = line.replace("ACTION:", "").strip()
            
            return why_matters or "Important signal for your focus areas", action or "Research and consider implications"
        
        except Exception as e:
            print(f"Error generating explanations: {e}")
            return self._heuristic_why_matters(item), self._heuristic_action(item)
    
    @staticmethod
    def _heuristic_why_matters(item) -> str:
        """Fallback: generate why_matters heuristically."""
        if item.deadline:
            return f"Time-sensitive: {item.title} has a deadline approaching"
        
        if any(action_verb in item.title.lower() for action_verb in ["apply", "hiring", "event", "deadline"]):
            return f"Actionable opportunity: {item.title}"
        
        return f"Relevant signal: {item.title}"
    
    @staticmethod
    def _heuristic_action(item) -> str:
        """Fallback: generate suggested_action heuristically."""
        if item.url:
            return f"Click to learn more: {item.url[:50]}..."
        
        if item.deadline:
            return "Review deadline and take action"
        
        if any(word in item.title.lower() for word in ["apply", "register", "join"]):
            return "Complete the application or registration"
        
        return "Learn more about this signal and consider implications"
