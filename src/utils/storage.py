import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from config import settings

async def store_file(file: UploadFile, storage_path: str) -> str:
    """
    Store a file in the filesystem and return its relative path.
    
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

def delete_file(file_path: str) -> bool:
    """
    Delete a file from the filesystem.
    
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