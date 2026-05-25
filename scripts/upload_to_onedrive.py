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
            content = f.read()
        
        # Upload to OneDrive
        onedrive_path = f"/DailyInsights/{today}.json"
        print(f"📤 Uploading to: {onedrive_path}")
        
        success = client.write_file(onedrive_path, content)
        
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
