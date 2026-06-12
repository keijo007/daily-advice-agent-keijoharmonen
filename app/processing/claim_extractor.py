"""
Claim Extractor for Personal Signal OS.

Extracts factual claims from items and assesses:
- Evidence level (anecdote, data, research, official, unknown)
- Possible source bias
- How to verify
"""

from typing import List, Optional
from app.models import ContentItem, Claim, SourceBias, EvidenceLevel
import re


class ClaimExtractor:
    """Extract and analyze claims from items."""
    
    def extract_claims(self, items: List[ContentItem]) -> List[Claim]:
        """Extract claims from a list of items."""
        claims = []
        
        for item in items:
            item_claims = self.extract_from_item(item)
            claims.extend(item_claims)
        
        return claims
    
    def extract_from_item(self, item: ContentItem) -> List[Claim]:
        """Extract claims from a single item."""
        if item.claims:
            # Item already has claims marked
            return [
                Claim(
                    claim_text=claim,
                    source=item.author or item.source.value,
                    source_bias=item.source_bias,
                    evidence_level=self._assess_evidence_level(item),
                    possible_bias=self._assess_bias(item),
                    how_to_verify=self._suggest_verification(item),
                    recommended_action=self._recommend_action(item),
                )
                for claim in item.claims
            ]
        
        # Otherwise, extract sentences that look like claims
        claims = []
        sentences = self._extract_sentences(item.content)
        
        for sentence in sentences:
            if self._looks_like_claim(sentence):
                claims.append(
                    Claim(
                        claim_text=sentence,
                        source=item.author or item.source.value,
                        source_bias=item.source_bias,
                        evidence_level=self._assess_evidence_level(item),
                        possible_bias=self._assess_bias(item),
                        how_to_verify=self._suggest_verification(item),
                        recommended_action=self._recommend_action(item),
                    )
                )
        
        return claims[:5]  # Limit to top 5 claims per item
    
    @staticmethod
    def _extract_sentences(text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting (could be enhanced with NLTK)
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    @staticmethod
    def _looks_like_claim(sentence: str) -> bool:
        """Check if sentence looks like a factual claim."""
        # Claims typically have verbs and describe facts, not opinions
        claim_keywords = [
            "is", "are", "was", "were", "has", "have", "shows", "shows",
            "study", "research", "data", "found", "discovered", "increased",
            "decreased", "grows", "growing", "according to"
        ]
        
        sentence_lower = sentence.lower()
        
        # Avoid pure opinions
        opinion_markers = ["i think", "i believe", "in my opinion", "seems like", "probably"]
        if any(marker in sentence_lower for marker in opinion_markers):
            return False
        
        # Should contain claim keywords
        return any(keyword in sentence_lower for keyword in claim_keywords)
    
    @staticmethod
    def _assess_evidence_level(item: ContentItem) -> EvidenceLevel:
        """Assess the evidence level based on source type and content."""
        # Strong evidence from research/official sources
        if item.source_bias == SourceBias.RESEARCH:
            return EvidenceLevel.RESEARCH
        if item.source_bias == SourceBias.OFFICIAL:
            return EvidenceLevel.OFFICIAL
        
        # Check for metrics/numbers in content
        if re.search(r'\$?\d+[\d.,]*%?', item.content):
            return EvidenceLevel.DATA
        
        # Journalist/community sources usually have mixed evidence
        if item.source_bias in [SourceBias.JOURNALIST, SourceBias.COMMUNITY]:
            return EvidenceLevel.DATA
        
        # Operators/investors and personal are often anecdotal
        if item.source_bias in [SourceBias.OPERATOR, SourceBias.INVESTOR, SourceBias.PERSONAL]:
            return EvidenceLevel.ANECDOTE
        
        return EvidenceLevel.UNKNOWN
    
    @staticmethod
    def _assess_bias(item: ContentItem) -> str:
        """Explain potential bias of the source."""
        bias_explanations = {
            SourceBias.OPERATOR: "Founder/operator may oversell their product or vision",
            SourceBias.INVESTOR: "Investor has financial incentive; may push trends they've backed",
            SourceBias.JOURNALIST: "Journalist may simplify complex topics; may chase narratives",
            SourceBias.RESEARCH: "Research-based; generally minimal bias but may have publication bias",
            SourceBias.OFFICIAL: "Official statement; generally accurate but may be carefully worded",
            SourceBias.COMMUNITY: "Community member; useful but high variance in expertise/accuracy",
            SourceBias.PERSONAL: "Personal experience; subjective and not generalizable",
            SourceBias.UNKNOWN: "Unknown source; cannot assess bias",
        }
        
        return bias_explanations.get(item.source_bias, "Unknown source bias")
    
    @staticmethod
    def _suggest_verification(item: ContentItem) -> str:
        """Suggest how to verify the claim."""
        if item.source_bias == SourceBias.RESEARCH:
            return "Review the original research paper for methodology and conclusions"
        elif item.source_bias == SourceBias.OFFICIAL:
            return "Check official sources for confirmation"
        elif item.source_bias == SourceBias.JOURNALIST:
            return "Look for data/studies cited in the article; fact-check key numbers"
        elif item.source_bias == SourceBias.OPERATOR:
            return "Interview customers or users; check metrics/reviews independent of source"
        elif item.source_bias == SourceBias.INVESTOR:
            return "Check regulatory filings, independent analyses, and recent performance"
        elif item.source_bias == SourceBias.COMMUNITY:
            return "Look for corroboration from multiple community members or experts"
        elif item.source_bias == SourceBias.PERSONAL:
            return "Seek similar experiences from others; check if generalizable"
        else:
            return "Seek independent verification from trusted sources"
    
    @staticmethod
    def _recommend_action(item: ContentItem) -> str:
        """Recommend what to do with this claim."""
        # High-credibility sources: act on claims
        if item.source_bias in [SourceBias.RESEARCH, SourceBias.OFFICIAL]:
            return "act"
        
        # Medium: verify then follow up
        if item.source_bias in [SourceBias.JOURNALIST, SourceBias.OPERATOR]:
            return "verify"
        
        # Low credibility: just follow/monitor
        if item.source_bias in [SourceBias.COMMUNITY, SourceBias.PERSONAL]:
            return "follow"
        
        return "verify"
