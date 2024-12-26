import os
import re
from urllib.parse import unquote

def clean_filename(filename: str) -> str:
    """Clean filename by removing illegal characters"""
    return re.sub(r'[\\/*?:"<>|]', '', filename)

def get_file_extension(media_type: str) -> str:
    """Get file extension based on media type"""
    extensions = {
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/svg+xml': '.svg'
    }
    return extensions.get(media_type, '.jpg')

def ensure_dir(directory: str) -> None:
    """Ensure directory exists, create if not"""
    os.makedirs(directory, exist_ok=True) 