"""Agent adapters."""

from src.agents.summary_agent import SummaryAgent
from src.agents.signal_agent import SignalAgent
from src.agents.opportunity_agent import OpportunityAgent
from src.agents.reflection_agent import ReflectionAgent
from src.agents.claim_checker_agent import ClaimCheckerAgent

__all__ = [
    "SummaryAgent",
    "SignalAgent",
    "OpportunityAgent",
    "ReflectionAgent",
    "ClaimCheckerAgent",
]
