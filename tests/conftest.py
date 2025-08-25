import pytest
import asyncio
import os
import sys
import tempfile
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Add project paths to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'workers'))

# Mock imports that might not be available
try:
    import redis
except ImportError:
    redis = Mock()

try:
    from supabase import create_client
except ImportError:
    create_client = Mock()

# Set test environment
os.environ["TESTING"] = "true"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # Test database

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    with patch('redis.from_url') as mock_redis:
        mock_client = Mock()
        mock_redis.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    mock_client = Mock()
    mock_client.table.return_value = mock_client
    mock_client.select.return_value = mock_client
    mock_client.insert.return_value = mock_client
    mock_client.update.return_value = mock_client
    mock_client.eq.return_value = mock_client
    mock_client.execute.return_value = Mock(data=[{'id': 'test-id', 'email': 'test@example.com'}])
    return mock_client

@pytest.fixture
def mock_database(mock_supabase):
    """Mock database instance."""
    with patch('shared.database.Database') as MockDatabase:
        db_instance = Mock()
        db_instance.supabase = mock_supabase
        MockDatabase.return_value = db_instance
        yield db_instance

@pytest.fixture
def mock_storage():
    """Mock storage instance."""
    storage = Mock()
    storage.upload_file.return_value = "test-path"
    storage.download_file.return_value = b"test-data"
    storage.get_public_url.return_value = "https://example.com/test.mp4"
    return storage

@pytest.fixture
def client(mock_database, mock_redis, mock_storage):
    """FastAPI test client with mocked dependencies."""
    with patch('backend.main.db', mock_database), \
         patch('backend.main.storage', mock_storage), \
         patch('backend.main.redis_conn', mock_redis):
        
        from backend.main import app
        return TestClient(app)

@pytest.fixture
def sample_user():
    """Sample user data for testing."""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "subscription_tier": "free",
        "clips_used_today": 0,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }

@pytest.fixture
def sample_video():
    """Sample video data for testing."""
    return {
        "id": "test-video-id",
        "user_id": "test-user-id",
        "title": "Test Video",
        "source": "upload",
        "source_url": None,
        "file_path": "videos/test-video-id.mp4",
        "duration": 120.5,
        "file_size": 1024000,
        "status": "completed",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }

@pytest.fixture
def sample_transcript():
    """Sample transcript data for testing."""
    return {
        "id": "test-transcript-id",
        "video_id": "test-video-id",
        "text": "This is a sample transcript for testing purposes.",
        "segments": [
            {
                "start": 0.0,
                "end": 3.5,
                "text": "This is a sample transcript",
                "words": [
                    {"start": 0.0, "end": 0.5, "word": "This", "probability": 0.99},
                    {"start": 0.5, "end": 0.8, "word": "is", "probability": 0.98}
                ]
            }
        ],
        "language": "en",
        "created_at": "2025-01-01T00:00:00Z"
    }

@pytest.fixture
def sample_highlight():
    """Sample highlight data for testing."""
    return {
        "id": "test-highlight-id",
        "video_id": "test-video-id",
        "start_time": 10.0,
        "end_time": 30.0,
        "score": 0.85,
        "keywords": ["amazing", "incredible", "wow"],
        "title": "Amazing moment from the video",
        "description": "This is a viral moment",
        "created_at": "2025-01-01T00:00:00Z"
    }

@pytest.fixture
def sample_clip():
    """Sample clip data for testing."""
    return {
        "id": "test-clip-id",
        "video_id": "test-video-id",
        "highlight_id": "test-highlight-id",
        "user_id": "test-user-id",
        "title": "Test Clip",
        "file_path": "clips/test-clip-id_9:16_720p.mp4",
        "export_format": "9:16",
        "resolution": "720p",
        "has_watermark": True,
        "file_size": 512000,
        "status": "completed",
        "created_at": "2025-01-01T00:00:00Z"
    }

@pytest.fixture
def sample_job():
    """Sample job data for testing."""
    return {
        "id": "test-job-id",
        "user_id": "test-user-id",
        "job_type": "transcribe",
        "status": "processing",
        "progress": 50,
        "error_message": None,
        "metadata": {"video_id": "test-video-id"},
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }

@pytest.fixture
def auth_headers(sample_user):
    """Authentication headers for testing."""
    # Mock JWT token
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJzdXBhYmFzZSIsInN1YiI6InRlc3QtdXNlci1pZCJ9.test"
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def temp_video_file():
    """Create a temporary video file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
        # Write some dummy video data
        temp_file.write(b"fake video data for testing")
        temp_file.flush()
        yield temp_file.name
    
    # Clean up
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)

@pytest.fixture
def mock_paystack():
    """Mock Paystack service for testing."""
    paystack = Mock()
    paystack.get_payment_url.return_value = "https://checkout.paystack.com/test"
    paystack.verify_transaction.return_value = {
        "status": True,
        "data": {
            "status": "success",
            "amount": 1500,
            "metadata": {"user_id": "test-user-id", "plan_type": "premium"},
            "reference": "test-reference"
        }
    }
    paystack.verify_webhook.return_value = True
    return paystack

@pytest.fixture
def mock_job_queue():
    """Mock RQ job queue for testing."""
    queue = Mock()
    queue.enqueue.return_value = Mock(id="test-job-id")
    return queue

@pytest.fixture
def mock_whisper_model():
    """Mock Whisper model for testing."""
    with patch('faster_whisper.WhisperModel') as MockWhisper:
        model = Mock()
        model.transcribe.return_value = (
            [Mock(start=0.0, end=3.5, text="Test transcript", words=[])],
            Mock(language="en")
        )
        MockWhisper.return_value = model
        yield model

@pytest.fixture
def mock_video_clip():
    """Mock MoviePy VideoFileClip for testing."""
    with patch('moviepy.editor.VideoFileClip') as MockVideoClip:
        clip = Mock()
        clip.duration = 120.0
        clip.w = 1920
        clip.h = 1080
        clip.size = (1920, 1080)
        clip.fps = 30.0
        clip.audio = Mock()
        clip.subclip.return_value = clip
        clip.resize.return_value = clip
        clip.crop.return_value = clip
        MockVideoClip.return_value.__enter__.return_value = clip
        yield clip
