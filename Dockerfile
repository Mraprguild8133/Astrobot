# Multi-stage Dockerfile for AstroGeminiBot with Web Status Service
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose ports
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f https://astrobot-uyjw.onrender.com/api/health || exit 1

# Default command - can be overridden
CMD ["python", "web_status.py"]

# Production stage with gunicorn
FROM base as production

USER root
RUN pip install --no-cache-dir gunicorn
USER app

# Production command
CMD ["gunicorn", "--bind", "54.188.71.94:5000", "--workers", "2", "--timeout", "60", "web_status:app"]

# Bot-only stage for running just the Telegram bot
FROM base as bot-only

# Run the bot
CMD ["python", "main.py"]

# Development stage with additional tools
FROM base as development

USER root
RUN pip install --no-cache-dir pytest black flake8 mypy
USER app

# Development command
CMD ["python", "web_status.py"]
