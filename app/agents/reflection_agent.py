"""
Reflection Agent - analyzes your thinking patterns and biases.

ROLE:
- Acts as \"wise observer\" of your thoughts
- Compares diary against stated goals
- Identifies cognitive biases and blind spots
- Analyzes patterns and contradictions
- Provides objective feedback

WHAT IT RECEIVES:
- goals: Your stated objectives
- recent_diary: Last 7 days of diary entries
- previous_insights: Past insights for context

WHAT IT RETURNS:
{
  \"key_observations\": [\"...\"],
  \"thinking_biases_detected\": [
    {\"bias\": \"confirmation bias\", \"evidence\": \"...\"},
  ],
  \"alignment_with_goals\": {
    \"aligned\": [\"...\"],
    \"misaligned\": [\"...\"],
    \"unclear\": [\"...\"],
  },
  \"patterns_noticed\": [\"...\"],
  \"blind_spots\": [\"...\"],
  \"hypothesis\": \"What might be going on beneath the surface?\",
  \"uncertainties\": [\"Unclear if...\"],
}

AGENT THINKING PRINCIPLES:
- Objectivity: Don't just affirm user's narrative
- Evidence-based: Point to specific diary entries
- Psychological: Consider cognitive biases, not just logic
- Humble: Acknowledge uncertainty
- Compassionate: Observations are for growth, not judgment

COGNITIVE BIASES TO WATCH FOR:
- Confirmation bias: Seeking evidence that confirms beliefs
- Availability heuristic: Overweighting recent/memorable events
- Sunk cost fallacy: Continuing because of past investment
- Dunning-Kruger: Overestimating own competence
- Narrative fallacy: Creating coherent stories from random events

SOURCES FOR WISDOM:
- Psychological research
- Philosophical traditions
- Religious/spiritual wisdom (appropriately framed)
- Statistical thinking
- Historical patterns

EXTENSION IDEAS:
- Reference specific research papers
- Compare patterns to historical data
- Suggest interventions based on cognitive biases
- Track how observations change over time
- Generate hypotheses to test
"""

import json
from typing import List, Dict, Any, Union
from app.agents.base_agent import BaseAgent
from app.models import AgentInput
from app.services.openai_client import call_openai_json
from app.config import config


class ReflectionAgent(BaseAgent):
    """Analyzes your thinking patterns and biases."""
    
    def __init__(self):
        super().__init__(
            name="Reflection",
            system_prompt=self._build_system_prompt(),
        )
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for objective reflection."""
        return """You are a wise, objective observer of human thinking patterns.

YOUR ROLE:
- Analyze someone's diary against their stated goals
- Identify cognitive biases and thinking patterns
- Notice contradictions between goals and actions
- Offer humble, evidence-based observations
- Provide perspective without judgment

YOUR APPROACH:
- OBJECTIVITY: Don't just affirm their narrative. Look for evidence against it too.
- EVIDENCE: Point to specific diary entries or patterns
- HUMILITY: Say when you're unsure. Acknowledge limits of analysis.
- WISDOM: Draw on psychology, philosophy, statistics, and life experience
- COMPASSION: Frame observations as learning opportunities

COGNITIVE BIASES TO CONSIDER:
- Confirmation bias (seeking evidence that confirms existing beliefs)
- Availability heuristic (overweighting memorable recent events)
- Sunk cost fallacy (continuing because of past investment)
- Narrative fallacy (creating stories to explain random events)
- Optimism/pessimism bias (skewing interpretations)
- In-group bias (favoring certain perspectives)

