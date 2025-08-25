"""
Script Management API Routes
Handles AI script generation, editing, and optimization
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
import uuid
from datetime import datetime

from ...models.schemas import (
    Script, ScriptCreate, ScriptUpdate, ApiResponse, 
    User, Video, ProcessClipRequest, PaginatedResponse
)
from ...services.auth import get_current_user
from ...services.database import get_database
from ...services.analytics import track_event
from ...tasks.script_tasks import generate_script_task, optimize_script_task
from ...utils.permissions import check_feature_access

router = APIRouter(prefix="/scripts", tags=["scripts"])

@router.post("/generate", response_model=ApiResponse[Script])
async def generate_script(
    request: ScriptCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Generate AI script from video transcription"""
    
    # Check if user has access to script generation
    if not await check_feature_access(current_user, "script_generation"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Script generation requires a paid subscription"
        )
    
    # Verify video exists and belongs to user
    video = await db.videos.get_by_id_and_user(request.video_id, current_user.id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Check if video has transcription
    transcription = await db.transcriptions.get_by_video_id(request.video_id)
    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video must be transcribed before script generation"
        )
    
    # Create script record
    script_data = {
        "id": str(uuid.uuid4()),
        "video_id": request.video_id,
        "user_id": current_user.id,
        "title": request.title,
        "content": "Generating script...",
        "platform_optimization": request.platform_optimization,
        "is_ai_generated": True,
        "status": "draft"
    }
    
    script = await db.scripts.create(script_data)
    
    # Queue script generation task
    task_id = generate_script_task.delay(
        script_id=script.id,
        transcription_text=transcription.full_text,
        video_duration=video.duration_seconds or 60,
        platform=request.platform_optimization,
        custom_prompt=request.custom_prompt,
        include_timestamps=request.include_timestamps
    )
    
    # Track analytics
    background_tasks.add_task(
        track_event,
        user_id=current_user.id,
        event_type="script_generation_started",
        event_data={
            "script_id": script.id,
            "video_id": request.video_id,
            "platform": request.platform_optimization,
            "has_custom_prompt": bool(request.custom_prompt)
        }
    )
    
    return ApiResponse(
        success=True,
        data=script,
        message="Script generation started"
    )

