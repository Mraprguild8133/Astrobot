"""
Google Gemini service implementation for AstroGeminiBot
Handles Google Gemini model interactions
"""

import logging
from typing import List, Dict, Optional
from google import genai
from google.genai import types
from .base_ai_service import BaseAIService

logger = logging.getLogger(__name__)

class GeminiService(BaseAIService):
    """Google Gemini service implementation"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = genai.Client(api_key=api_key)
        
        # Note that the newest Gemini model series is "gemini-2.5-flash" or "gemini-2.5-pro"
        # do not change this unless explicitly requested by the user
        self.available_models = [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.0-pro"
        ]
        
        logger.info("Gemini service initialized")
    
    async def generate_response(
        self, 
        user_message: str, 
        conversation_context: List[Dict[str, str]] = None,
        model: str = None
    ) -> str:
        """Generate response using Gemini API"""
        try:
            # Use default model if none specified
            if not model or model not in self.available_models:
                model = "gemini-2.5-flash"  # Default to newest fast model
            
            # Prepare conversation context
            conversation_parts = []
            
            # Add conversation context
            if conversation_context:
                for message in conversation_context[-10:]:  # Limit context
                    role = message.get('role', 'user')
                    content = message.get('content', '')
                    
                    if not content.strip():
                        continue
                    
                    # Add conversation history as context
                    if role == 'user':
                        conversation_parts.append(f"User: {content}")
                    elif role in ['assistant', 'ai']:
                        conversation_parts.append(f"Assistant: {content}")
            
            # Prepare the prompt with context
            if conversation_parts:
                context_text = "\n".join(conversation_parts[-10:])  # Last 10 exchanges
                full_prompt = (
                    f"Previous conversation:\n{context_text}\n\n"
                    f"Current user message: {user_message}\n\n"
                    f"Please respond to the current user message, taking into account the conversation context. "
                    f"Be helpful, accurate, and conversational."
                )
            else:
                full_prompt = user_message
            
            logger.debug(f"Sending request to Gemini with model {model}")
            
            # Generate response
            response = self.client.models.generate_content(
                model=model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2000,
                    system_instruction=(
                        "You are AstroGeminiBot, a helpful AI assistant. "
                        "Provide clear, accurate, and helpful responses. "
                        "Be conversational but professional."
                    )
                )
            )
            
            if response and response.text:
                content = response.text.strip()
                logger.debug(f"Received response from Gemini: {len(content)} characters")
                return content
            else:
                logger.warning("No response content from Gemini")
                return "I apologize, but I couldn't generate a response. Please try again."
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise e
    
    def get_available_models(self) -> List[str]:
        """Get list of available Gemini models"""
        return self.available_models.copy()
    
    def get_service_name(self) -> str:
        """Get service name"""
        return "gemini"
    
    def format_conversation_context(self, context: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format conversation context for Gemini API"""
        if not context:
            return []
        
        # Gemini handles context differently, so we'll format it as conversation history
        formatted = []
        for message in context[-8:]:  # Limit to last 8 messages
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if not content.strip():
                continue
            
            formatted.append({
                "role": role,
                "content": content
            })
        
        return formatted
