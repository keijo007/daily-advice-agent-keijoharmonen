"""
Markdown Renderer for Personal Signal OS Daily Brief.

Renders DailyBrief to readable Markdown format.

Output structure:
# YYYY-MM-DD

## 1. Top Signals

## 2. Opportunities

## 3. Claims to Verify

## 4. Weak Signals

## 5. Thinking Mirror

## 6. Recommended Action Today

## 7. Low Priority / Noise
"""

from app.models import DailyBrief
from datetime import datetime


class MarkdownRenderer:
    """Render DailyBrief to Markdown format."""
    
    def render(self, brief: DailyBrief) -> str:
        """
        Render DailyBrief to Markdown string.
        
        Returns:
            Markdown string ready to write to file
        """
        lines = []
        
        # Header
        lines.append(f"# {brief.date}")
        lines.append("")
        
        # Section 1: Top Signals
        lines.append("## 1. Top Signals")
        lines.append("")
        if brief.top_signals:
            for i, signal in enumerate(brief.top_signals, 1):
                lines.append(f"### {i}. {signal.title}")
                lines.append("")
                lines.append(f"**Source:** {signal.source}")
                lines.append(f"**Type:** {signal.source_type.value}")
                lines.append(f"**Score:** {signal.score:.1f}/10")
                lines.append("")
                lines.append(f"**Why it matters:** {signal.why_matters}")
                lines.append("")
                lines.append(f"**Suggested action:** {signal.suggested_action}")
                
                if signal.url:
                    lines.append(f"**Link:** [{signal.url[:50]}...]({signal.url})")
                
                if signal.topics:
                    lines.append(f"**Topics:** {', '.join(signal.topics)}")
                
                lines.append("")
        else:
            lines.append("No top signals today.")
            lines.append("")
        
        # Section 2: Opportunities
        lines.append("## 2. Opportunities")
        lines.append("")
        if brief.opportunities:
            for i, opp in enumerate(brief.opportunities, 1):
                lines.append(f"### {i}. {opp.title}")
                lines.append("")
                lines.append(f"**Type:** {opp.opportunity_type or 'Opportunity'}")
                lines.append(f"**Why relevant:** {opp.why_relevant}")
                lines.append("")
                
                if opp.deadline:
                    deadline_str = opp.deadline.strftime("%Y-%m-%d")
                    days_until = (opp.deadline - datetime.now()).days
                    lines.append(f"**Deadline:** {deadline_str} ({days_until} days)")
                    lines.append("")
                
                lines.append(f"**Next action:** {opp.next_action}")
                lines.append(f"**Source:** {opp.source}")
                
                if opp.url:
                    lines.append(f"**Link:** [{opp.url[:50]}...]({opp.url})")
                
                lines.append("")
        else:
            lines.append("No opportunities found today.")
            lines.append("")
        
        # Section 3: Claims to Verify
        lines.append("## 3. Claims to Verify")
        lines.append("")
        if brief.claims_to_verify:
            for i, claim in enumerate(brief.claims_to_verify, 1):
                lines.append(f"### {i}. {claim.claim_text[:80]}")
                lines.append("")
                lines.append(f"**Source:** {claim.source}")
                lines.append(f"**Source bias:** {claim.source_bias.value}")
                lines.append(f"**Evidence level:** {claim.evidence_level.value}")
                lines.append("")
                lines.append(f"**Possible bias:** {claim.possible_bias}")
                lines.append("")
                lines.append(f"**How to verify:** {claim.how_to_verify}")
                lines.append("")
                lines.append(f"**Recommended action:** {claim.recommended_action}")
                lines.append("")
        else:
            lines.append("No claims to verify today.")
            lines.append("")
        
        # Section 4: Weak Signals
        lines.append("## 4. Weak Signals")
        lines.append("")
        if brief.weak_signals:
            lines.append("These may not be clearly important yet but could become important if repeated:")
            lines.append("")
            for i, ws in enumerate(brief.weak_signals, 1):
                lines.append(f"**{i}. {ws.title}**")
                lines.append(f"- {ws.why_weak}")
                lines.append(f"- Source: {ws.source}")
                if ws.url:
                    lines.append(f"- Link: [{ws.url[:30]}...]({ws.url})")
                lines.append("")
        else:
            lines.append("No weak signals today.")
            lines.append("")
        
        # Section 5: Thinking Mirror
        lines.append("## 5. Thinking Mirror")
        lines.append("")
        if brief.thinking_mirror:
            tm = brief.thinking_mirror
            lines.append(f"**What you seem to be focusing on:** {tm.repeated_focus}")
            lines.append("")
            lines.append(f"**Possible blind spot:** {tm.possible_blind_spot}")
            lines.append("")
            lines.append(f"**Possible bias:** {tm.possible_bias}")
            lines.append("")
            lines.append(f"**One question for you:** {tm.one_question}")
            
            if tm.suggested_adjustment:
                lines.append("")
                lines.append(f"**Suggested adjustment:** {tm.suggested_adjustment}")
            
            lines.append("")
        else:
            lines.append("No reflection today (need more data).")
            lines.append("")
        
        # Section 6: Recommended Action Today
        lines.append("## 6. Recommended Action Today")
        lines.append("")
        lines.append(brief.recommended_action_today)
        lines.append("")
        
        # Section 7: Low Priority / Noise
        lines.append("## 7. Low Priority / Noise")
        lines.append("")
        if brief.low_priority_noise:
            lines.append("Things that appeared in inputs but likely distractions today:")
            lines.append("")
            for i, noise in enumerate(brief.low_priority_noise[:10], 1):
                lines.append(f"**{i}. {noise['title']}**")
                lines.append(f"- {noise['reason']}")
                lines.append(f"- Source: {noise['source']}")
                lines.append("")
        else:
            lines.append("No low-priority noise today.")
            lines.append("")
        
        # Footer
        lines.append("---")
        lines.append("")
        lines.append(f"**Brief generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Items collected:** {brief.collected_items_count}")
        lines.append(f"**Items scored:** {brief.scored_items_count}")
        lines.append(f"**Sources used:** {', '.join(brief.sources_used[:5])}")
        if len(brief.sources_used) > 5:
            lines.append(f"... and {len(brief.sources_used) - 5} more sources")
        lines.append("")
        
        return "\n".join(lines)
    
    def save_to_file(self, brief: DailyBrief, output_path: str) -> bool:
        """
        Render and save brief to Markdown file.
        
        Args:
            brief: DailyBrief object
            output_path: Path to output file (e.g., "outputs/daily_briefs/2026-06-10.md")
        
        Returns:
            True if saved successfully
        """
        try:
            markdown = self.render(brief)
            
            # Create directory if needed
            import os
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown)
            
            return True
        
        except Exception as e:
            print(f"Error saving brief to file: {e}")
            return False
