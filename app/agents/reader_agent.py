"""
Reader Agent - summarizes new content from external sources.

ROLE:
- Reads today's new external content (RSS, WhatsApp, etc.)
- Summarizes it efficiently while preserving important quotes
- Separates facts from opinions/interpretations
- Does NOT add personal interpretation

WHAT IT RECEIVES:
- new_items: List of ContentItem from today's collection
- goals: Your goals (for context, but not judgment)
- No diary (diary is for reflection agent)

WHAT IT RETURNS:
{
  \"summary\": \"Concise summary of key learnings\",
  \"key_topics\": [\"topic1\", \"topic2\"],
  \"important_quotes\": [
    {\"quote\": \"...\", \"source\": \"...attribuition\"},
  ],
  \"facts_vs_opinions\": {
    \"facts\": [\"...\"],
    \"opinions\": [\"...\"],
    \"interpretations\": [\"...\"],
  },
  \"sources_used\": [\"source1\", \"source2\"],
}

AGENT THINKING PRINCIPLES:
- Accuracy first: Never hallucinate or invent content
- Neutrality: Report what was said, not judgment
- Efficiency: Keep it brief and actionable
- Evidence: Quote directly, don't paraphrase
- Scope: Only new items, not from memory

EXTENSION IDEAS:
- Add readability scoring (how important is this?)
- Sentiment analysis (is this positive/negative news?)
- Categorize by topic automatically
- Extract entities (who, what, where, when)
"""

import json
from typing import List, Dict, Any
from app.agents.base_agent import BaseAgent
from app.models import AgentInput, ContentItem
from app.services.openai_client import call_openai_json
from app.config import config


class ReaderAgent(BaseAgent):
    """Summarizes new external content."""
    
    def __init__(self):
        super().__init__(
            name="Reader",
            system_prompt=self._build_system_prompt(),
        )
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for this agent."""
        return """You are a creative reader and summarizer.

YOUR ROLE:
- Read new external content provided
- Summarize the most useful learnings clearly
- Preserve important quotes and attribution when available
- Highlight key themes and takeaways
- When content comes from Telegram, capture the most relevant points, patterns, and potential action signals

GUIDELINES:
- Never invent or hallucinate information
- Attribute quotes to source/author when possible
- Be factual, but allow the summary to flow naturally
- Keep the output concise and useful
- Organize around what matters most in the content

OUTPUT: Return valid JSON with keys:
- summary: Main learnings
- key_topics: List of topics covered
- important_quotes: List of {quote, source} objects
- facts_vs_opinions: Breakdown of facts vs opinions
- sources_used: List of source names
"""
    
    def think(self, agent_input: AgentInput) -> Dict[str, Any]:
        """
        Summarize new content.
        
        Args:
            agent_input: Contains new_items, goals, etc.
        
        Returns:
            Dictionary with summary, quotes, etc.
        """
        
        if not agent_input.new_items:
            print("ℹ️  Reader Agent: No new items to analyze")
            return {
                "summary": "No new content today.",
                "key_topics": [],
                "important_quotes": [],
                "facts_vs_opinions": {"facts": [], "opinions": [], "interpretations": []},
                "sources_used": [],
            }
        
        print(f"📖 Reader Agent: Analyzing {len(agent_input.new_items)} items...")
        
        # Format items for the prompt
        items_text = self._format_items_for_context(agent_input.new_items)
        
        # Build the user message
        user_message = f"""Please analyze these new items and provide a summary:

{items_text}

Remember:
- Preserve direct quotes with attribution
- Separate facts from opinions
- Be objective and factual
- No interpretation or judgment"""
        
        try:
            # Call OpenAI
            result = call_openai_json(
                system_prompt=self.system_prompt,
                user_message=user_message,
                max_tokens=config.MAX_TOKENS_READER,
            )
            
            print("  ✓ Analysis complete")
            return result
        
        except Exception as e:
            print(f"  ✗ Error in Reader Agent: {e}")
            return {
                "summary": "Error analyzing content",
                "error": str(e),
                "sources_used": [item.source.value for item in agent_input.new_items],
            }
