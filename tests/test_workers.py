import pytest
from unittest.mock import patch, Mock, MagicMock
import tempfile
import os

def test_transcription_worker_success(mock_database, mock_whisper_model, sample_video):
    """Test successful video transcription."""
    from workers.transcription import transcribe_video
    
    # Mock database responses
    mock_database.get_video.return_value = sample_video
    mock_database.update_job.return_value = None
    mock_database.create_transcript.return_value = {"id": "test-transcript-id"}
    mock_database.storage.download_file.return_value = b"fake video data"
    
    # Mock MoviePy
    with patch('moviepy.editor.VideoFileClip') as mock_video_clip:
        mock_clip = Mock()
        mock_clip.audio = Mock()
        mock_video_clip.return_value.__enter__.return_value = mock_clip
        
        # Mock tempfile
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = "temp_file.wav"
            
            # Run transcription
            transcribe_video("test-video-id", "test-job-id")
            
            # Verify database calls
            mock_database.get_video.assert_called_with("test-video-id")
            mock_database.create_transcript.assert_called_once()
            assert mock_database.update_job.call_count >= 2  # Progress updates

def test_highlight_detection_success(mock_database, sample_video, sample_transcript):
    """Test successful highlight detection."""
    from workers.highlight_detector import detect_highlights
    
    # Mock database responses
    mock_database.get_video.return_value = sample_video
    mock_database.get_transcript.return_value = sample_transcript
    mock_database.update_job.return_value = None
    mock_database.create_highlight.return_value = {"id": "test-highlight-id"}
    mock_database.storage.download_file.return_value = b"fake video data"
    
    # Mock video processing
    with patch('cv2.VideoCapture') as mock_cap:
        mock_cap.return_value.isOpened.return_value = True
        mock_cap.return_value.read.return_value = (False, None)  # End of video
        mock_cap.return_value.get.return_value = 30.0  # FPS
        mock_cap.return_value.release.return_value = None
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = "temp_file.mp4"
            
            # Run highlight detection
            detect_highlights("test-video-id", 5, "test-job-id")
            
            # Verify database calls
            mock_database.get_video.assert_called_with("test-video-id")
            mock_database.get_transcript.assert_called_with("test-video-id")
            assert mock_database.create_highlight.call_count >= 1

def test_video_editor_export_success(mock_database, mock_video_clip, sample_clip, sample_highlight, sample_video):
    """Test successful clip export."""
    from workers.video_editor import export_clip
    
    # Mock database responses
    mock_database.get_clip.return_value = sample_clip
    mock_database.get_highlights.return_value = [sample_highlight]
    mock_database.get_video.return_value = sample_video
    mock_database.get_transcript.return_value = {"segments": []}
    mock_database.update_job.return_value = None
    mock_database.update_clip.return_value = None
    mock_database.storage.download_file.return_value = b"fake video data"
    mock_database.storage.upload_file.return_value = "uploaded_path"
    
    with patch('tempfile.NamedTemporaryFile') as mock_temp:
        mock_temp.return_value.__enter__.return_value.name = "temp_file.mp4"
        
        # Run clip export
        export_clip("test-clip-id", True, "test-job-id")
        
        # Verify database calls
        mock_database.get_clip.assert_called_with("test-clip-id")
        mock_database.update_clip.assert_called_once()
        assert mock_database.update_job.call_count >= 2

def test_face_tracking_analysis(mock_database, sample_video):
    """Test face tracking analysis."""
    from workers.face_tracking import analyze_video_subjects
    
    # Mock database responses
    mock_database.get_video.return_value = sample_video
    mock_database.update_job.return_value = None
    mock_database.update_video.return_value = None
    mock_database.storage.download_file.return_value = b"fake video data"
    
    # Mock OpenCV
    with patch('cv2.VideoCapture') as mock_cap:
        mock_cap.return_value.get.return_value = 1920  # Width/Height
        mock_cap.return_value.release.return_value = None
        
        # Mock MediaPipe
        with patch('mediapipe.solutions.face_detection') as mock_mp:
            mock_detection = Mock()
            mock_detection.process.return_value.detections = []
            mock_mp.FaceDetection.return_value = mock_detection
            
            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp.return_value.__enter__.return_value.name = "temp_file.mp4"
                
                # Run face tracking
                result = analyze_video_subjects("test-video-id", "test-job-id")
                
                # Verify results
                assert "video_id" in result
                assert "tracking_quality" in result
                mock_database.update_video.assert_called_once()

def test_enhanced_transcription_with_speaker_detection(mock_database, sample_video):
    """Test enhanced transcription with speaker diarization."""
    from workers.enhanced_transcription import transcribe_with_speaker_detection
    
    # Mock database responses
    mock_database.get_video.return_value = sample_video
    mock_database.update_job.return_value = None
    mock_database.create_transcript.return_value = {"id": "test-transcript-id"}
    mock_database.storage.download_file.return_value = b"fake video data"
    
    # Mock WhisperX
    with patch('workers.enhanced_transcription.WHISPERX_AVAILABLE', True):
        with patch('whisperx.load_model') as mock_load:
            mock_model = Mock()
            mock_model.transcribe.return_value = {"segments": [], "language": "en"}
            mock_load.return_value = mock_model
            
            with patch('whisperx.load_align_model') as mock_align:
                mock_align.return_value = (Mock(), Mock())
                
                with patch('whisperx.align') as mock_align_func:
                    mock_align_func.return_value = {"segments": []}
                    
                    with patch('whisperx.DiarizationPipeline') as mock_diarize:
                        mock_diarize.return_value.return_value = []
                        
                        with patch('whisperx.assign_word_speakers') as mock_assign:
                            mock_assign.return_value = {"segments": [
                                {
                                    "start": 0.0,
                                    "end": 3.0,
                                    "text": "Test speech",
                                    "speaker": "SPEAKER_00",
                                    "words": []
                                }
                            ]}
                            
                            with patch('moviepy.editor.VideoFileClip'), \
                                 patch('tempfile.NamedTemporaryFile') as mock_temp:
                                mock_temp.return_value.__enter__.return_value.name = "temp_file"
                                
                                # Run enhanced transcription
                                transcribe_with_speaker_detection("test-video-id", "test-job-id")
                                
                                # Verify database calls
                                mock_database.create_transcript.assert_called_once()

