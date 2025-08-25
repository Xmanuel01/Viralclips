import os
import sys
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
import json
import time

# Setup structured logging
def setup_logging():
    """Setup structured logging for production."""
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    
    # Create custom formatter for JSON logs
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            
            # Add extra fields if present
            if hasattr(record, 'user_id'):
                log_entry['user_id'] = record.user_id
            if hasattr(record, 'video_id'):
                log_entry['video_id'] = record.video_id
            if hasattr(record, 'job_id'):
                log_entry['job_id'] = record.job_id
            if hasattr(record, 'duration'):
                log_entry['duration'] = record.duration
            if hasattr(record, 'error_type'):
                log_entry['error_type'] = record.error_type
            
            # Add exception info if present
            if record.exc_info:
                log_entry['exception'] = {
                    'type': record.exc_info[0].__name__,
                    'message': str(record.exc_info[1]),
                    'traceback': traceback.format_exception(*record.exc_info)
                }
            
            return json.dumps(log_entry)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler for persistent logs
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = logging.FileHandler('logs/app.log')
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    return root_logger

# Initialize logger
logger = setup_logging()

class MetricsCollector:
    """Collect and track application metrics."""
    
    def __init__(self):
        self.metrics = {
            'video_processing': {
                'total_videos': 0,
                'successful_transcriptions': 0,
                'failed_transcriptions': 0,
                'successful_highlights': 0,
                'failed_highlights': 0,
                'successful_exports': 0,
                'failed_exports': 0,
                'average_processing_time': 0.0
            },
            'user_activity': {
                'total_users': 0,
                'active_users_today': 0,
                'clips_created_today': 0,
                'premium_conversions': 0
            },
            'system_performance': {
                'api_requests_total': 0,
                'api_errors_total': 0,
                'average_response_time': 0.0,
                'queue_size': 0,
                'worker_utilization': 0.0
            }
        }
    
    def increment_counter(self, category: str, metric: str, value: int = 1):
        """Increment a counter metric."""
        if category in self.metrics and metric in self.metrics[category]:
            self.metrics[category][metric] += value
            logger.info(f"Metric incremented: {category}.{metric} = {self.metrics[category][metric]}")
    
    def set_gauge(self, category: str, metric: str, value: float):
        """Set a gauge metric."""
        if category in self.metrics and metric in self.metrics[category]:
            self.metrics[category][metric] = value
            logger.info(f"Metric set: {category}.{metric} = {value}")
    
    def record_timing(self, category: str, metric: str, duration: float):
        """Record timing information."""
        if category in self.metrics and metric in self.metrics[category]:
            # Simple moving average
            current = self.metrics[category][metric]
            self.metrics[category][metric] = (current + duration) / 2
            logger.info(f"Timing recorded: {category}.{metric} = {duration}s")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        return self.metrics.copy()

# Global metrics collector
metrics = MetricsCollector()

