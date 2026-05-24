"""
AI Agents for Daily Insight Agent.

WHY AGENTS:
- Separate concerns: each agent has one job
- Agent pattern enables testability and extensibility
- Each agent can be replaced/improved independently

HOW IT RELATES TO AGENT THINKING:
- Reader Agent: "What did I learn today?"
- Reflection Agent: "What patterns do I see in myself?"
- Coach Agent: "What should I do about it?"

This is inspired by multi-agent systems where:
- Agents have specialized roles
- They work with standardized interfaces (ContentItem, DailyInsight)
- They can be chained or parallelized

HOW TO EXTEND:
- Add new agent types (e.g., RiskAnalyzer, OpportunitySurvey)
- Make agents smarter with prompt engineering
- Add agent-to-agent communication
- Create specialized agents for different goal areas
"""

from typing import List, Optional
from app.models import ContentItem, DailyInsight
from app.services.openai_client import OpenAIClient


class ReaderAgent:
    """
    Reader Agent: Summarize today's information.
    
    ROLE:
    - Read all new items from today
    - Extract key learnings
    - Preserve original voice and important quotes
    - Don't hallucinate - only use provided content
    - Distinguish facts vs. opinions vs. interpretations
    
    OUTPUT USED BY: Coach Agent (for final advice)
    """

    def __init__(self, openai_client: OpenAIClient, system_prompt: str):
        """
        Args:
            openai_client: OpenAI API wrapper
            system_prompt: Instructions for the reader (from prompts/reader_prompt.md)
        """
        self.openai_client = openai_client
        self.system_prompt = system_prompt

    def analyze(self, items: List[ContentItem], max_tokens: int = 1000) -> Optional[str]:
        """
        Analyze new items and generate summary.
        
        Args:
            items: Content items collected today
            max_tokens: Max response length
            
        Returns:
            Reader's summary or None if error
        """
        
        if not items:
            return "No new items to summarize today."

        # Format items for the prompt
        formatted_items = self._format_items(items)

        user_message = f"""
Please analyze these items from today and provide a summary:

{formatted_items}

Focus on:
1. Key learnings and insights
2. Important quotes or original statements
3. Distinguish between facts, opinions, and interpretations
4. Don't add information not in the items above
"""

        return self.openai_client.call_with_prompt(
            system_prompt=self.system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
        )

    def _format_items(self, items: List[ContentItem]) -> str:
        """Format ContentItems for display in prompt."""
        formatted = []
        for i, item in enumerate(items, 1):
            formatted.append(f"""
Item {i} ({item.source.value}):
Title: {item.title}
Author: {item.author}
Time: {item.timestamp.isoformat()}
Content: {item.content[:500]}...
""")
        return "\n".join(formatted)


class ReflectionAgent:
    """
    Reflection Agent: Objective self-analysis.
    
    ROLE:
    - Read diary + goals
    - Identify patterns, biases, contradictions
    - Act as objective observer ("wise stranger")
    - Use research/statistics/heuristics
    - Honor philosophical/spiritual perspectives without pseudoscience
    - Be honest about uncertainty
    
    OUTPUT USED BY: Coach Agent (for personalized advice)
    """

    def __init__(self, openai_client: OpenAIClient, system_prompt: str):
        self.openai_client = openai_client
        self.system_prompt = system_prompt

    def analyze(
        self,
        goals: Optional[str],
        recent_diary: Optional[str],
        reader_summary: Optional[str],
        max_tokens: int = 1500,
    ) -> Optional[str]:
        """
        Analyze user's goals and diary for patterns and biases.
        
        Args:
            goals: Current goals from goals.txt
            recent_diary: Recent diary entries
            reader_summary: Today's content summary from Reader Agent
            max_tokens: Max response length
            
        Returns:
            Reflection's analysis or None
        """

        user_message = f"""
I'm reflecting on my situation. Please help me see patterns and blind spots:

MY GOALS:
{goals or "Not provided"}

RECENT DIARY ENTRIES:
{recent_diary or "Not provided"}

TODAY'S SUMMARY (from reading):
{reader_summary or "Not provided"}

Please analyze:
1. What patterns do you see in my thinking?
2. What cognitive biases might I be exhibiting?
3. Are there contradictions between my goals and diary?
4. What would a wise, objective observer notice about me?
5. What uncertainty should I acknowledge?
"""

        return self.openai_client.call_with_prompt(
            system_prompt=self.system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
        )


class CoachAgent:
    """
    Coach Agent: Actionable advice and insights.
    
    ROLE:
    - Combine Reader + Reflection
    - Provide ONE concrete, realistic action for today
    - Suggest ONE possible project idea (if appropriate)
    - Warn of risks in decisions
    - Don't give generic motivation
    - Say "I don't have enough info" if true
    
    OUTPUT: Final DailyInsight for user
    """

    def __init__(self, openai_client: OpenAIClient, system_prompt: str):
        self.openai_client = openai_client
        self.system_prompt = system_prompt

    def generate_insight(
        self,
        reader_summary: Optional[str],
        reflection_analysis: Optional[str],
        sources: List[str],
        max_tokens: int = 800,
    ) -> Optional[str]:
        """
        Generate final daily insight combining all analysis.
        
        Args:
            reader_summary: Today's content from Reader Agent
            reflection_analysis: Self-analysis from Reflection Agent
            sources: List of sources used (for attribution)
            max_tokens: Max response length
            
        Returns:
            Structured insight or None
        """

        user_message = f"""
Based on today's learning and reflection, provide a daily insight:

WHAT I LEARNED TODAY:
{reader_summary or "Not provided"}

MY REFLECTION:
{reflection_analysis or "Not provided"}

Please provide in this exact format:
1. MAIN INSIGHT: [One sentence summary]
2. PRACTICAL TIP: [Concrete, realistic advice]
3. ONE DAY ACTION: [Something I can do in 24 hours]
4. POSSIBLE PROJECT IDEA: [If applicable, or "Not applicable"]
5. IMPORTANT QUOTES: [Key quotes from today's reading, with sources]
6. UNCERTAINTIES: [What we don't know or can't be sure about]
7. THINKING BIASES DETECTED: [Cognitive biases noticed]
8. WARNING: [Any risky decisions to reconsider?]
"""

        return self.openai_client.call_with_prompt(
            system_prompt=self.system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
        )


# Factory functions for easy initialization
def create_reader_agent(
    openai_client: OpenAIClient,
    system_prompt: str,
) -> ReaderAgent:
    """Create a Reader Agent."""
    return ReaderAgent(openai_client, system_prompt)


def create_reflection_agent(
    openai_client: OpenAIClient,
    system_prompt: str,
) -> ReflectionAgent:
    """Create a Reflection Agent."""
    return ReflectionAgent(openai_client, system_prompt)


def create_coach_agent(
    openai_client: OpenAIClient,
    system_prompt: str,
) -> CoachAgent:
    """Create a Coach Agent."""
    return CoachAgent(openai_client, system_prompt)
