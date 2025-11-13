"""
Google Drive Integration Service

Provides methods to interact with Google Drive API.
"""

import logging
from typing import Dict, Any, Optional, List
import io
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GoogleDriveService:
    """Service for Google Drive API integration."""
    
    def __init__(self, credentials_dict: Dict[str, Any]):
        """
        Initialize Google Drive service.
        
        Args:
            credentials_dict: OAuth2 credentials dictionary
        """
        try:
            self.credentials = Credentials.from_authorized_user_info(credentials_dict)
            self.service = build('drive', 'v3', credentials=self.credentials)
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {e}")
            raise
    
    async def upload_file(
        self,
        file_name: str,
        content: str,
        mime_type: str = "text/plain",
        folder_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload a file to Google Drive.
        
        Args:
            file_name: Name of the file
            content: File content as string
            mime_type: MIME type of the file
            folder_id: Optional parent folder ID
            
        Returns:
            File metadata including file ID
        """
        try:
            file_metadata = {'name': file_name}
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Create file in memory
            fh = io.BytesIO(content.encode('utf-8'))
            media = MediaIoBaseUpload(fh, mimetype=mime_type, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, mimeType, createdTime, webViewLink'
            ).execute()
            
            logger.info(f"File uploaded to Google Drive: {file.get('id')}")
            
            return {
                "success": True,
                "file_id": file.get('id'),
                "file_name": file.get('name'),
                "mime_type": file.get('mimeType'),
                "created_time": file.get('createdTime'),
                "web_view_link": file.get('webViewLink'),
            }
            
        except HttpError as e:
            logger.error(f"Google Drive API error: {e}")
            raise Exception(f"Google Drive API error: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise
    
    async def download_file(self, file_id: str) -> Dict[str, Any]:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            File content and metadata
        """
        try:
            # Get file metadata
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='name, mimeType'
            ).execute()
            
            # Download file content
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            content = fh.getvalue().decode('utf-8')
            
            logger.info(f"File downloaded from Google Drive: {file_id}")
            
            return {
                "success": True,
                "file_id": file_id,
                "file_name": file_metadata.get('name'),
                "mime_type": file_metadata.get('mimeType'),
                "content": content,
            }
            
        except HttpError as e:
            logger.error(f"Google Drive API error: {e}")
            raise Exception(f"Google Drive API error: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            raise
    
    async def list_files(
        self,
        folder_id: Optional[str] = None,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """
        List files in Google Drive.
        
        Args:
            folder_id: Optional folder ID to list files from
            page_size: Number of files to return
            
        Returns:
            List of files
        """
        try:
            query = "trashed = false"
            
            if folder_id:
                query += f" and '{folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                pageSize=page_size,
                fields="files(id, name, mimeType, createdTime, modifiedTime, size, webViewLink)"
            ).execute()
            
            files = results.get('files', [])
            
            logger.info(f"Listed {len(files)} files from Google Drive")
            
            return {
                "success": True,
                "count": len(files),
                "files": files,
            }
            
        except HttpError as e:
            logger.error(f"Google Drive API error: {e}")
            raise Exception(f"Google Drive API error: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            raise
    
    async def delete_file(self, file_id: str) -> Dict[str, Any]:
        """
        Delete a file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            Success status
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            
            logger.info(f"File deleted from Google Drive: {file_id}")
            
            return {
                "success": True,
                "file_id": file_id,
            }
            
        except HttpError as e:
            logger.error(f"Google Drive API error: {e}")
            raise Exception(f"Google Drive API error: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            raise
    
    async def share_file(
        self,
        file_id: str,
        email: str,
        role: str = "reader",
    ) -> Dict[str, Any]:
        """
        Share a file with a user.
        
        Args:
            file_id: Google Drive file ID
            email: Email address to share with
            role: Permission role ('reader', 'writer', 'commenter')
            
        Returns:
            Permission ID
        """
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email,
            }
            
            result = self.service.permissions().create(
                fileId=file_id,
                body=permission,
                fields='id',
                sendNotificationEmail=True,
            ).execute()
            
            logger.info(f"File shared with {email}: {file_id}")
            
            return {
                "success": True,
                "file_id": file_id,
                "permission_id": result.get('id'),
                "email": email,
                "role": role,
            }
            
        except HttpError as e:
            logger.error(f"Google Drive API error: {e}")
            raise Exception(f"Google Drive API error: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to share file: {e}")
            raise
