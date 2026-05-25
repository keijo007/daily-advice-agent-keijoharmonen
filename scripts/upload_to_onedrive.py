"""
Upload generated insights to OneDrive (optional).

This script uploads today's generated insight JSON file to OneDrive.
Requires Azure credentials in environment variables.

FOLDER STRUCTURE IN ONEDRIVE:
  /DailyInsights/
    2026-05-25.json
    2026-05-26.json
    ...
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.onedrive_client import OneDriveClient
from app.config import config


def build_text_summary(data: dict) -> str:
    """Build a readable text summary from the daily insight JSON."""
    lines = []
    lines.append(f"Date: {data.get('date', '')}")
    lines.append("")
    lines.append("Main insight:")
    lines.append(data.get("main_insight", ""))
    lines.append("")
    lines.append("Practical tip:")
    lines.append(data.get("practical_tip", ""))
    lines.append("")
    lines.append("One-day action:")
    lines.append(data.get("one_day_action", ""))
    lines.append("")
    lines.append("Source summary:")
    lines.append(data.get("source_summary", ""))
    lines.append("")
    lines.append("Self reflection:")
    lines.append(data.get("self_reflection", ""))
    lines.append("")
    lines.append("Thinking biases detected:")
    biases = data.get("thinking_biases_detected", [])
    if isinstance(biases, list):
        lines.extend([f"- {b}" for b in biases])
    else:
        lines.append(str(biases))
    lines.append("")
    lines.append("Uncertainties / warnings:")
    warnings = data.get("uncertainties", [])
    if isinstance(warnings, list):
        lines.extend([f"- {w}" for w in warnings])
    else:
        lines.append(str(warnings))
    lines.append("")
    lines.append("Sources used:")
    sources = data.get("sources_used", [])
    if isinstance(sources, list):
        lines.extend([f"- {s}" for s in sources])
    else:
        lines.append(str(sources))

    return "\n".join(lines).strip() + "\n"


def upload_to_onedrive():
    """Upload today's insight files to OneDrive."""
    
    print("\n📤 UPLOADING TO ONEDRIVE")
    print("-" * 40)
    
    try:
        client = OneDriveClient()
        
        if not client.enabled:
            print("⚠️  OneDrive not configured - skipping upload")
            print("   Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID")
            return
        
        # Get today's insight
        today = datetime.now().strftime("%Y-%m-%d")
        json_file = Path(f"data/daily_insights/{today}.json")
        
        if not json_file.exists():
            print(f"⚠️  File not found: {json_file}")
            return
        
        # Read the JSON file
        print(f"📂 Reading: {json_file}")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        summary_text = build_text_summary(data)

        # Upload to OneDrive as text
        if config.ONEDRIVE_DAILY_INSIGHTS_SHARE_URL:
            print("📤 Uploading to shared folder link")
            success = client.upload_to_shared_folder(
                config.ONEDRIVE_DAILY_INSIGHTS_SHARE_URL,
                f"{today}.txt",
                summary_text,
            )
        else:
            base_path = config.ONEDRIVE_DAILY_INSIGHTS_PATH
            onedrive_path = f"{base_path}/{today}.txt"
            print(f"📤 Uploading to: {onedrive_path}")

            success = client.write_file(onedrive_path, summary_text)
        
        if success:
            print(f"✓ Successfully uploaded to OneDrive")
            print(f"   Location: /DailyInsights/{today}.json\n")
        else:
            print(f"✗ Failed to upload to OneDrive\n")
            # Don't fail the workflow - continue gracefully
    
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON format: {e}")
    except Exception as e:
        print(f"✗ Error uploading to OneDrive: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    upload_to_onedrive()
