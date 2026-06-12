"""
Claim Checker Agent for Personal Signal OS.

Formats claims and provides verification guidance.
"""

from typing import List, Optional
from app.models import Claim
from app.services.openai_client import OpenAIClient


class ClaimCheckerAgent:
    """Format and prioritize claims to verify."""
    
    def __init__(self, openai_client: Optional['OpenAIClient'] = None):
        """Initialize with optional OpenAI client."""
        self.openai_client = openai_client
    
    def process(self, claims: List[Claim]) -> List[Claim]:
        """
        Process and rank claims by importance.
        
        Prioritizes high-impact claims from credible sources.
        """
        # Score claims by importance
        def claim_importance(claim: Claim):
            importance = 0.0
            
            # High priority: official/research sources with important claims
            if claim.source_bias.value in ["official", "research"]:
                importance += 5.0
            
            # High priority: claims about opportunities/deadlines
            if any(word in claim.claim_text.lower() for word in ["deadline", "hiring", "funding"]):
                importance += 4.0
            
            # High priority: claims with data
            if claim.evidence_level.value == "data":
                importance += 2.0
            
            # Low priority: anecdotal claims from unknown sources
            if claim.evidence_level.value == "anecdote":
                importance -= 2.0
            
            return importance
        
        sorted_claims = sorted(claims, key=claim_importance, reverse=True)
        
        return sorted_claims[:5]  # Return top 5
