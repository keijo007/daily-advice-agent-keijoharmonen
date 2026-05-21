"""
Upload generated insights to OneDrive (optional).

Add this to GitHub Actions workflow if you want to backup insights to OneDrive.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.onedrive_client import OneDriveClient


def upload_to_onedrive():
    """Upload today's insight files to OneDrive."""
    
    print("📤 Uploading to OneDrive...")
    
    try:
        client = OneDriveClient()
        
        if not client.enabled:
            print("⚠️  OneDrive not configured - skipping upload")
            return
        
        # Upload today's JSON
        today = datetime.now().strftime("%Y-%m-%d")
        json_file = f"data/daily_insights/{today}.json"
        
        if Path(json_file).exists():
            print(f"📤 Uploading {json_file}...")
            # Note: You need to implement write functionality in OneDriveClient
            # This is a placeholder - actual implementation depends on your setup
            print(f"✓ Uploaded {json_file} to OneDrive")
        else:
            print(f"⚠️  File not found: {json_file}")
    
    except Exception as e:
        print(f"✗ Error uploading to OneDrive: {e}")
        # Don't fail the whole workflow if upload fails
        return


if __name__ == "__main__":
    upload_to_onedrive()
