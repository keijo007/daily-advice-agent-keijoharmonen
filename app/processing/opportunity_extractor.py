"""
Opportunity Extractor for Personal Signal OS.

Finds and extracts opportunities from items:
- Events, conferences, meetups
- Job postings, internships
- Funding, grants, scholarships
- Volunteering opportunities
- Applications and competitions
- Communities and learning opportunities
"""

from datetime import datetime
from typing import List, Optional
from app.models import ContentItem, Opportunity, SourceType
import re


class OpportunityExtractor:
    """Extract opportunities from content items."""
    
    # Keyword patterns for different opportunity types
    OPPORTUNITY_KEYWORDS = {
        "job": ["hiring", "job opening", "position", "career opportunity", "recruitment",
                "now hiring", "open position", "we're hiring", "apply now", "career"],
        "internship": ["internship", "intern", "co-op", "internships available", "apply for internship"],
        "event": ["conference", "meetup", "summit", "workshop", "webinar", "talk", "presentation",
                 "event", "gathering", "join us", "happening", "coming soon", "save the date",
                 "virtual event", "in-person event"],
        "grant": ["grant", "funding", "funded", "grant opportunity", "apply for grant",
                 "funding available", "grants open"],
        "scholarship": ["scholarship", "scholarships", "educational grant", "tuition support"],
        "application": ["apply", "application", "apply now", "applications open", "call for applications",
                       "submissions open", "entry period", "acceptance window"],
        "hackathon": ["hackathon", "hack-a-thon", "coding competition", "hackfest"],
        "competition": ["competition", "contest", "challenge", "award", "prize", "winners"],
        "volunteer": ["volunteer", "volunteering", "volunteers needed", "volunteer opportunity",
                     "community service", "help needed"],
        "learning": ["course", "training", "bootcamp", "class", "learning opportunity", "certification",
                    "school", "university", "program", "degree"],
    }
    
    def extract_opportunities(self, items: List[ContentItem]) -> List[Opportunity]:
        """Extract opportunities from a list of items."""
        opportunities = []
        
        for item in items:
            opp = self.extract_from_item(item)
            if opp:
                opportunities.append(opp)
        
        return opportunities
    
    def extract_from_item(self, item: ContentItem) -> Optional[Opportunity]:
        """
        Extract opportunity from a single item if present.
        
        Returns: Opportunity or None
        """
        text = f"{item.title} {item.content}".lower()
        
        # Check if item contains opportunity keywords
        opportunity_type = self._detect_opportunity_type(text)
        if not opportunity_type:
            return None
        
        # Extract deadline if present
        deadline = self._extract_deadline(item)
        
        # Extract action step
        next_action = self._extract_next_action(item, opportunity_type)
        
        # Create relevance explanation
        why_relevant = self._explain_relevance(item, opportunity_type)
        
        return Opportunity(
            title=item.title,
            description=item.content[:500],  # Truncate to 500 chars
            why_relevant=why_relevant,
            deadline=deadline,
            next_action=next_action,
            source=item.author or item.source.value,
            url=item.url,
            opportunity_type=opportunity_type,
        )
    
    def _detect_opportunity_type(self, text: str) -> Optional[str]:
        """Detect what type of opportunity this is."""
        for opp_type, keywords in self.OPPORTUNITY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return opp_type
        
        return None
    
    def _extract_deadline(self, item: ContentItem) -> Optional[datetime]:
        """
        Extract deadline from item.
        
        Checks:
        1. Item deadline field (already parsed)
        2. Text patterns in content
        """
        if item.deadline:
            return item.deadline
        
        # Look for deadline patterns in text
        text = f"{item.title} {item.content}".lower()
        
        deadline_patterns = [
            r"deadline[:\s]+([a-z]+ \d{1,2}(?:st|nd|rd|th)?(?:\s*,?\s*\d{4})?)",
            r"apply by ([a-z]+ \d{1,2}(?:st|nd|rd|th)?(?:\s*,?\s*\d{4})?)",
            r"until ([a-z]+ \d{1,2}(?:st|nd|rd|th)?(?:\s*,?\s*\d{4})?)",
            r"due ([a-z]+ \d{1,2}(?:st|nd|rd|th)?(?:\s*,?\s*\d{4})?)",
            r"(\d{1,2}/\d{1,2}/\d{2,4})",
            r"(\d{4}-\d{2}-\d{2})",
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, text)
            if match:
                # Parse the found date (simple parsing, could be enhanced)
                date_str = match.group(1)
                # For MVP, we keep it as string; could parse with dateutil
                return None  # TODO: Implement date parsing
        
        return None
    
    def _extract_next_action(self, item: ContentItem, opportunity_type: str) -> str:
        """Generate recommended next action based on opportunity type."""
        if item.url:
            return f"Visit {item.url} to learn more and apply"
        
        # Generic actions by type
        actions = {
            "job": "Visit the company's careers page or job board to apply",
            "internship": "Prepare your resume and cover letter, then apply",
            "event": "Check the event website for registration details",
            "grant": "Review eligibility requirements and submit application",
            "scholarship": "Complete the application form with required documents",
            "application": "Review requirements and submit your application",
            "hackathon": "Register and gather your team",
            "competition": "Review rules and prepare your submission",
            "volunteer": "Contact the organization to learn about roles and sign up",
            "learning": "Check prerequisites and enroll in the program",
        }
        
        return actions.get(opportunity_type, "Take action to pursue this opportunity")
    
    def _explain_relevance(self, item: ContentItem, opportunity_type: str) -> str:
        """Generate explanation of why this opportunity is relevant."""
        explanations = {
            "job": f"Job opportunity: {item.title}",
            "internship": f"Internship opportunity: {item.title}",
            "event": f"Upcoming event: {item.title}",
            "grant": f"Potential funding: {item.title}",
            "scholarship": f"Scholarship opportunity: {item.title}",
            "application": f"Application deadline: {item.title}",
            "hackathon": f"Hackathon: {item.title}",
            "competition": f"Competition: {item.title}",
            "volunteer": f"Volunteer opportunity: {item.title}",
            "learning": f"Learning opportunity: {item.title}",
        }
        
        return explanations.get(opportunity_type, item.title)
