-- Enhanced Supabase Database Schema for Viral Clips App
-- This schema includes all new features: scripting, templates, analytics, enhanced billing

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (enhanced)
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE,
    full_name VARCHAR(255),
    avatar_url TEXT,
    subscription_tier VARCHAR(20) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'basic', 'pro', 'agency', 'lifetime_basic', 'lifetime_pro')),
    subscription_status VARCHAR(20) DEFAULT 'active' CHECK (subscription_status IN ('active', 'cancelled', 'expired', 'trial')),
    subscription_starts_at TIMESTAMP WITH TIME ZONE,
    subscription_ends_at TIMESTAMP WITH TIME ZONE,
    daily_clips_used INTEGER DEFAULT 0,
    daily_clips_limit INTEGER DEFAULT 2,
    total_clips_created INTEGER DEFAULT 0,
    credits_remaining INTEGER DEFAULT 0,
    paystack_customer_id VARCHAR(255),
    onboarding_completed BOOLEAN DEFAULT false,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Videos table (enhanced)
CREATE TABLE IF NOT EXISTS videos (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    description TEXT,
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('upload', 'youtube', 'vimeo', 'twitch')),
    source_url TEXT,
    file_path TEXT,
    file_size BIGINT,
    duration_seconds INTEGER,
    format VARCHAR(20),
    resolution VARCHAR(20),
    fps INTEGER,
    thumbnail_url TEXT,
    processing_status VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    processing_progress INTEGER DEFAULT 0,
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Scripts table (NEW)
CREATE TABLE IF NOT EXISTS scripts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    platform_optimization VARCHAR(20) DEFAULT 'general' CHECK (platform_optimization IN ('general', 'tiktok', 'youtube', 'instagram', 'twitter')),
    engagement_score DECIMAL(3,2) DEFAULT 0.0,
    sentiment_score DECIMAL(3,2) DEFAULT 0.0,
    keywords TEXT[],
    hashtags TEXT[],
    hooks TEXT[],
    ctas TEXT[],
    timestamps JSONB DEFAULT '[]', -- Array of {start_time, end_time, section_type, content}
    is_ai_generated BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Templates table (NEW)
