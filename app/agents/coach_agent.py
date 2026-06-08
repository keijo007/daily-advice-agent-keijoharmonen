"""
Coach Agent - combines insights and gives personalized advice.

ROLE:
- Acts as your personal coach/mentor
- Combines reader's insights + reflection's observations
- Gives one concrete, actionable tip
- Identifies one realistic project/idea
- Warns about potential risks
- Synthesizes everything into ONE daily insight

WHAT IT RECEIVES:
- Reader Agent output: summaries, key topics
- Reflection Agent output: biases, patterns, observations
- Goals: Your objectives (to align advice)
- Diary: Recent entries (for personalization)

WHAT IT RETURNS:
{
  \"main_insight\": \"High-level takeaway\",
  \"practical_tip\": \"One concrete, actionable thing you can do today\",
  \"one_day_action\": \"Specific steps for today\",
  \"possible_project_idea\": \"Optional project/idea to consider\",
  \"warnings\": [\"Risks or considerations\"],
  \"confidence\": 0.85,  # How confident in this advice
}

AGENT THINKING PRINCIPLES:
- ACTIONABILITY: Advice must be doable in one day
- SPECIFICITY: Not vague platitudes, concrete actions
- REALISM: Based on your goals and patterns
- HUMILITY: Acknowledge limits and uncertainties
- RELEVANCE: Tie to today's content + your patterns
- CAUTION: Warn about risks (esp. financial/health decisions)

KEY CONSTRAINTS:
- ONE practical tip (not a list of 10 ideas)
- ONE day action (time-bound, realistic)
- No generic motivation speech
- No advice that contradicts stated goals
- If data is insufficient, say so clearly

SPECIAL HANDLING:
- Finance/investment: Add disclaimer, separate observation/hypothesis/action
- Health advice: Conservative, encourage professional consultation
- Risky decisions: Highlight downside and alternatives
- Conflicting patterns: Acknowledge the tension

OUTPUT FORMAT:
- practical_tip: One actionable suggestion
- one_day_action: Concrete steps
- possible_project_idea: Optional (can be null)
- warnings: List of considerations/risks
- confidence: 0-1 confidence level
"""

import json
from typing import Dict, Any, Optional, List, Union
from app.agents.base_agent import BaseAgent
from app.models import AgentInput, DailyInsight
from app.services.openai_client import call_openai_json
from app.config import config


class CoachAgent(BaseAgent):
    """Combines insights and gives personalized, actionable advice."""
    
    def __init__(self):
        super().__init__(
            name="Coach",
            system_prompt=self._build_system_prompt(),
        )
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for coaching."""
        return """You are a wise, practical coach who gives specific, actionable advice.

YOUR ROLE:
- Synthesize Reader (content summary) + Reflection (pattern analysis)
- Offer practical guidance that feels tailored and grounded
- Suggest a realistic project idea if it adds value
- Identify meaningful risks or considerations
- Tie advice to the person's goals and recent patterns

YOUR PRINCIPLES:
- ACTIONABILITY: Keep guidance grounded and achievable
- SPECIFICITY: Prefer concrete examples over vague language
- REALISM: Based on actual patterns, not wishful thinking
- HONESTY: Name conflicts or uncertainty clearly
- HUMILITY: Don't overstate certainty
- CAUTION: Note risk in domains like money or health

WHAT MAKES GOOD ADVICE:
✓ Clear and practical
✓ Connected to today's learnings or ongoing patterns
✓ Feels personalized and not overly rigid
✓ Acknowledges uncertainty or trade-offs when needed
✗ Empty motivation without use
✗ Overly formal checklists
✗ Advice that ignores the person's own goals

SPECIAL CASES:
- Finance/Investment: Add a clear disclaimer and keep it observational
- Health/Medical: Be conservative and encourage professional input
- Big decisions: Acknowledge complexity and offer practical next steps

OUTPUT GUIDANCE: Return valid JSON with:
- practical_tip: A useful, concrete suggestion
- one_day_action: A realistic step to take today
- possible_project_idea: Optional project idea or null
- warnings: List of relevant considerations
- confidence: A judgment of confidence 0-1
- reasoning: Brief explanation of your thinking
Feel free to use a natural, flexible voice as long as the result is clear and actionable.
"""
    
    def think(self, agent_input: AgentInput) -> Dict[str, Any]:
        """
        Generate personalized coaching advice.
        
        Args:
            agent_input: Combined input with reader/reflection outputs
        
        Returns:
            Dictionary with practical_tip, one_day_action, etc.
        """
        
        print(f"🏆 Coach Agent: Synthesizing insights and generating advice...")
        
        previous_context = self._format_previous_insights_context(agent_input)
        
        # We expect reader and reflection outputs in the input
        user_message = f"""Based on today's analysis, provide one piece of actionable coaching advice.

