"""
Message handlers for AstroGeminiBot
Handles text messages and AI responses
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class MessageHandlers:
    """Handles incoming messages and AI responses"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.rate_limiter = bot.rate_limiter
        self.conversation_manager = bot.conversation_manager
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages"""
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        
        logger.info(f"Message from user {user_id} ({user.username}): {message_text[:100]}...")
        
        # Check rate limiting
        if not self.rate_limiter.is_allowed(user_id):
            remaining_time = self.rate_limiter.get_reset_time(user_id)
            await update.message.reply_text(
                f"⚠️ **Rate Limit Exceeded**\n\n"
                f"You've reached the maximum number of requests per time window.\n"
                f"Please wait {remaining_time:.0f} seconds before sending another message.\n\n"
                f"Limit: {self.rate_limiter.requests_per_window} requests per {self.rate_limiter.window_size} seconds",
                parse_mode='Markdown'
            )
            return
        
        # Get user preferences
        user_prefs = self.conversation_manager.get_user_preferences(user_id)
        service_name = user_prefs.get('service', 'gemini')
        model_name = user_prefs.get('model', 'gemini-2.5-flash')
        
        # Get AI service
        service = self.config.get_service(service_name)
        if not service:
            await update.message.reply_text(
                f"❌ **Service Unavailable**\n\n"
                f"The {service_name} service is not available. "
                f"Please use `/model` to select a different service.\n\n"
                f"Available services: {', '.join(self.config.get_available_services())}",
                parse_mode='Markdown'
            )
            return
        
        # Send typing indicator
        await update.message.chat.send_action("typing")
        
        try:
            # Add user message to conversation
            self.conversation_manager.add_message(user_id, "user", message_text)
            
            # Get conversation context
            conversation = self.conversation_manager.get_conversation(user_id)
            context_messages = conversation.get_context_messages() if conversation else []
            
            # Generate AI response
            response = await service.generate_response(
                user_message=message_text,
                conversation_context=context_messages,
                model=model_name
            )
            
            if response:
                # Add AI response to conversation
                self.conversation_manager.add_message(user_id, "assistant", response)
                
                # Send response to user
                await update.message.reply_text(response)
                
                logger.info(f"Response sent to user {user_id} using {service_name}/{model_name}")
            else:
                await update.message.reply_text(
                    "❌ **No Response Generated**\n\n"
                    "The AI service didn't generate a response. Please try again.",
                    parse_mode='Markdown'
                )
        
        except Exception as e:
            logger.error(f"Error generating response for user {user_id}: {e}", exc_info=True)
            
            # Try fallback to another service
            fallback_response = await self._try_fallback_services(
                user_id, message_text, service_name, context_messages
            )
            
            if fallback_response:
                # Add fallback response to conversation
                self.conversation_manager.add_message(user_id, "assistant", fallback_response)
                await update.message.reply_text(fallback_response)
                logger.info(f"Fallback response sent to user {user_id}")
            else:
                await update.message.reply_text(
                    f"❌ **Error Generating Response**\n\n"
                    f"I encountered an error while processing your message. "
                    f"Please try again or use `/model` to select a different AI service.\n\n"
                    f"Error: {str(e)[:100]}...",
                    parse_mode='Markdown'
                )
    
    async def _try_fallback_services(self, user_id: int, message: str, failed_service: str, context_messages: list) -> str:
        """Try to get response from alternative AI services"""
        available_services = self.config.get_available_services()
        
        for service_name in available_services:
            if service_name == failed_service:
                continue
            
            try:
                service = self.config.get_service(service_name)
                if service:
                    logger.info(f"Trying fallback service {service_name} for user {user_id}")
                    
                    # Get default model for fallback service
                    models = service.get_available_models()
                    fallback_model = models[0] if models else None
                    
                    if fallback_model:
                        response = await service.generate_response(
                            user_message=message,
                            conversation_context=context_messages,
                            model=fallback_model
                        )
                        
                        if response:
                            # Update user preferences to working service
                            self.conversation_manager.update_user_preferences(user_id, {
                                'service': service_name,
                                'model': fallback_model
                            })
                            
                            fallback_notice = (
                                f"⚠️ *Switched to {service_name.title()}/{fallback_model} "
                                f"due to {failed_service} service error*\n\n"
                            )
                            
                            return fallback_notice + response
            
            except Exception as e:
                logger.error(f"Fallback service {service_name} also failed: {e}")
                continue
        
        return None
