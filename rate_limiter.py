"""
Rate limiting implementation for AstroGeminiBot
Uses sliding window algorithm to track and limit user requests
"""

import time
import logging
from collections import defaultdict, deque
from typing import Dict, Deque, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RateLimitStats:
    """Statistics for rate limiting"""
    total_requests: int = 0
    blocked_requests: int = 0
    unique_users: int = 0
    
    def get_block_rate(self) -> float:
        """Calculate the percentage of blocked requests"""
        if self.total_requests == 0:
            return 0.0
        return (self.blocked_requests / self.total_requests) * 100

class RateLimiter:
    """
    Sliding window rate limiter implementation
    Tracks requests per user and enforces limits
    """
    
    def __init__(self, requests_per_window: int = 10, window_size: int = 60):
        """
        Initialize rate limiter
        
        Args:
            requests_per_window: Maximum requests allowed per window
            window_size: Time window in seconds
        """
        self.requests_per_window = requests_per_window
        self.window_size = window_size
        
        # User request tracking: user_id -> deque of timestamps
        self.user_requests: Dict[int, Deque[float]] = defaultdict(lambda: deque())
        
        # Statistics tracking
        self.stats = RateLimitStats()
        
        logger.info(f"Rate limiter initialized: {requests_per_window} requests per {window_size}s")
    
    def is_allowed(self, user_id: int) -> bool:
        """
        Check if user is allowed to make a request
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if request is allowed, False if rate limited
        """
        current_time = time.time()
        user_requests = self.user_requests[user_id]
        
        # Remove old requests outside the current window
        while user_requests and current_time - user_requests[0] > self.window_size:
            user_requests.popleft()
        
        # Update statistics
        self.stats.total_requests += 1
        if user_id not in [uid for uid in self.user_requests.keys() if self.user_requests[uid]]:
            self.stats.unique_users = len([uid for uid in self.user_requests.keys() if self.user_requests[uid]])
        
        # Check if user has exceeded the limit
        if len(user_requests) >= self.requests_per_window:
            self.stats.blocked_requests += 1
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False
        
        # Add current request timestamp
        user_requests.append(current_time)
        return True
    
    def get_remaining_requests(self, user_id: int) -> int:
        """Get number of remaining requests for user in current window"""
        current_time = time.time()
        user_requests = self.user_requests[user_id]
        
        # Clean old requests
        while user_requests and current_time - user_requests[0] > self.window_size:
            user_requests.popleft()
        
        return max(0, self.requests_per_window - len(user_requests))
    
    def get_reset_time(self, user_id: int) -> float:
        """Get time until rate limit resets for user"""
        user_requests = self.user_requests[user_id]
        if not user_requests:
            return 0
        
        current_time = time.time()
        oldest_request = user_requests[0]
        reset_time = oldest_request + self.window_size
        
        return max(0, reset_time - current_time)
    
    def get_user_stats(self, user_id: int) -> Dict[str, any]:
        """Get detailed statistics for a specific user"""
        current_time = time.time()
        user_requests = self.user_requests[user_id]
        
        # Clean old requests
        while user_requests and current_time - user_requests[0] > self.window_size:
            user_requests.popleft()
        
        return {
            "requests_in_window": len(user_requests),
            "remaining_requests": self.get_remaining_requests(user_id),
            "reset_time_seconds": self.get_reset_time(user_id),
            "is_rate_limited": len(user_requests) >= self.requests_per_window
        }
    
    def get_global_stats(self) -> RateLimitStats:
        """Get global rate limiting statistics"""
        # Update unique users count
        active_users = len([uid for uid in self.user_requests.keys() if self.user_requests[uid]])
        self.stats.unique_users = active_users
        
        return self.stats
    
    def cleanup_old_data(self):
        """Clean up old request data to prevent memory leaks"""
        current_time = time.time()
        users_to_remove = []
        
        for user_id, requests in self.user_requests.items():
            # Remove old requests
            while requests and current_time - requests[0] > self.window_size:
                requests.popleft()
            
            # Mark empty request queues for removal
            if not requests:
                users_to_remove.append(user_id)
        
        # Remove empty user entries
        for user_id in users_to_remove:
            del self.user_requests[user_id]
        
        if users_to_remove:
            logger.debug(f"Cleaned up data for {len(users_to_remove)} inactive users")
