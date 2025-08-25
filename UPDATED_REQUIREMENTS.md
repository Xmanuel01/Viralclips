# Viral Clips Generator - Updated Requirements

You are my coding partner. I want you to help me build a full-stack web app that automatically converts long videos (YouTube links or uploaded files) into short, viral-ready clips similar to 2Shorts.ai and OpusClip, but free/freemium.

## Core Requirements

### 1. Video Ingestion
- Upload local video files (MP4, MOV, AVI, MKV support)
- Accept YouTube video links (extract with pytube or yt-dlp)
- Accept Vimeo, Twitch, and other platform links
- Save videos in Supabase storage (free tier)
- Video preprocessing and format validation
- Progress tracking for large uploads

### 2. Transcription + Subtitles
- Use `faster-whisper` for fast CPU transcription
- Optionally integrate WhisperX for word-level timestamps and speaker diarization
- Multi-language transcription support (English, Spanish, French, German, etc.)
- Generate accurate subtitles (SRT + hardcoded captions with FFmpeg)
- **Animated subtitle styles:**
  - Word-by-word highlight
  - Typewriter effect
  - Bounce animations
  - Custom fonts and colors
  - Emoji integration
- Subtitle positioning options (top, middle, bottom)
- Custom subtitle templates and presets

### 3. **AI Script Writing & Enhancement** ⭐ NEW FEATURE
- **Script generation from video content:**
  - Extract key talking points from transcription
  - Generate engaging hooks and CTAs
  - Create platform-specific scripts (TikTok vs YouTube Shorts style)
  - Support for 1+ hour video script processing
- **Script editor with:**
  - Rich text formatting
  - Highlight important phrases
  - Add custom intros/outros
  - Insert transition phrases
  - Sentiment analysis and engagement scoring
- **Script-to-video alignment:**
  - Match script sections to video timestamps
  - Auto-generate clips based on script structure
  - Custom pacing control

### 4. Highlight & Clip Detection
- **Enhanced detection algorithms:**
  - `PySceneDetect` for scene changes
  - `KeyBERT` + HuggingFace Transformers (summarization + keyword spotting)
  - Sentiment analysis for emotional peaks
  - Volume/audio intensity analysis
  - Face detection and emotion recognition
- **Smart ranking system:**
  - Viral potential scoring algorithm
  - Engagement prediction based on content type
  - Platform-specific optimization (TikTok vs Instagram vs YouTube)
- **Custom highlight creation:**
  - Manual timestamp selection
  - Keyword-based clip generation
  - Topic-based segmentation
- Automatically cut top 3–10 highlights per video (configurable)

### 5. **Advanced Video Editing** ⭐ ENHANCED
- **Core editing with FFmpeg + MoviePy:**
  - Cutting & merging with frame-perfect precision
  - Adding animated subtitles with custom styling
  - Branding overlays (logo, watermark, lower thirds)
  - Background music integration
  - Sound effect library
- **Multi-aspect ratio export:**
  - 9:16 vertical (TikTok/Reels)
  - 1:1 square (Instagram)
  - 16:9 horizontal (YouTube)
  - Custom dimensions
- **Smart cropping with OpenCV + MediaPipe:**
  - Subject tracking (keep speaker centered)
  - Face detection and auto-framing
  - Object tracking for product videos
  - Motion-based cropping
- **Advanced features:**
  - Green screen removal
  - Background replacement
  - Color grading presets
  - Zoom and pan effects
  - Transition effects between clips
- **Template system:**
  - Pre-built video templates
  - Custom brand templates
  - Industry-specific templates (fitness, business, education)

### 6. **Export & Publishing** ⭐ UPDATED PRICING
- **Free Tier (with ads):**
  - 480p export with watermark
  - 2 clips/day limit
  - 30-second ad viewing required per clip
  - Basic subtitle styles only
  - Single aspect ratio (9:16 only)
- **Basic Plan ($7/month):** ⭐ UPDATED
  - 720p export, small watermark
  - 10 clips/day
  - All subtitle animations
  - Multi-aspect ratio export
  - Basic templates
- **Pro Plan ($19/month):** ⭐ UPDATED
  - 1080p export, no watermark
  - 50 clips/day
  - Batch processing (up to 5 videos)
  - All advanced editing features
  - Priority processing
  - API access
- **Agency Plan ($49/month):** ⭐ NEW
  - 4K export capability
  - Unlimited clips
  - White-label options
  - Team collaboration features
  - Custom branding removal
  - Dedicated support
- **Lifetime Options:** ⭐ UPDATED
  - Early Bird Lifetime Basic: $149 (limited time)
  - Lifetime Pro: $299 (limited quantity)
- **Downloads via Supabase storage with expiration links**
- **Future integrations:**
  - Direct publish to TikTok, Instagram Reels, YouTube Shorts
  - Scheduling and auto-posting
  - Analytics and performance tracking

### 7. **Backend Architecture**
- **FastAPI server with:**
  - JWT authentication
  - Rate limiting
  - Request/response logging
  - Error handling and monitoring
- **Enhanced task queue:**
  - Celery or RQ with Upstash Redis free tier
  - Priority queue for paid users
  - Progress tracking and ETA calculation
  - Retry logic for failed jobs
- **API Endpoints:**
  - `/upload` - File/URL upload
  - `/transcribe` - Audio transcription
  - `/highlight` - Clip detection
  - `/script/generate` - AI script generation ⭐ NEW
  - `/script/edit` - Script editing ⭐ NEW
  - `/export` - Video processing and export
  - `/jobs/status` - Real-time job monitoring
  - `/templates` - Template management ⭐ NEW
  - `/analytics` - Usage analytics ⭐ NEW

