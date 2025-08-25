import os
import sys
import tempfile
import json
from datetime import datetime
from typing import List, Dict, Any
import torch
try:
    import whisperx
    WHISPERX_AVAILABLE = True
except ImportError:
    WHISPERX_AVAILABLE = False

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database import Database
from utils import generate_id
from schemas import JobStatus

db = Database()

class EnhancedTranscription:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if torch.cuda.is_available() else "int8"
        
    def transcribe_with_whisperx(self, audio_path: str, video_id: str, job_id: str) -> Dict[str, Any]:
        """Enhanced transcription with speaker diarization using WhisperX."""
        try:
            if not WHISPERX_AVAILABLE:
                raise Exception("WhisperX not available")
            
            print(f"Starting WhisperX transcription for video {video_id}")
            
            # Update progress
            db.update_job(job_id, {
                "progress": 20,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            # Load WhisperX model
            model = whisperx.load_model("base", self.device, compute_type=self.compute_type)
            
            # Load audio
            audio = whisperx.load_audio(audio_path)
            
            # Transcribe with WhisperX
            result = model.transcribe(audio, batch_size=16)
            
            # Update progress
            db.update_job(job_id, {
                "progress": 40,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            # Load alignment model
            model_a, metadata = whisperx.load_align_model(
                language_code=result["language"], 
                device=self.device
            )
            
            # Align whisper output
            aligned_result = whisperx.align(result["segments"], model_a, metadata, audio, self.device, return_char_alignments=False)
            
            # Update progress
            db.update_job(job_id, {
                "progress": 60,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            # Assign speaker labels using diarization
            diarize_model = whisperx.DiarizationPipeline(use_auth_token="YOUR_HF_TOKEN", device=self.device)
            diarize_segments = diarize_model(audio)
            
            # Assign speakers to segments
            final_result = whisperx.assign_word_speakers(diarize_segments, aligned_result)
            
            # Update progress
            db.update_job(job_id, {
                "progress": 80,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            # Process segments for database storage
            processed_segments = []
            full_text = ""
            
            for segment in final_result["segments"]:
                segment_data = {
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                    "speaker": segment.get("speaker", "UNKNOWN"),
                    "words": []
                }
                
                # Add word-level data with speaker info
                if "words" in segment:
                    for word in segment["words"]:
                        word_data = {
                            "start": word["start"],
                            "end": word["end"],
                            "word": word["word"],
                            "probability": word.get("probability", 0.5),
                            "speaker": word.get("speaker", segment.get("speaker", "UNKNOWN"))
                        }
                        segment_data["words"].append(word_data)
                
                processed_segments.append(segment_data)
                full_text += f"[{segment_data['speaker']}] {segment['text']} "
            
            return {
                "segments": processed_segments,
                "language": result["language"],
                "full_text": full_text.strip(),
                "speaker_count": len(set(seg.get("speaker", "UNKNOWN") for seg in processed_segments))
            }
            
        except Exception as e:
            print(f"WhisperX transcription failed: {str(e)}")
            raise
            
    def extract_speaker_insights(self, segments: List[Dict]) -> Dict[str, Any]:
        """Analyze speaker patterns and interactions."""
        speaker_stats = {}
        speaker_changes = 0
        current_speaker = None
        
        for segment in segments:
            speaker = segment.get("speaker", "UNKNOWN")
            
            if speaker not in speaker_stats:
                speaker_stats[speaker] = {
                    "total_time": 0,
                    "segment_count": 0,
                    "words": 0,
                    "energy_level": 0
                }
            
            duration = segment["end"] - segment["start"]
            speaker_stats[speaker]["total_time"] += duration
            speaker_stats[speaker]["segment_count"] += 1
            speaker_stats[speaker]["words"] += len(segment["text"].split())
            
            # Track speaker changes for conversation dynamics
            if current_speaker and current_speaker != speaker:
                speaker_changes += 1
            current_speaker = speaker
        
        # Calculate conversation dynamics
        total_duration = sum(stats["total_time"] for stats in speaker_stats.values())
        for speaker, stats in speaker_stats.items():
            stats["speaking_percentage"] = (stats["total_time"] / total_duration * 100) if total_duration > 0 else 0
            stats["words_per_minute"] = (stats["words"] / (stats["total_time"] / 60)) if stats["total_time"] > 0 else 0
        
        return {
            "speaker_stats": speaker_stats,
            "speaker_changes": speaker_changes,
            "conversation_score": min(speaker_changes / 10, 1.0),  # Normalize to 0-1
            "dominant_speaker": max(speaker_stats.keys(), key=lambda x: speaker_stats[x]["total_time"]) if speaker_stats else None
        }
    
    def generate_speaker_timeline(self, segments: List[Dict]) -> List[Dict]:
        """Generate timeline showing speaker changes for visualization."""
        timeline = []
        
        for segment in segments:
            timeline.append({
                "start": segment["start"],
                "end": segment["end"],
                "speaker": segment.get("speaker", "UNKNOWN"),
                "text_preview": segment["text"][:50] + "..." if len(segment["text"]) > 50 else segment["text"]
            })
        
        return timeline

def transcribe_with_speaker_detection(video_id: str, job_id: str):
    """Main function for enhanced transcription with speaker detection."""
    try:
        transcriber = EnhancedTranscription()
        
        # Get video record
        video = db.get_video(video_id)
        if not video:
            raise Exception("Video not found")
        
        # Download and extract audio
        file_data = db.storage.download_file(video["file_path"])
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
            temp_video.write(file_data)
            temp_video_path = temp_video.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            temp_audio_path = temp_audio.name
        
        try:
            # Extract audio
            import moviepy.editor as mp
            video_clip = mp.VideoFileClip(temp_video_path)
            audio_clip = video_clip.audio
            audio_clip.write_audiofile(temp_audio_path, verbose=False, logger=None)
            
            # Enhanced transcription
            result = transcriber.transcribe_with_whisperx(temp_audio_path, video_id, job_id)
            
            # Analyze speaker insights
            speaker_insights = transcriber.extract_speaker_insights(result["segments"])
            
            # Generate speaker timeline
            speaker_timeline = transcriber.generate_speaker_timeline(result["segments"])
            
            # Save enhanced transcript to database
            transcript_data = {
                "id": generate_id(),
                "video_id": video_id,
                "text": result["full_text"],
                "segments": result["segments"],
                "language": result["language"],
                "metadata": {
                    "speaker_count": result["speaker_count"],
                    "speaker_insights": speaker_insights,
                    "speaker_timeline": speaker_timeline,
                    "enhanced_features": True
                },
                "created_at": datetime.utcnow().isoformat()
            }
            
            transcript = db.create_transcript(transcript_data)
            
            # Update job as completed
            db.update_job(job_id, {
                "status": JobStatus.COMPLETED.value,
                "progress": 100,
                "metadata": {
                    "speaker_count": result["speaker_count"],
                    "enhanced_features": True
                },
                "updated_at": datetime.utcnow().isoformat()
            })
            
            print(f"Enhanced transcription completed for video {video_id} with {result['speaker_count']} speakers")
            
            # Start highlight detection
            from highlight_detector import detect_highlights
            detect_highlights(video_id, 5, generate_id())
            
        finally:
            # Cleanup
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            
            if 'audio_clip' in locals():
                audio_clip.close()
            if 'video_clip' in locals():
                video_clip.close()
                
    except Exception as e:
        print(f"Error in enhanced transcription for video {video_id}: {str(e)}")
        db.update_job(job_id, {
            "status": JobStatus.FAILED.value,
            "error_message": str(e),
            "updated_at": datetime.utcnow().isoformat()
        })
