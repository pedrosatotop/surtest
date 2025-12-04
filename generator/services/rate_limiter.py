"""
Simple in-memory rate limiter for demo purposes.
In production, use Redis or similar.
"""
from typing import Any


import time
from collections import defaultdict
from django.conf import settings


class RateLimiter:
    """Simple rate limiter using in-memory storage."""
    
    def __init__(self):
        self.requests = defaultdict[Any, list](list)
        self.max_requests = settings.RATE_LIMIT_REQUESTS
        self.window_seconds = settings.RATE_LIMIT_WINDOW
    
    def is_allowed(self, ip_address: str) -> bool:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            ip_address: Client IP address
            
        Returns:
            True if request is allowed, False otherwise
        """
        now = time.time()
        
        # Clean old requests outside the window
        self.requests[ip_address] = [
            req_time for req_time in self.requests[ip_address]
            if now - req_time < self.window_seconds
        ]
        
        # Check if limit exceeded
        if len(self.requests[ip_address]) >= self.max_requests:
            return False
        
        # Record this request
        self.requests[ip_address].append(now)
        return True
    
    def get_remaining(self, ip_address: str) -> int:
        """Get remaining requests for IP address."""
        now = time.time()
        self.requests[ip_address] = [
            req_time for req_time in self.requests[ip_address]
            if now - req_time < self.window_seconds
        ]
        return max(0, self.max_requests - len(self.requests[ip_address]))


# Global rate limiter instance
rate_limiter = RateLimiter()

