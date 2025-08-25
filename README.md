# ViralClips.ai - AI-Powered Video Clipping Tool

Transform long videos into viral-ready clips automatically using AI. Similar to 2Shorts.ai and OpusClip, but built with 100% free and open-source tools.

## 🚀 Features

- **Video Ingestion**: Upload files or YouTube links
- **AI Transcription**: Fast CPU transcription with faster-whisper
- **Smart Highlight Detection**: Find viral moments using NLP and scene detection
- **Multi-Format Export**: 9:16 (TikTok), 1:1 (Instagram), 16:9 (YouTube)
- **Animated Subtitles**: Auto-generated captions
- **Freemium Model**: Free tier with premium upgrades

## 🏗️ Architecture

```
viral-clips-app/
├── frontend/          # Next.js + TailwindCSS
├── backend/           # FastAPI + Python
├── workers/           # Background processing
├── shared/            # Common schemas & utilities
└── database_schema.sql
```

## 🛠️ Tech Stack

### Frontend
- **Next.js 15** - React framework
- **TailwindCSS** - Styling
- **Supabase Auth** - Authentication
- **React Dropzone** - File uploads
- **Framer Motion** - Animations

### Backend
- **FastAPI** - Python API framework
- **RQ + Redis** - Job queue (Upstash free tier)
- **Supabase** - Database & storage

### AI/Video Processing
- **faster-whisper** - CPU transcription
- **PySceneDetect** - Scene change detection
- **KeyBERT + Transformers** - Keyword extraction & sentiment
- **MoviePy + FFmpeg** - Video editing
- **OpenCV** - Video analysis

## 📋 Prerequisites

### Required Software
1. **Python 3.9+**
2. **Node.js 18+**
3. **FFmpeg** - For video processing
4. **Git**

### Free Accounts Needed
1. **Supabase** (free tier) - Database & storage
2. **Upstash Redis** (free tier) - Job queue
3. **Vercel** (free tier) - Frontend hosting
4. **Render/Fly.io** (free tier) - Backend hosting

## 🚀 Quick Setup

### 1. Clone and Setup

```bash
git clone <your-repo>
cd viral-clips-app

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies  
cd ../frontend
npm install
```

### 2. Supabase Setup

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to SQL Editor and run the `database_schema.sql` file
3. Go to Storage → Create new bucket named "videos" (public)
4. Copy your project URL and anon key

### 3. Redis Setup (Upstash)

1. Create free account at [upstash.com](https://upstash.com)
2. Create new Redis database
3. Copy the Redis URL

### 4. Environment Variables

Create `.env` in the root directory:

```bash
# Copy from .env.example
cp .env.example .env

# Fill in your credentials
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
REDIS_URL=your_upstash_redis_url
```

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 5. Install FFmpeg

**Windows:**
```bash
# Using chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

## 🏃‍♂️ Running the Application

### Development Mode

**Terminal 1 - Backend API:**
```bash
cd backend
python main.py
# API will run on http://localhost:8000
```

**Terminal 2 - Worker Process:**
```bash
cd workers
python worker.py
# Worker will process background jobs
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
# Frontend will run on http://localhost:3000
```

### Production Mode

See deployment section below.

## 🎯 Usage Flow

1. **Sign Up**: Create account with email/password or OAuth
2. **Upload Video**: Drag & drop file or paste YouTube URL
3. **Auto Processing**: AI transcribes and finds highlights
4. **Review Highlights**: See top 5 viral moments detected
5. **Export Clips**: Choose format (9:16, 1:1, 16:9) and download

## 💰 Monetization

### Free Tier
- 3 clips per day
- 720p export
- Watermarked videos
- 100MB file limit

### Premium ($15/month)
- 20 clips per day
- 1080p export
- No watermark
- 1GB file limit
- Batch processing

### Lifetime ($99)
- All premium features
- One-time payment

## 🔧 Configuration

### AI Models

The app uses these models by default (all free):
- **Whisper**: `base` model (good speed/quality balance)
- **Sentiment**: `cardiffnlp/twitter-roberta-base-sentiment-latest`
- **Summarization**: `facebook/bart-large-cnn`
- **Keywords**: KeyBERT with sentence-transformers

### Video Processing

- **Scene Detection**: Content detector with 30.0 threshold
- **Clip Length**: 15-60 seconds optimal
- **Formats**: Vertical (9:16), Square (1:1), Horizontal (16:9)
- **Quality**: 720p (free), 1080p (premium)

## 🚀 Deployment

### Frontend (Vercel)

1. Connect GitHub repo to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push

### Backend (Render)

1. Create new Web Service on Render
2. Connect GitHub repo
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python main.py`
5. Add environment variables

### Workers (Render Background Worker)

1. Create new Background Worker on Render
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `python workers/worker.py`
4. Add environment variables

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📊 Monitoring

- **Supabase**: Database monitoring, auth logs
- **Upstash**: Redis queue monitoring
- **Render/Vercel**: Application logs and metrics

## 🔒 Security

- Row Level Security (RLS) enabled on all tables
- JWT-based authentication via Supabase
- File upload validation and size limits
- Rate limiting on API endpoints

## 🛠️ Development

### Adding New Features

1. **New API Endpoint**: Add to `backend/main.py`
2. **New Worker Function**: Add to appropriate worker file
3. **New Frontend Component**: Add to `frontend/src/components/`
4. **Database Changes**: Update `database_schema.sql`

### Code Style

- **Python**: Black formatter, flake8 linting
- **TypeScript**: ESLint, Prettier
- **Git**: Conventional commits

## 🐛 Troubleshooting

### Common Issues

**1. FFmpeg not found**
```bash
# Install FFmpeg (see installation section)
# Verify installation
ffmpeg -version
```

**2. Redis connection failed**
```bash
# Check Redis URL in .env
# Verify Upstash Redis is running
```

**3. Supabase authentication failed**
```bash
# Verify SUPABASE_URL and SUPABASE_ANON_KEY
# Check if user exists in auth.users table
```

**4. Video processing stuck**
```bash
# Check worker logs
# Restart worker process
# Check Redis queue status
```

**5. File upload fails**
```bash
# Check file size limits
# Verify video format is supported
# Check Supabase storage permissions
```

## 📈 Scaling

### Free Tier Limits
- **Supabase**: 500MB database, 1GB storage
- **Upstash Redis**: 10K commands/day
- **Vercel**: 100GB bandwidth
- **Render**: 750 hours/month

### Scaling Options
1. **Horizontal scaling**: Multiple worker instances
2. **Database**: Upgrade Supabase plan
3. **Storage**: Add AWS S3 or Cloudflare R2
4. **CDN**: Add Cloudflare for video delivery

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **GitHub Issues**: Bug reports and feature requests
- **Discord**: Community support (link coming soon)
- **Email**: support@viralclips.ai

---

Built with ❤️ for content creators who want to go viral!