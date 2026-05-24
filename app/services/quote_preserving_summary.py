"""
Quote preserving summary service - summarizes while keeping important quotes.

WHY THIS FILE EXISTS:
- When summarizing content, we want to preserve the original voice
- Key insights are often best expressed in original words
- Reader Agent uses this to keep articles authentic

HOW IT WORKS:
- Analyzes content for key quotes
- Summarizes around the quotes
- Creates a compressed version that stays faithful to original

AGENT RELEVANCE:
- Reader Agent: PRIMARY USER
- Preserves tone and credibility of sources
- Avoids hallucination by quoting directly

ALGORITHM:
1. Identify important sentences (length, keyword relevance)
2. Extract as quotes
3. Summarize remaining content
4. Combine: summary + quotes

EXTENSION IDEAS:
- Sentiment-aware quote selection
- Author-specific quote extraction
- Multi-language support
"""

import re
from typing import List, Tuple
from app.models import ContentItem


def extract_key_quotes(content: str, num_quotes: int = 3) -> List[str]:
    """
    Extract key quotes from content.
    
    HEURISTICS:
    - Longer sentences (> 50 chars, < 200 chars) tend to be more meaningful
    - Sentences with keywords (research, study, found, proved) are important
    - Mix of quote lengths for variety
    
    Args:
        content: Text to extract quotes from
        num_quotes: How many quotes to find
    
    Returns:
        List of extracted quotes
    """
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', content)
    
    # Score sentences
    scored = []
    keywords = ['research', 'study', 'found', 'proved', 'discovered', 'shows', 'indicates']
    
    for sent in sentences:
        sent = sent.strip()
        
        # Skip short sentences
        if len(sent) < 50 or len(sent) > 300:
            continue
        
        # Skip if looks like metadata (URL, etc.)
        if sent.startswith("http") or sent.startswith("["):
            continue
        
        # Score based on length and keywords
        score = len(sent)  # Prefer mid-length sentences
        
        for keyword in keywords:
            if keyword.lower() in sent.lower():
                score += 10
        
        scored.append((sent, score))
    
    # Return top N quotes, sorted by score
    scored.sort(key=lambda x: x[1], reverse=True)
    quotes = [sent for sent, _ in scored[:num_quotes]]
    
    return quotes


def summarize_preserving_quotes(
    item: ContentItem,
    max_summary_length: int = 500,
    num_quotes: int = 2,
) -> str:
    """
    Summarize content while preserving key quotes.
    
    OUTPUT FORMAT:
    \"\"\"
    [Summary of content]
    
    Key quotes:
    - \"Quote 1\"
    - \"Quote 2\"
    
    Source: [item.author]
    \"\"\"
    
    Args:
        item: ContentItem to summarize
        max_summary_length: Max length for summary part
        num_quotes: How many quotes to extract
    
    Returns:
        Summary with preserved quotes
    """
    
    # For now, this returns a formatted version that shows structure
    # In a full implementation, you'd use AI to summarize
    
    # Extract quotes
    quotes = extract_key_quotes(item.content, num_quotes)
    
    # Create output
    output = f"**{item.title}**\n\n"
    output += f"{item.content[:max_summary_length]}...\n\n"
    
    if quotes:
        output += "**Key Quotes:**\n"
        for quote in quotes:
            output += f'- "{quote}"\n'
    
    output += f"\nSource: {item.author}"
    if item.url:
        output += f" [{item.url}]"
    
    return output


def create_briefing(items: List[ContentItem], max_total_length: int = 2000) -> str:
    """
    Create a briefing from multiple items.
    
    Combines summaries into one coherent briefing.
    
    Args:
        items: Items to create briefing from
        max_total_length: Total max length
    
    Returns:
        Combined briefing text
    """
    
    briefing = "## Daily Briefing\n\n"
    current_length = 0
    
    for i, item in enumerate(items, 1):
        if current_length >= max_total_length:
            briefing += f"\n... and {len(items) - i + 1} more items"
            break
        
        summary = summarize_preserving_quotes(item, max_summary_length=300, num_quotes=1)
        briefing += f"{i}. {summary}\n\n"
        current_length += len(summary)
    
    return briefing