@router.get("/", response_model=ApiResponse[PaginatedResponse[Script]])
async def list_scripts(
    page: int = 1,
    page_size: int = 20,
    video_id: Optional[str] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """List user's scripts with filtering and pagination"""
    
    filters = {"user_id": current_user.id}
    if video_id:
        filters["video_id"] = video_id
    if platform:
        filters["platform_optimization"] = platform
    if status:
        filters["status"] = status
    
    scripts, total = await db.scripts.list_paginated(
        filters=filters,
        page=page,
        page_size=page_size,
        order_by="created_at DESC"
    )
    
    return ApiResponse(
        success=True,
        data=PaginatedResponse(
            data=scripts,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
    )

@router.get("/{script_id}", response_model=ApiResponse[Script])
async def get_script(
    script_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get a specific script"""
    
    script = await db.scripts.get_by_id_and_user(script_id, current_user.id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    
    return ApiResponse(success=True, data=script)

@router.put("/{script_id}", response_model=ApiResponse[Script])
async def update_script(
    script_id: str,
    request: ScriptUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Update a script"""
    
    script = await db.scripts.get_by_id_and_user(script_id, current_user.id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    
    # Update script
    update_data = request.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    updated_script = await db.scripts.update(script_id, update_data)
    
    # Track analytics
    background_tasks.add_task(
        track_event,
        user_id=current_user.id,
        event_type="script_updated",
        event_data={
            "script_id": script_id,
            "fields_updated": list(update_data.keys())
        }
    )
    
    return ApiResponse(
        success=True,
        data=updated_script,
        message="Script updated successfully"
    )

@router.post("/{script_id}/optimize", response_model=ApiResponse[dict])
async def optimize_script(
    script_id: str,
    target_platform: str,
    optimization_goals: Optional[List[str]] = None,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Optimize an existing script for better engagement"""
    
    # Check if user has access to script optimization
    if not await check_feature_access(current_user, "script_optimization"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Script optimization requires a Pro subscription"
        )
    
    script = await db.scripts.get_by_id_and_user(script_id, current_user.id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    
    # Queue optimization task
    task_id = optimize_script_task.delay(
        script_id=script_id,
        original_content=script.content,
        target_platform=target_platform,
        optimization_goals=optimization_goals or ['engagement', 'virality', 'platform_fit']
    )
    
    # Track analytics
    background_tasks.add_task(
        track_event,
        user_id=current_user.id,
        event_type="script_optimization_started",
        event_data={
            "script_id": script_id,
            "target_platform": target_platform,
            "optimization_goals": optimization_goals
        }
    )
    
    return ApiResponse(
        success=True,
        data={"task_id": task_id},
        message="Script optimization started"
    )

@router.delete("/{script_id}", response_model=ApiResponse[dict])
async def delete_script(
    script_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Delete a script"""
    
    script = await db.scripts.get_by_id_and_user(script_id, current_user.id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    
    await db.scripts.delete(script_id)
    
    # Track analytics
    background_tasks.add_task(
        track_event,
        user_id=current_user.id,
        event_type="script_deleted",
        event_data={"script_id": script_id}
    )
    
    return ApiResponse(
        success=True,
        message="Script deleted successfully"
    )

@router.post("/{script_id}/duplicate", response_model=ApiResponse[Script])
async def duplicate_script(
    script_id: str,
    new_platform: Optional[str] = None,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Duplicate a script, optionally for a different platform"""
    
    original_script = await db.scripts.get_by_id_and_user(script_id, current_user.id)
    if not original_script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    
    # Create duplicate
    duplicate_data = {
        "id": str(uuid.uuid4()),
        "video_id": original_script.video_id,
        "user_id": current_user.id,
        "title": f"{original_script.title} (Copy)",
        "content": original_script.content,
        "platform_optimization": new_platform or original_script.platform_optimization,
        "is_ai_generated": original_script.is_ai_generated,
        "status": "draft"
    }
    
    duplicate_script = await db.scripts.create(duplicate_data)
    
    # If platform changed, optimize for new platform
    if new_platform and new_platform != original_script.platform_optimization:
        optimize_script_task.delay(
            script_id=duplicate_script.id,
            original_content=duplicate_script.content,
            target_platform=new_platform,
            optimization_goals=['platform_fit']
        )
    
    # Track analytics
    background_tasks.add_task(
        track_event,
        user_id=current_user.id,
        event_type="script_duplicated",
        event_data={
            "original_script_id": script_id,
            "duplicate_script_id": duplicate_script.id,
            "new_platform": new_platform
        }
    )
    
    return ApiResponse(
        success=True,
        data=duplicate_script,
        message="Script duplicated successfully"
    )

@router.get("/{script_id}/performance", response_model=ApiResponse[dict])
async def get_script_performance(
    script_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get performance analytics for a script"""
    
    script = await db.scripts.get_by_id_and_user(script_id, current_user.id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    
    # Get clips created from this script
    clips = await db.clips.get_by_script_id(script_id)
    
    # Calculate performance metrics
    performance = {
        "engagement_score": script.engagement_score,
        "sentiment_score": script.sentiment_score,
        "clips_created": len(clips),
        "total_downloads": sum(1 for clip in clips if clip.download_url),
        "average_clip_duration": sum(clip.duration_seconds for clip in clips) / len(clips) if clips else 0,
        "platform_optimization": script.platform_optimization,
        "keywords": script.keywords,
        "hashtags": script.hashtags,
        "hooks_used": script.hooks,
        "ctas_used": script.ctas
    }
    
    return ApiResponse(success=True, data=performance)

@router.post("/{script_id}/export", response_model=ApiResponse[dict])
async def export_script(
    script_id: str,
    format: str = "txt",
    include_metadata: bool = False,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Export script in various formats"""
    
    script = await db.scripts.get_by_id_and_user(script_id, current_user.id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    
    if format not in ["txt", "json", "srt", "md"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported export format"
        )
    
    exported_content = await _export_script_content(script, format, include_metadata)
    
    return ApiResponse(
        success=True,
        data={
            "content": exported_content,
            "format": format,
            "filename": f"{script.title.replace(' ', '_')}.{format}"
        }
    )

async def _export_script_content(script: Script, format: str, include_metadata: bool) -> str:
    """Export script content in the specified format"""
    
    if format == "txt":
        content = script.content
        if include_metadata:
            content = f"Title: {script.title}\nPlatform: {script.platform_optimization}\nEngagement Score: {script.engagement_score}\n\n{content}"
        return content
    
    elif format == "json":
        return script.json() if include_metadata else {"content": script.content}
    
    elif format == "srt":
        # Convert timestamps to SRT format
        srt_content = ""
        for i, timestamp in enumerate(script.timestamps, 1):
            start_time = _seconds_to_srt_time(timestamp.start_time)
            end_time = _seconds_to_srt_time(timestamp.end_time)
            srt_content += f"{i}\n{start_time} --> {end_time}\n{timestamp.content}\n\n"
        return srt_content
    
    elif format == "md":
        md_content = f"# {script.title}\n\n"
        if include_metadata:
            md_content += f"**Platform:** {script.platform_optimization}\n"
            md_content += f"**Engagement Score:** {script.engagement_score}\n"
            md_content += f"**Keywords:** {', '.join(script.keywords)}\n"
            md_content += f"**Hashtags:** {' '.join(script.hashtags)}\n\n"
        md_content += script.content
        return md_content
    
    return script.content

def _seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
