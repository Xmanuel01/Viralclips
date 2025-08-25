# 🚀 Deployment Guide

This guide walks you through deploying ViralClips.ai to production using free tiers of various services.

## 📋 Prerequisites

- GitHub account (for code hosting)
- Supabase account (database & storage)
- Upstash account (Redis queue)
- Vercel account (frontend hosting)
- Render account (backend hosting)

## 🗄️ Database Setup (Supabase)

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create new project
2. Wait for project initialization (2-3 minutes)
3. Note down your project URL and anon key

### 2. Setup Database Schema

1. Go to SQL Editor in Supabase dashboard
2. Copy and paste contents of `database_schema.sql`
3. Run the script to create all tables and policies

### 3. Setup Storage

1. Go to Storage in Supabase dashboard
2. Create new bucket named "videos"
3. Make it public
4. Set up storage policies (included in schema)

### 4. Configure Authentication

1. Go to Authentication → Settings
2. Enable email sign-ups
3. Optionally enable OAuth providers (Google, GitHub)
4. Set redirect URLs for your domains

## 🔗 Redis Setup (Upstash)

### 1. Create Redis Database

1. Go to [upstash.com](https://upstash.com)
2. Create new Redis database (free tier)
3. Select region closest to your backend
4. Copy the Redis URL

### 2. Configure Access

- Note down the Redis URL (format: `redis://default:password@host:port`)
- This will be used in environment variables

## 🎨 Frontend Deployment (Vercel)

### 1. Prepare Repository

```bash
# Push your code to GitHub
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Deploy to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click "Import Project" and select your repository
3. Set root directory to `frontend`
4. Configure environment variables:

```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=https://your-backend-url.render.com
```

5. Deploy!

### 3. Custom Domain (Optional)

1. Add your custom domain in Vercel dashboard
2. Update DNS records as instructed
3. SSL certificate is automatic

## ⚙️ Backend Deployment (Render)

### 1. Create Web Service

1. Go to [render.com](https://render.com) and create account
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure service:

```
Name: viral-clips-api
Region: Choose closest to your users
Branch: main
Root Directory: backend
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: python main.py
```

### 2. Environment Variables

Add these in Render dashboard:

```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
REDIS_URL=your_upstash_redis_url
```

### 3. Deploy

- Render will automatically build and deploy
- Note your service URL (e.g., `https://your-app.onrender.com`)

## 🔄 Worker Deployment (Render Background Worker)

### 1. Create Background Worker

1. In Render dashboard, click "New +" → "Background Worker"
2. Connect same GitHub repository
3. Configure worker:

```
Name: viral-clips-worker
Region: Same as your web service
Branch: main
Root Directory: .
Runtime: Python 3
Build Command: pip install -r backend/requirements.txt
Start Command: python workers/worker.py
```

### 2. Environment Variables

Same environment variables as backend:

```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
REDIS_URL=your_upstash_redis_url
```

### 3. Scaling

- Free tier: 1 worker instance
- For more throughput, upgrade to paid plan for multiple workers

## 🔒 Security Configuration

### 1. Update CORS Origins

In `backend/main.py`, update allowed origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Development
        "https://your-app.vercel.app",  # Your Vercel domain
        "https://your-custom-domain.com",  # Custom domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Environment Security

- Use Render/Vercel environment variable features
- Never commit `.env` files
- Rotate keys regularly

## 📊 Monitoring & Analytics

### 1. Application Monitoring

**Render:**
- Built-in logs and metrics
- Set up alerts for service downtime

**Vercel:**
- Analytics dashboard
- Function performance monitoring

### 2. Database Monitoring

**Supabase:**
- Database usage metrics
- Auth analytics
- Storage usage

### 3. Queue Monitoring

**Upstash:**
- Redis metrics
- Command usage tracking

## 💳 Payment Integration (Stripe)

### 1. Setup Stripe

1. Create Stripe account
2. Get API keys (test and live)
3. Create products and pricing plans

### 2. Configure Webhooks

1. Set webhook endpoint: `https://your-backend.render.com/stripe/webhook`
2. Listen for events: `invoice.paid`, `customer.subscription.deleted`

### 3. Environment Variables

Add to backend:

```
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## 📈 Scaling Considerations

### Free Tier Limits

| Service | Limit | Upgrade Path |
|---------|-------|--------------|
| Supabase | 500MB DB, 1GB storage | $25/month for Pro |
| Upstash Redis | 10K commands/day | $0.2 per 100K commands |
| Vercel | 100GB bandwidth | $20/month for Pro |
| Render | 750 hours/month | $7/month for paid |

### Performance Optimization

1. **Database**:
   - Use indexes (already included)
   - Enable connection pooling
   - Cache frequent queries

2. **Video Processing**:
   - Queue high-priority jobs
   - Use smaller Whisper models for speed
   - Implement video preprocessing

3. **Storage**:
   - Compress videos before storage
   - Use CDN for clip delivery
   - Implement cleanup jobs

## 🚨 Troubleshooting

### Common Deployment Issues

**1. Build Failures**
```bash
# Check logs in Render/Vercel dashboard
# Verify all dependencies in requirements.txt/package.json
```

**2. Environment Variables**
```bash
# Double-check all env vars are set
# Verify URLs don't have trailing slashes
```

**3. Database Connection**
```bash
# Test Supabase connection
# Check RLS policies are correctly set
```

**4. Redis Connection**
```bash
# Verify Upstash Redis URL format
# Check Redis is accessible from your backend
```

### Health Checks

Test your deployment:

```bash
# Backend health
curl https://your-backend.render.com/

# Frontend
curl https://your-app.vercel.app

# Test video upload flow
# Check worker logs in Render dashboard
```

## 🔄 CI/CD Pipeline

### GitHub Actions (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Render
        # Render auto-deploys on push
        run: echo "Render will auto-deploy"
      - name: Deploy to Vercel
        # Vercel auto-deploys on push
        run: echo "Vercel will auto-deploy"
```

## 💡 Cost Optimization Tips

1. **Use free tiers maximally**:
   - Supabase: 500MB database
   - Upstash: 10K Redis commands
   - Vercel: 100GB bandwidth
   - Render: 750 hours

2. **Monitor usage**:
   - Set up alerts for approaching limits
   - Implement usage tracking

3. **Optimize processing**:
   - Use efficient video codecs
   - Compress before storage
   - Cache frequent operations

4. **Content delivery**:
   - Use Supabase public URLs
   - Implement proper caching headers

## 🎯 Go-Live Checklist

- [ ] Database schema deployed
- [ ] Storage bucket created and configured
- [ ] Backend deployed and healthy
- [ ] Workers running and processing jobs
- [ ] Frontend deployed and accessible
- [ ] Authentication working
- [ ] Video upload/processing flow tested
- [ ] Payment integration tested (if applicable)
- [ ] Monitoring and alerts configured
- [ ] Custom domain configured (optional)
- [ ] SSL certificates active

## 🚀 Launch Strategy

1. **Soft Launch**: Share with friends/family for testing
2. **Product Hunt**: Launch on Product Hunt
3. **Social Media**: Share on Twitter, LinkedIn
4. **Content Marketing**: Create demo videos
5. **SEO**: Optimize for "video clipping tool" keywords

## 📞 Support

- Check application logs in Render/Vercel dashboards
- Monitor Supabase real-time metrics
- Use Upstash Redis insights for queue monitoring

---

🎉 **Congratulations!** Your viral video clipping app is now live and ready to help content creators go viral!