def log_performance(operation_name: str):
    """Decorator to log performance metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            operation_id = f"{operation_name}_{int(start_time)}"
            
            logger.info(
                f"Starting operation: {operation_name}",
                extra={
                    'operation_id': operation_id,
                    'operation_name': operation_name
                }
            )
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"Operation completed: {operation_name}",
                    extra={
                        'operation_id': operation_id,
                        'operation_name': operation_name,
                        'duration': duration,
                        'status': 'success'
                    }
                )
                
                # Record metrics
                metrics.record_timing('system_performance', 'average_response_time', duration)
                metrics.increment_counter('system_performance', 'api_requests_total')
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    f"Operation failed: {operation_name}",
                    extra={
                        'operation_id': operation_id,
                        'operation_name': operation_name,
                        'duration': duration,
                        'status': 'error',
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    },
                    exc_info=True
                )
                
                # Record error metrics
                metrics.increment_counter('system_performance', 'api_errors_total')
                
                raise
        
        return wrapper
    return decorator

def log_user_action(action: str, user_id: str = None):
    """Decorator to log user actions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(
                f"User action: {action}",
                extra={
                    'user_id': user_id,
                    'action': action,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            try:
                result = func(*args, **kwargs)
                
                logger.info(
                    f"User action completed: {action}",
                    extra={
                        'user_id': user_id,
                        'action': action,
                        'status': 'success'
                    }
                )
                
                return result
                
            except Exception as e:
                logger.error(
                    f"User action failed: {action}",
                    extra={
                        'user_id': user_id,
                        'action': action,
                        'status': 'error',
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    },
                    exc_info=True
                )
                
                raise
        
        return wrapper
    return decorator

class HealthChecker:
    """System health monitoring."""
    
    def __init__(self):
        self.checks = {}
    
    def register_check(self, name: str, check_func):
        """Register a health check function."""
        self.checks[name] = check_func
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run all registered health checks."""
        results = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        for name, check_func in self.checks.items():
            try:
                start_time = time.time()
                check_result = check_func()
                duration = time.time() - start_time
                
                results['checks'][name] = {
                    'status': 'healthy' if check_result else 'unhealthy',
                    'duration': duration,
                    'details': check_result if isinstance(check_result, dict) else {}
                }
                
            except Exception as e:
                results['checks'][name] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                results['status'] = 'degraded'
                
                logger.error(
                    f"Health check failed: {name}",
                    extra={
                        'check_name': name,
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
        
        return results

# Global health checker
health_checker = HealthChecker()

def database_health_check():
    """Check database connectivity."""
    try:
        from database import Database
        db = Database()
        
        # Simple query to test connectivity
        result = db.supabase.table('users').select('id').limit(1).execute()
        
        return {
            'connected': True,
            'response_time': 0.1  # Would measure actual response time
        }
    except Exception as e:
        return False

def redis_health_check():
    """Check Redis connectivity."""
    try:
        import redis
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        r = redis.from_url(redis_url)
        r.ping()
        
        return {
            'connected': True,
            'queue_size': r.llen('default')  # Check default queue size
        }
    except Exception as e:
        return False

def storage_health_check():
    """Check storage system."""
    try:
        from database import Database, Storage
        db = Database()
        storage = Storage(db.supabase)
        
        # Test read access to storage
        buckets = db.supabase.storage.list_buckets()
        
        return {
            'accessible': True,
            'buckets': len(buckets) if buckets else 0
        }
    except Exception as e:
        return False

# Register default health checks
health_checker.register_check('database', database_health_check)
health_checker.register_check('redis', redis_health_check)
health_checker.register_check('storage', storage_health_check)

class AlertManager:
    """Handle system alerts and notifications."""
    
    def __init__(self):
        self.alert_thresholds = {
            'error_rate': 0.05,  # 5% error rate
            'response_time': 5.0,  # 5 seconds
            'queue_size': 100,    # 100 jobs in queue
            'disk_usage': 0.85    # 85% disk usage
        }
    
    def check_thresholds(self):
        """Check if any metrics exceed alert thresholds."""
        current_metrics = metrics.get_metrics()
        alerts = []
        
        # Error rate check
        total_requests = current_metrics['system_performance']['api_requests_total']
        total_errors = current_metrics['system_performance']['api_errors_total']
        
        if total_requests > 0:
            error_rate = total_errors / total_requests
            if error_rate > self.alert_thresholds['error_rate']:
                alerts.append({
                    'type': 'error_rate_high',
                    'message': f"Error rate ({error_rate:.2%}) exceeds threshold",
                    'severity': 'warning'
                })
        
        # Response time check
        avg_response = current_metrics['system_performance']['average_response_time']
        if avg_response > self.alert_thresholds['response_time']:
            alerts.append({
                'type': 'response_time_high',
                'message': f"Average response time ({avg_response:.2f}s) exceeds threshold",
                'severity': 'warning'
            })
        
        # Queue size check
        queue_size = current_metrics['system_performance']['queue_size']
        if queue_size > self.alert_thresholds['queue_size']:
            alerts.append({
                'type': 'queue_size_high',
                'message': f"Queue size ({queue_size}) exceeds threshold",
                'severity': 'critical'
            })
        
        for alert in alerts:
            self.send_alert(alert)
        
        return alerts
    
    def send_alert(self, alert: Dict[str, Any]):
        """Send alert notification."""
        logger.warning(
            f"Alert triggered: {alert['type']}",
            extra={
                'alert_type': alert['type'],
                'severity': alert['severity'],
                'message': alert['message']
            }
        )
        
        # In production, you would integrate with:
        # - Slack/Discord webhooks
        # - Email notifications
        # - PagerDuty/Opsgenie
        # - SMS alerts
        
        # Example webhook call (commented out)
        # self._send_webhook_alert(alert)
    
    def _send_webhook_alert(self, alert: Dict[str, Any]):
        """Send alert via webhook (example implementation)."""
        import requests
        
        webhook_url = os.environ.get('ALERT_WEBHOOK_URL')
        if not webhook_url:
            return
        
        payload = {
            'text': f"🚨 Alert: {alert['message']}",
            'severity': alert['severity'],
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'ViralClips.ai'
        }
        
        try:
            requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {str(e)}")

# Global alert manager
alert_manager = AlertManager()

def setup_monitoring():
    """Initialize monitoring system."""
    logger.info("Monitoring system initialized")
    
    # Start periodic health checks (in production, this would run in a separate thread)
    def periodic_checks():
        health_results = health_checker.run_health_checks()
        alerts = alert_manager.check_thresholds()
        
        if health_results['status'] != 'healthy':
            logger.warning(
                "System health degraded",
                extra={'health_status': health_results['status']}
            )
    
    return periodic_checks

# Error handling utilities
class APIError(Exception):
    """Base API error class."""
    def __init__(self, message: str, status_code: int = 500, error_type: str = None):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type or self.__class__.__name__
        super().__init__(self.message)

class ValidationError(APIError):
    """Validation error."""
    def __init__(self, message: str):
        super().__init__(message, 400, "ValidationError")

class AuthenticationError(APIError):
    """Authentication error."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401, "AuthenticationError")

class RateLimitError(APIError):
    """Rate limit error."""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, 429, "RateLimitError")

class ProcessingError(APIError):
    """Video processing error."""
    def __init__(self, message: str):
        super().__init__(message, 500, "ProcessingError")

def handle_exceptions(func):
    """Decorator to handle and log exceptions consistently."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            logger.warning(
                f"API error in {func.__name__}: {e.message}",
                extra={
                    'error_type': e.error_type,
                    'status_code': e.status_code,
                    'function': func.__name__
                }
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in {func.__name__}: {str(e)}",
                extra={
                    'error_type': type(e).__name__,
                    'function': func.__name__
                },
                exc_info=True
            )
            raise APIError(f"Internal server error: {str(e)}", 500)
    
    return wrapper