CREATE TABLE IF NOT EXISTS templates (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, -- NULL for system templates
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- 'business', 'fitness', 'education', 'entertainment', etc.
    type VARCHAR(20) NOT NULL CHECK (type IN ('video', 'subtitle', 'brand')),
    is_premium BOOLEAN DEFAULT false,
    is_system_template BOOLEAN DEFAULT false,
    config JSONB NOT NULL, -- Template configuration (colors, fonts, animations, etc.)
    preview_url TEXT,
    usage_count INTEGER DEFAULT 0,
    rating DECIMAL(2,1) DEFAULT 0.0,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Clips table (enhanced)
CREATE TABLE IF NOT EXISTS clips (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    script_id UUID REFERENCES scripts(id) ON DELETE SET NULL,
    template_id UUID REFERENCES templates(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    description TEXT,
    start_time DECIMAL(10,3) NOT NULL,
    end_time DECIMAL(10,3) NOT NULL,
    duration_seconds DECIMAL(10,3) GENERATED ALWAYS AS (end_time - start_time) STORED,
    highlight_score DECIMAL(3,2) DEFAULT 0.0,
    viral_potential_score DECIMAL(3,2) DEFAULT 0.0,
    aspect_ratio VARCHAR(10) DEFAULT '9:16' CHECK (aspect_ratio IN ('9:16', '1:1', '16:9', 'custom')),
    resolution VARCHAR(20) DEFAULT '720p',
    export_status VARCHAR(20) DEFAULT 'pending' CHECK (export_status IN ('pending', 'processing', 'completed', 'failed')),
    export_progress INTEGER DEFAULT 0,
    file_path TEXT,
    file_size BIGINT,
    download_url TEXT,
    download_expires_at TIMESTAMP WITH TIME ZONE,
    subtitle_config JSONB DEFAULT '{}', -- Subtitle styling configuration
    editing_config JSONB DEFAULT '{}', -- Video editing configuration
    branding_config JSONB DEFAULT '{}', -- Brand assets configuration
    export_settings JSONB DEFAULT '{}', -- Export quality, watermark, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analytics table (NEW)
CREATE TABLE IF NOT EXISTS analytics (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    clip_id UUID REFERENCES clips(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'video_upload', 'clip_created', 'clip_downloaded', 'script_generated', etc.
    event_data JSONB DEFAULT '{}',
    processing_time_ms INTEGER,
    file_size_bytes BIGINT,
    user_agent TEXT,
    ip_address INET,
    country_code VARCHAR(2),
    device_type VARCHAR(20),
    browser VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Jobs table (enhanced)
CREATE TABLE IF NOT EXISTS jobs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL, -- 'transcription', 'highlight_detection', 'script_generation', 'clip_export'
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 0, -- Higher for paid users
    progress INTEGER DEFAULT 0,
    eta_seconds INTEGER,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    result_data JSONB DEFAULT '{}',
    task_id VARCHAR(255), -- Celery task ID
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Billing table (NEW)
CREATE TABLE IF NOT EXISTS billing (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    paystack_transaction_id VARCHAR(255) UNIQUE,
    paystack_reference VARCHAR(255) UNIQUE,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_method VARCHAR(50),
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('subscription', 'one_time', 'refund')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'successful', 'failed', 'refunded')),
    description TEXT,
    invoice_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Brand Assets table (NEW)
CREATE TABLE IF NOT EXISTS brand_assets (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('logo', 'watermark', 'intro', 'outro', 'background')),
    file_path TEXT NOT NULL,
    file_size BIGINT,
    dimensions VARCHAR(20), -- e.g., "1920x1080"
    format VARCHAR(10), -- png, jpg, mp4, etc.
    is_default BOOLEAN DEFAULT false,
    position JSONB DEFAULT '{}', -- x, y, width, height, opacity
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Transcriptions table (enhanced)
CREATE TABLE IF NOT EXISTS transcriptions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    language VARCHAR(10) DEFAULT 'en',
    model_used VARCHAR(50), -- 'faster-whisper', 'whisperx'
    confidence_score DECIMAL(3,2),
    full_text TEXT NOT NULL,
    segments JSONB NOT NULL, -- Array of {start, end, text, confidence, speaker_id}
    speakers JSONB DEFAULT '[]', -- Speaker diarization data
    keywords JSONB DEFAULT '[]', -- Extracted keywords with scores
    sentiment_analysis JSONB DEFAULT '{}', -- Overall sentiment scores
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Usage Tracking table (NEW)
CREATE TABLE IF NOT EXISTS usage_tracking (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    clips_created INTEGER DEFAULT 0,
    videos_uploaded INTEGER DEFAULT 0,
    scripts_generated INTEGER DEFAULT 0,
    processing_minutes INTEGER DEFAULT 0,
    storage_used_mb INTEGER DEFAULT 0,
    api_calls INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- Referrals table (NEW)
CREATE TABLE IF NOT EXISTS referrals (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    referrer_id UUID REFERENCES users(id) ON DELETE CASCADE,
    referee_id UUID REFERENCES users(id) ON DELETE CASCADE,
    referral_code VARCHAR(20) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'cancelled')),
    reward_type VARCHAR(20) DEFAULT 'credits' CHECK (reward_type IN ('credits', 'discount', 'free_month')),
    reward_amount INTEGER DEFAULT 5, -- 5 extra clips or $5 discount
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id);
CREATE INDEX IF NOT EXISTS idx_videos_processing_status ON videos(processing_status);
CREATE INDEX IF NOT EXISTS idx_clips_video_id ON clips(video_id);
CREATE INDEX IF NOT EXISTS idx_clips_user_id ON clips(user_id);
CREATE INDEX IF NOT EXISTS idx_scripts_video_id ON scripts(video_id);
CREATE INDEX IF NOT EXISTS idx_scripts_user_id ON scripts(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_user_id ON analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_created_at ON analytics(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_templates_category ON templates(category);
CREATE INDEX IF NOT EXISTS idx_templates_type ON templates(type);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_user_date ON usage_tracking(user_id, date);
CREATE INDEX IF NOT EXISTS idx_billing_user_id ON billing(user_id);
CREATE INDEX IF NOT EXISTS idx_brand_assets_user_id ON brand_assets(user_id);

-- Row Level Security (RLS) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE scripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE clips ENABLE ROW LEVEL SECURITY;
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing ENABLE ROW LEVEL SECURITY;
ALTER TABLE brand_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE transcriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE referrals ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own data" ON users FOR ALL USING (auth.uid() = id);
CREATE POLICY "Users can view own videos" ON videos FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own scripts" ON scripts FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own clips" ON clips FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view templates" ON templates FOR SELECT USING (is_system_template = true OR auth.uid() = user_id);
CREATE POLICY "Users can manage own templates" ON templates FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own analytics" ON analytics FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own jobs" ON jobs FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own billing" ON billing FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own brand assets" ON brand_assets FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own transcriptions" ON transcriptions FOR SELECT USING (auth.uid() = (SELECT user_id FROM videos WHERE id = video_id));
CREATE POLICY "Users can view own usage" ON usage_tracking FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own referrals" ON referrals FOR ALL USING (auth.uid() = referrer_id OR auth.uid() = referee_id);

-- Functions for automatic timestamping
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_videos_updated_at BEFORE UPDATE ON videos FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_scripts_updated_at BEFORE UPDATE ON scripts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_clips_updated_at BEFORE UPDATE ON clips FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_billing_updated_at BEFORE UPDATE ON billing FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_brand_assets_updated_at BEFORE UPDATE ON brand_assets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to reset daily clips usage
CREATE OR REPLACE FUNCTION reset_daily_clips()
RETURNS void AS $$
BEGIN
    UPDATE users SET daily_clips_used = 0;
END;
$$ LANGUAGE plpgsql;

-- Insert default system templates
INSERT INTO templates (name, description, category, type, is_system_template, config) VALUES
('Modern Minimal', 'Clean, modern subtitle style with minimal animations', 'general', 'subtitle', true, '{"font": "Inter", "size": 24, "color": "#FFFFFF", "background": "rgba(0,0,0,0.8)", "animation": "fade", "position": "bottom"}'),
('Vibrant Pop', 'Colorful, energetic style perfect for entertainment content', 'entertainment', 'subtitle', true, '{"font": "Montserrat", "size": 28, "color": "#FF6B6B", "background": "rgba(255,255,255,0.9)", "animation": "bounce", "position": "center"}'),
('Business Professional', 'Professional look for corporate and business content', 'business', 'subtitle', true, '{"font": "Roboto", "size": 22, "color": "#2C3E50", "background": "rgba(255,255,255,0.95)", "animation": "slide", "position": "bottom"}'),
('Fitness Energy', 'High-energy style for fitness and sports content', 'fitness', 'subtitle', true, '{"font": "Oswald", "size": 26, "color": "#00D4AA", "background": "rgba(0,0,0,0.7)", "animation": "pulse", "position": "top"}'),
('Education Focus', 'Clear, readable style for educational content', 'education', 'subtitle', true, '{"font": "Source Sans Pro", "size": 24, "color": "#34495E", "background": "rgba(255,255,255,0.9)", "animation": "typewriter", "position": "bottom"}');
