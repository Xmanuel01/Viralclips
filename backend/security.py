import os
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from functools import wraps
import redis
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import re

# Redis client for rate limiting
redis_client = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"))

class RateLimiter:
    """Redis-based rate limiter with different strategies."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def is_allowed(self, key: str, limit: int, window: int, strategy: str = "fixed") -> tuple[bool, dict]:
        """
        Check if request is allowed based on rate limiting strategy.
        
        Args:
            key: Unique identifier for the rate limit (e.g., user_id, ip_address)
            limit: Maximum number of requests allowed
            window: Time window in seconds
            strategy: Rate limiting strategy ("fixed", "sliding", "token_bucket")
        
        Returns:
            (is_allowed, info_dict)
        """
        if strategy == "sliding":
            return self._sliding_window(key, limit, window)
        elif strategy == "token_bucket":
            return self._token_bucket(key, limit, window)
        else:
            return self._fixed_window(key, limit, window)
    
    def _fixed_window(self, key: str, limit: int, window: int) -> tuple[bool, dict]:
        """Fixed window rate limiting."""
        current_time = int(time.time())
        window_start = current_time - (current_time % window)
        redis_key = f"rate_limit:fixed:{key}:{window_start}"
        
        try:
            with self.redis.pipeline() as pipe:
                pipe.incr(redis_key)
                pipe.expire(redis_key, window)
                results = pipe.execute()
                
                current_count = results[0]
                
                return (current_count <= limit), {
                    "current_count": current_count,
                    "limit": limit,
                    "window": window,
                    "reset_time": window_start + window,
                    "strategy": "fixed_window"
                }
        except Exception:
            # If Redis is down, allow the request
            return True, {}
    
    def _sliding_window(self, key: str, limit: int, window: int) -> tuple[bool, dict]:
        """Sliding window rate limiting using sorted sets."""
        current_time = time.time()
        redis_key = f"rate_limit:sliding:{key}"
        
        try:
            with self.redis.pipeline() as pipe:
                # Remove expired entries
                pipe.zremrangebyscore(redis_key, 0, current_time - window)
                # Count current requests
                pipe.zcard(redis_key)
                # Add current request
                pipe.zadd(redis_key, {str(current_time): current_time})
                # Set expiry
                pipe.expire(redis_key, window)
                results = pipe.execute()
                
                current_count = results[1] + 1  # Include current request
                
                if current_count > limit:
                    # Remove the request we just added since it's not allowed
                    pipe.zrem(redis_key, str(current_time))
                    pipe.execute()
                
                return (current_count <= limit), {
                    "current_count": current_count,
                    "limit": limit,
                    "window": window,
                    "strategy": "sliding_window"
                }
        except Exception:
            return True, {}
    
    def _token_bucket(self, key: str, capacity: int, refill_rate: int) -> tuple[bool, dict]:
        """Token bucket rate limiting."""
        redis_key = f"rate_limit:bucket:{key}"
        current_time = time.time()
        
        try:
            bucket_data = self.redis.hgetall(redis_key)
            
            if bucket_data:
                tokens = float(bucket_data.get(b'tokens', capacity))
                last_refill = float(bucket_data.get(b'last_refill', current_time))
            else:
                tokens = capacity
                last_refill = current_time
            
            # Calculate new tokens based on time passed
            time_passed = current_time - last_refill
            new_tokens = min(capacity, tokens + (time_passed * refill_rate))
            
            # Check if request is allowed
            if new_tokens >= 1:
                new_tokens -= 1
                allowed = True
            else:
                allowed = False
            
            # Update bucket state
            with self.redis.pipeline() as pipe:
                pipe.hset(redis_key, mapping={
                    'tokens': new_tokens,
                    'last_refill': current_time
                })
                pipe.expire(redis_key, 3600)  # 1 hour expiry
                pipe.execute()
            
            return allowed, {
                "tokens_remaining": new_tokens,
                "capacity": capacity,
                "refill_rate": refill_rate,
                "strategy": "token_bucket"
            }
        except Exception:
            return True, {}

# Global rate limiter
rate_limiter = RateLimiter(redis_client)

def rate_limit(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000,
    requests_per_day: int = 10000,
    key_func: callable = None,
    strategy: str = "sliding"
):
    """
    Rate limiting decorator with multiple time windows.
    
    Args:
        requests_per_minute: Requests allowed per minute
        requests_per_hour: Requests allowed per hour
        requests_per_day: Requests allowed per day
        key_func: Function to generate rate limit key from request
        strategy: Rate limiting strategy
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Generate rate limit key
            if key_func:
                key = key_func(request)
            else:
                # Default to IP address
                key = request.client.host
            
            # Check multiple time windows
            limits = [
                (requests_per_minute, 60, "minute"),
                (requests_per_hour, 3600, "hour"),
                (requests_per_day, 86400, "day")
            ]
            
            for limit, window, period in limits:
                if limit > 0:
                    allowed, info = rate_limiter.is_allowed(
                        f"{key}:{period}", limit, window, strategy
                    )
                    
                    if not allowed:
                        raise HTTPException(
                            status_code=429,
                            detail=f"Rate limit exceeded: {limit} requests per {period}",
                            headers={
                                "X-RateLimit-Limit": str(limit),
                                "X-RateLimit-Remaining": str(max(0, limit - info.get("current_count", 0))),
                                "X-RateLimit-Reset": str(info.get("reset_time", int(time.time()) + window)),
                                "Retry-After": str(window)
                            }
                        )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator

