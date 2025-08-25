import os
from supabase import create_client, Client
from typing import Optional, List, Dict, Any


class Database:
    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL", "")
        key: str = os.environ.get("SUPABASE_ANON_KEY", "")
        self.supabase: Client = create_client(url, key)
    
    async def create_user(self, user_data: dict) -> dict:
        """Create a new user record."""
        result = self.supabase.table('users').insert(user_data).execute()
        return result.data[0] if result.data else None
    
    async def get_user(self, user_id: str) -> Optional[dict]:
        """Get user by ID."""
        result = self.supabase.table('users').select("*").eq('id', user_id).execute()
        return result.data[0] if result.data else None
    
    async def update_user(self, user_id: str, updates: dict) -> dict:
        """Update user record."""
        result = self.supabase.table('users').update(updates).eq('id', user_id).execute()
        return result.data[0] if result.data else None
    
    async def create_video(self, video_data: dict) -> dict:
        """Create a new video record."""
        result = self.supabase.table('videos').insert(video_data).execute()
        return result.data[0] if result.data else None
    
    async def get_video(self, video_id: str) -> Optional[dict]:
        """Get video by ID."""
        result = self.supabase.table('videos').select("*").eq('id', video_id).execute()
        return result.data[0] if result.data else None
    
    async def get_user_videos(self, user_id: str, limit: int = 10) -> List[dict]:
        """Get videos for a user."""
        result = self.supabase.table('videos').select("*").eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
        return result.data or []
    
    async def update_video(self, video_id: str, updates: dict) -> dict:
        """Update video record."""
        result = self.supabase.table('videos').update(updates).eq('id', video_id).execute()
        return result.data[0] if result.data else None
    
    async def create_transcript(self, transcript_data: dict) -> dict:
        """Create a new transcript record."""
        result = self.supabase.table('transcripts').insert(transcript_data).execute()
        return result.data[0] if result.data else None
    
    async def get_transcript(self, video_id: str) -> Optional[dict]:
        """Get transcript for a video."""
        result = self.supabase.table('transcripts').select("*").eq('video_id', video_id).execute()
        return result.data[0] if result.data else None
    
    async def create_highlight(self, highlight_data: dict) -> dict:
        """Create a new highlight record."""
        result = self.supabase.table('highlights').insert(highlight_data).execute()
        return result.data[0] if result.data else None
    
    async def get_highlights(self, video_id: str) -> List[dict]:
        """Get highlights for a video."""
        result = self.supabase.table('highlights').select("*").eq('video_id', video_id).order('score', desc=True).execute()
        return result.data or []
    
    async def create_clip(self, clip_data: dict) -> dict:
        """Create a new clip record."""
        result = self.supabase.table('clips').insert(clip_data).execute()
        return result.data[0] if result.data else None
    
    async def get_clip(self, clip_id: str) -> Optional[dict]:
        """Get clip by ID."""
        result = self.supabase.table('clips').select("*").eq('id', clip_id).execute()
        return result.data[0] if result.data else None
    
    async def get_user_clips(self, user_id: str, limit: int = 20) -> List[dict]:
        """Get clips for a user."""
        result = self.supabase.table('clips').select("*").eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
        return result.data or []
    
    async def update_clip(self, clip_id: str, updates: dict) -> dict:
        """Update clip record."""
        result = self.supabase.table('clips').update(updates).eq('id', clip_id).execute()
        return result.data[0] if result.data else None
    
    async def create_job(self, job_data: dict) -> dict:
        """Create a new job record."""
        result = self.supabase.table('jobs').insert(job_data).execute()
        return result.data[0] if result.data else None
    
    async def get_job(self, job_id: str) -> Optional[dict]:
        """Get job by ID."""
        result = self.supabase.table('jobs').select("*").eq('id', job_id).execute()
        return result.data[0] if result.data else None
    
    async def update_job(self, job_id: str, updates: dict) -> dict:
        """Update job record."""
        result = self.supabase.table('jobs').update(updates).eq('id', job_id).execute()
        return result.data[0] if result.data else None
    
    async def get_user_daily_clips_count(self, user_id: str) -> int:
        """Get number of clips created by user today."""
        result = self.supabase.table('clips').select("id", count="exact").eq('user_id', user_id).gte('created_at', 'today()').execute()
        return result.count or 0


# Storage helper functions
class Storage:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.bucket_name = "videos"
    
    def upload_file(self, file_path: str, file_data: bytes) -> str:
        """Upload file to Supabase storage."""
        result = self.supabase.storage.from_(self.bucket_name).upload(file_path, file_data)
        return result.path if hasattr(result, 'path') else file_path
    
    def get_public_url(self, file_path: str) -> str:
        """Get public URL for a file."""
        result = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
        return result['publicURL'] if isinstance(result, dict) else str(result)
    
    def download_file(self, file_path: str) -> bytes:
        """Download file from Supabase storage."""
        result = self.supabase.storage.from_(self.bucket_name).download(file_path)
        return result
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from Supabase storage."""
        try:
            self.supabase.storage.from_(self.bucket_name).remove([file_path])
            return True
        except Exception:
            return False
