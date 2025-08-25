// Shared types for the Viral Clips App

export type SubscriptionTier = 'free' | 'basic' | 'pro' | 'agency' | 'lifetime_basic' | 'lifetime_pro';
export type SubscriptionStatus = 'active' | 'cancelled' | 'expired' | 'trial';
export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
export type PaymentStatus = 'pending' | 'successful' | 'failed' | 'refunded';
export type AspectRatio = '9:16' | '1:1' | '16:9' | 'custom';
export type Platform = 'general' | 'tiktok' | 'youtube' | 'instagram' | 'twitter';
export type TemplateType = 'video' | 'subtitle' | 'brand';
export type BrandAssetType = 'logo' | 'watermark' | 'intro' | 'outro' | 'background';
export type SourceType = 'upload' | 'youtube' | 'vimeo' | 'twitch';

export interface User {
  id: string;
  email: string;
  username?: string;
  full_name?: string;
  avatar_url?: string;
  subscription_tier: SubscriptionTier;
  subscription_status: SubscriptionStatus;
  subscription_starts_at?: string;
  subscription_ends_at?: string;
  daily_clips_used: number;
  daily_clips_limit: number;
  total_clips_created: number;
  credits_remaining: number;
  paystack_customer_id?: string;
  onboarding_completed: boolean;
  preferences: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Video {
  id: string;
  user_id: string;
  title?: string;
  description?: string;
  source_type: SourceType;
  source_url?: string;
  file_path?: string;
  file_size?: number;
  duration_seconds?: number;
  format?: string;
  resolution?: string;
  fps?: number;
  thumbnail_url?: string;
  processing_status: ProcessingStatus;
  processing_progress: number;
  processing_started_at?: string;
  processing_completed_at?: string;
  error_message?: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Script {
  id: string;
  video_id: string;
  user_id: string;
  title: string;
  content: string;
  platform_optimization: Platform;
  engagement_score: number;
  sentiment_score: number;
  keywords: string[];
  hashtags: string[];
  hooks: string[];
  ctas: string[];
  timestamps: ScriptTimestamp[];
  is_ai_generated: boolean;
  version: number;
  status: 'draft' | 'published' | 'archived';
  created_at: string;
  updated_at: string;
}

export interface ScriptTimestamp {
  start_time: number;
  end_time: number;
  section_type: 'hook' | 'content' | 'cta' | 'transition';
  content: string;
}

export interface Template {
  id: string;
  user_id?: string;
  name: string;
  description?: string;
  category: string;
  type: TemplateType;
  is_premium: boolean;
  is_system_template: boolean;
  config: TemplateConfig;
  preview_url?: string;
  usage_count: number;
  rating: number;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface TemplateConfig {
  // Subtitle template config
  font?: string;
  size?: number;
  color?: string;
  background?: string;
  animation?: 'fade' | 'bounce' | 'slide' | 'pulse' | 'typewriter' | 'none';
  position?: 'top' | 'center' | 'bottom';
  
  // Video template config
  intro_duration?: number;
  outro_duration?: number;
  transition_type?: string;
  background_music?: string;
  
  // Brand template config
  logo_position?: Position;
  watermark_opacity?: number;
  brand_colors?: string[];
}

export interface Position {
  x: number;
  y: number;
  width?: number;
  height?: number;
  opacity?: number;
}

export interface Clip {
  id: string;
  video_id: string;
  script_id?: string;
  template_id?: string;
  user_id: string;
  title?: string;
  description?: string;
  start_time: number;
  end_time: number;
  duration_seconds: number;
  highlight_score: number;
  viral_potential_score: number;
  aspect_ratio: AspectRatio;
  resolution: string;
  export_status: ProcessingStatus;
  export_progress: number;
  file_path?: string;
  file_size?: number;
  download_url?: string;
  download_expires_at?: string;
  subtitle_config: SubtitleConfig;
  editing_config: EditingConfig;
  branding_config: BrandingConfig;
  export_settings: ExportSettings;
  created_at: string;
  updated_at: string;
}

export interface SubtitleConfig {
  template_id?: string;
  font?: string;
  size?: number;
  color?: string;
  background?: string;
  animation?: string;
  position?: string;
  custom_styles?: Record<string, any>;
}

export interface EditingConfig {
  background_music?: string;
  volume_level?: number;
  fade_in?: number;
  fade_out?: number;
  filters?: string[];
  transitions?: string[];
}

export interface BrandingConfig {
  logo_asset_id?: string;
  watermark_asset_id?: string;
  intro_asset_id?: string;
  outro_asset_id?: string;
  background_asset_id?: string;
}

export interface ExportSettings {
  quality: 'low' | 'medium' | 'high' | 'ultra';
  format: 'mp4' | 'mov' | 'webm';
  bitrate?: number;
  framerate?: number;
  include_watermark: boolean;
  compression_level: number;
}

export interface Analytics {
  id: string;
  user_id: string;
  video_id?: string;
  clip_id?: string;
  event_type: string;
  event_data: Record<string, any>;
  processing_time_ms?: number;
  file_size_bytes?: number;
  user_agent?: string;
  ip_address?: string;
  country_code?: string;
  device_type?: string;
  browser?: string;
  created_at: string;
}

export interface Job {
  id: string;
  user_id: string;
  video_id?: string;
  job_type: 'transcription' | 'highlight_detection' | 'script_generation' | 'clip_export' | 'template_processing';
  status: JobStatus;
  priority: number;
  progress: number;
  eta_seconds?: number;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  result_data: Record<string, any>;
  task_id?: string;
  retry_count: number;
  max_retries: number;
  created_at: string;
  updated_at: string;
}

export interface BrandAsset {
  id: string;
  user_id: string;
  name: string;
  type: BrandAssetType;
  file_path: string;
  file_size?: number;
  dimensions?: string;
  format?: string;
  is_default: boolean;
  position: Position;
  created_at: string;
  updated_at: string;
}

export interface Transcription {
  id: string;
  video_id: string;
  language: string;
  model_used: string;
  confidence_score: number;
  full_text: string;
  segments: TranscriptionSegment[];
  speakers: Speaker[];
  keywords: Keyword[];
  sentiment_analysis: SentimentAnalysis;
  processing_time_ms?: number;
  created_at: string;
}

export interface TranscriptionSegment {
  start: number;
  end: number;
  text: string;
  confidence: number;
  speaker_id?: string;
  words?: WordTimestamp[];
}

export interface WordTimestamp {
  word: string;
  start: number;
  end: number;
  confidence: number;
}

export interface Speaker {
  id: string;
  name?: string;
  segments: number[];
}

export interface Keyword {
  word: string;
  score: number;
  frequency: number;
}

export interface SentimentAnalysis {
  overall_sentiment: 'positive' | 'negative' | 'neutral';
  sentiment_score: number;
  emotions: Record<string, number>;
  viral_indicators: string[];
}

export interface UsageTracking {
  id: string;
  user_id: string;
  date: string;
  clips_created: number;
  videos_uploaded: number;
  scripts_generated: number;
  processing_minutes: number;
  storage_used_mb: number;
  api_calls: number;
  created_at: string;
}

export interface Billing {
  id: string;
  user_id: string;
  paystack_transaction_id?: string;
  paystack_reference?: string;
  amount: number;
  currency: string;
  payment_method?: string;
  transaction_type: 'subscription' | 'one_time' | 'refund';
  status: PaymentStatus;
  description?: string;
  invoice_url?: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Referral {
  id: string;
  referrer_id: string;
  referee_id: string;
  referral_code: string;
  status: 'pending' | 'completed' | 'cancelled';
  reward_type: 'credits' | 'discount' | 'free_month';
  reward_amount: number;
  completed_at?: string;
  created_at: string;
}

// API Request/Response types
export interface CreateScriptRequest {
  video_id: string;
  platform_optimization?: Platform;
  custom_prompt?: string;
  include_timestamps?: boolean;
}

export interface EditScriptRequest {
  content: string;
  title?: string;
  platform_optimization?: Platform;
}

export interface CreateTemplateRequest {
  name: string;
  description?: string;
  category: string;
  type: TemplateType;
  config: TemplateConfig;
  tags?: string[];
}

export interface ProcessClipRequest {
  video_id: string;
  script_id?: string;
  template_id?: string;
  start_time: number;
  end_time: number;
  aspect_ratio: AspectRatio;
  resolution: string;
  subtitle_config?: SubtitleConfig;
  editing_config?: EditingConfig;
  branding_config?: BrandingConfig;
  export_settings?: ExportSettings;
}

export interface UploadVideoRequest {
  title?: string;
  description?: string;
  source_type: SourceType;
  source_url?: string;
}

// Dashboard Analytics types
export interface DashboardStats {
  total_videos: number;
  total_clips: number;
  total_scripts: number;
  processing_time_saved: number;
  storage_used: number;
  clips_remaining_today: number;
  subscription_status: SubscriptionStatus;
  subscription_expires_at?: string;
}

export interface AnalyticsChartData {
  date: string;
  clips_created: number;
  videos_uploaded: number;
  scripts_generated: number;
  processing_minutes: number;
}

export interface PricingPlan {
  id: string;
  name: string;
  price: number;
  billing_period: 'monthly' | 'yearly' | 'lifetime';
  features: string[];
  limitations: Record<string, number | string>;
  is_popular?: boolean;
  is_lifetime?: boolean;
  discount_percentage?: number;
}

// Frontend component props
export interface ScriptEditorProps {
  script?: Script;
  video?: Video;
  onSave: (script: Partial<Script>) => void;
  onGenerate: (request: CreateScriptRequest) => void;
  isGenerating?: boolean;
}

export interface TemplateGalleryProps {
  category?: string;
  type?: TemplateType;
  selectedTemplate?: string;
  onSelectTemplate: (template: Template) => void;
  showUserTemplates?: boolean;
}

export interface SubtitleCustomizerProps {
  config: SubtitleConfig;
  onChange: (config: SubtitleConfig) => void;
  previewText?: string;
}

export interface VideoTimelineProps {
  video: Video;
  transcription?: Transcription;
  clips: Clip[];
  selectedClip?: string;
  onClipSelect: (clipId: string) => void;
  onClipCreate: (startTime: number, endTime: number) => void;
  onClipEdit: (clipId: string, updates: Partial<Clip>) => void;
}

export interface AnalyticsDashboardProps {
  user: User;
  dateRange: {
    start: Date;
    end: Date;
  };
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface JobProgress {
  job_id: string;
  status: JobStatus;
  progress: number;
  eta_seconds?: number;
  current_step?: string;
  error_message?: string;
}

// Webhook types
export interface PaystackWebhook {
  event: string;
  data: {
    reference: string;
    amount: number;
    customer: {
      email: string;
      customer_code: string;
    };
    status: string;
    metadata?: Record<string, any>;
  };
}

// Configuration types
export interface AppConfig {
  supabase: {
    url: string;
    anon_key: string;
  };
  backend: {
    url: string;
    timeout: number;
  };
  paystack: {
    public_key: string;
  };
  features: {
    script_generation: boolean;
    advanced_editing: boolean;
    analytics: boolean;
    collaboration: boolean;
  };
  limits: Record<SubscriptionTier, {
    daily_clips: number;
    max_video_length: number;
    max_file_size: number;
    available_resolutions: string[];
    features: string[];
  }>;
}

// Error types
export interface AppError {
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}

// Form validation schemas (for frontend)
export interface CreateVideoForm {
  title?: string;
  description?: string;
  source_type: SourceType;
  source_url?: string;
  file?: File;
}

export interface CreateScriptForm {
  title: string;
  platform_optimization: Platform;
  custom_prompt?: string;
  include_timestamps: boolean;
}

export interface BrandAssetForm {
  name: string;
  type: BrandAssetType;
  file: File;
  is_default: boolean;
  position: Position;
}

export interface TemplateForm {
  name: string;
  description?: string;
  category: string;
  type: TemplateType;
  config: TemplateConfig;
  tags: string[];
}

// Subscription management
export interface SubscriptionDetails {
  tier: SubscriptionTier;
  status: SubscriptionStatus;
  current_period_start?: string;
  current_period_end?: string;
  cancel_at_period_end?: boolean;
  paystack_subscription_code?: string;
}

export interface UsageDetails {
  current_period: {
    clips_created: number;
    videos_uploaded: number;
    scripts_generated: number;
    storage_used_mb: number;
  };
  limits: {
    daily_clips: number;
    monthly_clips: number;
    max_video_length: number;
    max_storage_mb: number;
  };
  remaining: {
    clips_today: number;
    storage_mb: number;
  };
}
