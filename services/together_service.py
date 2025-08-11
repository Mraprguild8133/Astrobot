"""
Together AI service implementation for AstroGeminiBot
Handles Together AI model interactions using httpx
"""

import logging
import httpx
from typing import List, Dict, Optional
import json
from .base_ai_service import BaseAIService

logger = logging.getLogger(__name__)

class TogetherService(BaseAIService):
    """Together AI service implementation"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.api_url = "https://api.together.xyz/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Popular open-source models available on Together AI
        self.available_models = [
            "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", 
            "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
            "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "mistralai/Mistral-7B-Instruct-v0.3",
            "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
            "Qwen/Qwen2.5-72B-Instruct-Turbo"
        ]
        
        logger.info("Together AI service initialized")
    
    async def generate_response(
        self, 
        user_message: str, 
        conversation_context: List[Dict[str, str]] = None,
        model: str = None
    ) -> str:
        """Generate response using Together AI API"""
        try:
            # Use default model if none specified
            if not model or model not in self.available_models:
                model = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"  # Default to Llama
            
            # Prepare messages for Together AI API
            messages = []
            
            # Add system message
            messages.append({
                "role": "system",
                "content": (
                    "You are AstroGeminiBot, a helpful AI assistant. "
                    "Provide clear, accurate, and helpful responses. "
                    "Be conversational but professional."
                )
            })
            
            # Add conversation context
            if conversation_context:
                formatted_context = self.format_conversation_context(conversation_context)
                messages.extend(formatted_context)
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Prepare request payload
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": 2000,
                "temperature": 0.7,
                "top_p": 0.9,
                "repetition_penalty": 1.1,
                "stream": False
            }
            
            logger.debug(f"Sending request to Together AI with model {model}")
            
            # Make API request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("choices") and len(data["choices"]) > 0:
                        content = data["choices"][0]["message"]["content"]
                        logger.debug(f"Received response from Together AI: {len(content)} characters")
                        return content.strip()
                    else:
                        logger.warning("No choices in Together AI response")
                        return "I apologize, but I couldn't generate a response. Please try again."
                
                else:
                    error_msg = f"Together AI API error: {response.status_code}"
                    if response.content:
                        try:
                            error_data = response.json()
                            error_msg += f" - {error_data.get('error', {}).get('message', 'Unknown error')}"
                        except:
                            error_msg += f" - {response.text[:100]}"
                    
                    logger.error(error_msg)
                    raise Exception(error_msg)
            
        except httpx.TimeoutException:
            logger.error("Together AI request timed out")
            raise Exception("Request timed out. Please try again.")
        except Exception as e:
            logger.error(f"Together AI API error: {e}")
            raise e
    
    def get_available_models(self) -> List[str]:
        """Get list of available Together AI models"""
        return self.available_models.copy()
    
    def get_service_name(self) -> str:
        """Get service name"""
        return "together"
    
    def format_conversation_context(self, context: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format conversation context for Together AI API"""
        if not context:
            return []
        
        formatted = []
        for message in context[-8:]:  # Limit to last 8 messages
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if not content.strip():
                continue
            
            # Map roles to Together AI format (OpenAI-compatible)
            if role == 'user':
                formatted.append({"role": "user", "content": content})
            elif role in ['assistant', 'ai']:
                formatted.append({"role": "assistant", "content": content})
            elif role == 'system':
                formatted.append({"role": "system", "content": content})
        
        return formatted
