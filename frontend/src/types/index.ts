export enum JobStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed"
}

export enum VideoSource {
  UPLOAD = "upload",
  YOUTUBE = "youtube"
}

export enum ExportFormat {
  VERTICAL = "9:16",
  SQUARE = "1:1",
  HORIZONTAL = "16:9"
}

export enum SubscriptionTier {
  FREE = "free",
  PREMIUM = "premium",
  LIFETIME = "lifetime"
}

export interface User {
  id: string;
  email: string;
  subscription_tier: SubscriptionTier;
  clips_used_today: number;
  created_at: string;
  updated_at: string;
}

export interface Video {
  id: string;
  user_id: string;
  title: string;
  source: VideoSource;
  source_url?: string;
  file_path: string;
  duration: number;
  file_size: number;
  status: JobStatus;
  created_at: string;
  updated_at: string;
}

export interface Transcript {
  id: string;
  video_id: string;
  text: string;
  segments: TranscriptSegment[];
  language: string;
  created_at: string;
}

export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
  words?: TranscriptWord[];
}

export interface TranscriptWord {
  start: number;
  end: number;
  word: string;
  probability: number;
}

export interface Highlight {
  id: string;
  video_id: string;
  start_time: number;
  end_time: number;
  score: number;
  keywords: string[];
  title: string;
  description?: string;
  created_at: string;
}

export interface Clip {
  id: string;
  video_id: string;
  highlight_id: string;
  user_id: string;
  title: string;
  file_path: string;
  export_format: ExportFormat;
  resolution: string;
  has_watermark: boolean;
  file_size: number;
  status: JobStatus;
  created_at: string;
}

export interface Job {
  id: string;
  user_id: string;
  job_type: string;
  status: JobStatus;
  progress: number;
  error_message?: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Request/Response Types
export interface VideoUploadRequest {
  title: string;
  source: VideoSource;
  source_url?: string;
}

export interface VideoUploadResponse {
  video_id: string;
  upload_url?: string;
  job_id: string;
}

export interface TranscribeRequest {
  video_id: string;
}

export interface HighlightRequest {
  video_id: string;
  max_highlights: number;
}

export interface ExportRequest {
  highlight_id: string;
  export_format: ExportFormat;
  include_subtitles: boolean;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  error_message?: string;
  result?: Record<string, any>;
}

export interface UserStats {
  subscription_tier: SubscriptionTier;
  clips_used_today: number;
  clips_remaining: number;
  max_clips_per_day: number;
}

// UI Component Props
export interface VideoCardProps {
  video: Video;
  onTranscribe: (videoId: string) => void;
  onHighlight: (videoId: string) => void;
}

export interface HighlightCardProps {
  highlight: Highlight;
  onExport: (highlightId: string, format: ExportFormat) => void;
}

export interface ClipCardProps {
  clip: Clip;
  onDownload: (clipId: string) => void;
  onPreview: (clipId: string) => void;
}

export interface ProgressBarProps {
  progress: number;
  status: JobStatus;
  className?: string;
}

export interface UploadAreaProps {
  onFileSelect: (file: File) => void;
  onUrlSubmit: (url: string, title: string) => void;
  maxFileSize: number;
  acceptedFormats: string[];
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface VideosResponse {
  videos: Video[];
}

export interface HighlightsResponse {
  highlights: Highlight[];
}

export interface ClipsResponse {
  clips: Clip[];
}

export interface DownloadResponse {
  download_url: string;
}

// Utility Types
export interface AspectRatioOption {
  label: string;
  value: ExportFormat;
  description: string;
  icon: string;
}

export interface SubscriptionFeature {
  name: string;
  free: string | boolean;
  premium: string | boolean;
}

export interface PricingPlan {
  name: string;
  price: number;
  period: string;
  features: SubscriptionFeature[];
  highlighted?: boolean;
}

// Constants
export const ASPECT_RATIO_OPTIONS: AspectRatioOption[] = [
  {
    label: "Vertical",
    value: ExportFormat.VERTICAL,
    description: "Perfect for TikTok, Instagram Reels",
    icon: "📱"
  },
  {
    label: "Square",
    value: ExportFormat.SQUARE,
    description: "Great for Instagram posts",
    icon: "⬜"
  },
  {
    label: "Horizontal",
    value: ExportFormat.HORIZONTAL,
    description: "YouTube Shorts, landscape",
    icon: "📺"
  }
];

export const MAX_FILE_SIZE_FREE = 100 * 1024 * 1024; // 100MB
export const MAX_FILE_SIZE_PREMIUM = 1024 * 1024 * 1024; // 1GB
export const MAX_CLIPS_PER_DAY_FREE = 3;
export const MAX_CLIPS_PER_DAY_PREMIUM = 20;
