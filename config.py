"""
Configuration management for AstroGeminiBot
Handles environment variables and service initialization
"""

import os
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Config:
    """Configuration class that manages all bot settings and AI service initialization"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Telegram configuration
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        # AI Service API Keys
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.together_api_key = os.getenv("TOGETHER_API_KEY")
        
        # Rate limiting configuration
        self.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
        self.rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
        
        # Conversation management
        self.conversation_timeout = int(os.getenv("CONVERSATION_TIMEOUT", "1800"))  # 30 minutes
        self.max_conversation_length = int(os.getenv("MAX_CONVERSATION_LENGTH", "20"))
        
        # AI service configuration
        self.default_service = os.getenv("DEFAULT_AI_SERVICE", "gemini")
        self.default_model = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")
        
        # Admin configuration
        admin_ids_str = os.getenv("ADMIN_USER_IDS", "")
        self.admin_user_ids = set()
        if admin_ids_str:
            try:
                self.admin_user_ids = set(int(uid.strip()) for uid in admin_ids_str.split(",") if uid.strip())
                logger.info(f"Admin users configured: {len(self.admin_user_ids)} admins")
            except ValueError as e:
                logger.error(f"Invalid admin user IDs format: {e}")
                self.admin_user_ids = set()
        
        # Initialize AI services
        self.ai_services = {}
        self._initialize_ai_services()
        
        # Validate that at least one AI service is available
        if not self.ai_services:
            raise ValueError("At least one AI service API key must be provided")
        
        logger.info(f"Configuration loaded. Available services: {list(self.ai_services.keys())}")
    
    def _initialize_ai_services(self):
        """Initialize available AI services based on API keys"""
        
        # Initialize Gemini service
        if self.gemini_api_key:
            try:
                from services.gemini_service import GeminiService
                self.ai_services["gemini"] = GeminiService(self.gemini_api_key)
                logger.info("Gemini service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini service: {e}")
        
        # Initialize Together AI service
        if self.together_api_key:
            try:
                from services.together_service import TogetherService
                self.ai_services["together"] = TogetherService(self.together_api_key)
                logger.info("Together AI service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Together AI service: {e}")
    
    def get_available_services(self) -> List[str]:
        """Get list of available AI services"""
        return list(self.ai_services.keys())
    
    def get_service(self, service_name: str):
        """Get AI service by name"""
        return self.ai_services.get(service_name)
    
    def get_default_service(self):
        """Get default AI service"""
        if self.default_service in self.ai_services:
            return self.ai_services[self.default_service]
        
        # Return first available service if default is not available
        if self.ai_services:
            return list(self.ai_services.values())[0]
        
        return None
    
    def get_all_models(self) -> Dict[str, List[str]]:
        """Get all available models from all services"""
        models = {}
        for service_name, service in self.ai_services.items():
            try:
                models[service_name] = service.get_available_models()
            except Exception as e:
                logger.error(f"Failed to get models for {service_name}: {e}")
                models[service_name] = []
        return models
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin"""
        return user_id in self.admin_user_ids
    
    def add_admin(self, user_id: int) -> bool:
        """Add user as admin"""
        if user_id not in self.admin_user_ids:
            self.admin_user_ids.add(user_id)
            logger.info(f"Added admin user: {user_id}")
            return True
        return False
    
    def remove_admin(self, user_id: int) -> bool:
        """Remove user from admin"""
        if user_id in self.admin_user_ids:
            self.admin_user_ids.remove(user_id)
            logger.info(f"Removed admin user: {user_id}")
            return True
        return False
