import os
import sys
import tempfile
import re
from datetime import datetime
from typing import List, Dict, Tuple
import scenedetect
from scenedetect.video_manager import VideoManager
from scenedetect.scene_manager import SceneManager
from scenedetect.detectors import ContentDetector
from keybert import KeyBERT
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database import Database
from utils import generate_id
from schemas import JobStatus


db = Database()

# Initialize models for highlight detection
keybert_model = KeyBERT()

# Initialize sentiment analysis pipeline
sentiment_analyzer = pipeline(
    "sentiment-analysis", 
    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    return_all_scores=True
)

# Initialize summarization pipeline
summarizer = pipeline(
    "summarization", 
    model="facebook/bart-large-cnn",
    max_length=50,
    min_length=10
)

# Viral keywords and phrases that tend to perform well
VIRAL_KEYWORDS = [
    "amazing", "incredible", "unbelievable", "shocking", "wow", "omg", "crazy",
    "insane", "mind-blowing", "epic", "legendary", "viral", "trending", "hot",
    "breaking", "exclusive", "secret", "hack", "trick", "tip", "mistake", "fail",
    "win", "success", "transformation", "before", "after", "reveal", "exposed",
    "truth", "reality", "facts", "study", "research", "proven", "science",
    "money", "rich", "poor", "millionaire", "billionaire", "expensive", "cheap",
    "free", "deal", "offer", "limited", "urgent", "now", "today", "never",
    "always", "everyone", "nobody", "first", "last", "best", "worst", "top",
    "bottom", "new", "old", "young", "genius", "stupid", "smart", "dumb"
]


