import os
import uuid
import hashlib
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs


def generate_id() -> str:
    """Generate a unique ID for database records."""
    return str(uuid.uuid4())


def get_file_hash(file_path: str) -> str:
    """Generate MD5 hash of a file for deduplication."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def extract_youtube_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various YouTube URL formats."""
    parsed_url = urlparse(url)
    
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query)['v'][0]
        if parsed_url.path[:7] == '/embed/':
            return parsed_url.path.split('/')[2]
        if parsed_url.path[:3] == '/v/':
            return parsed_url.path.split('/')[2]
    
    return None


def format_duration(seconds: float) -> str:
    """Convert seconds to human-readable duration."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def get_video_filename(video_id: str, extension: str = "mp4") -> str:
    """Generate standardized video filename."""
    return f"video_{video_id}.{extension}"


def get_clip_filename(clip_id: str, format_type: str, resolution: str, extension: str = "mp4") -> str:
    """Generate standardized clip filename."""
    return f"clip_{clip_id}_{format_type}_{resolution}.{extension}"


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:255]  # Limit filename length


def calculate_aspect_ratio_dimensions(original_width: int, original_height: int, 
                                    target_ratio: str) -> Tuple[int, int]:
    """Calculate new dimensions for aspect ratio conversion."""
    if target_ratio == "9:16":
        # Vertical format
        if original_width > original_height:
            # Landscape to portrait - crop to center
            new_height = original_height
            new_width = int(original_height * 9 / 16)
        else:
            # Already portrait or square
            new_width = original_width
            new_height = int(original_width * 16 / 9)
            
    elif target_ratio == "1:1":
        # Square format
        size = min(original_width, original_height)
        new_width = new_height = size
        
    else:  # "16:9"
        # Horizontal format
        if original_height > original_width:
            # Portrait to landscape
            new_width = original_width
            new_height = int(original_width * 9 / 16)
        else:
            # Already landscape or square
            new_height = original_height
            new_width = int(original_height * 16 / 9)
    
    return new_width, new_height


def is_valid_video_extension(filename: str) -> bool:
    """Check if file has a valid video extension."""
    valid_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
    return os.path.splitext(filename.lower())[1] in valid_extensions


def format_file_size(size_bytes: int) -> str:
    """Convert bytes to human-readable file size."""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


# Constants
MAX_FILE_SIZE_FREE = 100 * 1024 * 1024  # 100MB for free users
MAX_FILE_SIZE_PREMIUM = 1024 * 1024 * 1024  # 1GB for premium users
MAX_CLIPS_PER_DAY_FREE = 3
MAX_CLIPS_PER_DAY_PREMIUM = 20
MAX_VIDEO_DURATION_FREE = 600  # 10 minutes
MAX_VIDEO_DURATION_PREMIUM = 3600  # 1 hour
