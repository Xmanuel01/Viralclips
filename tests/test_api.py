import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
import json

def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Viral Clips API", "version": "1.0.0"}

def test_upload_video_youtube_success(client, auth_headers, sample_user, mock_database):
    """Test successful YouTube video upload."""
    # Mock authentication
    with patch('backend.main.get_current_user', return_value=sample_user):
        # Mock database operations
        mock_database.create_video.return_value = {"id": "test-video-id"}
        mock_database.create_job.return_value = {"id": "test-job-id"}
        
        response = client.post(
            "/upload",
            json={
                "title": "Test YouTube Video",
                "source": "youtube",
                "source_url": "https://youtube.com/watch?v=test"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "video_id" in data
        assert "job_id" in data
        assert data["upload_url"] is None  # YouTube doesn't need upload URL

def test_upload_video_file_success(client, auth_headers, sample_user, mock_database):
    """Test successful file upload request."""
    with patch('backend.main.get_current_user', return_value=sample_user):
        mock_database.create_video.return_value = {"id": "test-video-id"}
        mock_database.create_job.return_value = {"id": "test-job-id"}
        
        response = client.post(
            "/upload",
            json={
                "title": "Test File Upload",
                "source": "upload"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "video_id" in data
        assert "job_id" in data
        assert "upload_url" in data

def test_upload_video_unauthorized(client):
    """Test video upload without authentication."""
    response = client.post(
        "/upload",
        json={
            "title": "Test Video",
            "source": "upload"
        }
    )
    
    assert response.status_code == 401

def test_transcribe_video_success(client, auth_headers, sample_user, sample_video, mock_database):
    """Test successful video transcription request."""
    with patch('backend.main.get_current_user', return_value=sample_user):
        mock_database.get_video.return_value = sample_video
        mock_database.create_job.return_value = {"id": "test-job-id"}
        
        response = client.post(
            "/transcribe",
            json={"video_id": "test-video-id"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "message" in data

def test_transcribe_video_not_found(client, auth_headers, sample_user, mock_database):
    """Test transcription request for non-existent video."""
    with patch('backend.main.get_current_user', return_value=sample_user):
        mock_database.get_video.return_value = None
        
        response = client.post(
            "/transcribe",
            json={"video_id": "non-existent-id"},
            headers=auth_headers
        )
        
        assert response.status_code == 404

def test_detect_highlights_success(client, auth_headers, sample_user, sample_video, sample_transcript, mock_database):
    """Test successful highlight detection."""
    with patch('backend.main.get_current_user', return_value=sample_user):
        mock_database.get_video.return_value = sample_video
        mock_database.get_transcript.return_value = sample_transcript
        mock_database.create_job.return_value = {"id": "test-job-id"}
        
        response = client.post(
            "/highlight",
            json={
                "video_id": "test-video-id",
                "max_highlights": 5
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "message" in data

def test_detect_highlights_no_transcript(client, auth_headers, sample_user, sample_video, mock_database):
    """Test highlight detection without transcript."""
    with patch('backend.main.get_current_user', return_value=sample_user):
        mock_database.get_video.return_value = sample_video
        mock_database.get_transcript.return_value = None
        
        response = client.post(
            "/highlight",
            json={
                "video_id": "test-video-id",
                "max_highlights": 5
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "must be transcribed first" in response.json()["detail"]

def test_export_clip_success(client, auth_headers, sample_user, sample_highlight, mock_database):
    """Test successful clip export."""
    with patch('backend.main.get_current_user', return_value=sample_user):
        mock_database.get_user_daily_clips_count.return_value = 1  # Under limit
        mock_database.get_highlights.return_value = [sample_highlight]
        mock_database.create_clip.return_value = {"id": "test-clip-id"}
        mock_database.create_job.return_value = {"id": "test-job-id"}
        
        response = client.post(
            "/export",
            json={
                "highlight_id": "test-highlight-id",
                "export_format": "9:16",
                "include_subtitles": True
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "clip_id" in data
        assert "message" in data

def test_export_clip_daily_limit_exceeded(client, auth_headers, sample_user, mock_database):
    """Test clip export when daily limit is exceeded."""
    with patch('backend.main.get_current_user', return_value=sample_user):
        mock_database.get_user_daily_clips_count.return_value = 5  # Over free limit
        
        response = client.post(
            "/export",
            json={
                "highlight_id": "test-highlight-id",
                "export_format": "9:16",
                "include_subtitles": True
            },
            headers=auth_headers
        )
        
        assert response.status_code == 429
        assert "Daily clip limit reached" in response.json()["detail"]

def test_get_job_status_success(client, auth_headers, sample_user, sample_job, mock_database):
    """Test successful job status retrieval."""
    with patch('backend.main.get_current_user', return_value=sample_user):
        mock_database.get_job.return_value = sample_job
        
        response = client.get(
            "/jobs/test-job-id/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-id"
        assert data["status"] == "processing"
        assert data["progress"] == 50

def test_get_job_status_not_found(client, auth_headers, sample_user, mock_database):
    """Test job status for non-existent job."""
    with patch('backend.main.get_current_user', return_value=sample_user):
        mock_database.get_job.return_value = None
        
        response = client.get(
            "/jobs/non-existent-id/status",
            headers=auth_headers
        )
        
        assert response.status_code == 404

def test_get_user_videos(client, auth_headers, sample_user, sample_video, mock_database):
    """Test getting user's videos."""
    with patch('backend.main.get_current_user', return_value=sample_user):
        mock_database.get_user_videos.return_value = [sample_video]
        
        response = client.get("/videos", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "videos" in data
        assert len(data["videos"]) == 1
        assert data["videos"][0]["id"] == "test-video-id"

def test_get_video_highlights(client, auth_headers, sample_user, sample_video, sample_highlight, mock_database):
    """Test getting video highlights."""
    with patch('backend.main.get_current_user', return_value=sample_user):
        mock_database.get_video.return_value = sample_video
        mock_database.get_highlights.return_value = [sample_highlight]
        
        response = client.get(
            "/videos/test-video-id/highlights",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "highlights" in data
        assert len(data["highlights"]) == 1
        assert data["highlights"][0]["id"] == "test-highlight-id"

def test_get_user_clips(client, auth_headers, sample_user, sample_clip, mock_database):
    """Test getting user's clips."""
    with patch('backend.main.get_current_user', return_value=sample_user):
        mock_database.get_user_clips.return_value = [sample_clip]
        
        response = client.get("/clips", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "clips" in data
        assert len(data["clips"]) == 1
        assert data["clips"][0]["id"] == "test-clip-id"

def test_download_clip_success(client, auth_headers, sample_user, mock_database):
    """Test successful clip download."""
    completed_clip = {
        "id": "test-clip-id",
        "user_id": "test-user-id",
        "status": "completed",
        "file_path": "clips/test-clip-id.mp4"
    }
    
    with patch('backend.main.get_current_user', return_value=sample_user):
        mock_database.get_clip.return_value = completed_clip
        
        response = client.get(
            "/clips/test-clip-id/download",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "download_url" in data

def test_download_clip_not_ready(client, auth_headers, sample_user, sample_clip, mock_database):
    """Test download for clip that's not ready."""
    processing_clip = {**sample_clip, "status": "processing"}
    
    with patch('backend.main.get_current_user', return_value=sample_user):
        mock_database.get_clip.return_value = processing_clip
        
        response = client.get(
            "/clips/test-clip-id/download",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "not ready for download" in response.json()["detail"]

def test_get_user_stats(client, auth_headers, sample_user, mock_database):
    """Test getting user statistics."""
    with patch('backend.main.get_current_user', return_value=sample_user):
        mock_database.get_user_daily_clips_count.return_value = 2
        
        response = client.get("/user/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["subscription_tier"] == "free"
        assert data["clips_used_today"] == 2
        assert data["clips_remaining"] == 1
        assert data["max_clips_per_day"] == 3

def test_get_payment_plans(client):
    """Test getting payment plans."""
    response = client.get("/payment/plans")
    
    assert response.status_code == 200
    data = response.json()
    assert "plans" in data

def test_initialize_payment_success(client, auth_headers, sample_user, mock_paystack):
    """Test payment initialization."""
    with patch('backend.main.get_current_user', return_value=sample_user), \
         patch('backend.main.paystack', mock_paystack):
        
        response = client.post(
            "/payment/initialize",
            json={"plan_type": "premium"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "payment_url" in data
        assert "plan_type" in data
        assert "amount" in data

def test_initialize_payment_invalid_plan(client, auth_headers, sample_user):
    """Test payment initialization with invalid plan."""
    with patch('backend.main.get_current_user', return_value=sample_user):
        
        response = client.post(
            "/payment/initialize",
            json={"plan_type": "invalid_plan"},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Invalid plan type" in response.json()["detail"]

def test_verify_payment_success(client, auth_headers, sample_user, mock_paystack, mock_database):
    """Test successful payment verification."""
    with patch('backend.main.get_current_user', return_value=sample_user), \
         patch('backend.main.paystack', mock_paystack):
        
        mock_paystack.process_successful_payment.return_value = {
            "subscription_tier": "premium",
            "amount_paid": 15.0,
            "transaction_reference": "test-ref"
        }
        mock_database.update_user.return_value = sample_user
        
        response = client.post(
            "/payment/verify",
            json={"reference": "test-reference"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["subscription_tier"] == "premium"
        assert data["amount_paid"] == 15.0

def test_verify_payment_failed(client, auth_headers, sample_user, mock_paystack):
    """Test failed payment verification."""
    with patch('backend.main.get_current_user', return_value=sample_user), \
         patch('backend.main.paystack', mock_paystack):
        
        mock_paystack.verify_transaction.return_value = {
            "status": False,
            "data": {"status": "failed"}
        }
        
        response = client.post(
            "/payment/verify",
            json={"reference": "failed-reference"},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "verification failed" in response.json()["detail"]
