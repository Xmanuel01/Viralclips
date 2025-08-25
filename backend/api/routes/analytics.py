"""
Analytics API Routes
Handles usage tracking, performance metrics, and dashboard analytics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from collections import defaultdict

from ...models.schemas import (
    Analytics, AnalyticsCreate, ApiResponse, User,
    DashboardStats, AnalyticsChartData, UsageTracking
)
from ...services.auth import get_current_user
from ...services.database import get_database
from ...utils.permissions import check_feature_access

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard", response_model=ApiResponse[DashboardStats])
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get dashboard statistics for the current user"""
    
    # Get basic counts
    total_videos = await db.videos.count({"user_id": current_user.id})
    total_clips = await db.clips.count({"user_id": current_user.id})
    total_scripts = await db.scripts.count({"user_id": current_user.id})
    
    # Calculate processing time saved (estimate based on clips created)
    # Assume each clip saves 15 minutes of manual editing
    processing_time_saved = total_clips * 15
    
    # Get storage usage
    storage_used = await _calculate_storage_usage(current_user.id, db)
    
    # Calculate clips remaining today
    clips_remaining_today = max(0, current_user.daily_clips_limit - current_user.daily_clips_used)
    
    stats = DashboardStats(
        total_videos=total_videos,
        total_clips=total_clips,
        total_scripts=total_scripts,
        processing_time_saved=processing_time_saved,
        storage_used=storage_used,
        clips_remaining_today=clips_remaining_today,
        subscription_status=current_user.subscription_status,
        subscription_expires_at=current_user.subscription_ends_at
    )
    
    return ApiResponse(success=True, data=stats)

@router.get("/usage", response_model=ApiResponse[List[AnalyticsChartData]])
async def get_usage_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get usage analytics for chart display"""
    
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    # Get usage tracking data
    usage_data = await db.usage_tracking.get_date_range(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Fill in missing dates with zero values
    chart_data = []
    current_date = start_date
    usage_dict = {item.date: item for item in usage_data}
    
    while current_date <= end_date:
        date_str = current_date.isoformat()
        usage = usage_dict.get(current_date)
        
        chart_data.append(AnalyticsChartData(
            date=date_str,
            clips_created=usage.clips_created if usage else 0,
            videos_uploaded=usage.videos_uploaded if usage else 0,
            scripts_generated=usage.scripts_generated if usage else 0,
            processing_minutes=usage.processing_minutes if usage else 0
        ))
        
        current_date += timedelta(days=1)
    
    return ApiResponse(success=True, data=chart_data)

@router.get("/performance", response_model=ApiResponse[dict])
async def get_performance_analytics(
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get detailed performance analytics"""
    
    # Check if user has access to advanced analytics
    if not await check_feature_access(current_user, "advanced_analytics"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Advanced analytics require a Pro subscription"
        )
    
    # Calculate date range
    days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = days_map[period]
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get analytics events
    events = await db.analytics.get_events_by_date_range(
        user_id=current_user.id,
        start_date=start_date,
        end_date=datetime.utcnow()
    )
    
    # Process events into performance metrics
    performance_data = await _process_performance_events(events, current_user.id, db)
    
    return ApiResponse(success=True, data=performance_data)