def test_video_processor_youtube_download():
    """Test YouTube video download."""
    from workers.video_processor import download_youtube_video
    
    with patch('workers.video_processor.db') as mock_db:
        mock_db.update_video.return_value = None
        mock_db.storage.upload_file.return_value = "uploaded_path"
        
        # Mock yt-dlp
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_ydl.return_value.__enter__.return_value.extract_info.side_effect = [
                {"title": "Test Video", "duration": 120},  # Info extraction
                {"title": "Test Video", "duration": 120}   # Download
            ]
            mock_ydl.return_value.__enter__.return_value.prepare_filename.return_value = "temp_video.mp4"
            
            with patch('os.path.getsize', return_value=1024000), \
                 patch('os.path.exists', return_value=True), \
                 patch('os.remove'), \
                 patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = b"video data"
                
                # Run download
                download_youtube_video("test-video-id", "https://youtube.com/watch?v=test")
                
                # Verify database update
                mock_db.update_video.assert_called()

def test_video_processor_file_processing():
    """Test video file processing."""
    from workers.video_processor import process_video
    
    with patch('workers.video_processor.db') as mock_db:
        mock_db.get_video.return_value = {
            "id": "test-video-id",
            "file_path": "videos/test.mp4"
        }
        mock_db.update_video.return_value = None
        mock_db.storage.download_file.return_value = b"video data"
        
        with patch('moviepy.editor.VideoFileClip') as mock_clip:
            mock_clip.return_value.__enter__.return_value.duration = 120.0
            mock_clip.return_value.__enter__.return_value.w = 1920
            mock_clip.return_value.__enter__.return_value.h = 1080
            
            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp.return_value.__enter__.return_value.name = "temp_file.mp4"
                
                # Run processing
                process_video("test-video-id")
                
                # Verify database update
                mock_db.update_video.assert_called()

def test_highlight_detector_viral_keyword_scoring():
    """Test viral keyword scoring in highlight detection."""
    from workers.highlight_detector import calculate_keyword_score, VIRAL_KEYWORDS
    
    # Test high scoring text
    high_score_text = "This is amazing and incredible wow"
    score = calculate_keyword_score(high_score_text)
    assert score > 0.5
    
    # Test low scoring text
    low_score_text = "This is a normal sentence"
    score = calculate_keyword_score(low_score_text)
    assert score < 0.2
    
    # Test empty text
    empty_score = calculate_keyword_score("")
    assert empty_score == 0.0

def test_highlight_detector_sentiment_analysis():
    """Test sentiment analysis in highlight detection."""
    from workers.highlight_detector import calculate_sentiment_score
    
    with patch('workers.highlight_detector.sentiment_analyzer') as mock_analyzer:
        # Mock positive sentiment
        mock_analyzer.return_value = [[
            {"label": "POSITIVE", "score": 0.95},
            {"label": "NEGATIVE", "score": 0.05}
        ]]
        
        score = calculate_sentiment_score("This is fantastic!")
        assert score == 0.95
        
        # Mock negative sentiment
        mock_analyzer.return_value = [[
            {"label": "NEGATIVE", "score": 0.8},
            {"label": "POSITIVE", "score": 0.2}
        ]]
        
        score = calculate_sentiment_score("This is terrible")
        assert score == 0.5  # Default for non-positive

def test_video_editor_aspect_ratio_conversion(mock_video_clip):
    """Test aspect ratio conversion."""
    from workers.video_editor import apply_aspect_ratio
    
    # Test vertical conversion
    mock_video_clip.size = (1920, 1080)
    result = apply_aspect_ratio(mock_video_clip, "9:16")
    assert result is not None
    
    # Test square conversion
    result = apply_aspect_ratio(mock_video_clip, "1:1")
    assert result is not None
    
    # Test horizontal conversion
    result = apply_aspect_ratio(mock_video_clip, "16:9")
    assert result is not None

def test_video_editor_subtitle_addition(mock_video_clip, sample_transcript):
    """Test subtitle addition to video."""
    from workers.video_editor import add_subtitles
    
    mock_video_clip.duration = 30.0
    mock_video_clip.w = 1920
    
    with patch('moviepy.editor.TextClip') as mock_text:
        mock_text_instance = Mock()
        mock_text.return_value = mock_text_instance
        mock_text_instance.set_position.return_value = mock_text_instance
        mock_text_instance.set_duration.return_value = mock_text_instance
        mock_text_instance.set_start.return_value = mock_text_instance
        
        with patch('moviepy.editor.CompositeVideoClip') as mock_composite:
            mock_composite.return_value = mock_video_clip
            
            result = add_subtitles(mock_video_clip, sample_transcript, 0.0, 10.0)
            assert result is not None

def test_worker_error_handling(mock_database):
    """Test error handling in workers."""
    from workers.transcription import transcribe_video
    
    # Mock database error
    mock_database.get_video.side_effect = Exception("Database error")
    mock_database.update_job.return_value = None
    
    # Run transcription (should handle error gracefully)
    transcribe_video("test-video-id", "test-job-id")
    
    # Verify error was logged in job
    error_calls = [call for call in mock_database.update_job.call_args_list 
                  if 'error_message' in call[0][1]]
    assert len(error_calls) > 0
