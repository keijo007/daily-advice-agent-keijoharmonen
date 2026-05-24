"""
Base Agent abstract class.

WHY THIS FILE EXISTS:
- Defines the interface for all AI agents
- Ensures consistent input/output across agents
- Makes agents composable and testable

AGENT ARCHITECTURE CONCEPT:
- Each agent has a specific role
- Agents receive AgentInput (context)
- Agents return structured output
- Agents can be chained (output of one becomes input to next)

HOW IT WORKS:
- Implement think() method to add AI logic
- Agent loads its system prompt
- Calls OpenAI API
- Parses and returns structured result

THREE AGENTS IN THIS SYSTEM:
1. ReaderAgent: Summarizes new external content
2. ReflectionAgent: Analyzes your diary vs goals
3. CoachAgent: Combines insights, gives advice

EXTENSION IDEAS:
- Add logging/tracing for debugging
- Cache responses for efficiency
- Add confidence scores to outputs
- Support multiple model backends
- Add human-in-the-loop review
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from app.models import AgentInput, ContentItem, DailyInsight


class BaseAgent(ABC):
    """Abstract base class for AI agents."""
    
    def __init__(self, name: str, system_prompt: Optional[str] = None):
        """
        Initialize agent.
        
        Args:
            name: Agent name (for logging)
            system_prompt: System prompt for OpenAI (optional)
        """
        self.name = name
        self.system_prompt = system_prompt or self._load_system_prompt()
    
    @abstractmethod
    def think(self, agent_input: AgentInput) -> dict:
        """
        Process input and return analysis.
        
        This is where the AI logic happens.
        Each agent subclass implements its own thinking process.
        
        Args:
            agent_input: Combined input data (items, goals, diary, etc.)
        
        Returns:
            Dictionary with analysis results (structure varies by agent)
        """
        pass
    
    def _load_system_prompt(self) -> str:
        """
        Load system prompt from file.
        
        Override if you want custom prompt loading logic.
        """
        return "You are a helpful AI assistant."
    
    def _format_items_for_context(self, items: List[ContentItem], max_chars: int = 5000) -> str:
        """
        Format items into readable context for the prompt.
        
        PRIVACY NOTE:
        - Truncates to max_chars to limit what goes to OpenAI
        - Only send necessary information
        
        Args:
            items: Items to format
            max_chars: Maximum characters to include
        
        Returns:
            Formatted context string
        """
        context = ""
        for item in items:
            if len(context) >= max_chars:
                context += f"\n\n... and {len(items) - items.index(item)} more items"
                break
            
            context += f"**{item.title}** (from {item.source.value})\n"
            context += f"{item.content[:500]}...\n\n"
        
        return context
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"
