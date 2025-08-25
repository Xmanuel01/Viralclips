import os
import sys
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
import redis
from rq import Queue

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from shared.schemas import (
    VideoUploadRequest, VideoUploadResponse, TranscribeRequest,
    HighlightRequest, ExportRequest, JobStatusResponse, JobStatus
)
from database import Database, Storage
from utils import generate_id, extract_youtube_video_id, is_valid_video_extension
from paystack_service import PaystackService, get_plan_amount
from monitoring import (
    log_performance, handle_exceptions, metrics, health_checker, 
    setup_monitoring, APIError, ValidationError, AuthenticationError
)
from security import (
    rate_limit, InputValidator, SecurityHeaders, login_tracker,
    PasswordValidator, generate_csp_header
)

app = FastAPI(title="Viral Clips API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection for job queue
redis_conn = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"))
job_queue = Queue(connection=redis_conn)

# Database and storage instances
db = Database()
storage = Storage(db.supabase)
paystack = PaystackService()

security = HTTPBearer()


async def get_current_user(token: str = Depends(security)):
    """Get current user from JWT token."""
    try:
        # Verify JWT token with Supabase
        response = db.supabase.auth.get_user(token.credentials)
        if response.user:
            user = await db.get_user(response.user.id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")


@app.get("/")
async def root():
    return {"message": "Viral Clips API", "version": "1.0.0"}


@app.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    request: VideoUploadRequest,
    current_user: dict = Depends(get_current_user)
):
    """Upload a video file or YouTube link."""
    try:
        video_id = generate_id()
        
        # Create video record
        video_data = {
            "id": video_id,
            "user_id": current_user["id"],
            "title": request.title,
            "source": request.source.value,
            "source_url": str(request.source_url) if request.source_url else None,
            "file_path": f"videos/{video_id}.mp4",
            "duration": 0,  # Will be updated after processing
            "file_size": 0,  # Will be updated after processing
            "status": JobStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        video = await db.create_video(video_data)
        
        # Create processing job
        job_id = generate_id()
        job_data = {
            "id": job_id,
            "user_id": current_user["id"],
            "job_type": "upload",
            "status": JobStatus.PENDING.value,
            "progress": 0,
            "metadata": {"video_id": video_id},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        job = await db.create_job(job_data)
        
        # Queue video processing job
        if request.source == "youtube":
            job_queue.enqueue('workers.video_processor.download_youtube_video', 
                            video_id, str(request.source_url))
        
        # Generate upload URL for direct file upload
        upload_url = None
        if request.source == "upload":
            upload_url = storage.get_public_url(f"uploads/{video_id}")
        
        return VideoUploadResponse(
            video_id=video_id,
            upload_url=upload_url,
            job_id=job_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-file")
async def upload_file(
    video_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Handle direct file upload."""
    try:
        # Validate file
        if not is_valid_video_extension(file.filename):
            raise HTTPException(status_code=400, detail="Invalid video file format")
        
        # Check file size limits
        file_content = await file.read()
        max_size = 1024 * 1024 * 1024 if current_user["subscription_tier"] == "premium" else 100 * 1024 * 1024
        
        if len(file_content) > max_size:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Upload to storage
        file_path = f"videos/{video_id}.mp4"
        storage.upload_file(file_path, file_content)
        
        # Update video record
        await db.update_video(video_id, {
            "file_size": len(file_content),
            "status": JobStatus.PROCESSING.value,
            "updated_at": datetime.utcnow().isoformat()
        })
        
        # Queue transcription job
        job_queue.enqueue('workers.video_processor.process_video', video_id)
        
        return {"message": "File uploaded successfully", "video_id": video_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transcribe")
async def transcribe_video(
    request: TranscribeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Start video transcription."""
    try:
        video = await db.get_video(request.video_id)
        if not video or video["user_id"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Create transcription job
        job_id = generate_id()
        job_data = {
            "id": job_id,
            "user_id": current_user["id"],
            "job_type": "transcribe",
            "status": JobStatus.PENDING.value,
            "progress": 0,
            "metadata": {"video_id": request.video_id},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        job = await db.create_job(job_data)
        
        # Queue transcription
        job_queue.enqueue('workers.transcription.transcribe_video', request.video_id, job_id)
        
        return {"job_id": job_id, "message": "Transcription started"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/highlight")
async def detect_highlights(
    request: HighlightRequest,
    current_user: dict = Depends(get_current_user)
):
    """Detect highlights in a video."""
    try:
        video = await db.get_video(request.video_id)
        if not video or video["user_id"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Check if transcript exists
        transcript = await db.get_transcript(request.video_id)
        if not transcript:
            raise HTTPException(status_code=400, detail="Video must be transcribed first")
        
        # Create highlight detection job
        job_id = generate_id()
        job_data = {
            "id": job_id,
            "user_id": current_user["id"],
            "job_type": "highlight",
            "status": JobStatus.PENDING.value,
            "progress": 0,
            "metadata": {"video_id": request.video_id, "max_highlights": request.max_highlights},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        job = await db.create_job(job_data)
        
        # Queue highlight detection
        job_queue.enqueue('workers.highlight_detector.detect_highlights', 
                         request.video_id, request.max_highlights, job_id)
        
        return {"job_id": job_id, "message": "Highlight detection started"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export")
async def export_clip(
    request: ExportRequest,
    current_user: dict = Depends(get_current_user)
):
    """Export a highlight as a clip."""
    try:
        # Check daily limits
        daily_clips = await db.get_user_daily_clips_count(current_user["id"])
        max_clips = 20 if current_user["subscription_tier"] == "premium" else 3
        
        if daily_clips >= max_clips:
            raise HTTPException(status_code=429, detail="Daily clip limit reached")
        
        # Get highlight
        highlights = await db.get_highlights(request.highlight_id)
        if not highlights:
            raise HTTPException(status_code=404, detail="Highlight not found")
        
        highlight = highlights[0]
        
        # Create clip record
        clip_id = generate_id()
        resolution = "1080p" if current_user["subscription_tier"] == "premium" else "720p"
        has_watermark = current_user["subscription_tier"] == "free"
        
        clip_data = {
            "id": clip_id,
            "video_id": highlight["video_id"],
            "highlight_id": request.highlight_id,
            "user_id": current_user["id"],
            "title": highlight["title"],
            "file_path": f"clips/{clip_id}_{request.export_format.value}_{resolution}.mp4",
            "export_format": request.export_format.value,
            "resolution": resolution,
            "has_watermark": has_watermark,
            "file_size": 0,  # Will be updated after processing
            "status": JobStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat()
        }
        
        clip = await db.create_clip(clip_data)
        
        # Create export job
        job_id = generate_id()
        job_data = {
            "id": job_id,
            "user_id": current_user["id"],
            "job_type": "export",
            "status": JobStatus.PENDING.value,
            "progress": 0,
            "metadata": {
                "clip_id": clip_id,
                "include_subtitles": request.include_subtitles
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        job = await db.create_job(job_data)
        
        # Queue clip export
        job_queue.enqueue('workers.video_editor.export_clip', 
                         clip_id, request.include_subtitles, job_id)
        
        return {"job_id": job_id, "clip_id": clip_id, "message": "Clip export started"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get job status and progress."""
    try:
        job = await db.get_job(job_id)
        if not job or job["user_id"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatusResponse(
            job_id=job_id,
            status=JobStatus(job["status"]),
            progress=job["progress"],
            error_message=job.get("error_message"),
            result=job.get("metadata", {})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/videos")
async def get_user_videos(current_user: dict = Depends(get_current_user)):
    """Get user's videos."""
    try:
        videos = await db.get_user_videos(current_user["id"])
        return {"videos": videos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/videos/{video_id}/highlights")
async def get_video_highlights(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get highlights for a video."""
    try:
        video = await db.get_video(video_id)
        if not video or video["user_id"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Video not found")
        
        highlights = await db.get_highlights(video_id)
        return {"highlights": highlights}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/clips")
async def get_user_clips(current_user: dict = Depends(get_current_user)):
    """Get user's clips."""
    try:
        clips = await db.get_user_clips(current_user["id"])
        return {"clips": clips}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/clips/{clip_id}/download")
async def download_clip(
    clip_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get download URL for a clip."""
    try:
        clip = await db.get_clip(clip_id)
        if not clip or clip["user_id"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Clip not found")
        
        if clip["status"] != JobStatus.COMPLETED.value:
            raise HTTPException(status_code=400, detail="Clip not ready for download")
        
        download_url = storage.get_public_url(clip["file_path"])
        return {"download_url": download_url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/stats")
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """Get user statistics."""
    try:
        daily_clips = await db.get_user_daily_clips_count(current_user["id"])
        max_clips = 20 if current_user["subscription_tier"] == "premium" else 3
        
        return {
            "subscription_tier": current_user["subscription_tier"],
            "clips_used_today": daily_clips,
            "clips_remaining": max(0, max_clips - daily_clips),
            "max_clips_per_day": max_clips
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Paystack Payment Endpoints
@app.get("/payment/plans")
async def get_payment_plans():
    """Get available payment plans."""
    try:
        from paystack_service import PAYSTACK_PLANS
        return {"plans": PAYSTACK_PLANS}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/payment/initialize")
async def initialize_payment(
    plan_type: str,
    current_user: dict = Depends(get_current_user)
):
    """Initialize payment for a subscription plan."""
    try:
        # Validate plan type
        if plan_type not in ["premium", "lifetime"]:
            raise HTTPException(status_code=400, detail="Invalid plan type")
        
        # Get plan amount
        amount = get_plan_amount(plan_type)
        
        # Get payment URL from Paystack
        payment_url = paystack.get_payment_url(
            email=current_user["email"],
            amount=amount,
            plan_type=plan_type,
            user_id=current_user["id"]
        )
        
        return {
            "payment_url": payment_url,
            "plan_type": plan_type,
            "amount": amount / 100  # Convert back to dollars for display
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/payment/verify")
async def verify_payment(
    reference: str,
    current_user: dict = Depends(get_current_user)
):
    """Verify payment and upgrade user subscription."""
    try:
        # Verify transaction with Paystack
        transaction = paystack.verify_transaction(reference)
        
        if not transaction.get("status") or transaction["data"]["status"] != "success":
            raise HTTPException(status_code=400, detail="Payment verification failed")
        
        # Process successful payment
        payment_details = paystack.process_successful_payment(transaction["data"])
        
        # Update user subscription
        subscription_updates = {
            "subscription_tier": payment_details["subscription_tier"],
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Reset daily clips for premium users
        if payment_details["subscription_tier"] in ["premium", "lifetime"]:
            subscription_updates["clips_used_today"] = 0
        
        updated_user = await db.update_user(current_user["id"], subscription_updates)
        
        return {
            "message": "Payment successful! Subscription upgraded.",
            "subscription_tier": payment_details["subscription_tier"],
            "amount_paid": payment_details["amount_paid"],
            "transaction_reference": payment_details["transaction_reference"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/payment/webhook")
async def paystack_webhook(
    request: Request
):
    """Handle Paystack webhook for payment events."""
    try:
        # Get raw body and signature
        body = await request.body()
        signature = request.headers.get("x-paystack-signature", "")
        
        # Verify webhook signature
        if not paystack.verify_webhook(body, signature):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        # Parse webhook data
        import json
        webhook_data = json.loads(body.decode('utf-8'))
        
        event = webhook_data.get("event")
        data = webhook_data.get("data")
        
        if event == "charge.success":
            # Handle successful payment
            metadata = data.get("metadata", {})
            user_id = metadata.get("user_id")
            
            if user_id:
                payment_details = paystack.process_successful_payment(data)
                
                # Update user subscription
                await db.update_user(user_id, {
                    "subscription_tier": payment_details["subscription_tier"],
                    "clips_used_today": 0,  # Reset clips for new subscribers
                    "updated_at": datetime.utcnow().isoformat()
                })
                
                print(f"Subscription upgraded for user {user_id} to {payment_details['subscription_tier']}")
        
        elif event == "subscription.disable":
            # Handle subscription cancellation
            customer_email = data.get("customer", {}).get("email")
            if customer_email:
                # Find user by email and downgrade
                # This would require additional database query
                pass
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