CONTEXT:
- Goals: {agent_input.goals or '(Not provided)'}
- Recent diary patterns: {agent_input.recent_diary[:500] if agent_input.recent_diary else '(Not provided)'}
- Today's key content: {self._format_items_for_context(agent_input.new_items, max_chars=800) if agent_input.new_items else '(No new items)'}
{previous_context if previous_context else ''}
Generate ONE practical tip that is:
1. Specific and actionable (not vague)
2. Doable in one day
3. Based on today's learnings or observed patterns
4. Aligned with stated goals (or flag conflicts)

Avoid repeating the same high-level takeaway or action from prior insights. If today's work is a continuation, frame it as progression rather than repetition.

If suggesting financial/health advice, add appropriate disclaimers."""
        
        try:
            result = call_openai_json(
                system_prompt=self.system_prompt,
                user_message=user_message,
                max_tokens=config.MAX_TOKENS_COACH,
            )
            
            print("  ✓ Coaching advice generated")
            return self._normalize_output(result)
        
        except Exception as e:
            print(f"  ✗ Error in Coach Agent: {e}")
            return {
                "practical_tip": "Unable to generate advice due to error",
                "error": str(e),
                "warnings": [],
                "confidence": 0.0,
            }
    
    def _ensure_list(self, value: Union[List[str], str, None]) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _normalize_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(result, dict):
            return {
                "practical_tip": "Unable to generate advice due to error",
                "one_day_action": "",
                "possible_project_idea": None,
                "warnings": [],
                "confidence": 0.0,
            }

        result["warnings"] = self._ensure_list(result.get("warnings", []))
        result["practical_tip"] = result.get("practical_tip", "") or ""
        result["one_day_action"] = result.get("one_day_action", "") or ""
        result["possible_project_idea"] = result.get("possible_project_idea")
        return result

    def _format_previous_insights_context(self, agent_input: AgentInput) -> str:
        """Format prior insights into a short context block."""
        lines = []
        if agent_input.previous_insights:
            lines.append("PREVIOUS DAILY INSIGHTS:")
            for insight in agent_input.previous_insights[: config.PREVIOUS_INSIGHTS_LIMIT]:
                lines.append(f"- {insight.date}: {insight.main_insight} (Action: {insight.one_day_action})")

        if agent_input.previous_insight_summaries:
            lines.append("PREVIOUS INSIGHT SUMMARIES FROM ONE DRIVE:")
            for summary in agent_input.previous_insight_summaries[: config.PREVIOUS_INSIGHTS_LIMIT]:
                first_line = summary.splitlines()[0]
                lines.append(f"- {first_line}")

        return "\n".join(lines) + "\n\n" if lines else ""

    def create_daily_insight(
        self,
        reader_output: Dict[str, Any],
        reflection_output: Dict[str, Any],
        coach_output: Dict[str, Any],
        sources_used: list,
    ) -> DailyInsight:
        """
        Combine all agent outputs into final DailyInsight.
        
        Args:
            reader_output: Reader Agent's analysis
            reflection_output: Reflection Agent's analysis
            coach_output: Coach Agent's advice
            sources_used: List of sources analyzed
        
        Returns:
            DailyInsight structured object
        """
        from datetime import datetime
        
        return DailyInsight(
            date=datetime.now().strftime("%Y-%m-%d"),
            main_insight=coach_output.get("practical_tip", "No insight generated"),
            source_summary=reader_output.get("summary", ""),
            self_reflection=reflection_output.get("hypothesis", ""),
            thinking_biases_detected=reflection_output.get("thinking_biases_detected", []),
            practical_tip=coach_output.get("practical_tip", ""),
            one_day_action=coach_output.get("one_day_action", ""),
            possible_project_idea=coach_output.get("possible_project_idea"),
            important_quotes=reader_output.get("important_quotes", []),
            uncertainties=self._ensure_list(reflection_output.get("uncertainties", [])) + self._ensure_list(coach_output.get("warnings", [])),
            sources_used=sources_used,
        )
