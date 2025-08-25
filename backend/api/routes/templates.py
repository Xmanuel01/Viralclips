"""
Template Management API Routes
Handles video templates, subtitle styles, and brand templates
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File
from typing import List, Optional
import uuid
import json
from datetime import datetime

from ...models.schemas import (
    Template, TemplateCreate, TemplateUpdate, ApiResponse,
    TemplateType, User, PaginatedResponse
)
from ...services.auth import get_current_user
from ...services.database import get_database
from ...services.analytics import track_event
from ...services.storage import upload_file
from ...utils.permissions import check_feature_access

router = APIRouter(prefix="/templates", tags=["templates"])

@router.get("/", response_model=ApiResponse[PaginatedResponse[Template]])
async def list_templates(
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    type: Optional[TemplateType] = None,
    include_system: bool = True,
    include_user: bool = True,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """List available templates with filtering"""
    
    filters = {}
    
    # Build filters
    if category:
        filters["category"] = category
    if type:
        filters["type"] = type
    
    # Handle system vs user templates
    if include_system and include_user:
        # Include both system templates and user's own templates
        filters["OR"] = [
            {"is_system_template": True},
            {"user_id": current_user.id}
        ]
    elif include_system:
        filters["is_system_template"] = True
    elif include_user:
        filters["user_id"] = current_user.id
    else:
        # If neither selected, default to system templates
        filters["is_system_template"] = True
    
    templates, total = await db.templates.list_paginated(
        filters=filters,
        page=page,
        page_size=page_size,
        order_by="usage_count DESC, created_at DESC"
    )
    
    return ApiResponse(
        success=True,
        data=PaginatedResponse(
            data=templates,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
    )

@router.get("/categories", response_model=ApiResponse[List[dict]])
async def get_template_categories(
    type: Optional[TemplateType] = None,
    db = Depends(get_database)
):
    """Get available template categories"""
    
    filters = {"is_system_template": True}
    if type:
        filters["type"] = type
    
    categories = await db.templates.get_distinct_categories(filters)
    
    # Add category metadata
    category_data = []
    for category in categories:
        template_count = await db.templates.count({"category": category, **filters})
        category_data.append({
            "name": category,
            "display_name": category.replace("_", " ").title(),
            "template_count": template_count,
            "description": _get_category_description(category)
        })
    
    return ApiResponse(success=True, data=category_data)

@router.get("/{template_id}", response_model=ApiResponse[Template])
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get a specific template"""
    
    template = await db.templates.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check permissions for user templates
    if not template.is_system_template and template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this template"
        )
    
    # Check premium template access
    if template.is_premium and not await check_feature_access(current_user, "premium_templates"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium templates require a paid subscription"
        )
    
    return ApiResponse(success=True, data=template)

@router.post("/", response_model=ApiResponse[Template])
async def create_template(
    request: TemplateCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Create a custom template"""
    
    # Check if user can create templates
    if not await check_feature_access(current_user, "custom_templates"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Custom templates require a Pro subscription"
        )
    
    # Create template
    template_data = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
        "name": request.name,
        "description": request.description,
        "category": request.category,
        "type": request.type,
        "config": request.config.dict(),
        "tags": request.tags or [],
        "is_premium": False,
        "is_system_template": False
    }
    
    template = await db.templates.create(template_data)
    
    # Track analytics
    background_tasks.add_task(
        track_event,
        user_id=current_user.id,
        event_type="template_created",
        event_data={
            "template_id": template.id,
            "template_type": request.type,
            "category": request.category
        }
    )
    
    return ApiResponse(
        success=True,
        data=template,
        message="Template created successfully"
    )

@router.put("/{template_id}", response_model=ApiResponse[Template])
async def update_template(
    template_id: str,
    request: TemplateUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Update a custom template"""
    
    template = await db.templates.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check ownership
    if template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own templates"
        )
    
    # Update template
    update_data = request.dict(exclude_unset=True)
    if "config" in update_data:
        update_data["config"] = update_data["config"].dict()
    update_data["updated_at"] = datetime.utcnow()
    
    updated_template = await db.templates.update(template_id, update_data)
    
    # Track analytics
    background_tasks.add_task(
        track_event,
        user_id=current_user.id,
        event_type="template_updated",
        event_data={
            "template_id": template_id,
            "fields_updated": list(update_data.keys())
        }
    )
    
    return ApiResponse(
        success=True,
        data=updated_template,
        message="Template updated successfully"
    )

