from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, HttpUrl


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoSource(str, Enum):
    UPLOAD = "upload"
    YOUTUBE = "youtube"


class ExportFormat(str, Enum):
    VERTICAL = "9:16"  # TikTok, Instagram Reels
    SQUARE = "1:1"     # Instagram Post
    HORIZONTAL = "16:9" # YouTube Shorts


class SubscriptionTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    LIFETIME = "lifetime"


# Pydantic Models
class User(BaseModel):
    id: str
    email: str
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    clips_used_today: int = 0
    created_at: datetime
    updated_at: datetime


class Video(BaseModel):
    id: str
    user_id: str
    title: str
    source: VideoSource
    source_url: Optional[HttpUrl] = None
    file_path: str
    duration: float
    file_size: int
    status: JobStatus = JobStatus.PENDING
    created_at: datetime
    updated_at: datetime


class Transcript(BaseModel):
    id: str
    video_id: str
    text: str
    segments: List[dict]  # Word-level timestamps
    language: str = "en"
    created_at: datetime


class Highlight(BaseModel):
    id: str
    video_id: str
    start_time: float
    end_time: float
    score: float  # Viral potential score
    keywords: List[str]
    title: str
    description: Optional[str] = None
    created_at: datetime


class Clip(BaseModel):
    id: str
    video_id: str
    highlight_id: str
    user_id: str
    title: str
    file_path: str
    export_format: ExportFormat
    resolution: str  # "720p" or "1080p"
    has_watermark: bool
    file_size: int
    status: JobStatus = JobStatus.PENDING
    created_at: datetime


class Job(BaseModel):
    id: str
    user_id: str
    job_type: str  # "transcribe", "highlight", "export"
    status: JobStatus
    progress: int = 0
    error_message: Optional[str] = None
    metadata: dict = {}
    created_at: datetime
    updated_at: datetime


# Request/Response Models
class VideoUploadRequest(BaseModel):
    title: str
    source: VideoSource
    source_url: Optional[HttpUrl] = None


class VideoUploadResponse(BaseModel):
    video_id: str
    upload_url: Optional[str] = None  # For direct file upload
    job_id: str


class TranscribeRequest(BaseModel):
    video_id: str


class HighlightRequest(BaseModel):
    video_id: str
    max_highlights: int = 5


class ExportRequest(BaseModel):
    highlight_id: str
    export_format: ExportFormat = ExportFormat.VERTICAL
    include_subtitles: bool = True


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int
    error_message: Optional[str] = None
    result: Optional[dict] = None
