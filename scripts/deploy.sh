#!/bin/bash

# Production deployment script for ViralClips.ai
set -e

echo "🚀 Starting ViralClips.ai deployment..."

# Check if environment is production
if [ "$NODE_ENV" != "production" ]; then
    echo "❌ This script should only run in production environment"
    echo "Set NODE_ENV=production to continue"
    exit 1
fi

# Check required environment variables
required_vars=(
    "SUPABASE_URL"
    "SUPABASE_ANON_KEY"
    "SUPABASE_SERVICE_KEY"
    "REDIS_URL"
    "PAYSTACK_PUBLIC_KEY"
    "PAYSTACK_SECRET_KEY"
)

echo "🔍 Checking environment variables..."
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing required environment variable: $var"
        exit 1
    fi
    echo "✅ $var is set"
done

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p ssl
mkdir -p backups

# Test database connection
echo "🗄️ Testing database connection..."
python3 -c "
import os
import sys
sys.path.append('shared')
from database import Database
try:
    db = Database()
    result = db.supabase.table('users').select('id').limit(1).execute()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
"

# Test Redis connection
echo "📦 Testing Redis connection..."
python3 -c "
import redis
import os
try:
    r = redis.from_url(os.environ.get('REDIS_URL'))
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    sys.exit(1)
"

# Build Docker images
echo "🐳 Building Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Run database migrations (if any)
echo "🔄 Running database migrations..."
python3 scripts/migrate.py

# Start services
echo "🚀 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Health checks
echo "🏥 Running health checks..."

# Check backend health
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker-compose -f docker-compose.prod.yml logs backend
    exit 1
fi

# Check Redis health
if docker-compose -f docker-compose.prod.yml exec redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis health check failed"
    exit 1
fi

# Check worker processes
worker_count=$(docker-compose -f docker-compose.prod.yml ps worker | grep -c "Up")
if [ "$worker_count" -gt 0 ]; then
    echo "✅ Workers are running ($worker_count instances)"
else
    echo "❌ No workers are running"
    exit 1
fi

# Setup monitoring
echo "📊 Setting up monitoring..."
python3 scripts/setup_monitoring.py

# Create backup
echo "💾 Creating backup..."
python3 scripts/backup.py

# Setup log rotation
echo "📝 Setting up log rotation..."
sudo cp scripts/logrotate.conf /etc/logrotate.d/viralclips

echo "🎉 Deployment completed successfully!"
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "🔗 API Endpoint: http://localhost:8000"
echo "📈 Health Check: http://localhost:8000/"
echo "📋 Logs: docker-compose -f docker-compose.prod.yml logs"
echo ""
echo "🚨 Important: Don't forget to:"
echo "  1. Set up SSL certificates"
echo "  2. Configure domain DNS"
echo "  3. Set up monitoring alerts"
echo "  4. Schedule regular backups"
echo ""
echo "✅ ViralClips.ai is now running in production!"
