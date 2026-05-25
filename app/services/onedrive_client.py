"""OneDrive integration for cloud deployment."""

import os
from typing import List, Optional
import logging

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
        self.tenant_id = os.getenv("AZURE_TENANT_ID", "")
        
        # Flag: is OneDrive integration enabled?
        self.enabled = all([self.client_id, self.client_secret, self.tenant_id])
        
        if self.enabled:
            self._init_graph_client()
    
    def _init_graph_client(self):
        """Initialize Microsoft Graph API client."""
        try:
            from azure.identity import ClientSecretCredential
            from azure.storage.filedatalake import DataLakeServiceClient
            
            self.credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            logger.info("✓ OneDrive client initialized successfully")
        except ImportError:
            logger.warning("⚠ azure-identity not installed. Install with: pip install azure-identity azure-storage-file-datalake")
            self.enabled = False
        except Exception as e:
            logger.error(f"✗ Failed to initialize OneDrive: {e}")
            self.enabled = False
    
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
            
            # Get access token
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            token_data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "https://graph.microsoft.com/.default"
            }
            
            token_response = requests.post(token_url, data=token_data)
            access_token = token_response.json()["access_token"]
            
            # Get file from OneDrive using Microsoft Graph API
            # First, find the file
            search_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{file_path}"
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
            
            # Get access token
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            token_data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "https://graph.microsoft.com/.default"
            }
            
            token_response = requests.post(token_url, data=token_data)
            access_token = token_response.json()["access_token"]
            
            # List files
            list_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{folder_path}:/children"
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
            
            # Get access token
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            token_data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "https://graph.microsoft.com/.default"
            }
            
            token_response = requests.post(token_url, data=token_data)
            if token_response.status_code != 200:
                logger.error(f"✗ Failed to get access token: {token_response.status_code}")
                return False
            
            access_token = token_response.json()["access_token"]
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Upload file to OneDrive
            # Path format: /drive/root:/path/to/file:/content
            upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{file_path}:/content"
            
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
