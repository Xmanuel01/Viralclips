-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types
CREATE TYPE subscription_tier AS ENUM ('free', 'premium', 'lifetime');
CREATE TYPE video_source AS ENUM ('upload', 'youtube');
CREATE TYPE job_status AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE export_format AS ENUM ('9:16', '1:1', '16:9');

-- Users table (extends Supabase auth.users)
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    subscription_tier subscription_tier DEFAULT 'free',
    clips_used_today INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Videos table
CREATE TABLE public.videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    source video_source NOT NULL,
    source_url TEXT,
    file_path TEXT NOT NULL,
    duration FLOAT DEFAULT 0,
    file_size BIGINT DEFAULT 0,
    status job_status DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Transcripts table
CREATE TABLE public.transcripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID NOT NULL REFERENCES public.videos(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    segments JSONB NOT NULL,
    language TEXT DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Highlights table
CREATE TABLE public.highlights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID NOT NULL REFERENCES public.videos(id) ON DELETE CASCADE,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    score FLOAT NOT NULL,
    keywords TEXT[] DEFAULT '{}',
    title TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Clips table
CREATE TABLE public.clips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID NOT NULL REFERENCES public.videos(id) ON DELETE CASCADE,
    highlight_id UUID NOT NULL REFERENCES public.highlights(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    file_path TEXT NOT NULL,
    export_format export_format NOT NULL,
    resolution TEXT NOT NULL,
    has_watermark BOOLEAN DEFAULT true,
    file_size BIGINT DEFAULT 0,
    status job_status DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Jobs table
CREATE TABLE public.jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    job_type TEXT NOT NULL,
    status job_status DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_videos_user_id ON public.videos(user_id);
CREATE INDEX idx_videos_status ON public.videos(status);
CREATE INDEX idx_transcripts_video_id ON public.transcripts(video_id);
CREATE INDEX idx_highlights_video_id ON public.highlights(video_id);
CREATE INDEX idx_highlights_score ON public.highlights(score DESC);
CREATE INDEX idx_clips_user_id ON public.clips(user_id);
CREATE INDEX idx_clips_status ON public.clips(status);
CREATE INDEX idx_jobs_user_id ON public.jobs(user_id);
CREATE INDEX idx_jobs_status ON public.jobs(status);

-- Row Level Security (RLS) policies
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transcripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.highlights ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clips ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own data" ON public.users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own data" ON public.users FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own videos" ON public.videos FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own videos" ON public.videos FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own videos" ON public.videos FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own transcripts" ON public.transcripts FOR SELECT USING (
    auth.uid() = (SELECT user_id FROM public.videos WHERE id = video_id)
);
CREATE POLICY "Users can insert own transcripts" ON public.transcripts FOR INSERT WITH CHECK (
    auth.uid() = (SELECT user_id FROM public.videos WHERE id = video_id)
);

CREATE POLICY "Users can view own highlights" ON public.highlights FOR SELECT USING (
    auth.uid() = (SELECT user_id FROM public.videos WHERE id = video_id)
);
CREATE POLICY "Users can insert own highlights" ON public.highlights FOR INSERT WITH CHECK (
    auth.uid() = (SELECT user_id FROM public.videos WHERE id = video_id)
);

CREATE POLICY "Users can view own clips" ON public.clips FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own clips" ON public.clips FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own clips" ON public.clips FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own jobs" ON public.jobs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own jobs" ON public.jobs FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own jobs" ON public.jobs FOR UPDATE USING (auth.uid() = user_id);

-- Function to automatically create user record
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email)
    VALUES (NEW.id, NEW.email);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create user record on signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to reset daily clip count
CREATE OR REPLACE FUNCTION reset_daily_clips()
RETURNS void AS $$
BEGIN
    UPDATE public.users SET clips_used_today = 0;
END;
$$ LANGUAGE plpgsql;

-- Storage bucket for videos (run in Supabase dashboard)
-- INSERT INTO storage.buckets (id, name, public) VALUES ('videos', 'videos', true);

-- Storage policies for videos bucket
-- CREATE POLICY "Users can upload own videos" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'videos' AND auth.uid()::text = (storage.foldername(name))[1]);
-- CREATE POLICY "Users can view own videos" ON storage.objects FOR SELECT USING (bucket_id = 'videos' AND auth.uid()::text = (storage.foldername(name))[1]);
-- CREATE POLICY "Users can delete own videos" ON storage.objects FOR DELETE USING (bucket_id = 'videos' AND auth.uid()::text = (storage.foldername(name))[1]);
