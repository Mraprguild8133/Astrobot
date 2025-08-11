"""
Conversation management for AstroGeminiBot
Handles user conversation context and preferences
"""

import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class Message:
    """Represents a single message in a conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class Conversation:
    """Represents a user's conversation"""
    user_id: int
    messages: List[Message] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation"""
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.last_activity = time.time()
    
    def get_context_messages(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """Get recent messages formatted for AI context"""
        recent_messages = self.messages[-max_messages:] if max_messages > 0 else self.messages
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            }
            for msg in recent_messages
        ]
    
    def trim_messages(self, max_length: int):
        """Trim conversation to maximum length, keeping recent messages"""
        if len(self.messages) > max_length:
            # Keep the most recent messages
            self.messages = self.messages[-max_length:]
            logger.debug(f"Trimmed conversation for user {self.user_id} to {max_length} messages")
    
    def is_expired(self, timeout_seconds: int) -> bool:
        """Check if conversation has expired"""
        return (time.time() - self.last_activity) > timeout_seconds

class ConversationManager:
    """Manages user conversations and preferences"""
    
    def __init__(self, conversation_timeout: int = 1800, max_conversation_length: int = 20):
        """
        Initialize conversation manager
        
        Args:
            conversation_timeout: Time in seconds after which conversations expire
            max_conversation_length: Maximum number of messages to keep per conversation
        """
        self.conversation_timeout = conversation_timeout
        self.max_conversation_length = max_conversation_length
        
        # Storage for conversations and user preferences
        self.conversations: Dict[int, Conversation] = {}
        self.user_preferences: Dict[int, Dict[str, any]] = defaultdict(dict)
        
        logger.info(f"Conversation manager initialized: timeout={conversation_timeout}s, max_length={max_conversation_length}")
    
    def get_conversation(self, user_id: int) -> Optional[Conversation]:
        """Get conversation for user, creating if doesn't exist"""
        # Clean up expired conversations
        self._cleanup_expired_conversations()
        
        if user_id not in self.conversations:
            self.conversations[user_id] = Conversation(user_id=user_id)
            logger.debug(f"Created new conversation for user {user_id}")
        
        return self.conversations[user_id]
    
    def add_message(self, user_id: int, role: str, content: str):
        """Add a message to user's conversation"""
        conversation = self.get_conversation(user_id)
        conversation.add_message(role, content)
        
        # Trim conversation if it gets too long
        conversation.trim_messages(self.max_conversation_length)
        
        logger.debug(f"Added {role} message to user {user_id} conversation")
    
    def clear_conversation(self, user_id: int):
        """Clear conversation for user"""
        if user_id in self.conversations:
            del self.conversations[user_id]
            logger.info(f"Cleared conversation for user {user_id}")
    
    def get_user_preferences(self, user_id: int) -> Dict[str, any]:
        """Get user preferences"""
        # Set default preferences if none exist
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                'service': 'gemini',
                'model': 'gemini-2.5-flash'
            }
        
        return self.user_preferences[user_id]
    
    def update_user_preferences(self, user_id: int, preferences: Dict[str, any]):
        """Update user preferences"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        
        self.user_preferences[user_id].update(preferences)
        logger.debug(f"Updated preferences for user {user_id}: {preferences}")
    
    def get_conversation_stats(self, user_id: int) -> Dict[str, any]:
        """Get conversation statistics for user"""
        conversation = self.conversations.get(user_id)
        
        if not conversation:
            return {
                "message_count": 0,
                "conversation_age": 0,
                "last_activity": 0
            }
        
        current_time = time.time()
        return {
            "message_count": len(conversation.messages),
            "conversation_age": current_time - conversation.created_at,
            "last_activity": current_time - conversation.last_activity,
            "user_messages": len([msg for msg in conversation.messages if msg.role == "user"]),
            "assistant_messages": len([msg for msg in conversation.messages if msg.role == "assistant"])
        }
    
    def get_global_stats(self) -> Dict[str, any]:
        """Get global conversation statistics"""
        active_conversations = 0
        total_messages = 0
        
        for conversation in self.conversations.values():
            if not conversation.is_expired(self.conversation_timeout):
                active_conversations += 1
                total_messages += len(conversation.messages)
        
        return {
            "active_conversations": active_conversations,
            "total_conversations": len(self.conversations),
            "total_messages": total_messages,
            "unique_users": len(self.user_preferences)
        }
    
    def _cleanup_expired_conversations(self):
        """Clean up expired conversations to prevent memory leaks"""
        current_time = time.time()
        expired_users = []
        
        for user_id, conversation in self.conversations.items():
            if conversation.is_expired(self.conversation_timeout):
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self.conversations[user_id]
            logger.debug(f"Cleaned up expired conversation for user {user_id}")
        
        if expired_users:
            logger.info(f"Cleaned up {len(expired_users)} expired conversations")
    
    def force_cleanup(self):
        """Force cleanup of all expired data"""
        self._cleanup_expired_conversations()
        
        # Also clean up user preferences for users with no recent activity
        active_user_ids = set(self.conversations.keys())
        inactive_preferences = []
        
        for user_id in list(self.user_preferences.keys()):
            if user_id not in active_user_ids:
                inactive_preferences.append(user_id)
        
        # Keep preferences for some time even after conversations expire
        # Only remove after extended inactivity
        if len(inactive_preferences) > 100:  # Arbitrary threshold
            for user_id in inactive_preferences[:50]:  # Remove oldest half
                del self.user_preferences[user_id]
            logger.info(f"Cleaned up {50} inactive user preferences")
