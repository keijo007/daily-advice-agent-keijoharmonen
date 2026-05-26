"""OneDrive integration for cloud deployment."""

import os
from typing import List, Optional
import logging
import base64
from urllib.parse import quote

logger = logging.getLogger(__name__)


class OneDriveClient:
    """
    Read files from OneDrive using Microsoft Graph API.
    
    This enables the cloud deployment to:
    1. Read goals from your OneDrive folder
    2. Read diary entries from your OneDrive diary
    3. Work without local machine running
    """
    
    def __init__(self):
        """Initialize OneDrive connection."""
        self.client_id = os.getenv("AZURE_CLIENT_ID", "")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET", "")
        self.refresh_token = os.getenv("ONEDRIVE_REFRESH_TOKEN", "").strip()
        self.refresh_scope = os.getenv("ONEDRIVE_REFRESH_SCOPE", "").strip()
        self.tenant_id = os.getenv("ONEDRIVE_TENANT_ID", "").strip()
        if not self.tenant_id:
            self.tenant_id = os.getenv("AZURE_TENANT_ID", "").strip()
        if not self.tenant_id and self.refresh_token:
            self.tenant_id = "consumers"
        
        # Flag: is OneDrive integration enabled?
        self.enabled = bool(self.client_id and self.tenant_id and (self.client_secret or self.refresh_token))
        
        if self.enabled:
            self._init_graph_client()
        elif self.tenant_id == "consumers" and not self.refresh_token:
            logger.warning("⚠ OneDrive personal account requires ONEDRIVE_REFRESH_TOKEN")
    
    def _init_graph_client(self):
        """Initialize OneDrive client (requests-based)."""
        logger.info("✓ OneDrive client ready (requests-based)")

    def _drive_base_url(self) -> str:
        """Return Graph base URL for the target drive."""
        drive_id = os.getenv("ONEDRIVE_DRIVE_ID", "").strip()
        user_id = os.getenv("ONEDRIVE_USER_ID", "").strip()

        if drive_id:
            return f"https://graph.microsoft.com/v1.0/drives/{drive_id}"
        if user_id:
            return f"https://graph.microsoft.com/v1.0/users/{user_id}/drive"
        return "https://graph.microsoft.com/v1.0/me/drive"

    @staticmethod
    def _encode_path(path: str) -> str:
        """URL-encode OneDrive path segments while preserving slashes."""
        return quote(path.strip("/"), safe="/")

    @staticmethod
    def _share_id_from_url(share_url: str) -> str:
        """Convert a share URL into Graph shareId (u! base64url)."""
        raw = share_url.encode("utf-8")
        b64 = base64.b64encode(raw).decode("utf-8")
        b64url = b64.replace("+", "-").replace("/", "_").replace("=", "")
        return f"u!{b64url}"

    def _get_shared_item(self, share_url: str) -> Optional[dict]:
        """Get drive item metadata for a share URL."""
        access_token = self._get_access_token()
        if not access_token:
            return None

        try:
            import requests

            share_id = self._share_id_from_url(share_url)
            url = f"https://graph.microsoft.com/v1.0/shares/{share_id}/driveItem"
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                return response.json()

            logger.error(f"✗ Failed to resolve share link: {response.status_code}")
            logger.debug(f"Response: {response.text}")
            return None
        except Exception as e:
            logger.error(f"✗ Error resolving share link: {e}")
            return None

    def read_shared_file(self, share_url: str) -> Optional[str]:
        """Read a file from a share URL."""
        if not self.enabled:
            return None

        item = self._get_shared_item(share_url)
        if not item:
            return None

        try:
            import requests

            drive_id = item.get("parentReference", {}).get("driveId")
            item_id = item.get("id")
            if not drive_id or not item_id:
                logger.error("✗ Missing driveId or itemId for shared file")
                return None

            access_token = self._get_access_token()
            if not access_token:
                return None

            url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/content"
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.text

            logger.error(f"✗ Failed to read shared file: {response.status_code}")
            logger.debug(f"Response: {response.text}")
            return None
        except Exception as e:
            logger.error(f"✗ Error reading shared file: {e}")
            return None

    def upload_to_shared_folder(self, folder_share_url: str, filename: str, content: str) -> bool:
        """Upload a file into a shared folder."""
        if not self.enabled:
            return False

        item = self._get_shared_item(folder_share_url)
        if not item:
            return False

        try:
            import requests

            drive_id = item.get("parentReference", {}).get("driveId")
            folder_id = item.get("id")
            if not drive_id or not folder_id:
                logger.error("✗ Missing driveId or folderId for shared folder")
                return False

            access_token = self._get_access_token()
            if not access_token:
                return False

            content_type = "text/plain; charset=utf-8" if filename.endswith(".txt") else "application/json"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": content_type,
            }

            upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{folder_id}:/{quote(filename)}:/content"
            response = requests.put(upload_url, headers=headers, data=content.encode("utf-8"))

            if response.status_code in [200, 201]:
                logger.info(f"✓ Uploaded file to shared folder: {filename}")
                return True

            logger.error(f"✗ Failed to upload to shared folder: {response.status_code}")
            logger.debug(f"Response: {response.text}")
            return False
        except Exception as e:
            logger.error(f"✗ Error uploading to shared folder: {e}")
            return False

    def _get_access_token(self) -> Optional[str]:
        """Get Microsoft Graph access token."""
        if not self.enabled:
            return None

        try:
            import requests

            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            if self.refresh_token:
                token_data = {
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "refresh_token": self.refresh_token,
                }
                if self.client_secret and self.tenant_id != "consumers":
                    token_data["client_secret"] = self.client_secret
                if self.refresh_scope:
                    token_data["scope"] = self.refresh_scope
            else:
                token_data = {
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "https://graph.microsoft.com/.default",
                }

            token_response = requests.post(token_url, data=token_data)
            if token_response.status_code != 200:
                logger.error(f"✗ Failed to get access token: {token_response.status_code}")
                logger.error(f"✗ Token error response: {token_response.text}")
                return None

            return token_response.json().get("access_token")

        except Exception as e:
            logger.error(f"✗ Error getting access token: {e}")
            return None

    def ensure_folder_path(self, folder_path: str) -> bool:
        """Ensure a nested folder path exists in OneDrive."""
        if not self.enabled:
            return False

        try:
            import requests

            access_token = self._get_access_token()
            if not access_token:
                return False

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            parts = [p for p in folder_path.strip("/").split("/") if p]
            current_path = ""

            for part in parts:
                ok = self._create_folder(part, current_path, headers)
                if not ok:
                    return False
                current_path = f"{current_path}/{part}" if current_path else part

            return True
        except Exception as e:
            logger.error(f"✗ Error ensuring folder path: {e}")
            return False

    def _create_folder(self, name: str, parent_path: str, headers: dict) -> bool:
        """Create a folder under the given parent path (idempotent)."""
        import requests

        base_url = self._drive_base_url()
        if parent_path:
            encoded_parent = self._encode_path(parent_path)
            url = f"{base_url}/root:/{encoded_parent}:/children"
        else:
            url = f"{base_url}/root/children"

        body = {
            "name": name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail",
        }

        response = requests.post(url, headers=headers, json=body)

        if response.status_code in [200, 201]:
            return True
        if response.status_code == 409:
            return True

        logger.error(f"✗ Failed to create folder '{name}': {response.status_code}")
        logger.debug(f"Response: {response.text}")
        return False
    
    def read_file(self, file_path: str) -> Optional[str]:
        """
        Read file from OneDrive.
        
        Args:
            file_path: Path like "/Documents/goals.txt" or "goals.txt"
        
        Returns:
            File contents as string, or None if error
        
        Example:
            content = client.read_file("/Documents/goals.txt")
        """
        if not self.enabled:
            logger.warning("OneDrive client not enabled - check AZURE_CLIENT_ID, etc.")
            return None
        
        try:
            import requests

            access_token = self._get_access_token()
            if not access_token:
                return None
            
            # Get file from OneDrive using Microsoft Graph API
            # First, find the file
            base_url = self._drive_base_url()
            encoded_path = self._encode_path(file_path)
            search_url = f"{base_url}/root:/{encoded_path}"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            response = requests.get(search_url, headers=headers)
            
            if response.status_code == 200:
                file_id = response.json()["id"]
                
                # Get file contents
                content_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content"
                content_response = requests.get(content_url, headers=headers)
                
                if content_response.status_code == 200:
                    logger.info(f"✓ Read file from OneDrive: {file_path}")
                    return content_response.text
                else:
                    logger.error(f"✗ Failed to read file contents: {content_response.status_code}")
                    return None
            else:
                logger.error(f"✗ File not found on OneDrive: {file_path}")
                logger.debug(f"Response: {response.json()}")
                return None
            
        except ImportError:
            logger.error("requests library not installed")
            return None
        except KeyError as e:
            logger.error(f"✗ Invalid token response: {e}")
            return None
        except Exception as e:
            logger.error(f"✗ Error reading from OneDrive: {e}")
            return None
    
    def list_files(self, folder_path: str = "/Documents") -> Optional[List[str]]:
        """
        List files in OneDrive folder.
        
        Args:
            folder_path: Folder path like "/Documents" or "/Diary"
        
        Returns:
            List of file names, or None if error
        """
        if not self.enabled:
            return None
        
        try:
            import requests

            access_token = self._get_access_token()
            if not access_token:
                return None
            
            # List files
            base_url = self._drive_base_url()
            encoded_path = self._encode_path(folder_path)
            list_url = f"{base_url}/root:/{encoded_path}:/children"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            response = requests.get(list_url, headers=headers)
            
            if response.status_code == 200:
                files = [item["name"] for item in response.json()["value"]]
                logger.info(f"✓ Listed {len(files)} files from OneDrive: {folder_path}")
                return files
            else:
                logger.error(f"✗ Failed to list files: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"✗ Error listing OneDrive files: {e}")
            return None
    
    def read_diary_files(self, folder_path: str = "/Diary", limit: int = 7) -> List[str]:
        """
        Read recent diary files from OneDrive.
        
        Args:
            folder_path: Where diary files are stored (default: /Diary)
            limit: Number of recent files to read (default: 7)
        
        Returns:
            List of diary contents (one per file)
        
        Example:
            diary_entries = client.read_diary_files("/MyDiary", limit=7)
            for entry in diary_entries:
                print(entry[:100])
        """
        if not self.enabled:
            return []
        
        try:
            # List all files in diary folder
            files = self.list_files(folder_path)
            if not files:
                logger.warning(f"No diary files found in {folder_path}")
                return []
            
            # Sort by name (assuming YYYY-MM-DD format) and take recent ones
            files.sort(reverse=True)
            recent_files = files[:limit]
            
            # Read each file
            diary_entries = []
            for filename in recent_files:
                content = self.read_file(f"{folder_path}/{filename}")
                if content:
                    diary_entries.append(content)
            
            logger.info(f"✓ Read {len(diary_entries)} diary entries from OneDrive")
            return diary_entries
            
        except Exception as e:
            logger.error(f"✗ Error reading diary files: {e}")
            return []
    
    def write_file(self, file_path: str, content: str) -> bool:
        """
        Write file to OneDrive.
        
        Args:
            file_path: Path like "/DailyInsights/2026-05-25.json"
            content: File contents to write
        
        Returns:
            True if successful, False otherwise
        
        Example:
            success = client.write_file("/DailyInsights/2026-05-25.json", json_content)
        """
        if not self.enabled:
            logger.warning("OneDrive client not enabled - check AZURE_CLIENT_ID, etc.")
            return False
        
        try:
            import requests

            access_token = self._get_access_token()
            if not access_token:
                return False

            folder_path = "/".join(file_path.strip("/").split("/")[:-1])
            if folder_path:
                if not self.ensure_folder_path(f"/{folder_path}"):
                    return False

            content_type = "application/json"
            if file_path.endswith(".txt"):
                content_type = "text/plain; charset=utf-8"
            if file_path.endswith(".md"):
                content_type = "text/markdown; charset=utf-8"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": content_type,
            }
            
            # Upload file to OneDrive
            # Path format: /drive/root:/path/to/file:/content
            base_url = self._drive_base_url()
            encoded_path = self._encode_path(file_path)
            upload_url = f"{base_url}/root:/{encoded_path}:/content"
            
            upload_response = requests.put(upload_url, headers=headers, data=content.encode('utf-8'))
            
            if upload_response.status_code in [200, 201]:
                logger.info(f"✓ Uploaded file to OneDrive: {file_path}")
                return True
            else:
                logger.error(f"✗ Failed to upload file: {upload_response.status_code}")
                logger.debug(f"Response: {upload_response.text}")
                return False
        
        except ImportError:
            logger.error("requests library not installed")
            return False
        except KeyError as e:
            logger.error(f"✗ Invalid token response: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Error writing to OneDrive: {e}")
            return False


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Initialize
    client = OneDriveClient()
    
    # Example 1: Read goals
    print("Reading goals from OneDrive...")
    goals = client.read_file("/Documents/goals.txt")
    if goals:
        print(f"Goals:\n{goals[:200]}...")
    
    # Example 2: List diary files
    print("\nListing diary files...")
    diary_files = client.list_files("/Diary")
    if diary_files:
        print(f"Found {len(diary_files)} diary files: {diary_files}")
    
    # Example 3: Read recent diary entries
    print("\nReading recent diary entries...")
    entries = client.read_diary_files("/Diary", limit=7)
    print(f"Read {len(entries)} entries")
    for i, entry in enumerate(entries, 1):
        print(f"Entry {i}: {entry[:100]}...")
