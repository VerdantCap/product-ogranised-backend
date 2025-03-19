import os
import uuid
import logging
import boto3
from botocore.client import Config
from pathlib import Path
from fastapi import UploadFile
from config import settings

# Set up a logger for the storage utility
logger = logging.getLogger(__name__)

def get_s3_client():
    """
    Create and return an S3 client configured to use MinIO.
    
    Returns:
        boto3.client: Configured S3 client
    """
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'  # MinIO doesn't require a specific region
        )
        return s3_client
    except Exception as e:
        logger.error(f"Failed to create S3 client: {str(e)}")
        raise e

async def get_file_size(file_path: str) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: The path to the file
        
    Returns:
        int: The size of the file in bytes
    """
    # Check if S3 storage is enabled
    if hasattr(settings, 'USE_S3_STORAGE') and settings.USE_S3_STORAGE:
        return await get_file_size_s3(file_path)
    else:
        return get_file_size_local(file_path)

async def get_file_size_s3(file_path: str) -> int:
    """
    Get the size of a file stored in S3/MinIO.
    
    Args:
        file_path: The relative path to the file in S3
        
    Returns:
        int: The size of the file in bytes
    """
    # Determine which bucket to use
    bucket_name = settings.S3_FILES_BUCKET_NAME
    
    # Get the S3 client
    s3_client = get_s3_client()
    
    try:
        # Get the file metadata
        response = s3_client.head_object(Bucket=bucket_name, Key=file_path)
        return response.get('ContentLength', 0)
    except Exception as e:
        logger.error(f"Failed to get file size from S3: {str(e)}")
        return 0

def get_file_size_local(file_path: str) -> int:
    """
    Get the size of a file stored in the local filesystem.
    
    Args:
        file_path: The relative path to the file
        
    Returns:
        int: The size of the file in bytes
    """
    full_path = os.path.join(settings.STORAGE_DIR, file_path)
    try:
        if os.path.exists(full_path):
            return os.path.getsize(full_path)
        return 0
    except Exception as e:
        logger.error(f"Failed to get file size: {str(e)}")
        return 0

def ensure_bucket_exists(bucket_name):
    """
    Ensure that the specified bucket exists, creating it if necessary.
    
    Args:
        bucket_name: Name of the bucket to check/create
    """
    s3_client = get_s3_client()
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except Exception:
        # Bucket doesn't exist, create it
        try:
            s3_client.create_bucket(Bucket=bucket_name)
            # Set bucket policy to allow public read access if needed
            s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=f'''{{
                    "Version": "2012-10-17",
                    "Statement": [
                        {{
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": ["s3:GetObject"],
                            "Resource": ["arn:aws:s3:::{bucket_name}/*"]
                        }}
                    ]
                }}'''
            )
        except Exception as e:
            logger.error(f"Failed to create bucket {bucket_name}: {str(e)}")
            raise e

async def store_file_s3(file: UploadFile, storage_path: str) -> str:
    """
    Store a file in S3/MinIO and return its relative path.
    
    Args:
        file: The uploaded file
        storage_path: The relative path where the file should be stored
            e.g. "workspaces/1/files" or "workspaces/1/items/2"
            
    Returns:
        str: The relative path to the stored file in S3
    """
    # Create a unique filename to avoid collisions
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Construct the full storage path
    s3_key = f"{storage_path}/{unique_filename}"
    
    # Determine which bucket to use
    bucket_name = settings.S3_FILES_BUCKET_NAME
    
    # Ensure the bucket exists
    ensure_bucket_exists(bucket_name)
    
    # Get the S3 client
    s3_client = get_s3_client()
    
    try:
        # Read the file content
        file_content = await file.read()
        
        # Upload the file to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=file_content,
            ContentType=file.content_type
        )
        
        # Return the S3 path
        return s3_key
    except Exception as e:
        logger.error(f"Failed to upload file to S3: {str(e)}")
        raise e

def delete_file_s3(file_path: str) -> bool:
    """
    Delete a file from S3/MinIO.
    
    Args:
        file_path: The relative path to the file in S3
            
    Returns:
        bool: True if file was deleted, False if file doesn't exist
    """
    # Determine which bucket to use
    bucket_name = settings.S3_FILES_BUCKET_NAME
    
    # Get the S3 client
    s3_client = get_s3_client()
    
    try:
        # Check if the file exists
        s3_client.head_object(Bucket=bucket_name, Key=file_path)
        
        # Delete the file
        s3_client.delete_object(Bucket=bucket_name, Key=file_path)
        return True
    except Exception as e:
        logger.error(f"Failed to delete file from S3: {str(e)}")
        return False

def get_file_url(file_path: str) -> str:
    """
    Get the URL for a file stored in S3/MinIO.
    
    Args:
        file_path: The relative path to the file in S3
            
    Returns:
        str: The URL to access the file
    """
    # Determine which bucket to use
    bucket_name = settings.S3_FILES_BUCKET_NAME
    
    # Construct the URL
    url = f"{settings.S3_ENDPOINT_URL}/{bucket_name}/{file_path}"
    return url

async def store_file_local(file: UploadFile, storage_path: str) -> str:
    """
    Store a file in the local filesystem and return its relative path.
    
    Args:
        file: The uploaded file
        storage_path: The relative path where the file should be stored
            e.g. "workspaces/1/files" or "workspaces/1/items/2"
            
    Returns:
        str: The relative path to the stored file
    """
    # Create a unique filename to avoid collisions
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Construct the full storage path
    full_storage_path = os.path.join(settings.STORAGE_DIR, storage_path)
    
    # Create directories if they don't exist
    os.makedirs(full_storage_path, exist_ok=True)
    
    # Construct the full file path
    full_file_path = os.path.join(full_storage_path, unique_filename)
    
    # Write the file
    try:
        # Read the file in chunks to handle large files efficiently
        with open(full_file_path, "wb") as f:
            while contents := await file.read(1024 * 1024):  # Read in 1MB chunks
                f.write(contents)
    except Exception as e:
        # If there's an error, try to clean up the file if it was created
        if os.path.exists(full_file_path):
            os.remove(full_file_path)
        raise e
    
    # Return the relative path (without STORAGE_DIR prefix)
    return os.path.join(storage_path, unique_filename)

def delete_file_local(file_path: str) -> bool:
    """
    Delete a file from the local filesystem.
    
    Args:
        file_path: The relative path to the file
            
    Returns:
        bool: True if file was deleted, False if file doesn't exist
    """
    full_path = os.path.join(settings.STORAGE_DIR, file_path)
    try:
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
    except Exception:
        return False

async def store_file(file: UploadFile, storage_path: str) -> str:
    """
    Store a file using the configured storage backend (S3/MinIO or local filesystem).
    
    Args:
        file: The uploaded file
        storage_path: The relative path where the file should be stored
            
    Returns:
        str: The relative path to the stored file
    """
    # Check if S3 storage is enabled
    if hasattr(settings, 'USE_S3_STORAGE') and settings.USE_S3_STORAGE:
        return await store_file_s3(file, storage_path)
    else:
        return await store_file_local(file, storage_path)

def delete_file(file_path: str) -> bool:
    """
    Delete a file using the configured storage backend (S3/MinIO or local filesystem).
    
    Args:
        file_path: The relative path to the file
            
    Returns:
        bool: True if file was deleted, False if file doesn't exist
    """
    # Check if S3 storage is enabled
    if hasattr(settings, 'USE_S3_STORAGE') and settings.USE_S3_STORAGE:
        return delete_file_s3(file_path)
    else:
        return delete_file_local(file_path)