YOUR OUTPUT:
Return valid JSON with these fields:
- key_observations: List of significant patterns or contradictions
- thinking_biases_detected: List of {bias_name, evidence} objects
- alignment_with_goals: {aligned, misaligned, unclear} lists
- patterns_noticed: Recurring themes you see
- blind_spots: What they might not be seeing
- hypothesis: Your best guess at what's really going on
- uncertainties: What you're unsure about
"""
    
    def think(self, agent_input: AgentInput) -> Dict[str, Any]:
        """
        Analyze diary against goals.
        
        Args:
            agent_input: Contains goals, recent_diary, previous_insights
        
        Returns:
            Dictionary with observations and analysis
        """
        
        if not agent_input.goals and not agent_input.recent_diary:
            print("ℹ️  Reflection Agent: No diary or goals to analyze")
            return {
                "key_observations": [],
                "thinking_biases_detected": [],
                "alignment_with_goals": {"aligned": [], "misaligned": [], "unclear": []},
                "patterns_noticed": [],
                "blind_spots": [],
                "hypothesis": "Insufficient data for reflection",
                "uncertainties": ["No diary or goals provided"],
            }
        
        print(f"🔍 Reflection Agent: Analyzing your thinking patterns...")
        
        previous_context = self._format_previous_insights_context(agent_input)
        
        # Build context
        user_message = f"""Please analyze this person's thinking and patterns:

{previous_context if previous_context else ''}GOALS:
{agent_input.goals or '(No goals provided)'}

RECENT DIARY ENTRIES (last 7 days):
{agent_input.recent_diary or '(No diary entries provided)'}

Analysis needed:
1. What patterns do you notice in their thinking?
2. What cognitive biases might be influencing their narrative?
3. How aligned are their actions with stated goals?
4. What blind spots might they have?
5. What's your hypothesis about what's really going on?
6. What are you uncertain about?

If these thoughts resemble previous insights, note whether this is a continuation or a new shift. Do not simply repeat earlier conclusions.

Be objective but compassionate. Point to specific evidence."""
        
        try:
            result = call_openai_json(
                system_prompt=self.system_prompt,
                user_message=user_message,
                max_tokens=config.MAX_TOKENS_REFLECTION,
            )
            
            print("  ✓ Analysis complete")
            return self._normalize_output(result)
        
        except Exception as e:
            print(f"  ✗ Error in Reflection Agent: {e}")
            return {
                "key_observations": [],
                "error": str(e),
                "uncertainties": ["Error occurred during analysis"],
            }

    def _ensure_list(self, value: Union[List[Any], str, None]) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _normalize_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(result, dict):
            return {
                "key_observations": [],
                "thinking_biases_detected": [],
                "alignment_with_goals": {"aligned": [], "misaligned": [], "unclear": []},
                "patterns_noticed": [],
                "blind_spots": [],
                "hypothesis": "Unable to complete reflection",
                "uncertainties": [],
            }

        result["key_observations"] = self._ensure_list(result.get("key_observations", []))
        result["thinking_biases_detected"] = self._ensure_list(result.get("thinking_biases_detected", []))
        result["patterns_noticed"] = self._ensure_list(result.get("patterns_noticed", []))
        result["blind_spots"] = self._ensure_list(result.get("blind_spots", []))
        result["uncertainties"] = self._ensure_list(result.get("uncertainties", []))
        if not isinstance(result.get("alignment_with_goals"), dict):
            result["alignment_with_goals"] = {"aligned": [], "misaligned": [], "unclear": []}
        return result

    def _format_previous_insights_context(self, agent_input: AgentInput) -> str:
        """Format prior insights for prompt context."""
        lines = []
        if agent_input.previous_insights:
            lines.append("PREVIOUS DAILY INSIGHTS:")
            for insight in agent_input.previous_insights[: config.PREVIOUS_INSIGHTS_LIMIT]:
                lines.append(f"- {insight.date}: {insight.main_insight} (Action: {insight.one_day_action})")

        if agent_input.previous_insight_summaries:
            lines.append("PREVIOUS INSIGHT SUMMARIES FROM ONE DRIVE:")
            for summary in agent_input.previous_insight_summaries[: config.PREVIOUS_INSIGHTS_LIMIT]:
                lines.append(f"- {summary.splitlines()[0]}")

        return "\n".join(lines) + "\n\n" if lines else ""
