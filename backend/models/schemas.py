"""
Enhanced Pydantic schemas for Viral Clips App
Includes all new features: scripting, templates, analytics, enhanced billing
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum

# Enums
class SubscriptionTier(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    AGENCY = "agency"
    LIFETIME_BASIC = "lifetime_basic"
    LIFETIME_PRO = "lifetime_pro"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    TRIAL = "trial"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Platform(str, Enum):
    GENERAL = "general"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"

class TemplateType(str, Enum):
    VIDEO = "video"
    SUBTITLE = "subtitle"
    BRAND = "brand"

class BrandAssetType(str, Enum):
    LOGO = "logo"
    WATERMARK = "watermark"
    INTRO = "intro"
    OUTRO = "outro"
    BACKGROUND = "background"

class SourceType(str, Enum):
    UPLOAD = "upload"
    YOUTUBE = "youtube"
    VIMEO = "vimeo"
    TWITCH = "twitch"

class AspectRatio(str, Enum):
    VERTICAL = "9:16"
    SQUARE = "1:1"
    HORIZONTAL = "16:9"
    CUSTOM = "custom"

# Base Models
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        use_enum_values = True

class Position(BaseModel):
    x: float = Field(..., ge=0, le=1, description="X position as percentage (0-1)")
    y: float = Field(..., ge=0, le=1, description="Y position as percentage (0-1)")
    width: Optional[float] = Field(None, ge=0, le=1, description="Width as percentage (0-1)")
    height: Optional[float] = Field(None, ge=0, le=1, description="Height as percentage (0-1)")
    opacity: Optional[float] = Field(1.0, ge=0, le=1, description="Opacity (0-1)")

class TemplateConfig(BaseModel):
    # Subtitle template config
    font: Optional[str] = "Inter"
    size: Optional[int] = Field(24, ge=12, le=72)
    color: Optional[str] = "#FFFFFF"
    background: Optional[str] = "rgba(0,0,0,0.8)"
    animation: Optional[Literal["fade", "bounce", "slide", "pulse", "typewriter", "none"]] = "fade"
    position: Optional[Literal["top", "center", "bottom"]] = "bottom"
    
    # Video template config
    intro_duration: Optional[float] = Field(None, ge=0, le=10)
    outro_duration: Optional[float] = Field(None, ge=0, le=10)
    transition_type: Optional[str] = None
    background_music: Optional[str] = None
    
    # Brand template config
    logo_position: Optional[Position] = None
    watermark_opacity: Optional[float] = Field(0.5, ge=0, le=1)
    brand_colors: Optional[List[str]] = []

# User Models
class UserBase(BaseSchema):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    referral_code: Optional[str] = None

class UserUpdate(BaseSchema):
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class User(UserBase):
    id: str
    subscription_tier: SubscriptionTier
    subscription_status: SubscriptionStatus
    subscription_starts_at: Optional[datetime] = None
    subscription_ends_at: Optional[datetime] = None
    daily_clips_used: int = 0
    daily_clips_limit: int = 2
    total_clips_created: int = 0
    credits_remaining: int = 0
    paystack_customer_id: Optional[str] = None
    onboarding_completed: bool = False
    preferences: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

# Video Models
class VideoBase(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    source_type: SourceType
    source_url: Optional[str] = None

class VideoCreate(VideoBase):
    pass

class VideoUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    processing_status: Optional[ProcessingStatus] = None
    processing_progress: Optional[int] = Field(None, ge=0, le=100)
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class Video(VideoBase):
    id: str
    user_id: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    duration_seconds: Optional[int] = None
    format: Optional[str] = None
    resolution: Optional[str] = None
    fps: Optional[int] = None
    thumbnail_url: Optional[str] = None
    processing_status: ProcessingStatus
    processing_progress: int = 0
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

# Script Models
class ScriptTimestamp(BaseModel):
    start_time: float = Field(..., ge=0)
    end_time: float = Field(..., ge=0)
    section_type: Literal["hook", "content", "cta", "transition"]
    content: str

    @validator('end_time')
    def end_time_must_be_greater_than_start(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be greater than start_time')
        return v

class ScriptBase(BaseSchema):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=10)
    platform_optimization: Platform = Platform.GENERAL

class ScriptCreate(ScriptBase):
    video_id: str
    custom_prompt: Optional[str] = None
    include_timestamps: bool = True

class ScriptUpdate(BaseSchema):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=10)
    platform_optimization: Optional[Platform] = None
    status: Optional[Literal["draft", "published", "archived"]] = None

class Script(ScriptBase):
    id: str
    video_id: str
    user_id: str
    engagement_score: float = Field(0.0, ge=0, le=1)
    sentiment_score: float = Field(0.0, ge=-1, le=1)
    keywords: List[str] = []
    hashtags: List[str] = []
    hooks: List[str] = []
    ctas: List[str] = []
    timestamps: List[ScriptTimestamp] = []
    is_ai_generated: bool = True
    version: int = 1
    status: Literal["draft", "published", "archived"] = "draft"
    created_at: datetime
    updated_at: datetime

# Template Models
class TemplateBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: str = Field(..., min_length=1, max_length=50)
    type: TemplateType
    config: TemplateConfig

class TemplateCreate(TemplateBase):
    tags: Optional[List[str]] = []

class TemplateUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    config: Optional[TemplateConfig] = None
    tags: Optional[List[str]] = None

class Template(TemplateBase):
    id: str
    user_id: Optional[str] = None
    is_premium: bool = False
    is_system_template: bool = False
    preview_url: Optional[str] = None
    usage_count: int = 0
    rating: float = Field(0.0, ge=0, le=5)
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime

# Brand Asset Models
class BrandAssetBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    type: BrandAssetType
    is_default: bool = False
    position: Position

class BrandAssetCreate(BrandAssetBase):
    pass

class BrandAssetUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_default: Optional[bool] = None
    position: Optional[Position] = None

class BrandAsset(BrandAssetBase):
    id: str
    user_id: str
    file_path: str
    file_size: Optional[int] = None
    dimensions: Optional[str] = None
    format: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Clip Models
class SubtitleConfig(BaseModel):
    template_id: Optional[str] = None
    font: Optional[str] = "Inter"
    size: Optional[int] = Field(24, ge=12, le=72)
    color: Optional[str] = "#FFFFFF"
    background: Optional[str] = "rgba(0,0,0,0.8)"
    animation: Optional[str] = "fade"
    position: Optional[str] = "bottom"
    custom_styles: Optional[Dict[str, Any]] = {}

class EditingConfig(BaseModel):
    background_music: Optional[str] = None
    volume_level: Optional[float] = Field(1.0, ge=0, le=2)
    fade_in: Optional[float] = Field(0.0, ge=0, le=5)
    fade_out: Optional[float] = Field(0.0, ge=0, le=5)
    filters: Optional[List[str]] = []
    transitions: Optional[List[str]] = []

class BrandingConfig(BaseModel):
    logo_asset_id: Optional[str] = None
    watermark_asset_id: Optional[str] = None
    intro_asset_id: Optional[str] = None
    outro_asset_id: Optional[str] = None
    background_asset_id: Optional[str] = None

class ExportSettings(BaseModel):
    quality: Literal["low", "medium", "high", "ultra"] = "medium"
    format: Literal["mp4", "mov", "webm"] = "mp4"
    bitrate: Optional[int] = None
    framerate: Optional[int] = None
    include_watermark: bool = True
    compression_level: int = Field(5, ge=1, le=10)

class ClipBase(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: float = Field(..., ge=0)
    end_time: float = Field(..., ge=0)
    aspect_ratio: AspectRatio = AspectRatio.VERTICAL
    resolution: str = "720p"

    @validator('end_time')
    def end_time_must_be_greater_than_start(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be greater than start_time')
        return v

class ClipCreate(ClipBase):
    video_id: str
    script_id: Optional[str] = None
    template_id: Optional[str] = None
    subtitle_config: Optional[SubtitleConfig] = SubtitleConfig()
    editing_config: Optional[EditingConfig] = EditingConfig()
    branding_config: Optional[BrandingConfig] = BrandingConfig()
    export_settings: Optional[ExportSettings] = ExportSettings()

class ClipUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    export_status: Optional[ProcessingStatus] = None
    export_progress: Optional[int] = Field(None, ge=0, le=100)
    subtitle_config: Optional[SubtitleConfig] = None
    editing_config: Optional[EditingConfig] = None
    branding_config: Optional[BrandingConfig] = None
    export_settings: Optional[ExportSettings] = None

class Clip(ClipBase):
    id: str
    video_id: str
    script_id: Optional[str] = None
    template_id: Optional[str] = None
    user_id: str
    duration_seconds: float
    highlight_score: float = Field(0.0, ge=0, le=1)
    viral_potential_score: float = Field(0.0, ge=0, le=1)
    export_status: ProcessingStatus = ProcessingStatus.PENDING
    export_progress: int = 0
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_url: Optional[str] = None
    download_expires_at: Optional[datetime] = None
    subtitle_config: SubtitleConfig
    editing_config: EditingConfig
    branding_config: BrandingConfig
    export_settings: ExportSettings
    created_at: datetime
    updated_at: datetime

# Transcription Models
class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float
    confidence: float

class TranscriptionSegment(BaseModel):
    start: float
    end: float
    text: str
    confidence: float
    speaker_id: Optional[str] = None
    words: Optional[List[WordTimestamp]] = []

class Speaker(BaseModel):
    id: str
    name: Optional[str] = None
    segments: List[int] = []

class Keyword(BaseModel):
    word: str
    score: float
    frequency: int

class SentimentAnalysis(BaseModel):
    overall_sentiment: Literal["positive", "negative", "neutral"]
    sentiment_score: float = Field(..., ge=-1, le=1)
    emotions: Dict[str, float] = {}
    viral_indicators: List[str] = []

class TranscriptionBase(BaseSchema):
    language: str = "en"
    model_used: str = "faster-whisper"

class TranscriptionCreate(TranscriptionBase):
    video_id: str

class Transcription(TranscriptionBase):
    id: str
    video_id: str
    confidence_score: float
    full_text: str
    segments: List[TranscriptionSegment]
    speakers: List[Speaker] = []
    keywords: List[Keyword] = []
    sentiment_analysis: SentimentAnalysis
    processing_time_ms: Optional[int] = None
    created_at: datetime

# Job Models
class JobBase(BaseSchema):
    job_type: Literal["transcription", "highlight_detection", "script_generation", "clip_export", "template_processing"]
    priority: int = Field(0, ge=0, le=10)

class JobCreate(JobBase):
    video_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class JobUpdate(BaseSchema):
    status: Optional[JobStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    eta_seconds: Optional[int] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None

class Job(JobBase):
    id: str
    user_id: str
    video_id: Optional[str] = None
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    eta_seconds: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_data: Dict[str, Any] = {}
    task_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime
    updated_at: datetime

# Analytics Models
class AnalyticsCreate(BaseSchema):
    video_id: Optional[str] = None
    clip_id: Optional[str] = None
    event_type: str = Field(..., min_length=1)
    event_data: Dict[str, Any] = {}
    processing_time_ms: Optional[int] = None
    file_size_bytes: Optional[int] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    country_code: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None

class Analytics(AnalyticsCreate):
    id: str
    user_id: str
    created_at: datetime

# Billing Models
class BillingBase(BaseSchema):
    amount: Decimal = Field(..., ge=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    transaction_type: Literal["subscription", "one_time", "refund"]
    description: Optional[str] = None

class BillingCreate(BillingBase):
    paystack_reference: str
    metadata: Optional[Dict[str, Any]] = {}

class BillingUpdate(BaseSchema):
    status: Optional[Literal["pending", "successful", "failed", "refunded"]] = None
    paystack_transaction_id: Optional[str] = None
    payment_method: Optional[str] = None
    invoice_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class Billing(BillingBase):
    id: str
    user_id: str
    paystack_transaction_id: Optional[str] = None
    paystack_reference: str
    payment_method: Optional[str] = None
    status: Literal["pending", "successful", "failed", "refunded"] = "pending"
    invoice_url: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

# Usage Tracking Models
class UsageTrackingCreate(BaseSchema):
    date: date
    clips_created: int = 0
    videos_uploaded: int = 0
    scripts_generated: int = 0
    processing_minutes: int = 0
    storage_used_mb: int = 0
    api_calls: int = 0

class UsageTracking(UsageTrackingCreate):
    id: str
    user_id: str
    created_at: datetime

# API Request/Response Models
class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None

class PaginatedResponse(BaseModel):
    data: List[Any]
    total: int
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total_pages: int

class JobProgress(BaseModel):
    job_id: str
    status: JobStatus
    progress: int = Field(..., ge=0, le=100)
    eta_seconds: Optional[int] = None
    current_step: Optional[str] = None
    error_message: Optional[str] = None

# Dashboard Models
class DashboardStats(BaseModel):
    total_videos: int
    total_clips: int
    total_scripts: int
    processing_time_saved: int  # in minutes
    storage_used: int  # in MB
    clips_remaining_today: int
    subscription_status: SubscriptionStatus
    subscription_expires_at: Optional[datetime] = None

class AnalyticsChartData(BaseModel):
    date: str
    clips_created: int
    videos_uploaded: int
    scripts_generated: int
    processing_minutes: int

# Pricing Models
class PricingPlan(BaseModel):
    id: str
    name: str
    price: float
    billing_period: Literal["monthly", "yearly", "lifetime"]
    features: List[str]
    limitations: Dict[str, Any]
    is_popular: bool = False
    is_lifetime: bool = False
    discount_percentage: Optional[float] = None

# Upload Models
class UploadVideoRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    source_type: SourceType
    source_url: Optional[str] = None

    @validator('source_url')
    def validate_source_url(cls, v, values):
        if values.get('source_type') in ['youtube', 'vimeo', 'twitch'] and not v:
            raise ValueError('source_url is required for external video sources')
        return v

class ProcessClipRequest(BaseModel):
    video_id: str
    script_id: Optional[str] = None
    template_id: Optional[str] = None
    start_time: float = Field(..., ge=0)
    end_time: float = Field(..., ge=0)
    aspect_ratio: AspectRatio = AspectRatio.VERTICAL
    resolution: str = "720p"
    subtitle_config: Optional[SubtitleConfig] = SubtitleConfig()
    editing_config: Optional[EditingConfig] = EditingConfig()
    branding_config: Optional[BrandingConfig] = BrandingConfig()
    export_settings: Optional[ExportSettings] = ExportSettings()

    @validator('end_time')
    def end_time_must_be_greater_than_start(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be greater than start_time')
        return v

# Subscription Models
class SubscriptionDetails(BaseModel):
    tier: SubscriptionTier
    status: SubscriptionStatus
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    paystack_subscription_code: Optional[str] = None

class UsageDetails(BaseModel):
    current_period: Dict[str, int]
    limits: Dict[str, int]
    remaining: Dict[str, int]

# Webhook Models
class PaystackWebhookData(BaseModel):
    reference: str
    amount: int
    customer: Dict[str, Any]
    status: str
    metadata: Optional[Dict[str, Any]] = None

class PaystackWebhook(BaseModel):
    event: str
    data: PaystackWebhookData

# Error Models
class AppError(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# Constants for subscription limits
SUBSCRIPTION_LIMITS = {
    SubscriptionTier.FREE: {
        "daily_clips": 2,
        "max_video_length": 3600,  # 1 hour in seconds
        "max_file_size": 500 * 1024 * 1024,  # 500MB
        "available_resolutions": ["480p"],
        "features": ["basic_subtitles", "single_aspect_ratio", "ads_required"],
        "export_formats": ["mp4"],
        "watermark_required": True
    },
    SubscriptionTier.BASIC: {
        "daily_clips": 10,
        "max_video_length": 7200,  # 2 hours
        "max_file_size": 1024 * 1024 * 1024,  # 1GB
        "available_resolutions": ["480p", "720p"],
        "features": ["animated_subtitles", "multi_aspect_ratio", "basic_templates"],
        "export_formats": ["mp4", "mov"],
        "watermark_required": True
    },
    SubscriptionTier.PRO: {
        "daily_clips": 50,
        "max_video_length": 14400,  # 4 hours
        "max_file_size": 5 * 1024 * 1024 * 1024,  # 5GB
        "available_resolutions": ["480p", "720p", "1080p"],
        "features": ["all_features", "batch_processing", "priority_queue", "api_access"],
        "export_formats": ["mp4", "mov", "webm"],
        "watermark_required": False
    },
    SubscriptionTier.AGENCY: {
        "daily_clips": -1,  # Unlimited
        "max_video_length": -1,  # Unlimited
        "max_file_size": 50 * 1024 * 1024 * 1024,  # 50GB
        "available_resolutions": ["480p", "720p", "1080p", "4k"],
        "features": ["all_features", "white_label", "team_collaboration", "dedicated_support"],
        "export_formats": ["mp4", "mov", "webm"],
        "watermark_required": False
    },
    SubscriptionTier.LIFETIME_BASIC: {
        "daily_clips": 10,
        "max_video_length": 7200,
        "max_file_size": 2 * 1024 * 1024 * 1024,  # 2GB
        "available_resolutions": ["480p", "720p"],
        "features": ["animated_subtitles", "multi_aspect_ratio", "basic_templates"],
        "export_formats": ["mp4", "mov"],
        "watermark_required": True
    },
    SubscriptionTier.LIFETIME_PRO: {
        "daily_clips": 50,
        "max_video_length": 14400,
        "max_file_size": 10 * 1024 * 1024 * 1024,  # 10GB
        "available_resolutions": ["480p", "720p", "1080p"],
        "features": ["all_features", "batch_processing", "priority_queue"],
        "export_formats": ["mp4", "mov", "webm"],
        "watermark_required": False
    }
}
