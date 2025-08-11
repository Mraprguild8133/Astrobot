"""
Command handlers for AstroGeminiBot
Handles all /command interactions
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Dict, List

logger = logging.getLogger(__name__)

class CommandHandlers:
    """Handles all bot commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.rate_limiter = bot.rate_limiter
        self.conversation_manager = bot.conversation_manager
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        
        logger.info(f"User {user_id} ({user.username}) started the bot")
        
        welcome_message = (
            f"🤖 **Welcome to AstroGeminiBot, {user.first_name}!**\n\n"
            "I'm a multi-AI assistant that can help you with various tasks using "
            "different AI providers including OpenAI, Google Gemini, and Together AI.\n\n"
            "**Available Commands:**\n"
            "• `/help` - Show detailed help\n"
            "• `/model` - Select AI model\n"
            "• `/stats` - View your usage statistics\n"
            "• `/clear` - Clear conversation history\n\n"
            "**Available AI Services:**\n"
            f"• {', '.join(self.config.get_available_services())}\n\n"
            "Just send me a message and I'll respond using the selected AI model!"
        )
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "🤖 **AstroGeminiBot Help**\n\n"
            "**Basic Usage:**\n"
            "Simply send me any message and I'll respond using the selected AI model.\n\n"
            "**Commands:**\n"
            "• `/start` - Welcome message and overview\n"
            "• `/help` - This help message\n"
            "• `/model` - Select AI service and model\n"
            "• `/stats` - View usage statistics and rate limits\n"
            "• `/clear` - Clear your conversation history\n\n"
            "**Features:**\n"
            "• 💬 **Conversation Memory**: I remember our conversation context\n"
            "• 🔄 **Multiple AI Providers**: Choose from OpenAI, Gemini, and Together AI\n"
            "• ⚡ **Rate Limiting**: Fair usage limits to ensure service availability\n"
            "• 📊 **Usage Statistics**: Track your usage and remaining requests\n\n"
            "**Tips:**\n"
            "• Be specific in your questions for better responses\n"
            "• Use `/clear` if you want to start a fresh conversation\n"
            "• Check `/stats` to monitor your usage limits\n\n"
            "Enjoy chatting with AI! 🚀"
        )
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def model(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /model command - show model selection"""
        user_id = update.effective_user.id
        
        # Get current user preferences
        user_prefs = self.conversation_manager.get_user_preferences(user_id)
        current_service = user_prefs.get('service', 'gemini')
        current_model = user_prefs.get('model', 'gemini-2.5-flash')
        
        # Create inline keyboard for service selection
        keyboard = []
        
        for service_name in self.config.get_available_services():
            emoji = "✅" if service_name == current_service else "🔘"
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {service_name.title()}", 
                    callback_data=f"service_{service_name}"
                )
            ])
        
        # Add model selection for current service
        service = self.config.get_service(current_service)
        if service:
            models = service.get_available_models()
            keyboard.append([InlineKeyboardButton("━━━ Models ━━━", callback_data="ignore")])
            
            for model in models[:10]:  # Limit to 10 models to avoid keyboard size limits
                emoji = "✅" if model == current_model else "🔘"
                keyboard.append([
                    InlineKeyboardButton(
                        f"{emoji} {model}", 
                        callback_data=f"model_{current_service}_{model}"
                    )
                ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            f"🤖 **AI Model Selection**\n\n"
            f"**Current Service:** {current_service.title()}\n"
            f"**Current Model:** {current_model}\n\n"
            "Select a service or model below:"
        )
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user_id = update.effective_user.id
        
        # Get rate limiting stats
        user_stats = self.rate_limiter.get_user_stats(user_id)
        global_stats = self.rate_limiter.get_global_stats()
        
        # Get conversation stats
        conversation = self.conversation_manager.get_conversation(user_id)
        conversation_length = len(conversation.messages) if conversation else 0
        
        # Get user preferences
        user_prefs = self.conversation_manager.get_user_preferences(user_id)
        current_service = user_prefs.get('service', 'gemini')
        current_model = user_prefs.get('model', 'gemini-2.5-flash')
        
        stats_message = (
            f"📊 **Your Usage Statistics**\n\n"
            f"**Current Settings:**\n"
            f"• Service: {current_service.title()}\n"
            f"• Model: {current_model}\n\n"
            f"**Rate Limiting:**\n"
            f"• Requests this window: {user_stats['requests_in_window']}/{self.rate_limiter.requests_per_window}\n"
            f"• Remaining requests: {user_stats['remaining_requests']}\n"
            f"• Reset in: {user_stats['reset_time_seconds']:.0f} seconds\n"
            f"• Status: {'⚠️ Limited' if user_stats['is_rate_limited'] else '✅ Available'}\n\n"
            f"**Conversation:**\n"
            f"• Messages in current session: {conversation_length}\n"
            f"• Max conversation length: {self.config.max_conversation_length}\n\n"
            f"**Global Statistics:**\n"
            f"• Total requests processed: {global_stats.total_requests}\n"
            f"• Active users: {global_stats.unique_users}\n"
            f"• Block rate: {global_stats.get_block_rate():.1f}%"
        )
        
        await update.message.reply_text(stats_message, parse_mode='Markdown')
    
    async def clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command"""
        user_id = update.effective_user.id
        
        # Clear conversation
        self.conversation_manager.clear_conversation(user_id)
        
        await update.message.reply_text(
            "🗑️ **Conversation Cleared**\n\n"
            "Your conversation history has been cleared. "
            "Starting fresh for our next interaction!",
            parse_mode='Markdown'
        )
    
    async def admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command - admin only"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text(
                "❌ **Access Denied**\n\n"
                "This command is only available to bot administrators.",
                parse_mode='Markdown'
            )
            return
        
        # Get global statistics
        global_rate_stats = self.rate_limiter.get_global_stats()
        global_conv_stats = self.conversation_manager.get_global_stats()
        
        admin_message = (
            f"🔧 **Admin Dashboard**\n\n"
            f"**Bot Status:**\n"
            f"• Available services: {', '.join(self.config.get_available_services())}\n"
            f"• Admin users: {len(self.config.admin_user_ids)}\n\n"
            f"**Global Statistics:**\n"
            f"• Total requests: {global_rate_stats.total_requests}\n"
            f"• Blocked requests: {global_rate_stats.blocked_requests}\n"
            f"• Block rate: {global_rate_stats.get_block_rate():.1f}%\n"
            f"• Active conversations: {global_conv_stats['active_conversations']}\n"
            f"• Total conversations: {global_conv_stats['total_conversations']}\n"
            f"• Total messages: {global_conv_stats['total_messages']}\n"
            f"• Unique users: {global_conv_stats['unique_users']}\n\n"
            f"**Admin Commands:**\n"
            f"• `/admin` - Show this dashboard\n"
            f"• `/broadcast <message>` - Send message to all users\n"
            f"• `/admins` - List admin users"
        )
        
        await update.message.reply_text(admin_message, parse_mode='Markdown')
    
    async def broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /broadcast command - admin only"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text(
                "❌ **Access Denied**\n\n"
                "This command is only available to bot administrators.",
                parse_mode='Markdown'
            )
            return
        
        if not context.args:
            await update.message.reply_text(
                "📢 **Broadcast Usage**\n\n"
                "Usage: `/broadcast <message>`\n\n"
                "Example: `/broadcast The bot will be updated in 1 hour`",
                parse_mode='Markdown'
            )
            return
        
        broadcast_message = " ".join(context.args)
        
        # Get all user IDs from conversation manager
        all_user_ids = list(self.conversation_manager.user_preferences.keys())
        
        if not all_user_ids:
            await update.message.reply_text(
                "📢 **No Users Found**\n\n"
                "No users have interacted with the bot yet.",
                parse_mode='Markdown'
            )
            return
        
        success_count = 0
        failed_count = 0
        
        await update.message.reply_text(
            f"📢 **Broadcasting to {len(all_user_ids)} users...**",
            parse_mode='Markdown'
        )
        
        for target_user_id in all_user_ids:
            if target_user_id == user_id:  # Skip the admin sending the message
                continue
                
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"📢 **Admin Message**\n\n{broadcast_message}",
                    parse_mode='Markdown'
                )
                success_count += 1
            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to send broadcast to user {target_user_id}: {e}")
        
        result_message = (
            f"📢 **Broadcast Complete**\n\n"
            f"• Successfully sent: {success_count}\n"
            f"• Failed to send: {failed_count}\n"
            f"• Total attempted: {len(all_user_ids) - 1}"
        )
        
        await update.message.reply_text(result_message, parse_mode='Markdown')
    
    async def admins(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admins command - admin only"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text(
                "❌ **Access Denied**\n\n"
                "This command is only available to bot administrators.",
                parse_mode='Markdown'
            )
            return
        
        if not self.config.admin_user_ids:
            await update.message.reply_text(
                "👥 **Admin Users**\n\n"
                "No admin users are currently configured.",
                parse_mode='Markdown'
            )
            return
        
        admin_list = "\n".join([f"• `{admin_id}`" for admin_id in sorted(self.config.admin_user_ids)])
        
        admin_message = (
            f"👥 **Admin Users** ({len(self.config.admin_user_ids)})\n\n"
            f"{admin_list}\n\n"
            f"*Configure admin users by setting the ADMIN_USER_IDS environment variable.*"
        )
        
        await update.message.reply_text(admin_message, parse_mode='Markdown')
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button callbacks"""
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        
        await query.answer()
        
        if data == "ignore":
            return
        
        if data.startswith("service_"):
            # Service selection
            service_name = data.replace("service_", "")
            if service_name in self.config.get_available_services():
                # Update user preferences
                self.conversation_manager.update_user_preferences(user_id, {
                    'service': service_name
                })
                
                # Get default model for the service
                service = self.config.get_service(service_name)
                if service:
                    models = service.get_available_models()
                    if models:
                        default_model = models[0]
                        self.conversation_manager.update_user_preferences(user_id, {
                            'model': default_model
                        })
                
                await query.edit_message_text(
                    f"✅ **Service Updated**\n\n"
                    f"Selected service: **{service_name.title()}**\n"
                    f"Default model: **{default_model if 'default_model' in locals() else 'N/A'}**\n\n"
                    "Use `/model` again to select a specific model.",
                    parse_mode='Markdown'
                )
        
        elif data.startswith("model_"):
            # Model selection
            parts = data.split("_", 2)
            if len(parts) == 3:
                service_name = parts[1]
                model_name = parts[2]
                
                # Update user preferences
                self.conversation_manager.update_user_preferences(user_id, {
                    'service': service_name,
                    'model': model_name
                })
                
                await query.edit_message_text(
                    f"✅ **Model Updated**\n\n"
                    f"Service: **{service_name.title()}**\n"
                    f"Model: **{model_name}**\n\n"
                    "You can now start chatting with the selected model!",
                    parse_mode='Markdown'
                )
