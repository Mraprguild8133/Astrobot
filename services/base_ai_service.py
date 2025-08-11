"""
Base AI service interface for AstroGeminiBot
Defines common interface for all AI providers
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class BaseAIService(ABC):
    """Abstract base class for AI services"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    @abstractmethod
    async def generate_response(
        self, 
        user_message: str, 
        conversation_context: List[Dict[str, str]] = None,
        model: str = None
    ) -> str:
        """
        Generate a response from the AI service
        
        Args:
            user_message: The user's input message
            conversation_context: Previous conversation messages
            model: Specific model to use (optional)
            
        Returns:
            Generated response string
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models for this service
        
        Returns:
            List of model names
        """
        pass
    
    @abstractmethod
    def get_service_name(self) -> str:
        """
        Get the name of this service
        
        Returns:
            Service name string
        """
        pass
    
    def format_conversation_context(self, context: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Format conversation context for the specific AI service
        
        Args:
            context: Raw conversation context
            
        Returns:
            Formatted context for the service
        """
        if not context:
            return []
        
        # Default formatting - can be overridden by specific services
        formatted = []
        for message in context:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            # Map roles to service-specific format
            if role == 'user':
                formatted.append({"role": "user", "content": content})
            elif role in ['assistant', 'ai', 'system']:
                formatted.append({"role": "assistant", "content": content})
        
        return formatted
    
    def handle_error(self, error: Exception) -> str:
        """
        Handle and format errors from the AI service
        
        Args:
            error: The exception that occurred
            
        Returns:
            User-friendly error message
        """
        error_message = str(error).lower()
        
        if "rate limit" in error_message or "quota" in error_message:
            return "⚠️ Rate limit exceeded. Please try again later or switch to another AI service."
        elif "api key" in error_message or "unauthorized" in error_message:
            return "❌ Authentication error. The API key may be invalid or expired."
        elif "timeout" in error_message:
            return "⏱️ Request timed out. Please try again."
        elif "model" in error_message and "not found" in error_message:
            return "❌ The selected model is not available. Please choose a different model."
        else:
            return f"❌ An error occurred: {str(error)[:100]}..."
