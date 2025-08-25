#!/usr/bin/env python3
"""
RQ Worker script for background video processing jobs.
Run this script to start processing jobs from the Redis queue.

Usage:
    python worker.py

Environment variables required:
    REDIS_URL - Redis connection URL
    SUPABASE_URL - Supabase project URL
    SUPABASE_ANON_KEY - Supabase anonymous key
"""

import os
import sys
import redis
from rq import Worker, Queue, Connection
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import worker functions
from video_processor import download_youtube_video, process_video
from transcription import transcribe_video
from highlight_detector import detect_highlights
from video_editor import export_clip

def main():
    """Start the RQ worker."""
    
    # Connect to Redis
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    redis_conn = redis.from_url(redis_url)
    
    # Create queues
    high_priority_queue = Queue('high', connection=redis_conn)
    default_queue = Queue('default', connection=redis_conn)
    low_priority_queue = Queue('low', connection=redis_conn)
    
    # Worker will process jobs from these queues in order
    queues = [high_priority_queue, default_queue, low_priority_queue]
    
    print("Starting RQ worker...")
    print(f"Connected to Redis at: {redis_url}")
    print(f"Listening on queues: {[q.name for q in queues]}")
    
    # Start worker
    worker = Worker(queues, connection=redis_conn)
    worker.work()

if __name__ == '__main__':
    main()