@router.delete("/{template_id}", response_model=ApiResponse[dict])
async def delete_template(
    template_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Delete a custom template"""
    
    template = await db.templates.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check ownership
    if template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete your own templates"
        )
    
    # Check if template is being used
    usage_count = await db.clips.count({"template_id": template_id})
    if usage_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete template: it's being used by {usage_count} clips"
        )
    
    await db.templates.delete(template_id)
    
    # Track analytics
    background_tasks.add_task(
        track_event,
        user_id=current_user.id,
        event_type="template_deleted",
        event_data={"template_id": template_id}
    )
    
    return ApiResponse(
        success=True,
        message="Template deleted successfully"
    )

@router.post("/{template_id}/preview", response_model=ApiResponse[dict])
async def generate_template_preview(
    template_id: str,
    preview_text: str = "Sample subtitle text for preview",
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Generate a preview for a template"""
    
    template = await db.templates.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check access permissions
    if not template.is_system_template and template.user_id != current_user.id:
        if template.is_premium and not await check_feature_access(current_user, "premium_templates"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this template"
            )
    
    # Generate preview based on template type
    if template.type == "subtitle":
        preview_data = {
            "type": "subtitle",
            "text": preview_text,
            "style": template.config,
            "css": _generate_subtitle_css(template.config),
            "animation_class": _get_animation_class(template.config.get("animation", "fade"))
        }
    elif template.type == "video":
        preview_data = {
            "type": "video",
            "config": template.config,
            "preview_description": _generate_video_preview_description(template.config)
        }
    else:  # brand template
        preview_data = {
            "type": "brand",
            "config": template.config,
            "preview_description": _generate_brand_preview_description(template.config)
        }
    
    return ApiResponse(success=True, data=preview_data)

@router.post("/{template_id}/rate", response_model=ApiResponse[dict])
async def rate_template(
    template_id: str,
    rating: float,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Rate a template (1-5 stars)"""
    
    if not 1 <= rating <= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )
    
    template = await db.templates.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check if user already rated this template
    existing_rating = await db.template_ratings.get_by_user_and_template(
        current_user.id, template_id
    )
    
    if existing_rating:
        # Update existing rating
        await db.template_ratings.update(existing_rating.id, {"rating": rating})
    else:
        # Create new rating
        await db.template_ratings.create({
            "id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "template_id": template_id,
            "rating": rating
        })
    
    # Recalculate template average rating
    avg_rating = await db.template_ratings.get_average_rating(template_id)
    await db.templates.update(template_id, {"rating": avg_rating})
    
    # Track analytics
    background_tasks.add_task(
        track_event,
        user_id=current_user.id,
        event_type="template_rated",
        event_data={
            "template_id": template_id,
            "rating": rating
        }
    )
    
    return ApiResponse(
        success=True,
        data={"new_average_rating": avg_rating},
        message="Template rated successfully"
    )

@router.post("/upload-preview", response_model=ApiResponse[dict])
async def upload_template_preview(
    template_id: str,
    preview_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Upload a preview image/video for a template"""
    
    template = await db.templates.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check ownership
    if template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only upload previews for your own templates"
        )
    
    # Validate file type
    if not preview_file.content_type.startswith(('image/', 'video/')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preview must be an image or video file"
        )
    
    # Upload file to storage
    file_path = await upload_file(
        preview_file,
        bucket="template-previews",
        folder=f"user_{current_user.id}"
    )
    
    # Update template with preview URL
    await db.templates.update(template_id, {"preview_url": file_path})
    
    return ApiResponse(
        success=True,
        data={"preview_url": file_path},
        message="Preview uploaded successfully"
    )

def _generate_subtitle_css(config: dict) -> str:
    """Generate CSS for subtitle preview"""
    
    return f"""
    .subtitle-preview {{
        font-family: '{config.get("font", "Inter")}', sans-serif;
        font-size: {config.get("size", 24)}px;
        color: {config.get("color", "#FFFFFF")};
        background: {config.get("background", "rgba(0,0,0,0.8)")};
        padding: 8px 16px;
        border-radius: 4px;
        text-align: center;
        position: absolute;
        {_get_position_css(config.get("position", "bottom"))};
        z-index: 10;
    }}
    """

def _get_position_css(position: str) -> str:
    """Get CSS positioning for subtitle"""
    
    if position == "top":
        return "top: 20px; left: 50%; transform: translateX(-50%)"
    elif position == "center":
        return "top: 50%; left: 50%; transform: translate(-50%, -50%)"
    else:  # bottom
        return "bottom: 20px; left: 50%; transform: translateX(-50%)"

def _get_animation_class(animation: str) -> str:
    """Get CSS animation class for subtitle"""
    
    animations = {
        "fade": "animate-fade-in",
        "bounce": "animate-bounce",
        "slide": "animate-slide-up",
        "pulse": "animate-pulse",
        "typewriter": "animate-typewriter",
        "none": ""
    }
    
    return animations.get(animation, "animate-fade-in")

def _generate_video_preview_description(config: dict) -> str:
    """Generate description for video template preview"""
    
    description = "Video template with:"
    
    if config.get("intro_duration"):
        description += f" {config['intro_duration']}s intro,"
    if config.get("outro_duration"):
        description += f" {config['outro_duration']}s outro,"
    if config.get("transition_type"):
        description += f" {config['transition_type']} transitions,"
    if config.get("background_music"):
        description += " background music,"
    
    return description.rstrip(",")

def _generate_brand_preview_description(config: dict) -> str:
    """Generate description for brand template preview"""
    
    description = "Brand template with:"
    
    if config.get("logo_position"):
        description += " positioned logo,"
    if config.get("watermark_opacity"):
        description += f" {int(config['watermark_opacity'] * 100)}% watermark opacity,"
    if config.get("brand_colors"):
        description += f" custom brand colors ({len(config['brand_colors'])} colors),"
    
    return description.rstrip(",")

def _get_category_description(category: str) -> str:
    """Get description for template category"""
    
    descriptions = {
        "general": "Versatile templates suitable for any content type",
        "business": "Professional templates for corporate and business content",
        "entertainment": "Fun, engaging templates for entertainment content",
        "education": "Clear, focused templates for educational content",
        "fitness": "High-energy templates for fitness and sports content",
        "lifestyle": "Aesthetic templates for lifestyle and personal content",
        "tech": "Modern templates for technology and innovation content",
        "food": "Appetizing templates for food and cooking content",
        "travel": "Adventure-themed templates for travel content",
        "gaming": "Dynamic templates for gaming content"
    }
    
    return descriptions.get(category, "Custom template category")
