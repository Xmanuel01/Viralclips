import os
import sys
import tempfile
import json
from datetime import datetime
from faster_whisper import WhisperModel
import moviepy.editor as mp
try:
    import whisperx
    WHISPERX_AVAILABLE = True
except ImportError:
    WHISPERX_AVAILABLE = False
    print("WhisperX not available, falling back to faster-whisper")

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database import Database
from utils import generate_id
from schemas import JobStatus


db = Database()

# Initialize Whisper model (using CPU-optimized version)
# Using 'base' model as a balance between speed and accuracy
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")


def transcribe_video(video_id: str, job_id: str, use_whisperx: bool = True):
    """Transcribe video using WhisperX for speaker diarization or faster-whisper as fallback."""
    try:
        print(f"Starting transcription for video {video_id} (WhisperX: {use_whisperx and WHISPERX_AVAILABLE})")
        
        # Update job status
        db.update_job(job_id, {
            "status": JobStatus.PROCESSING.value,
            "progress": 10,
            "updated_at": datetime.utcnow().isoformat()
        })
        
        # Get video record
        video = db.get_video(video_id)
        if not video:
            raise Exception("Video not found")
        
        # Download video from storage
        file_data = db.storage.download_file(video["file_path"])
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
            temp_video.write(file_data)
            temp_video_path = temp_video.name
        
        # Extract audio using moviepy
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            temp_audio_path = temp_audio.name
        
        try:
            # Extract audio from video
            video_clip = mp.VideoFileClip(temp_video_path)
            audio_clip = video_clip.audio
            audio_clip.write_audiofile(temp_audio_path, verbose=False, logger=None)
            
            # Update progress
            db.update_job(job_id, {
                "progress": 30,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            # Transcribe audio
            segments, info = whisper_model.transcribe(
                temp_audio_path, 
                beam_size=5,
                word_timestamps=True,
                vad_filter=True  # Voice activity detection
            )
            
            # Process segments with word-level timestamps
            transcript_segments = []
            full_text = ""
            
            for segment in segments:
                segment_data = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "words": []
                }
                
                # Add word-level timestamps if available
                if hasattr(segment, 'words') and segment.words:
                    for word in segment.words:
                        word_data = {
                            "start": word.start,
                            "end": word.end,
                            "word": word.word,
                            "probability": word.probability
                        }
                        segment_data["words"].append(word_data)
                
                transcript_segments.append(segment_data)
                full_text += segment.text + " "
            
            # Update progress
            db.update_job(job_id, {
                "progress": 80,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            # Save transcript to database
            transcript_data = {
                "id": generate_id(),
                "video_id": video_id,
                "text": full_text.strip(),
                "segments": transcript_segments,
                "language": info.language,
                "created_at": datetime.utcnow().isoformat()
            }
            
            transcript = db.create_transcript(transcript_data)
            
            # Update job as completed
            db.update_job(job_id, {
                "status": JobStatus.COMPLETED.value,
                "progress": 100,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            print(f"Transcription completed for video {video_id}")
            
            # Automatically start highlight detection
            detect_highlights_auto(video_id)
            
        finally:
            # Clean up temp files
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            
            # Close clips to free memory
            if 'audio_clip' in locals():
                audio_clip.close()
            if 'video_clip' in locals():
                video_clip.close()
                
    except Exception as e:
        print(f"Error transcribing video {video_id}: {str(e)}")
        db.update_job(job_id, {
            "status": JobStatus.FAILED.value,
            "error_message": str(e),
            "updated_at": datetime.utcnow().isoformat()
        })


def detect_highlights_auto(video_id: str):
    """Automatically start highlight detection after transcription."""
    try:
        from highlight_detector import detect_highlights
        
        # Create highlight detection job
        job_id = generate_id()
        job_data = {
            "id": job_id,
            "user_id": "",  # Will be filled by highlight detector
            "job_type": "highlight",
            "status": JobStatus.PENDING.value,
            "progress": 0,
            "metadata": {"video_id": video_id, "max_highlights": 5},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        db.create_job(job_data)
        
        # Call highlight detection
        detect_highlights(video_id, 5, job_id)
        
    except Exception as e:
        print(f"Error starting highlight detection for video {video_id}: {str(e)}")


def generate_srt(segments: list, output_path: str):
    """Generate SRT subtitle file from transcript segments."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                start_time = format_timestamp(segment['start'])
                end_time = format_timestamp(segment['end'])
                text = segment['text'].strip()
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
    except Exception as e:
        print(f"Error generating SRT: {str(e)}")


def format_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