class InputValidator:
    """Input validation and sanitization."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_url(url: str, allowed_domains: List[str] = None) -> bool:
        """Validate URL format and domain."""
        url_pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/[^?\s]*)?(?:\?[^#\s]*)?(?:#[^\s]*)?$'
        
        if not re.match(url_pattern, url):
            return False
        
        if allowed_domains:
            domain = url.split('/')[2].lower()
            return any(domain.endswith(allowed_domain) for allowed_domain in allowed_domains)
        
        return True
    
    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 255) -> str:
        """Sanitize filename to prevent path traversal."""
        # Remove path separators and special characters
        sanitized = re.sub(r'[^\w\-_\.]', '_', filename)
        # Limit length
        sanitized = sanitized[:max_length]
        # Ensure it's not empty
        if not sanitized:
            sanitized = "file"
        return sanitized
    
    @staticmethod
    def validate_video_file(filename: str, max_size_mb: int = 1000) -> tuple[bool, str]:
        """Validate video file."""
        allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        
        # Check extension
        ext = os.path.splitext(filename.lower())[1]
        if ext not in allowed_extensions:
            return False, f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
        
        return True, ""

class SecurityHeaders:
    """Security headers middleware."""
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://js.paystack.co; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https:;"
        )
        return response

class IPWhitelist:
    """IP address whitelisting for admin endpoints."""
    
    def __init__(self, whitelist: List[str] = None):
        self.whitelist = set(whitelist or [])
        # Add local IPs by default
        self.whitelist.update(['127.0.0.1', '::1', 'localhost'])
    
    def is_allowed(self, ip: str) -> bool:
        """Check if IP is whitelisted."""
        return ip in self.whitelist
    
    def add_ip(self, ip: str):
        """Add IP to whitelist."""
        self.whitelist.add(ip)
    
    def remove_ip(self, ip: str):
        """Remove IP from whitelist."""
        self.whitelist.discard(ip)

# Global IP whitelist for admin endpoints
admin_ip_whitelist = IPWhitelist()

def require_admin_ip(func):
    """Decorator to restrict access to whitelisted IPs."""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        client_ip = request.client.host
        
        if not admin_ip_whitelist.is_allowed(client_ip):
            raise HTTPException(
                status_code=403,
                detail="Access denied from this IP address"
            )
        
        return await func(request, *args, **kwargs)
    
    return wrapper

class PasswordValidator:
    """Password strength validation."""
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, List[str]]:
        """
        Validate password strength.
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            issues.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\?]', password):
            issues.append("Password must contain at least one special character")
        
        # Check for common passwords
        common_passwords = {'password', '123456', 'password123', 'admin', 'qwerty'}
        if password.lower() in common_passwords:
            issues.append("Password is too common")
        
        return len(issues) == 0, issues

class RequestSignatureValidator:
    """Validate request signatures for webhooks."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def validate_signature(self, payload: bytes, signature: str, algorithm: str = 'sha256') -> bool:
        """Validate request signature."""
        expected_signature = hashlib.new(
            algorithm, 
            self.secret_key.encode() + payload
        ).hexdigest()
        
        return signature == expected_signature

class LoginAttemptTracker:
    """Track and limit login attempts to prevent brute force attacks."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.max_attempts = 5
        self.lockout_duration = 900  # 15 minutes
    
    def is_locked_out(self, identifier: str) -> tuple[bool, Optional[int]]:
        """Check if identifier is locked out."""
        key = f"login_attempts:{identifier}"
        
        try:
            data = self.redis.hgetall(key)
            if not data:
                return False, None
            
            attempts = int(data.get(b'attempts', 0))
            lockout_until = data.get(b'lockout_until')
            
            if lockout_until:
                lockout_until = float(lockout_until)
                if time.time() < lockout_until:
                    return True, int(lockout_until - time.time())
                else:
                    # Lockout expired, reset attempts
                    self.redis.delete(key)
                    return False, None
            
            return False, None
        except Exception:
            return False, None
    
    def record_failed_attempt(self, identifier: str):
        """Record a failed login attempt."""
        key = f"login_attempts:{identifier}"
        
        try:
            with self.redis.pipeline() as pipe:
                pipe.hincrby(key, 'attempts', 1)
                pipe.expire(key, self.lockout_duration)
                results = pipe.execute()
                
                attempts = results[0]
                
                if attempts >= self.max_attempts:
                    # Lock out the user
                    lockout_until = time.time() + self.lockout_duration
                    pipe.hset(key, 'lockout_until', lockout_until)
                    pipe.expire(key, self.lockout_duration)
                    pipe.execute()
        except Exception:
            pass
    
    def clear_attempts(self, identifier: str):
        """Clear login attempts for identifier."""
        key = f"login_attempts:{identifier}"
        try:
            self.redis.delete(key)
        except Exception:
            pass

# Global login attempt tracker
login_tracker = LoginAttemptTracker(redis_client)

def check_login_attempts(identifier: str):
    """Decorator to check login attempts before processing."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            locked_out, remaining_time = login_tracker.is_locked_out(identifier)
            
            if locked_out:
                raise HTTPException(
                    status_code=429,
                    detail=f"Account temporarily locked due to too many failed attempts. Try again in {remaining_time} seconds.",
                    headers={"Retry-After": str(remaining_time)}
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Content Security Policy
CSP_POLICY = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "'unsafe-inline'", "https://js.paystack.co"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "img-src": ["'self'", "data:", "https:"],
    "font-src": ["'self'", "https:"],
    "connect-src": ["'self'", "https:"],
    "media-src": ["'self'"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"]
}

def generate_csp_header() -> str:
    """Generate Content Security Policy header."""
    csp_parts = []
    for directive, sources in CSP_POLICY.items():
        csp_parts.append(f"{directive} {' '.join(sources)}")
    
    return "; ".join(csp_parts)