def detect_highlights(video_id: str, max_highlights: int, job_id: str):
    """Detect highlights using NLP and scene detection."""
    try:
        print(f"Starting highlight detection for video {video_id}")
        
        # Update job status
        db.update_job(job_id, {
            "status": JobStatus.PROCESSING.value,
            "progress": 10,
            "updated_at": datetime.utcnow().isoformat()
        })
        
        # Get video and transcript
        video = db.get_video(video_id)
        transcript = db.get_transcript(video_id)
        
        if not video or not transcript:
            raise Exception("Video or transcript not found")
        
        # Download video for scene detection
        file_data = db.storage.download_file(video["file_path"])
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            temp_file.write(file_data)
            temp_path = temp_file.name
        
        try:
            # Step 1: Scene detection
            scene_changes = detect_scene_changes(temp_path)
            
            # Update progress
            db.update_job(job_id, {
                "progress": 30,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            # Step 2: Analyze transcript segments
            segments = transcript["segments"]
            segment_scores = analyze_transcript_segments(segments)
            
            # Update progress
            db.update_job(job_id, {
                "progress": 60,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            # Step 3: Combine scene detection with transcript analysis
            highlights = combine_analysis(segments, segment_scores, scene_changes, max_highlights)
            
            # Update progress
            db.update_job(job_id, {
                "progress": 80,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            # Step 4: Save highlights to database
            for highlight in highlights:
                highlight_data = {
                    "id": generate_id(),
                    "video_id": video_id,
                    "start_time": highlight["start_time"],
                    "end_time": highlight["end_time"],
                    "score": highlight["score"],
                    "keywords": highlight["keywords"],
                    "title": highlight["title"],
                    "description": highlight.get("description"),
                    "created_at": datetime.utcnow().isoformat()
                }
                db.create_highlight(highlight_data)
            
            # Update job as completed
            db.update_job(job_id, {
                "status": JobStatus.COMPLETED.value,
                "progress": 100,
                "metadata": {"highlights_found": len(highlights)},
                "updated_at": datetime.utcnow().isoformat()
            })
            
            print(f"Highlight detection completed for video {video_id}. Found {len(highlights)} highlights.")
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        print(f"Error detecting highlights for video {video_id}: {str(e)}")
        db.update_job(job_id, {
            "status": JobStatus.FAILED.value,
            "error_message": str(e),
            "updated_at": datetime.utcnow().isoformat()
        })


def detect_scene_changes(video_path: str) -> List[float]:
    """Detect scene changes in video using PySceneDetect."""
    try:
        scene_timestamps = []
        
        # Create video manager
        video_manager = VideoManager([video_path])
        scene_manager = SceneManager()
        
        # Add content detector
        scene_manager.add_detector(ContentDetector(threshold=30.0))
        
        # Perform scene detection
        video_manager.set_duration()
        video_manager.start()
        
        scene_manager.detect_scenes(frame_source=video_manager)
        scene_list = scene_manager.get_scene_list()
        
        # Extract scene start times
        for scene in scene_list:
            scene_timestamps.append(scene[0].get_seconds())
        
        return scene_timestamps
        
    except Exception as e:
        print(f"Error in scene detection: {str(e)}")
        return []


def analyze_transcript_segments(segments: List[Dict]) -> List[Dict]:
    """Analyze transcript segments for viral potential."""
    segment_scores = []
    
    for segment in segments:
        text = segment["text"]
        
        # Calculate various scores
        keyword_score = calculate_keyword_score(text)
        sentiment_score = calculate_sentiment_score(text)
        length_score = calculate_length_score(text)
        
        # Extract keywords
        keywords = extract_keywords(text)
        
        # Generate title
        title = generate_segment_title(text)
        
        # Combined score
        total_score = (keyword_score * 0.4) + (sentiment_score * 0.3) + (length_score * 0.3)
        
        segment_scores.append({
            "start_time": segment["start"],
            "end_time": segment["end"],
            "text": text,
            "score": total_score,
            "keywords": keywords,
            "title": title,
            "keyword_score": keyword_score,
            "sentiment_score": sentiment_score,
            "length_score": length_score
        })
    
    return segment_scores


def calculate_keyword_score(text: str) -> float:
    """Calculate score based on presence of viral keywords."""
    text_lower = text.lower()
    score = 0
    
    for keyword in VIRAL_KEYWORDS:
        if keyword in text_lower:
            score += 1
    
    # Normalize score (0-1)
    return min(score / 5, 1.0)


def calculate_sentiment_score(text: str) -> float:
    """Calculate sentiment score (positive emotions score higher)."""
    try:
        results = sentiment_analyzer(text)
        
        # Find positive sentiment score
        for result in results[0]:
            if result['label'].upper() in ['POSITIVE', 'JOY', 'EXCITEMENT']:
                return result['score']
        
        return 0.5  # Neutral if no positive sentiment found
        
    except Exception as e:
        print(f"Error in sentiment analysis: {str(e)}")
        return 0.5


def calculate_length_score(text: str) -> float:
    """Score based on text length (ideal for short clips)."""
    word_count = len(text.split())
    
    # Ideal range: 10-30 words (good for 15-60 second clips)
    if 10 <= word_count <= 30:
        return 1.0
    elif 5 <= word_count < 10 or 30 < word_count <= 50:
        return 0.7
    elif word_count < 5 or word_count > 50:
        return 0.3
    
    return 0.5


def extract_keywords(text: str) -> List[str]:
    """Extract keywords using KeyBERT."""
    try:
        keywords = keybert_model.extract_keywords(
            text, 
            keyphrase_ngram_range=(1, 2), 
            stop_words='english',
            top_k=5
        )
        return [keyword[0] for keyword in keywords]
    except Exception as e:
        print(f"Error extracting keywords: {str(e)}")
        return []


def generate_segment_title(text: str) -> str:
    """Generate a title for the segment."""
    try:
        # Try summarization first
        if len(text.split()) > 10:
            summary = summarizer(text, max_length=30, min_length=5)
            title = summary[0]['summary_text']
        else:
            title = text
        
        # Clean up title
        title = title.strip().rstrip('.')
        
        # Limit length
        if len(title) > 60:
            title = title[:57] + "..."
        
        return title
        
    except Exception as e:
        print(f"Error generating title: {str(e)}")
        # Fallback: use first few words
        words = text.split()[:8]
        return " ".join(words) + ("..." if len(text.split()) > 8 else "")


def combine_analysis(segments: List[Dict], segment_scores: List[Dict], 
                   scene_changes: List[float], max_highlights: int) -> List[Dict]:
    """Combine transcript analysis with scene detection to find best highlights."""
    
    highlights = []
    
    # Group segments by potential clips (15-60 seconds)
    potential_clips = []
    current_clip = []
    current_start = 0
    
    for i, segment_score in enumerate(segment_scores):
        current_clip.append(segment_score)
        
        # Check if we should end this potential clip
        duration = segment_score["end_time"] - current_start
        
        # End clip if duration is good (15-60 seconds) or we hit a scene change
        if (15 <= duration <= 60) or any(abs(sc - segment_score["end_time"]) < 2 for sc in scene_changes):
            if duration >= 10:  # Minimum clip length
                # Calculate combined score for this clip
                clip_score = calculate_clip_score(current_clip, scene_changes)
                
                potential_clips.append({
                    "start_time": current_start,
                    "end_time": segment_score["end_time"],
                    "duration": duration,
                    "score": clip_score,
                    "segments": current_clip.copy(),
                    "keywords": extract_clip_keywords(current_clip),
                    "title": generate_clip_title(current_clip)
                })
            
            # Reset for next clip
            current_clip = []
            current_start = segment_score["end_time"] if i < len(segment_scores) - 1 else 0
    
    # Sort by score and take top highlights
    potential_clips.sort(key=lambda x: x["score"], reverse=True)
    
    # Select non-overlapping highlights
    selected_highlights = []
    for clip in potential_clips:
        if len(selected_highlights) >= max_highlights:
            break
        
        # Check for overlap with existing highlights
        has_overlap = False
        for existing in selected_highlights:
            if (clip["start_time"] < existing["end_time"] and 
                clip["end_time"] > existing["start_time"]):
                has_overlap = True
                break
        
        if not has_overlap:
            selected_highlights.append({
                "start_time": clip["start_time"],
                "end_time": clip["end_time"],
                "score": clip["score"],
                "keywords": clip["keywords"],
                "title": clip["title"],
                "description": f"Duration: {clip['duration']:.1f}s"
            })
    
    return selected_highlights


def calculate_clip_score(segments: List[Dict], scene_changes: List[float]) -> float:
    """Calculate overall score for a potential clip."""
    if not segments:
        return 0
    
    # Average segment scores
    avg_score = sum(seg["score"] for seg in segments) / len(segments)
    
    # Bonus for scene changes (visual interest)
    scene_bonus = 0
    clip_start = segments[0]["start_time"]
    clip_end = segments[-1]["end_time"]
    
    for scene_time in scene_changes:
        if clip_start <= scene_time <= clip_end:
            scene_bonus += 0.1
    
    # Bonus for emotional peaks (high sentiment segments)
    emotion_bonus = 0
    for segment in segments:
        if segment.get("sentiment_score", 0) > 0.8:
            emotion_bonus += 0.1
    
    # Penalty for very short or very long clips
    duration = clip_end - clip_start
    duration_multiplier = 1.0
    if duration < 15:
        duration_multiplier = 0.7
    elif duration > 45:
        duration_multiplier = 0.8
    
    return (avg_score + scene_bonus + emotion_bonus) * duration_multiplier


def extract_clip_keywords(segments: List[Dict]) -> List[str]:
    """Extract combined keywords for a clip."""
    all_keywords = []
    for segment in segments:
        all_keywords.extend(segment.get("keywords", []))
    
    # Remove duplicates and return top 5
    unique_keywords = list(dict.fromkeys(all_keywords))
    return unique_keywords[:5]


def generate_clip_title(segments: List[Dict]) -> str:
    """Generate title for a clip based on its segments."""
    # Combine text from all segments
    combined_text = " ".join(seg["text"] for seg in segments)
    
    # Find the segment with highest score for title generation
    best_segment = max(segments, key=lambda x: x["score"])
    
    try:
        # Use the best segment's text for title
        title = generate_segment_title(best_segment["text"])
        return title
    except Exception:
        # Fallback to simple approach
        words = combined_text.split()[:6]
        return " ".join(words) + ("..." if len(combined_text.split()) > 6 else "")


def generate_segment_title(text: str) -> str:
    """Generate a catchy title for a text segment."""
    # Remove filler words and clean text
    text = re.sub(r'\b(um|uh|like|you know|so|well)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    
    words = text.split()
    
    if len(words) <= 8:
        return text
    
    # Try to find a compelling phrase within the first part
    for i in range(3, min(9, len(words))):
        phrase = " ".join(words[:i])
        if any(keyword in phrase.lower() for keyword in VIRAL_KEYWORDS[:20]):
            return phrase
    
    # Fallback to first 6 words
    return " ".join(words[:6]) + "..."


def is_high_energy_segment(segment: Dict) -> bool:
    """Determine if a segment has high energy/engagement."""
    text = segment["text"].lower()
    
    # Check for exclamation marks, caps, viral keywords
    energy_indicators = [
        "!" in segment["text"],
        any(word.isupper() for word in segment["text"].split()),
        any(keyword in text for keyword in VIRAL_KEYWORDS[:30]),
        segment.get("sentiment_score", 0) > 0.7
    ]
    
    return sum(energy_indicators) >= 2


def calculate_viral_potential(text: str, keywords: List[str], sentiment_score: float) -> float:
    """Calculate overall viral potential score."""
    base_score = sentiment_score
    
    # Keyword boost
    viral_keyword_count = sum(1 for kw in keywords if kw.lower() in VIRAL_KEYWORDS)
    keyword_boost = min(viral_keyword_count * 0.1, 0.3)
    
    # Length penalty (too long is bad for viral content)
    word_count = len(text.split())
    length_penalty = 0
    if word_count > 50:
        length_penalty = 0.2
    
    # Question boost (questions engage viewers)
    question_boost = 0.1 if "?" in text else 0
    
    return min(base_score + keyword_boost + question_boost - length_penalty, 1.0)
