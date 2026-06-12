"""
Feedback Store for Personal Signal OS.

Stores user feedback in JSONL format for future scoring refinement.

Feedback ratings:
- "+" : Useful signal
- "-" : Not useful / noise
- "?" : Maybe useful later
- "!" : Very important
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from app.models import Feedback


class FeedbackStore:
    """Store and retrieve feedback on items."""
    
    def __init__(self, feedback_file: Path = Path("data/feedback.jsonl")):
        """
        Initialize feedback store.
        
        Args:
            feedback_file: Path to JSONL feedback file
        """
        self.feedback_file = Path(feedback_file)
        self.feedback_file.parent.mkdir(parents=True, exist_ok=True)
    
    def save_feedback(self, feedback: Feedback) -> bool:
        """
        Save feedback entry to JSONL file.
        
        Returns:
            True if saved successfully
        """
        try:
            with open(self.feedback_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "date": feedback.date,
                    "item_id": feedback.item_id,
                    "rating": feedback.rating,
                    "note": feedback.note,
                    "timestamp": datetime.now().isoformat(),
                }, ensure_ascii=False) + "\n")
            
            return True
        
        except Exception as e:
            print(f"Error saving feedback: {e}")
            return False
    
    def get_feedback_for_item(self, item_id: str) -> List[Feedback]:
        """Get all feedback for a specific item."""
        if not self.feedback_file.exists():
            return []
        
        feedback_list = []
        
        try:
            with open(self.feedback_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    data = json.loads(line)
                    if data.get("item_id") == item_id:
                        feedback_list.append(Feedback(
                            date=data.get("date"),
                            item_id=data.get("item_id"),
                            rating=data.get("rating"),
                            note=data.get("note"),
                        ))
        
        except Exception as e:
            print(f"Error reading feedback: {e}")
        
        return feedback_list
    
    def get_feedback_stats(self) -> dict:
        """Get overall feedback statistics."""
        if not self.feedback_file.exists():
            return {"total": 0, "useful": 0, "noise": 0, "important": 0}
        
        stats = {"total": 0, "useful": 0, "noise": 0, "maybe": 0, "important": 0}
        
        try:
            with open(self.feedback_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    data = json.loads(line)
                    rating = data.get("rating")
                    
                    stats["total"] += 1
                    if rating == "+":
                        stats["useful"] += 1
                    elif rating == "-":
                        stats["noise"] += 1
                    elif rating == "?":
                        stats["maybe"] += 1
                    elif rating == "!":
                        stats["important"] += 1
        
        except Exception as e:
            print(f"Error reading feedback stats: {e}")
        
        return stats