@router.get("/exports", response_model=ApiResponse[dict])
async def get_export_analytics(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get analytics on export patterns and preferences"""
    
    # Get all user's clips
    clips = await db.clips.get_by_user_id(current_user.id)
    
    # Analyze export patterns
    aspect_ratio_stats = defaultdict(int)
    resolution_stats = defaultdict(int)
    format_stats = defaultdict(int)
    template_usage = defaultdict(int)
    
    for clip in clips:
        aspect_ratio_stats[clip.aspect_ratio] += 1
        resolution_stats[clip.resolution] += 1
        format_stats[clip.export_settings.get("format", "mp4")] += 1
        if clip.template_id:
            template_usage[clip.template_id] += 1
    
    # Get most used templates with names
    popular_templates = []
    for template_id, count in sorted(template_usage.items(), key=lambda x: x[1], reverse=True)[:5]:
        template = await db.templates.get_by_id(template_id)
        if template:
            popular_templates.append({
                "template_id": template_id,
                "template_name": template.name,
                "usage_count": count
            })
    
    export_analytics = {
        "aspect_ratio_preferences": dict(aspect_ratio_stats),
        "resolution_preferences": dict(resolution_stats),
        "format_preferences": dict(format_stats),
        "most_used_templates": popular_templates,
        "total_exports": len(clips),
        "average_clip_duration": sum(clip.duration_seconds for clip in clips) / len(clips) if clips else 0
    }
    
    return ApiResponse(success=True, data=export_analytics)

@router.get("/trends", response_model=ApiResponse[dict])
async def get_trending_analytics(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get trending content insights"""
    
    # Check if user has access to trend analytics
    if not await check_feature_access(current_user, "trend_analytics"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trend analytics require a Pro subscription"
        )
    
    # Get trending keywords across all user's content
    scripts = await db.scripts.get_by_user_id(current_user.id)
    
    # Aggregate keywords
    keyword_frequency = defaultdict(int)
    hashtag_frequency = defaultdict(int)
    
    for script in scripts:
        for keyword in script.keywords:
            keyword_frequency[keyword] += 1
        for hashtag in script.hashtags:
            hashtag_frequency[hashtag] += 1
    
    # Get trending topics (mock data - in production, this would come from external APIs)
    trending_topics = [
        {"topic": "AI automation", "growth": "+45%", "relevance": 0.8},
        {"topic": "productivity tips", "growth": "+32%", "relevance": 0.7},
        {"topic": "viral content", "growth": "+28%", "relevance": 0.9},
        {"topic": "social media marketing", "growth": "+23%", "relevance": 0.6},
        {"topic": "content creation", "growth": "+19%", "relevance": 0.8}
    ]
    
    trends_data = {
        "trending_keywords": dict(sorted(keyword_frequency.items(), key=lambda x: x[1], reverse=True)[:10]),
        "trending_hashtags": dict(sorted(hashtag_frequency.items(), key=lambda x: x[1], reverse=True)[:10]),
        "suggested_topics": trending_topics,
        "content_recommendations": await _generate_content_recommendations(keyword_frequency)
    }
    
    return ApiResponse(success=True, data=trends_data)

@router.post("/track", response_model=ApiResponse[dict])
async def track_custom_event(
    event: AnalyticsCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Track a custom analytics event"""
    
    # Create analytics record
    analytics_data = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
        **event.dict()
    }
    
    await db.analytics.create(analytics_data)
    
    return ApiResponse(
        success=True,
        message="Event tracked successfully"
    )

@router.get("/export-report", response_model=ApiResponse[dict])
async def export_analytics_report(
    format: str = Query("json", regex="^(json|csv)$"),
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Export comprehensive analytics report"""
    
    # Check if user has access to export reports
    if not await check_feature_access(current_user, "analytics_export"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analytics export requires a Pro subscription"
        )
    
    # Calculate date range
    days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = days_map[period]
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Gather all analytics data
    report_data = {
        "user_info": {
            "user_id": current_user.id,
            "subscription_tier": current_user.subscription_tier,
            "member_since": current_user.created_at.isoformat()
        },
        "report_period": {
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "days": days
        },
        "summary": await _generate_analytics_summary(current_user.id, start_date, db),
        "detailed_usage": await _get_detailed_usage(current_user.id, start_date, db),
        "performance_metrics": await _get_performance_metrics(current_user.id, start_date, db)
    }
    
    if format == "csv":
        csv_content = await _convert_to_csv(report_data)
        return ApiResponse(
            success=True,
            data={
                "content": csv_content,
                "filename": f"analytics_report_{period}_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
    
    return ApiResponse(success=True, data=report_data)

# Helper functions

async def _calculate_storage_usage(user_id: str, db) -> int:
    """Calculate total storage usage in MB"""
    
    videos = await db.videos.get_by_user_id(user_id)
    clips = await db.clips.get_by_user_id(user_id)
    
    total_bytes = 0
    
    # Sum video file sizes
    for video in videos:
        if video.file_size:
            total_bytes += video.file_size
    
    # Sum clip file sizes
    for clip in clips:
        if clip.file_size:
            total_bytes += clip.file_size
    
    return total_bytes // (1024 * 1024)  # Convert to MB

async def _process_performance_events(events: List[Analytics], user_id: str, db) -> Dict[str, Any]:
    """Process analytics events into performance metrics"""
    
    # Group events by type
    event_counts = defaultdict(int)
    processing_times = []
    file_sizes = []
    
    for event in events:
        event_counts[event.event_type] += 1
        
        if event.processing_time_ms:
            processing_times.append(event.processing_time_ms)
        
        if event.file_size_bytes:
            file_sizes.append(event.file_size_bytes)
    
    # Calculate averages
    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
    avg_file_size = sum(file_sizes) / len(file_sizes) if file_sizes else 0
    
    return {
        "event_summary": dict(event_counts),
        "average_processing_time_ms": avg_processing_time,
        "average_file_size_mb": avg_file_size / (1024 * 1024),
        "total_events": len(events),
        "most_active_day": await _get_most_active_day(events),
        "engagement_trends": await _calculate_engagement_trends(user_id, db)
    }

async def _get_most_active_day(events: List[Analytics]) -> str:
    """Find the most active day based on events"""
    
    day_counts = defaultdict(int)
    
    for event in events:
        day = event.created_at.strftime('%A')
        day_counts[day] += 1
    
    if day_counts:
        return max(day_counts, key=day_counts.get)
    
    return "No data"

async def _calculate_engagement_trends(user_id: str, db) -> Dict[str, float]:
    """Calculate engagement trends over time"""
    
    # Get recent scripts with engagement scores
    recent_scripts = await db.scripts.get_recent_by_user(user_id, limit=20)
    
    if len(recent_scripts) < 2:
        return {"trend": 0.0, "direction": "stable"}
    
    # Calculate trend
    older_avg = sum(script.engagement_score for script in recent_scripts[10:]) / len(recent_scripts[10:])
    newer_avg = sum(script.engagement_score for script in recent_scripts[:10]) / len(recent_scripts[:10])
    
    trend_change = newer_avg - older_avg
    
    return {
        "trend": trend_change,
        "direction": "improving" if trend_change > 0.05 else "declining" if trend_change < -0.05 else "stable",
        "current_average": newer_avg,
        "previous_average": older_avg
    }

async def _generate_analytics_summary(user_id: str, start_date: datetime, db) -> Dict[str, Any]:
    """Generate analytics summary for the specified period"""
    
    # Get data for the period
    videos = await db.videos.get_by_user_and_date_range(user_id, start_date, datetime.utcnow())
    clips = await db.clips.get_by_user_and_date_range(user_id, start_date, datetime.utcnow())
    scripts = await db.scripts.get_by_user_and_date_range(user_id, start_date, datetime.utcnow())
    
    return {
        "videos_uploaded": len(videos),
        "clips_created": len(clips),
        "scripts_generated": len(scripts),
        "total_processing_time": sum(
            (video.processing_completed_at - video.processing_started_at).total_seconds() / 60
            for video in videos
            if video.processing_started_at and video.processing_completed_at
        ),
        "success_rate": len([clip for clip in clips if clip.export_status == "completed"]) / len(clips) if clips else 0,
        "average_video_duration": sum(video.duration_seconds for video in videos if video.duration_seconds) / len(videos) if videos else 0,
        "average_clip_duration": sum(clip.duration_seconds for clip in clips) / len(clips) if clips else 0
    }

async def _get_detailed_usage(user_id: str, start_date: datetime, db) -> List[Dict[str, Any]]:
    """Get detailed daily usage breakdown"""
    
    events = await db.analytics.get_events_by_date_range(user_id, start_date, datetime.utcnow())
    
    # Group by date
    daily_usage = defaultdict(lambda: defaultdict(int))
    
    for event in events:
        date_key = event.created_at.date().isoformat()
        daily_usage[date_key][event.event_type] += 1
    
    # Convert to list format
    detailed_usage = []
    for date_str, event_counts in daily_usage.items():
        detailed_usage.append({
            "date": date_str,
            "events": dict(event_counts),
            "total_activity": sum(event_counts.values())
        })
    
    return sorted(detailed_usage, key=lambda x: x["date"])

async def _get_performance_metrics(user_id: str, start_date: datetime, db) -> Dict[str, Any]:
    """Get performance metrics for the period"""
    
    clips = await db.clips.get_by_user_and_date_range(user_id, start_date, datetime.utcnow())
    scripts = await db.scripts.get_by_user_and_date_range(user_id, start_date, datetime.utcnow())
    
    # Calculate metrics
    clip_success_rate = len([c for c in clips if c.export_status == "completed"]) / len(clips) if clips else 0
    avg_viral_score = sum(clip.viral_potential_score for clip in clips) / len(clips) if clips else 0
    avg_engagement_score = sum(script.engagement_score for script in scripts) / len(scripts) if scripts else 0
    
    # Platform breakdown
    platform_stats = defaultdict(int)
    for script in scripts:
        platform_stats[script.platform_optimization] += 1
    
    return {
        "clip_success_rate": clip_success_rate,
        "average_viral_score": avg_viral_score,
        "average_engagement_score": avg_engagement_score,
        "platform_breakdown": dict(platform_stats),
        "quality_metrics": {
            "high_scoring_clips": len([c for c in clips if c.viral_potential_score > 0.7]),
            "medium_scoring_clips": len([c for c in clips if 0.4 <= c.viral_potential_score <= 0.7]),
            "low_scoring_clips": len([c for c in clips if c.viral_potential_score < 0.4])
        }
    }

async def _generate_content_recommendations(keyword_frequency: Dict[str, int]) -> List[Dict[str, Any]]:
    """Generate content recommendations based on user's keyword usage"""
    
    # Find top keywords
    top_keywords = sorted(keyword_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
    
    recommendations = []
    for keyword, frequency in top_keywords:
        recommendations.append({
            "keyword": keyword,
            "frequency": frequency,
            "recommendation": f"Create more content around '{keyword}' - it appears frequently in your scripts",
            "suggested_platforms": ["tiktok", "youtube"] if frequency > 3 else ["instagram"],
            "potential_hashtags": [f"#{keyword.replace(' ', '')}", f"#{keyword.replace(' ', '')}tips"]
        })
    
    return recommendations

async def _convert_to_csv(data: Dict[str, Any]) -> str:
    """Convert analytics data to CSV format"""
    
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(["Metric", "Value"])
    
    # Write summary data
    summary = data["summary"]
    for key, value in summary.items():
        writer.writerow([key.replace("_", " ").title(), value])
    
    # Write daily usage data
    writer.writerow([])  # Empty row
    writer.writerow(["Date", "Videos Uploaded", "Clips Created", "Scripts Generated"])
    
    for daily_data in data["detailed_usage"]:
        events = daily_data["events"]
        writer.writerow([
            daily_data["date"],
            events.get("video_upload", 0),
            events.get("clip_created", 0),
            events.get("script_generated", 0)
        ])
    
    return output.getvalue()
