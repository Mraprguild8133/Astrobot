#!/usr/bin/env python3
"""
Simple Web Status Service for AstroGeminiBot
Lightweight status dashboard
"""

import os
import json
from datetime import datetime
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# HTML template inline for simplicity
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AstroGeminiBot Status</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(10px);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .status-card {
            background: rgba(255,255,255,0.2);
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            border: 1px solid rgba(255,255,255,0.3);
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .status-running { background-color: #4CAF50; }
        .status-error { background-color: #f44336; }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 5px 0;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        .refresh-btn {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px auto;
            display: block;
        }
        .api-link {
            color: #87CEEB;
            text-decoration: none;
        }
        .api-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AstroGeminiBot Status</h1>
            <p>Real-time monitoring dashboard</p>
        </div>

        <div class="status-card">
            <h2>
                <span class="status-indicator status-running"></span>
                Bot Status
            </h2>
            <div class="metric">
                <span>Status:</span>
                <span>{{ status.status|title }}</span>
            </div>
            <div class="metric">
                <span>Uptime:</span>
                <span>{{ status.uptime }}</span>
            </div>
            <div class="metric">
                <span>Environment:</span>
                <span>Replit Development</span>
            </div>
        </div>

        <div class="status-card">
            <h2>🧠 Configuration</h2>
            <div class="metric">
                <span>Telegram Bot:</span>
                <span>{{ 'Configured' if status.telegram_configured else 'Not Configured' }}</span>
            </div>
            <div class="metric">
                <span>Gemini API:</span>
                <span>{{ 'Configured' if status.gemini_configured else 'Not Configured' }}</span>
            </div>
            <div class="metric">
                <span>Together AI:</span>
                <span>{{ 'Configured' if status.together_configured else 'Not Configured' }}</span>
            </div>
            <div class="metric">
                <span>Admin Users:</span>
                <span>{{ 'Configured' if status.admin_configured else 'Not Configured' }}</span>
            </div>
        </div>

        <div class="status-card">
            <h2>🔗 API Endpoints</h2>
            <div class="metric">
                <span>Status API:</span>
                <span><a href="/api/status" class="api-link">/api/status</a></span>
            </div>
            <div class="metric">
                <span>Health Check:</span>
                <span><a href="/api/health" class="api-link">/api/health</a></span>
            </div>
        </div>

        <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
        
        <div style="text-align: center; margin-top: 20px; opacity: 0.8;">
            Last updated: {{ status.timestamp }}
        </div>
    </div>

    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Simple dashboard"""
    status = get_simple_status()
    return render_template_string(DASHBOARD_HTML, status=status)

@app.route('/api/status')
def api_status():
    """Simple status API"""
    return jsonify(get_simple_status())

@app.route('/api/health')
def api_health():
    """Simple health check"""
    status = get_simple_status()
    is_healthy = (
        status['telegram_configured'] and 
        (status['gemini_configured'] or status['together_configured'])
    )
    
    return jsonify({
        'healthy': is_healthy,
        'status': 'running' if is_healthy else 'degraded',
        'timestamp': datetime.now().isoformat()
    }), 200 if is_healthy else 503

def get_simple_status():
    """Get basic bot status"""
    # Check environment variables
    telegram_configured = bool(os.getenv('TELEGRAM_BOT_TOKEN'))
    gemini_configured = bool(os.getenv('GEMINI_API_KEY'))
    together_configured = bool(os.getenv('TOGETHER_API_KEY'))
    admin_configured = bool(os.getenv('ADMIN_USER_IDS'))
    
    # Calculate uptime (simple version)
    start_time = datetime.now()
    uptime = "Running"
    
    return {
        'status': 'running',
        'uptime': uptime,
        'timestamp': datetime.now().isoformat(),
        'telegram_configured': telegram_configured,
        'gemini_configured': gemini_configured,
        'together_configured': together_configured,
        'admin_configured': admin_configured,
        'environment': 'Replit Development'
    }

if __name__ == '__main__':
    print("Starting AstroGeminiBot Status Dashboard...")
    print("Dashboard available at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)