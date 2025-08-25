import os
import sys
import tempfile
from datetime import datetime
import subprocess
import moviepy.editor as mp
from moviepy.video.fx import resize
from moviepy.video.tools.subtitles import SubtitlesClip
import cv2
import numpy as np

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database import Database, Storage
from utils import generate_id, calculate_aspect_ratio_dimensions
from schemas import JobStatus


db = Database()
storage = Storage(db.supabase)


def export_clip(clip_id: str, include_subtitles: bool, job_id: str):
    """Export a highlight as a video clip."""
    try:
        print(f"Starting clip export for {clip_id}")
        
        # Update job status
        db.update_job(job_id, {
            "status": JobStatus.PROCESSING.value,
            "progress": 10,
            "updated_at": datetime.utcnow().isoformat()
        })
        
        # Get clip and related data
        clip = db.get_clip(clip_id)
        if not clip:
            raise Exception("Clip not found")
        
        highlight = db.get_highlights(clip["video_id"])
        highlight = next((h for h in highlight if h["id"] == clip["highlight_id"]), None)
        if not highlight:
            raise Exception("Highlight not found")
        
        video = db.get_video(clip["video_id"])
        if not video:
            raise Exception("Video not found")
        
        # Download original video
        video_data = storage.download_file(video["file_path"])
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
            temp_video.write(video_data)
            temp_video_path = temp_video.name
        
        try:
            # Load video clip
            with mp.VideoFileClip(temp_video_path) as original_clip:
                # Extract highlight segment
                start_time = highlight["start_time"]
                end_time = highlight["end_time"]
                
                # Add 1-2 seconds padding for better context
                padded_start = max(0, start_time - 1)
                padded_end = min(original_clip.duration, end_time + 1)
                
                highlight_clip = original_clip.subclip(padded_start, padded_end)
                
                # Update progress
                db.update_job(job_id, {
                    "progress": 30,
                    "updated_at": datetime.utcnow().isoformat()
                })
                
                # Apply aspect ratio conversion
                formatted_clip = apply_aspect_ratio(highlight_clip, clip["export_format"])
                
                # Update progress
                db.update_job(job_id, {
                    "progress": 50,
                    "updated_at": datetime.utcnow().isoformat()
                })
                
                # Add subtitles if requested
                if include_subtitles:
                    transcript = db.get_transcript(clip["video_id"])
                    if transcript:
                        formatted_clip = add_subtitles(formatted_clip, transcript, start_time, end_time)
                
                # Update progress
                db.update_job(job_id, {
                    "progress": 70,
                    "updated_at": datetime.utcnow().isoformat()
                })
                
                # Add watermark for free users
                if clip["has_watermark"]:
                    formatted_clip = add_watermark(formatted_clip)
                
                # Update progress
                db.update_job(job_id, {
                    "progress": 80,
                    "updated_at": datetime.utcnow().isoformat()
                })
                
                # Export video
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as output_file:
                    output_path = output_file.name
                
                # Set quality based on subscription
                quality = "high" if clip["resolution"] == "1080p" else "medium"
                
                formatted_clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True,
                    verbose=False,
                    logger=None,
                    preset='medium' if quality == "high" else 'fast'
                )
                
                # Upload to storage
                with open(output_path, 'rb') as f:
                    output_data = f.read()
                    storage.upload_file(clip["file_path"], output_data)
                
                # Update clip record
                file_size = len(output_data)
                db.update_clip(clip_id, {
                    "file_size": file_size,
                    "status": JobStatus.COMPLETED.value
                })
                
                # Update job as completed
                db.update_job(job_id, {
                    "status": JobStatus.COMPLETED.value,
                    "progress": 100,
                    "metadata": {"output_file_size": file_size},
                    "updated_at": datetime.utcnow().isoformat()
                })
                
                print(f"Clip export completed for {clip_id}")
                
        finally:
            # Clean up temp files
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            if 'output_path' in locals() and os.path.exists(output_path):
                os.remove(output_path)
            
    except Exception as e:
        print(f"Error exporting clip {clip_id}: {str(e)}")
        db.update_job(job_id, {
            "status": JobStatus.FAILED.value,
            "error_message": str(e),
            "updated_at": datetime.utcnow().isoformat()
        })


