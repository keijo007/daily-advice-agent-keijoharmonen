"""
Opportunity Agent for Personal Signal OS.

Formats opportunities extracted from items into Signal cards.
"""

from typing import List, Optional
from app.models import Opportunity, ScoredItem
from app.services.openai_client import OpenAIClient


class OpportunityAgent:
    """Format opportunities for daily brief."""
    
    def __init__(self, openai_client: Optional[OpenAIClient] = None):
        """Initialize with optional OpenAI client."""
        self.openai_client = openai_client
    
    def process(self, opportunities: List[Opportunity]) -> List[Opportunity]:
        """
        Process and rank opportunities.
        
        Sorts by urgency (deadline) and relevance.
        """
        # Sort by deadline urgency
        def urgency_key(opp):
            if not opp.deadline:
                return float('inf')  # No deadline = low priority
            
            from datetime import datetime
            days_until = (opp.deadline - datetime.now()).days
            return days_until if days_until >= 0 else float('inf')
        
        sorted_opps = sorted(opportunities, key=urgency_key)
        
        return sorted_opps[:5]  # Return top 5
