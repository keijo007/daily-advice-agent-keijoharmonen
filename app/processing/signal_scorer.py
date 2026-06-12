"""
Signal Scoring Engine for Personal Signal OS.

Implements transparent weighted formula to score each item and classify it.

SCORING FORMULA (0-10 scale):
    signal_score = 
      2.0 * relevance_to_goals
      + 1.5 * actionability
      + 1.5 * deadline_urgency
      + 1.2 * novelty
      + 1.0 * source_quality
      + 1.0 * repeated_across_sources
    + 0.8 * personal_fit
      - 1.5 * distraction_risk
      - 1.0 * weak_evidence

CLASSIFICATIONS:
    - SIGNAL (score >= 5.0): Top 5 items
    - WEAK_SIGNAL (3.0-4.9): May matter if repeated
    - OPPORTUNITY (any score): Has deadline/opportunity keywords
    - VERIFY (any score): Important claim needing verification
    - NOISE (< 3.0): Low priority
"""

from datetime import datetime
from typing import Dict, List, Optional
from app.models import ContentItem, ScoredItem, SignalType, SourceBias
import re

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


class SignalScorer:
    """Score items using transparent heuristic formula."""
    
    def __init__(self, goals: Optional[str] = None, current_state: Optional[str] = None):
        """
        Initialize scorer with goals and current state for relevance matching.
        
        Args:
            goals: Content of goals.md (for relevance scoring)
            current_state: Content of current_state.yaml (for context)
        """
        self.goals = goals or ""
        self.current_state = current_state or ""
        self.goal_keywords = self._extract_keywords(goals or "")
        self.avoid_keywords = self._extract_keywords(current_state or "", section="avoid")
        self._decision_deadlines = self._parse_decision_deadlines(self.current_state)
        self._repetition_scores: Dict[str, float] = {}
    
    def score_item(self, item: ContentItem, repeated_override: Optional[float] = None) -> ScoredItem:
        """
        Score an item and return ScoredItem with classification.
        
        Returns: ScoredItem with signal_score and signal_type
        """
        # Compute components
        relevance = self._relevance_to_goals(item)
        actionability = self._actionability(item)
        deadline_urgency = self._deadline_urgency(item)
        novelty = self._novelty(item)
        source_quality = self._source_quality(item)
        repeated = repeated_override if repeated_override is not None else self._repeated_across_sources(item)
        personal_fit = self._personal_fit(item)
        distraction = self._distraction_risk(item)
        weak_evidence = self._weak_evidence(item)
        
        # Apply weighted formula
        signal_score = (
            2.0 * relevance
            + 1.5 * actionability
            + 1.5 * deadline_urgency
            + 1.2 * novelty
            + 1.0 * source_quality
            + 1.0 * repeated
            + 0.8 * personal_fit
            - 1.5 * distraction
            - 1.0 * weak_evidence
        )
        
        # Clamp to 0-10 range
        signal_score = max(0.0, min(10.0, signal_score))
        
        # Classify
        signal_type = self._classify(signal_score, item)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            signal_score, relevance, actionability, deadline_urgency,
            novelty, source_quality, repeated, personal_fit, distraction, weak_evidence
        )
        
        return ScoredItem(
            item=item,
            signal_score=signal_score,
            signal_type=signal_type,
            reasoning=reasoning,
        )
    
    def score_items(self, items: List[ContentItem]) -> List[ScoredItem]:
        """Score a batch of items."""
        self._repetition_scores = self._build_repetition_scores(items)
        scored: List[ScoredItem] = []
        for item in items:
            key = self._repetition_key(item)
            scored.append(self.score_item(item, repeated_override=self._repetition_scores.get(key, 0.0)))
        return scored
    
    # ==================== SCORING COMPONENTS ====================
    
    def _relevance_to_goals(self, item: ContentItem) -> float:
        """
        0-1 score: How relevant is this to my current goals?
        
        Based on keyword overlap with goals.md.
        """
        if not self.goal_keywords:
            return 0.5  # Neutral if no goals provided
        
        text = f"{item.title} {item.content}".lower()
        
        # Count keyword hits
        hit_count = sum(1 for keyword in self.goal_keywords if keyword.lower() in text)
        
        # Also check if item topics overlap with goal keywords
        topic_hits = sum(1 for topic in item.topics if topic.lower() in self.goal_keywords)
        
        total_hits = hit_count + topic_hits * 2  # Weight topic hits higher
        
        # Return score: 0-1, higher if more hits
        return min(1.0, total_hits * 0.2)
    
    def _actionability(self, item: ContentItem) -> float:
        """
        0-1 score: How actionable is this item?
        
        High actionability if:
        - Contains verbs (do, try, apply, send, etc.)
        - Contains deadlines/dates
        - Contains calls-to-action
        - Has deadline field set
        """
        if item.actionability_score > 0:
            return min(1.0, item.actionability_score)
        
        text = f"{item.title} {item.content}".lower()
        
        score = 0.0
        
        # Check for action verbs
        action_verbs = ["apply", "sign", "submit", "send", "register", "join", "start",
                       "begin", "try", "test", "launch", "call", "email", "contact"]
        if any(verb in text for verb in action_verbs):
            score += 0.4
        
        # Check for dates/deadlines
        if self._contains_date(text):
            score += 0.3
        
        # Check for CTA language
        cta_keywords = ["deadline", "limited time", "hurry", "today", "now", "apply here"]
        if any(cta in text for cta in cta_keywords):
            score += 0.3
        
        # Check if item has deadline field
        if item.deadline:
            score += 0.2
        
        return min(1.0, score)
    
    def _deadline_urgency(self, item: ContentItem) -> float:
        """
        0-1 score: How urgent is the deadline?
        
        Exponential urgency based on days until deadline:
        - 0-3 days: 1.0 (critical)
        - 3-7 days: 0.8 (high)
        - 7-30 days: 0.5 (medium)
        - 30+ days: 0.2 (low)
        - No deadline: 0.0
        """
        deadline = item.deadline
        if not deadline:
            deadline = self._match_deadline_from_current_state(item)
            if not deadline:
                return 0.0
        
        today = datetime.now()
        days_until = (deadline - today).days
        
        if days_until < 0:
            return 0.0  # Deadline has passed
        elif days_until <= 3:
            return 1.0
        elif days_until <= 7:
            return 0.8
        elif days_until <= 30:
            return 0.5
        else:
            return 0.2
    
    def _novelty(self, item: ContentItem) -> float:
        """
        0-1 score: How novel/new is this information?
        
        Based on:
        - How recently was it published/collected?
        - Not already in our previous insights/knowledge
        """
        # Recent items (< 1 week) get higher novelty
        age_hours = (datetime.now() - item.timestamp).total_seconds() / 3600
        
        if age_hours < 24:
            return 1.0
        elif age_hours < 7 * 24:
            return 0.7
        elif age_hours < 30 * 24:
            return 0.4
        else:
            return 0.2
    
    def _source_quality(self, item: ContentItem) -> float:
        """
        0-1 score: How trustworthy is the source?
        
        Bias type weighting:
        - RESEARCH/OFFICIAL: 1.0 (high trust)
        - JOURNALIST: 0.7 (broad but may be shallow)
        - OPERATOR/INVESTOR: 0.6 (early signals but has bias)
        - COMMUNITY: 0.4 (useful but noisy)
        - PERSONAL: 0.5 (subjective, for reflection)
        - UNKNOWN: 0.3 (unverified)
        """
        bias_weights = {
            SourceBias.RESEARCH: 1.0,
            SourceBias.OFFICIAL: 1.0,
            SourceBias.JOURNALIST: 0.7,
            SourceBias.OPERATOR: 0.6,
            SourceBias.INVESTOR: 0.6,
            SourceBias.PERSONAL: 0.5,
            SourceBias.COMMUNITY: 0.4,
            SourceBias.UNKNOWN: 0.3,
        }
        
        return bias_weights.get(item.source_bias, 0.3)
    
    def _repeated_across_sources(self, item: ContentItem) -> float:
        """
        0-1 score: Is this repeated across multiple sources?
        
        Repetition score is precomputed in score_items() by comparing
        similar titles appearing from different sources.
        """
        return self._repetition_scores.get(self._repetition_key(item), 0.0)

    def _personal_fit(self, item: ContentItem) -> float:
        """0-1 score: fit with personal context (goals/current state/diary-like focus)."""
        text = f"{item.title} {item.content}".lower()
        score = 0.0

        focus_keywords = self._extract_keywords(self.current_state, section="current_focus")
        if focus_keywords:
            focus_hits = sum(1 for kw in focus_keywords if kw in text)
            score += min(0.6, focus_hits * 0.2)

        goal_hits = sum(1 for kw in self.goal_keywords if kw in text)
        score += min(0.4, goal_hits * 0.1)

        # Personal notes are useful for reflection fit, but not factual truth.
        if item.source_bias == SourceBias.PERSONAL:
            score += 0.2

        return min(1.0, score)
    
    def _distraction_risk(self, item: ContentItem) -> float:
        """
        0-1 score: How likely is this to be a distraction?
        
        High distraction if:
        - Pure entertainment (entertainment keywords)
        - Pure hype (hype keywords without substance)
        - Matches "avoid" keywords from current_state
        - Is off-topic from goals
        """
        text = f"{item.title} {item.content}".lower()
        
        score = 0.0
        
        # Entertainment keywords
        entertainment = ["funny", "viral", "meme", "celebrity", "gossip", "drama", "trending on tiktok"]
        if any(ent in text for ent in entertainment):
            score += 0.5
        
        # Pure hype without substance
        hype_keywords = ["revolutionary", "game-changer", "disrupting", "the next big thing"]
        hype_hits = sum(1 for hype in hype_keywords if hype in text)
        if hype_hits > 2 and "not verified" not in text and "claims" not in text:
            score += 0.3
        
        # Check against avoid keywords
        if self.avoid_keywords:
            avoid_hits = sum(1 for avoid in self.avoid_keywords if avoid.lower() in text)
            score += min(0.5, avoid_hits * 0.2)
        
        # Very short content is often low-value
        if len(item.content) < 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _weak_evidence(self, item: ContentItem) -> float:
        """
        0-1 score: How strong is the evidence for claims?
        
        High weak_evidence if:
        - Claims present but no sources cited
        - Anecdotal ("I think", "seems like", "heard that")
        - No data/metrics provided
        """
        text = f"{item.title} {item.content}".lower()
        
        score = 0.0
        
        # Anecdotal language
        anecdotal = ["i think", "seems like", "heard that", "probably", "maybe", "i feel like"]
        anecdotal_hits = sum(1 for phrase in anecdotal if phrase in text)
        score += min(0.5, anecdotal_hits * 0.15)
        
        # Claims without sources
        if item.claims and not any(item.url or item.author for _ in item.claims):
            score += 0.3
        
        # No metrics/data
        if not self._contains_numbers(text):
            score += 0.2
        
        return min(1.0, score)
    
    # ==================== CLASSIFICATION ====================
    
    def _classify(self, signal_score: float, item: ContentItem) -> SignalType:
        """
        Classify item based on score and content features.
        
        Rules:
        - If has deadline/opportunity keywords: OPPORTUNITY
        - If has claims or needs verification: VERIFY
        - If score >= 5.0: SIGNAL
        - If score 3.0-4.9: WEAK_SIGNAL
        - If score < 3.0: NOISE
        """
        # Check for opportunity indicators
        if self._is_opportunity(item):
            return SignalType.OPPORTUNITY
        
        # Check for claims needing verification
        if self._has_important_claim(item):
            return SignalType.VERIFY
        
        # Classify by score
        if signal_score >= 5.0:
            return SignalType.SIGNAL
        elif signal_score >= 3.0:
            return SignalType.WEAK_SIGNAL
        else:
            return SignalType.NOISE
    
    def _is_opportunity(self, item: ContentItem) -> bool:
        """Check if item is an opportunity (deadline, job, event, etc.)."""
        opportunity_keywords = [
            "deadline", "apply", "application", "job", "hiring", "internship",
            "grant", "scholarship", "hackathon", "competition", "event",
            "volunteer", "volunteering", "meetup", "conference", "course",
            "launching", "open position", "opening", "funded", "funding",
            "award", "contest", "startup", "founder", "community"
        ]
        
        text = f"{item.title} {item.content}".lower()
        
        # Strong signal: has deadline field
        if item.deadline:
            return True
        
        # Check keyword count
        keyword_hits = sum(1 for keyword in opportunity_keywords if keyword in text)
        return keyword_hits >= 2
    
    def _has_important_claim(self, item: ContentItem) -> bool:
        """Check if item has important claims that need verification."""
        if item.claims and len(item.claims) > 0:
            # Claims present and not from official/research source
            if item.source_bias not in [SourceBias.OFFICIAL, SourceBias.RESEARCH]:
                return True
        
        return False
    
    # ==================== HELPER METHODS ====================
    
    @staticmethod
    def _extract_keywords(text: str, section: str = "focus") -> List[str]:
        """
        Extract keywords from goals or current_state.
        
        Looks for sections like:
        - "focus:" or "current_focus:" for goal keywords
        - "avoid:" for distraction keywords
        """
        if not text:
            return []
        
        # Simple extraction: look for section, get next few lines
        pattern = rf"{section}[:\s]+(.*?)(?:^[a-z_]+:|$)"
        matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE | re.DOTALL)
        
        if not matches:
            return []
        
        # Split into lines and extract words
        lines = matches[0].strip().split("\n")
        keywords = []
        
        for line in lines:
            # Remove bullets, dashes, etc.
            line = re.sub(r"^[\s\-\*]+", "", line).strip()
            if line and len(line) > 2:
                # Extract main word or phrase
                words = line.split()[:3]  # Take first few words
                keywords.append(" ".join(words).lower())
        
        return keywords

    def _parse_decision_deadlines(self, current_state: str) -> List[Dict[str, str]]:
        """Parse decision_deadlines from current_state YAML or markdown-like text."""
        if not current_state:
            return []

        if yaml is not None:
            try:
                payload = yaml.safe_load(current_state) or {}
                deadlines = payload.get("decision_deadlines", [])
                parsed = []
                for entry in deadlines:
                    date = str((entry or {}).get("date", "")).strip()
                    description = str((entry or {}).get("description", "")).strip()
                    if date:
                        parsed.append({"date": date, "description": description})
                if parsed:
                    return parsed
            except Exception:
                pass

        # Fallback parser for markdown-like lists
        matches = re.findall(r"date:\s*\"?(20\d{2}-\d{2}-\d{2})\"?.*?description:\s*\"?([^\n\"]+)\"?", current_state, re.IGNORECASE | re.DOTALL)
        return [{"date": m[0], "description": m[1].strip()} for m in matches]

    def _match_deadline_from_current_state(self, item: ContentItem) -> Optional[datetime]:
        text = f"{item.title} {item.content}".lower()
        for entry in self._decision_deadlines:
            desc = (entry.get("description") or "").strip().lower()
            date_str = (entry.get("date") or "").strip()
            if not date_str:
                continue

            if not desc:
                # If no description, still allow date-only urgency cue if item mentions deadline terms.
                if "deadline" not in text and "result" not in text and "start date" not in text:
                    continue
            else:
                desc_tokens = [tok for tok in re.split(r"\W+", desc) if len(tok) > 3]
                if not any(tok in text for tok in desc_tokens):
                    continue

            try:
                return datetime.fromisoformat(date_str)
            except ValueError:
                continue

        return None

    def _repetition_key(self, item: ContentItem) -> str:
        base = item.url.strip().lower() if item.url else " ".join(item.title.lower().split())
        return base[:120]

    def _build_repetition_scores(self, items: List[ContentItem]) -> Dict[str, float]:
        """Estimate repeated_across_sources by distinct source mentions per similar item."""
        source_sets: Dict[str, set] = {}
        for item in items:
            key = self._repetition_key(item)
            source_sets.setdefault(key, set()).add((item.author or item.source.value).lower())

        scores: Dict[str, float] = {}
        for key, sources in source_sets.items():
            # 1 source -> 0.0, 2 -> 0.5, 3+ -> 1.0
            count = len(sources)
            if count <= 1:
                scores[key] = 0.0
            elif count == 2:
                scores[key] = 0.5
            else:
                scores[key] = 1.0
        return scores
    
    @staticmethod
    def _contains_date(text: str) -> bool:
        """Check if text contains date/deadline patterns."""
        date_patterns = [
            r"\d{1,2}/\d{1,2}/\d{2,4}",  # MM/DD/YYYY
            r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b",
            r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b",
            r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
            r"\b(deadline|due|by|until|before)\b",
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in date_patterns)
    
    @staticmethod
    def _contains_numbers(text: str) -> bool:
        """Check if text contains numbers/metrics."""
        return bool(re.search(r"\$?\d+[\d.,]*%?", text))
    
    def _generate_reasoning(self, score: float, relevance: float, actionability: float,
                           deadline_urgency: float, novelty: float, source_quality: float,
                           repeated: float, personal_fit: float, distraction: float,
                           weak_evidence: float) -> str:
        """Generate human-readable reasoning for the score."""
        components = []
        
        if relevance > 0.7:
            components.append("relevant to goals")
        if actionability > 0.7:
            components.append("highly actionable")
        if deadline_urgency > 0.8:
            components.append("urgent deadline")
        if novelty > 0.7:
            components.append("recent/novel")
        if source_quality > 0.8:
            components.append("high-quality source")
        if repeated > 0.5:
            components.append("repeated across sources")
        if personal_fit > 0.6:
            components.append("fits personal context")
        if distraction > 0.5:
            components.append("potential distraction")
        if weak_evidence > 0.5:
            components.append("weak evidence")
        
        if not components:
            components.append("neutral signal")
        
        return f"Score {score:.1f}/10: {', '.join(components)}"