### 8. **Enhanced Frontend (Next.js)** ⭐ MAJOR UPDATES
- **Modern UI/UX with TailwindCSS:**
  - Dark/light mode toggle
  - Mobile-responsive design
  - Drag-and-drop upload interface
  - Real-time progress indicators
  - Toast notifications
- **Dashboard features:**
  - **Video upload with preview**
  - **Script editor with live preview** ⭐ NEW
  - **Template gallery** ⭐ NEW
  - **Subtitle style customizer** ⭐ NEW
  - Transcribed text with highlight markers
  - Clip timeline editor
  - Batch processing queue
  - Export history and downloads
  - **Usage analytics dashboard** ⭐ NEW
  - **Billing and subscription management** ⭐ ENHANCED
- **Advanced editor interface:**
  - Video timeline with waveform visualization
  - Clip trimming with precision controls
  - Real-time preview window
  - Subtitle overlay editor
  - Brand asset manager
- **Onboarding flow:**
  - Interactive tutorial
  - Sample video processing
  - Feature highlights tour

### 9. **Database & Storage** ⭐ ENHANCED SCHEMA
- **Supabase Postgres DB:**
  - Users table (auth, subscription, usage limits)
  - Videos table (metadata, processing status)
  - Clips table (generated clips, settings)
  - Scripts table (AI-generated and user-edited) ⭐ NEW
  - Templates table (custom and default templates) ⭐ NEW
  - Analytics table (usage tracking, performance) ⭐ NEW
  - Jobs table (processing queue, status)
  - Billing table (payments, invoices)
- **Supabase storage buckets:**
  - Raw video uploads
  - Processed clips
  - Thumbnail images
  - Template assets ⭐ NEW
- **Redis (Upstash) for:**
  - Background job queue
  - Session caching
  - Rate limiting counters

### 10. **Payments & Monetization** ⭐ ENHANCED
- **Paystack integration with:**
  - Subscription management
  - Usage-based billing
  - Automatic renewal handling
  - Failed payment recovery
  - Invoice generation
- **Pricing tiers** (as detailed in Export section)
- **Monetization strategies:**
  - Video ads for free users (30s per clip)
  - Freemium subscription model
  - One-time lifetime purchase options
  - Referral program (earn extra clips)
  - White-label licensing for agencies
- **Analytics integration:**
  - Revenue tracking
  - User behavior analysis
  - Conversion funnel optimization

### 11. **Additional Features** ⭐ NEW SECTION
- **AI-powered features:**
  - Content suggestions based on trending topics
  - Hashtag generation
  - Thumbnail generation with A/B testing
  - Voice cloning for consistent narration
- **Collaboration tools:**
  - Team workspaces
  - Comment system on clips
  - Approval workflows
  - Asset sharing
- **Analytics & insights:**
  - Clip performance tracking
  - Audience engagement metrics
  - Export format analytics
  - Processing time optimization
- **API for developers:**
  - RESTful API with documentation
  - Webhook support for integrations
  - SDK for popular languages
  - Rate limiting and authentication

## Tech Stack (Open-source/Free Resources)
- **Frontend:** Next.js 14, TailwindCSS, Framer Motion, React Hook Form
- **Backend:** FastAPI (Python), Pydantic, SQLAlchemy
- **AI/ML:** faster-whisper, WhisperX, HuggingFace Transformers, KeyBERT, OpenAI GPT (for script generation)
- **Video processing:** FFmpeg, MoviePy, OpenCV, MediaPipe
- **Face/object tracking:** YOLO, MediaPipe, OpenCV
- **Database/Auth/Storage:** Supabase (Postgres + Auth + Storage)
- **Job queue:** Celery + Upstash Redis
- **Payments:** Paystack
- **Hosting:**
  - Vercel (frontend)
  - Render/Railway/Fly.io (backend + workers)
  - Supabase (database + storage)
  - Upstash (Redis)

## Enhanced Deliverables
- **Complete repo structure:**
  ```
  /viral-clips-app
  ├── /frontend (Next.js + Tailwind)
  │   ├── /components (reusable UI components)
  │   ├── /pages (routes and API)
  │   ├── /hooks (custom React hooks)
  │   ├── /stores (state management)
  │   └── /utils (helper functions)
  ├── /backend (FastAPI + Celery)
  │   ├── /api (route handlers)
  │   ├── /models (database models)
  │   ├── /services (business logic)
  │   ├── /tasks (background jobs)
  │   └── /utils (helper functions)
  ├── /workers (video/audio processing)
  │   ├── /processors (video processing logic)
  │   ├── /ai (ML model integrations)
  │   └── /templates (video templates)
  ├── /shared (schemas, types, constants)
  ├── /docs (API documentation)
  └── /deploy (deployment configurations)
  ```

- **Comprehensive starter code:**
  - Complete authentication flow (Supabase)
  - Full processing pipeline (upload → transcription → script generation → highlight detection → export)
  - Admin dashboard for monitoring
  - Payment integration with Paystack
  - Job queue with real-time updates
  - Template system implementation
  - Analytics tracking setup

## Updated Goals
- **Phase 1 (MVP):** Basic video-to-clips functionality with free tier
- **Phase 2:** Advanced editing, script generation, and paid tiers
- **Phase 3:** Direct social media publishing and analytics
- **Phase 4:** White-label solutions and enterprise features

**Primary objective:** Build on entirely **free tiers** and **open-source tools**, get first 1000 users within 3 months, achieve $1000 MRR within 6 months through freemium model + strategic lifetime deals.