def apply_aspect_ratio(clip: mp.VideoFileClip, target_format: str) -> mp.VideoFileClip:
    """Convert video to target aspect ratio."""
    original_width, original_height = clip.size
    
    if target_format == "9:16":
        # Vertical format (TikTok/Instagram Reels)
        target_width = 1080 if original_width >= 1080 else original_width
        target_height = int(target_width * 16 / 9)
        
        # Crop to center if needed
        if original_width / original_height > 9 / 16:
            # Too wide, crop horizontally
            crop_width = int(original_height * 9 / 16)
            x_center = original_width // 2
            clip = clip.crop(x1=x_center - crop_width//2, x2=x_center + crop_width//2)
        
        # Resize to target dimensions
        clip = clip.resize((target_width, target_height))
        
    elif target_format == "1:1":
        # Square format (Instagram Post)
        target_size = min(1080, min(original_width, original_height))
        
        # Crop to square
        if original_width > original_height:
            # Crop horizontally
            x_center = original_width // 2
            clip = clip.crop(x1=x_center - original_height//2, x2=x_center + original_height//2)
        elif original_height > original_width:
            # Crop vertically
            y_center = original_height // 2
            clip = clip.crop(y1=y_center - original_width//2, y2=y_center + original_width//2)
        
        # Resize to target dimensions
        clip = clip.resize((target_size, target_size))
        
    else:  # "16:9"
        # Horizontal format (YouTube Shorts)
        target_height = 720 if original_height >= 720 else original_height
        target_width = int(target_height * 16 / 9)
        
        # Crop to center if needed
        if original_height / original_width > 9 / 16:
            # Too tall, crop vertically
            crop_height = int(original_width * 9 / 16)
            y_center = original_height // 2
            clip = clip.crop(y1=y_center - crop_height//2, y2=y_center + crop_height//2)
        
        # Resize to target dimensions
        clip = clip.resize((target_width, target_height))
    
    return clip


def add_subtitles(clip: mp.VideoFileClip, transcript: dict, start_time: float, end_time: float) -> mp.VideoFileClip:
    """Add animated subtitles to video clip."""
    try:
        # Filter transcript segments for this clip
        relevant_segments = []
        for segment in transcript["segments"]:
            seg_start = segment["start"] - start_time  # Adjust to clip time
            seg_end = segment["end"] - start_time
            
            if seg_start < clip.duration and seg_end > 0:
                # Clip segment to video bounds
                seg_start = max(0, seg_start)
                seg_end = min(clip.duration, seg_end)
                
                relevant_segments.append({
                    "start": seg_start,
                    "end": seg_end,
                    "text": segment["text"].strip()
                })
        
        if not relevant_segments:
            return clip
        
        # Create subtitle clips
        subtitle_clips = []
        
        for segment in relevant_segments:
            # Create text clip for this segment
            txt_clip = mp.TextClip(
                segment["text"],
                fontsize=50,
                color='white',
                stroke_color='black',
                stroke_width=2,
                font='Arial-Bold',
                method='caption',
                size=(clip.w * 0.8, None)
            ).set_position(('center', 'bottom')).set_duration(segment["end"] - segment["start"]).set_start(segment["start"])
            
            subtitle_clips.append(txt_clip)
        
        # Composite subtitles with video
        if subtitle_clips:
            final_clip = mp.CompositeVideoClip([clip] + subtitle_clips)
            return final_clip
        
        return clip
        
    except Exception as e:
        print(f"Error adding subtitles: {str(e)}")
        return clip


def add_watermark(clip: mp.VideoFileClip) -> mp.VideoFileClip:
    """Add watermark to video for free users."""
    try:
        # Create simple text watermark
        watermark = mp.TextClip(
            "ViralClips.ai",
            fontsize=30,
            color='white',
            stroke_color='black',
            stroke_width=1,
            font='Arial'
        ).set_position(('right', 'top')).set_duration(clip.duration).set_opacity(0.7)
        
        # Composite watermark with video
        final_clip = mp.CompositeVideoClip([clip, watermark])
        return final_clip
        
    except Exception as e:
        print(f"Error adding watermark: {str(e)}")
        return clip


def apply_smart_crop(clip: mp.VideoFileClip, target_aspect: str, crop_data: dict = None) -> mp.VideoFileClip:
    """Apply smart cropping using MediaPipe face/pose tracking data."""
    try:
        if crop_data and target_aspect in crop_data.get('crop_regions', {}):
            # Use pre-calculated smart crop regions
            regions = crop_data['crop_regions'][target_aspect]
            
            def smart_crop_func(get_frame, t):
                # Find the crop region for this timestamp
                frame = get_frame(t)
                region = None
                
                # Find closest timestamp
                for r in regions:
                    if abs(r['timestamp'] - t) < 0.5:  # Within 0.5 seconds
                        region = r
                        break
                
                if region:
                    # Apply the smart crop
                    h, w = frame.shape[:2]
                    x1 = max(0, region['x'])
                    y1 = max(0, region['y'])
                    x2 = min(w, region['x'] + region['width'])
                    y2 = min(h, region['y'] + region['height'])
                    
                    return frame[y1:y2, x1:x2]
                else:
                    # Fallback to center crop
                    return apply_center_crop_to_frame(frame, target_aspect)
            
            return clip.fl(smart_crop_func)
        else:
            # Fallback to center crop
            return apply_center_crop(clip, target_aspect)
        
    except Exception as e:
        print(f"Error in smart crop: {str(e)}")
        return apply_center_crop(clip, target_aspect)


def apply_center_crop(clip: mp.VideoFileClip, target_aspect: str) -> mp.VideoFileClip:
    """Apply center crop to video."""
    w, h = clip.size
    
    if target_aspect == "9:16":
        # Vertical
        if w / h > 9 / 16:
            # Too wide, crop width
            new_w = int(h * 9 / 16)
            x1 = (w - new_w) // 2
            clip = clip.crop(x1=x1, x2=x1 + new_w)
    
    elif target_aspect == "1:1":
        # Square
        size = min(w, h)
        if w > h:
            x1 = (w - size) // 2
            clip = clip.crop(x1=x1, x2=x1 + size)
        elif h > w:
            y1 = (h - size) // 2
            clip = clip.crop(y1=y1, y2=y1 + size)
    
    return clip


def enhance_video_quality(clip: mp.VideoFileClip) -> mp.VideoFileClip:
    """Apply basic video enhancements."""
    try:
        # Basic color correction and stabilization would go here
        # For now, just return the original clip
        return clip
    except Exception as e:
        print(f"Error enhancing video: {str(e)}")
        return clip


def generate_thumbnail(clip: mp.VideoFileClip, output_path: str):
    """Generate thumbnail from video clip."""
    try:
        # Extract frame from middle of clip
        frame_time = clip.duration / 2
        frame = clip.get_frame(frame_time)
        
        # Save as JPEG
        import PIL.Image as Image
        img = Image.fromarray(frame)
        img.save(output_path, "JPEG", quality=85)
        
    except Exception as e:
        print(f"Error generating thumbnail: {str(e)}")


def create_preview_gif(clip: mp.VideoFileClip, output_path: str, duration: float = 3.0):
    """Create a short GIF preview of the clip."""
    try:
        # Create short preview clip
        preview_clip = clip.subclip(0, min(duration, clip.duration))
        
        # Resize for smaller file size
        preview_clip = preview_clip.resize(0.5)
        
        # Export as GIF
        preview_clip.write_gif(output_path, fps=10, verbose=False, logger=None)
        
    except Exception as e:
        print(f"Error creating preview GIF: {str(e)}")


def add_intro_outro(clip: mp.VideoFileClip, user_subscription: str) -> mp.VideoFileClip:
    """Add intro/outro for branding."""
    try:
        if user_subscription == "free":
            # Add simple text intro for free users
            intro = mp.TextClip(
                "Made with ViralClips.ai",
                fontsize=40,
                color='white',
                bg_color='black'
            ).set_duration(1).set_position('center')
            
            # Combine intro + main clip
            final_clip = mp.concatenate_videoclips([intro, clip])
            return final_clip
        
        return clip
        
    except Exception as e:
        print(f"Error adding intro/outro: {str(e)}")
        return clip


def optimize_for_platform(clip: mp.VideoFileClip, platform: str) -> mp.VideoFileClip:
    """Optimize video settings for specific platforms."""
    try:
        if platform == "tiktok":
            # TikTok prefers 9:16, high energy
            clip = apply_aspect_ratio(clip, "9:16")
        elif platform == "instagram":
            # Instagram supports multiple formats
            pass
        elif platform == "youtube":
            # YouTube Shorts are 9:16
            clip = apply_aspect_ratio(clip, "9:16")
        
        return clip
        
    except Exception as e:
        print(f"Error optimizing for platform {platform}: {str(e)}")
        return clip


def apply_viral_effects(clip: mp.VideoFileClip) -> mp.VideoFileClip:
    """Apply effects that make content more engaging."""
    try:
        # Add zoom effects at key moments
        # Add transition effects
        # For now, return original clip
        return clip
        
    except Exception as e:
        print(f"Error applying viral effects: {str(e)}")
        return clip
