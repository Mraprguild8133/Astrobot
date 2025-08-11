#!/usr/bin/env python3
"""
Web Status Service for AstroGeminiBot
Provides a web interface to monitor bot status and statistics
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

from flask import Flask, render_template, jsonify
import threading

# Setup basic logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import bot components for status monitoring
try:
    from config import Config
    from rate_limiter import RateLimiter
    from utils.conversation_manager import ConversationManager
except ImportError as e:
    logger.warning(f"Could not import bot components: {e}")

app = Flask(__name__)

class BotStatusMonitor:
    """Monitor bot status and provide web interface"""
    
    def __init__(self):
        self.config = None
        self.rate_limiter = None
        self.conversation_manager = None
        self.bot_start_time = datetime.now()
        self.last_update = datetime.now()
        
        # Initialize components
        try:
            self.config = Config()
            self.rate_limiter = RateLimiter()
            self.conversation_manager = ConversationManager()
            logger.info("Bot status monitor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize bot status monitor: {e}")
    
    def get_bot_status(self) -> Dict[str, Any]:
        """Get comprehensive bot status"""
        try:
            uptime = datetime.now() - self.bot_start_time
            
            # Get statistics
            if self.rate_limiter:
                rate_stats = self.rate_limiter.get_global_stats()
            else:
                rate_stats = type('obj', (object,), {
                    'total_requests': 0,
                    'blocked_requests': 0,
                    'get_block_rate': lambda: 0.0
                })()
            
            if self.conversation_manager:
                conv_stats = self.conversation_manager.get_global_stats()
            else:
                conv_stats = {
                    'active_conversations': 0,
                    'total_conversations': 0,
                    'total_messages': 0,
                    'unique_users': 0
                }
            
            # Get AI service status
            available_services = []
            if self.config:
                available_services = self.config.get_available_services()
                admin_count = len(self.config.admin_user_ids) if hasattr(self.config, 'admin_user_ids') else 0
            else:
                admin_count = 0
            
            return {
                'status': 'running',
                'uptime': str(uptime).split('.')[0],  # Remove microseconds
                'uptime_seconds': int(uptime.total_seconds()),
                'last_update': self.last_update.isoformat(),
                'bot_info': {
                    'available_services': available_services,
                    'admin_count': admin_count,
                    'default_service': getattr(self.config, 'default_service', 'unknown') if self.config else 'unknown',
                    'default_model': getattr(self.config, 'default_model', 'unknown') if self.config else 'unknown'
                },
                'statistics': {
                    'total_requests': rate_stats.total_requests,
                    'blocked_requests': rate_stats.blocked_requests,
                    'block_rate': round(rate_stats.get_block_rate(), 2),
                    'active_conversations': conv_stats['active_conversations'],
                    'total_conversations': conv_stats['total_conversations'],
                    'total_messages': conv_stats['total_messages'],
                    'unique_users': conv_stats['unique_users']
                },
                'health': {
                    'config_loaded': self.config is not None,
                    'rate_limiter_active': self.rate_limiter is not None,
                    'conversation_manager_active': self.conversation_manager is not None,
                    'services_available': len(available_services) > 0
                }
            }
        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'last_update': datetime.now().isoformat()
            }
    
    def update_status(self):
        """Update last activity timestamp"""
        self.last_update = datetime.now()

# Global status monitor instance
status_monitor = BotStatusMonitor()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    status = status_monitor.get_bot_status()
    return render_template('dashboard.html', status=status)

@app.route('/api/status')
def api_status():
    """API endpoint for bot status"""
    status = status_monitor.get_bot_status()
    status_monitor.update_status()
    return jsonify(status)

@app.route('/api/health')
def api_health():
    """Simple health check endpoint"""
    try:
        status = status_monitor.get_bot_status()
        is_healthy = (
            status.get('status') == 'running' and
            status.get('health', {}).get('config_loaded', False) and
            status.get('health', {}).get('services_available', False)
        )
        
        return jsonify({
            'healthy': is_healthy,
            'status': status.get('status', 'unknown'),
            'timestamp': datetime.now().isoformat()
        }), 200 if is_healthy else 503
    
    except Exception as e:
        return jsonify({
            'healthy': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/api/metrics')
def api_metrics():
    """Prometheus-style metrics endpoint"""
    try:
        status = status_monitor.get_bot_status()
        stats = status.get('statistics', {})
        
        metrics = [
            f"# HELP astrogeminibot_requests_total Total number of requests",
            f"# TYPE astrogeminibot_requests_total counter",
            f"astrogeminibot_requests_total {stats.get('total_requests', 0)}",
            "",
            f"# HELP astrogeminibot_blocked_requests_total Total number of blocked requests",
            f"# TYPE astrogeminibot_blocked_requests_total counter", 
            f"astrogeminibot_blocked_requests_total {stats.get('blocked_requests', 0)}",
            "",
            f"# HELP astrogeminibot_active_conversations Current active conversations",
            f"# TYPE astrogeminibot_active_conversations gauge",
            f"astrogeminibot_active_conversations {stats.get('active_conversations', 0)}",
            "",
            f"# HELP astrogeminibot_unique_users Total unique users",
            f"# TYPE astrogeminibot_unique_users gauge",
            f"astrogeminibot_unique_users {stats.get('unique_users', 0)}",
            "",
            f"# HELP astrogeminibot_uptime_seconds Bot uptime in seconds",
            f"# TYPE astrogeminibot_uptime_seconds gauge",
            f"astrogeminibot_uptime_seconds {status.get('uptime_seconds', 0)}",
        ]
        
        return '\n'.join(metrics), 200, {'Content-Type': 'text/plain'}
    
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return f"# Error generating metrics: {e}", 500, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=5000, debug=True)