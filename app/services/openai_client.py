"""
OpenAI API client wrapper.

WHY THIS LAYER EXISTS:
- Wraps OpenAI API calls in a clean interface
- Handles API errors gracefully
- Makes it easy for agents to call LLM without managing details
- Centralizes cost/token tracking

HOW IT RELATES TO AGENT THINKING:
- Each agent calls methods like call_with_prompt()
- Agent doesn't care about API details or error handling
- Enables easy model switching (e.g., gpt-4 → claude later)

HOW TO EXTEND:
- Add cost tracking/budget alerts
- Support multiple models
- Add retry logic with exponential backoff
- Cache responses to reduce API calls

SECURITY NOTE:
- API key is loaded from environment (.env)
- No keys hardcoded in this file
- Be careful not to log API responses (they contain user data)
"""

from typing import Optional
import os

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI library not installed. Install with: pip install openai")


class OpenAIClient:
    """
    Wrapper around OpenAI API.
    
    USAGE EXAMPLE:
    >>> client = OpenAIClient(api_key="sk-...")
    >>> response = client.call_with_prompt(
    ...     prompt="Summarize this content:",
    ...     content="...",
    ...     max_tokens=500
    ... )
    """

    def __init__(self, api_key: str, model: str = "gpt-4-1-mini"):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (from .env)
            model: Model to use (default: gpt-4-1-mini for cost efficiency)
        """
        self.api_key = api_key
        self.model = model
        self.client = None
        
        if OPENAI_AVAILABLE and api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            print("⚠️  OpenAI client not available. Check API key and library.")

    def call_with_prompt(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 500,
    ) -> Optional[str]:
        """
        Call OpenAI API with given prompts.
        
        SECURITY NOTE:
        - user_message may contain private diary/goal data
        - Response contains AI-generated analysis (also private)
        - Don't log or transmit these without user consent
        
        Args:
            system_prompt: Instructions for the model (e.g., from prompts/*.md)
            user_message: The actual content to analyze
            max_tokens: Max length of response
            
        Returns:
            Model's response or None if error
        """
        
        if not self.client:
            print("❌ OpenAI client not initialized")
            return None

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=max_tokens,
                temperature=0.7,  # Balanced between creative and consistent
            )
            
            return response.choices[0].message.content

        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return None

    def check_connection(self) -> bool:
        """Test if API connection works."""
        if not self.client:
            return False
        
        try:
            # Simple test call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=10,
            )
            return True
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False


# Factory function to create client from config
def create_openai_client(api_key: str, model: str = "gpt-4-1-mini") -> OpenAIClient:
    """Create OpenAI client from API key."""
    return OpenAIClient(api_key=api_key, model=model)
