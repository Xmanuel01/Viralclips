import os
import sys
import tempfile
from datetime import datetime
import yt_dlp
import moviepy.editor as mp
from moviepy.video.io.VideoFileClip import VideoFileClip

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database import Database
from utils import generate_id, get_video_filename, sanitize_filename
from schemas import JobStatus


db = Database()


def download_youtube_video(video_id: str, youtube_url: str):
    """Download video from YouTube and upload to storage."""
    try:
        # Update job status
        print(f"Starting YouTube download for video {video_id}")
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'best[height<=720]',  # Limit quality to save bandwidth
            'outtmpl': f'temp_%(id)s.%(ext)s',
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video info
            info = ydl.extract_info(youtube_url, download=False)
            title = sanitize_filename(info.get('title', 'Unknown'))
            duration = info.get('duration', 0)
            
            # Download video
            download_info = ydl.extract_info(youtube_url, download=True)
            temp_filename = ydl.prepare_filename(download_info)
            
            # Get file size
            file_size = os.path.getsize(temp_filename)
            
            # Upload to Supabase storage
            with open(temp_filename, 'rb') as f:
                file_data = f.read()
                file_path = f"videos/{video_id}.mp4"
                db.storage.upload_file(file_path, file_data)
            
            # Update video record
            updates = {
                "title": title,
                "duration": duration,
                "file_size": file_size,
                "status": JobStatus.COMPLETED.value,
                "updated_at": datetime.utcnow().isoformat()
            }
            db.update_video(video_id, updates)
            
            # Clean up temp file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            
            print(f"YouTube download completed for video {video_id}")
            
            # Automatically start transcription
            transcribe_video(video_id)
            
    except Exception as e:
        print(f"Error downloading YouTube video {video_id}: {str(e)}")
        # Update video status to failed
        db.update_video(video_id, {
            "status": JobStatus.FAILED.value,
            "updated_at": datetime.utcnow().isoformat()
        })


def process_video(video_id: str):
    """Process uploaded video file (get metadata, etc.)."""
    try:
        print(f"Processing video {video_id}")
        
        # Get video record
        video = db.get_video(video_id)
        if not video:
            raise Exception("Video not found")
        
        # Download video from storage for processing
        file_data = db.storage.download_file(video["file_path"])
        
        # Save to temporary file for moviepy
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            temp_file.write(file_data)
            temp_path = temp_file.name
        
        try:
            # Get video metadata using moviepy
            with VideoFileClip(temp_path) as clip:
                duration = clip.duration
                width = clip.w
                height = clip.h
            
            # Update video record with metadata
            updates = {
                "duration": duration,
                "status": JobStatus.COMPLETED.value,
                "updated_at": datetime.utcnow().isoformat()
            }
            db.update_video(video_id, updates)
            
            print(f"Video processing completed for {video_id}")
            
            # Automatically start transcription
            transcribe_video(video_id)
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
    except Exception as e:
        print(f"Error processing video {video_id}: {str(e)}")
        db.update_video(video_id, {
            "status": JobStatus.FAILED.value,
            "updated_at": datetime.utcnow().isoformat()
        })


def transcribe_video(video_id: str):
    """Start transcription after video processing."""
    try:
        # Import transcription worker
        from transcription import transcribe_video as transcribe_worker
        
        # Create transcription job
        job_id = generate_id()
        job_data = {
            "id": job_id,
            "user_id": "",  # Will be filled by transcription worker
            "job_type": "transcribe",
            "status": JobStatus.PENDING.value,
            "progress": 0,
            "metadata": {"video_id": video_id},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        db.create_job(job_data)
        
        # Call transcription directly
        transcribe_worker(video_id, job_id)
        
    except Exception as e:
        print(f"Error starting transcription for video {video_id}: {str(e)}")


def get_video_metadata(file_path: str) -> dict:
    """Extract metadata from video file."""
    try:
        with VideoFileClip(file_path) as clip:
            return {
                "duration": clip.duration,
                "width": clip.w,
                "height": clip.h,
                "fps": clip.fps
            }
    except Exception as e:
        print(f"Error extracting video metadata: {str(e)}")
        return {"duration": 0, "width": 0, "height": 0, "fps": 0}
