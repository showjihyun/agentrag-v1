"""
AWS S3 Integration Service

Supports S3 operations: upload, download, list, delete.
"""

import logging
from typing import Dict, Any, List, Optional, BinaryIO
from datetime import datetime
import io

logger = logging.getLogger(__name__)


class S3Service:
    """Service for AWS S3 operations."""
    
    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
        endpoint_url: Optional[str] = None,
    ):
        """
        Initialize S3 service.
        
        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region_name: AWS region
            endpoint_url: Custom endpoint URL (for S3-compatible services)
        """
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self.endpoint_url = endpoint_url
        
        self._client = None
    
    def _get_client(self):
        """Get or create boto3 S3 client."""
        if self._client is None:
            try:
                import boto3
                
                self._client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.region_name,
                    endpoint_url=self.endpoint_url,
                )
            except ImportError:
                raise ImportError("boto3 is required for S3 operations. Install with: pip install boto3")
        
        return self._client
    
    async def upload_file(
        self,
        bucket: str,
        key: str,
        file_content: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Upload a file to S3.
        
        Args:
            bucket: S3 bucket name
            key: Object key (file path in bucket)
            file_content: File content as bytes
            content_type: Content type (MIME type)
            metadata: Custom metadata
            
        Returns:
            Upload result
        """
        try:
            client = self._get_client()
            
            # Prepare upload parameters
            upload_params = {
                'Bucket': bucket,
                'Key': key,
                'Body': file_content,
            }
            
            if content_type:
                upload_params['ContentType'] = content_type
            
            if metadata:
                upload_params['Metadata'] = metadata
            
            # Upload file
            response = client.put_object(**upload_params)
            
            logger.info(f"Uploaded file to s3://{bucket}/{key}")
            
            return {
                "success": True,
                "action": "upload",
                "bucket": bucket,
                "key": key,
                "etag": response.get('ETag', '').strip('"'),
                "version_id": response.get('VersionId'),
                "size": len(file_content),
            }
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}", exc_info=True)
            return {
                "success": False,
                "action": "upload",
                "error": str(e),
                "bucket": bucket,
                "key": key,
            }
    
    async def download_file(
        self,
        bucket: str,
        key: str,
    ) -> Dict[str, Any]:
        """
        Download a file from S3.
        
        Args:
            bucket: S3 bucket name
            key: Object key
            
        Returns:
            Download result with file content
        """
        try:
            client = self._get_client()
            
            # Download file
            response = client.get_object(Bucket=bucket, Key=key)
            
            # Read content
            content = response['Body'].read()
            
            logger.info(f"Downloaded file from s3://{bucket}/{key}")
            
            return {
                "success": True,
                "action": "download",
                "bucket": bucket,
                "key": key,
                "content": content,
                "content_type": response.get('ContentType'),
                "size": response.get('ContentLength'),
                "last_modified": response.get('LastModified').isoformat() if response.get('LastModified') else None,
                "metadata": response.get('Metadata', {}),
            }
            
        except Exception as e:
            logger.error(f"S3 download failed: {e}", exc_info=True)
            return {
                "success": False,
                "action": "download",
                "error": str(e),
                "bucket": bucket,
                "key": key,
            }
    
    async def list_objects(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
    ) -> Dict[str, Any]:
        """
        List objects in S3 bucket.
        
        Args:
            bucket: S3 bucket name
            prefix: Filter by prefix
            max_keys: Maximum number of keys to return
            
        Returns:
            List of objects
        """
        try:
            client = self._get_client()
            
            # List objects
            params = {
                'Bucket': bucket,
                'MaxKeys': max_keys,
            }
            
            if prefix:
                params['Prefix'] = prefix
            
            response = client.list_objects_v2(**params)
            
            # Extract object information
            objects = []
            for obj in response.get('Contents', []):
                objects.append({
                    "key": obj['Key'],
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'].isoformat(),
                    "etag": obj.get('ETag', '').strip('"'),
                    "storage_class": obj.get('StorageClass'),
                })
            
            logger.info(f"Listed {len(objects)} objects from s3://{bucket}")
            
            return {
                "success": True,
                "action": "list",
                "bucket": bucket,
                "prefix": prefix,
                "objects": objects,
                "count": len(objects),
                "is_truncated": response.get('IsTruncated', False),
            }
            
        except Exception as e:
            logger.error(f"S3 list failed: {e}", exc_info=True)
            return {
                "success": False,
                "action": "list",
                "error": str(e),
                "bucket": bucket,
            }
    
    async def delete_object(
        self,
        bucket: str,
        key: str,
    ) -> Dict[str, Any]:
        """
        Delete an object from S3.
        
        Args:
            bucket: S3 bucket name
            key: Object key
            
        Returns:
            Delete result
        """
        try:
            client = self._get_client()
            
            # Delete object
            response = client.delete_object(Bucket=bucket, Key=key)
            
            logger.info(f"Deleted object s3://{bucket}/{key}")
            
            return {
                "success": True,
                "action": "delete",
                "bucket": bucket,
                "key": key,
                "delete_marker": response.get('DeleteMarker', False),
                "version_id": response.get('VersionId'),
            }
            
        except Exception as e:
            logger.error(f"S3 delete failed: {e}", exc_info=True)
            return {
                "success": False,
                "action": "delete",
                "error": str(e),
                "bucket": bucket,
                "key": key,
            }
    
    async def get_presigned_url(
        self,
        bucket: str,
        key: str,
        expiration: int = 3600,
        operation: str = "get_object",
    ) -> Dict[str, Any]:
        """
        Generate a presigned URL for S3 object.
        
        Args:
            bucket: S3 bucket name
            key: Object key
            expiration: URL expiration time in seconds
            operation: Operation type (get_object, put_object)
            
        Returns:
            Presigned URL
        """
        try:
            client = self._get_client()
            
            # Generate presigned URL
            url = client.generate_presigned_url(
                operation,
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned URL for s3://{bucket}/{key}")
            
            return {
                "success": True,
                "action": "presigned_url",
                "bucket": bucket,
                "key": key,
                "url": url,
                "expiration": expiration,
                "operation": operation,
            }
            
        except Exception as e:
            logger.error(f"Presigned URL generation failed: {e}", exc_info=True)
            return {
                "success": False,
                "action": "presigned_url",
                "error": str(e),
                "bucket": bucket,
                "key": key,
            }
    
    async def copy_object(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
    ) -> Dict[str, Any]:
        """
        Copy an object within S3.
        
        Args:
            source_bucket: Source bucket name
            source_key: Source object key
            dest_bucket: Destination bucket name
            dest_key: Destination object key
            
        Returns:
            Copy result
        """
        try:
            client = self._get_client()
            
            # Copy object
            copy_source = {'Bucket': source_bucket, 'Key': source_key}
            response = client.copy_object(
                CopySource=copy_source,
                Bucket=dest_bucket,
                Key=dest_key
            )
            
            logger.info(f"Copied s3://{source_bucket}/{source_key} to s3://{dest_bucket}/{dest_key}")
            
            return {
                "success": True,
                "action": "copy",
                "source_bucket": source_bucket,
                "source_key": source_key,
                "dest_bucket": dest_bucket,
                "dest_key": dest_key,
                "etag": response.get('CopyObjectResult', {}).get('ETag', '').strip('"'),
            }
            
        except Exception as e:
            logger.error(f"S3 copy failed: {e}", exc_info=True)
            return {
                "success": False,
                "action": "copy",
                "error": str(e),
                "source_bucket": source_bucket,
                "source_key": source_key,
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test S3 connection.
        
        Returns:
            Connection test result
        """
        try:
            client = self._get_client()
            
            # List buckets to test connection
            response = client.list_buckets()
            
            buckets = [bucket['Name'] for bucket in response.get('Buckets', [])]
            
            return {
                "success": True,
                "message": "Successfully connected to S3",
                "buckets": buckets,
                "bucket_count": len(buckets),
            }
            
        except Exception as e:
            logger.error(f"S3 connection test failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }
