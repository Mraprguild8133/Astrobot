# AstroGeminiBot

## Overview

AstroGeminiBot is a multi-AI Telegram bot that provides users access to Google Gemini and Together AI's open-source models. The bot features conversation management, rate limiting, user preferences, and a modular architecture that allows easy integration of new AI services. Users can interact with different AI models through a unified Telegram interface, with the ability to switch between providers and maintain conversation context.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework Architecture
The application uses the python-telegram-bot library as the core framework for handling Telegram interactions. The main bot class (`AstroGeminiBot`) orchestrates all components and manages the application lifecycle. Handler classes are separated by functionality - command handlers for slash commands and message handlers for text processing.

### Modular AI Service Architecture
The system implements a plugin-based architecture for AI services using an abstract base class (`BaseAIService`) that defines a common interface. Each AI provider (Gemini, Together AI) implements this interface, allowing for easy addition of new services without modifying core bot logic. Services are initialized at startup and managed through a configuration system.

### Rate Limiting System
A sliding window rate limiter tracks user requests using in-memory storage with deques to maintain request timestamps. The system enforces configurable limits (default: 10 requests per 60 seconds) and provides statistics tracking for monitoring bot usage patterns.

### Conversation Management
The bot maintains conversation context using an in-memory conversation manager that stores user messages and AI responses. Conversations support automatic trimming to prevent memory issues and include timestamp tracking for session management. The system stores user preferences for AI service and model selection.

### Configuration Management
Environment-based configuration system loads API keys and settings from environment variables with fallback defaults. The config class validates required credentials and initializes available AI services, ensuring at least one service is operational before bot startup. Admin access control is implemented through Telegram user ID verification stored in environment variables.

### Error Handling and Logging
Structured logging system with configurable levels and both console and file output options. The application includes graceful shutdown handling with signal management and comprehensive error handling throughout the request lifecycle.

## External Dependencies

### AI Service APIs
- **Google Gemini API**: Integrates Google's Gemini models (2.5-flash, 2.5-pro, 1.5-pro series)
- **Together AI API**: Accesses open-source models like Llama, Mixtral, and Qwen through REST API

### Telegram Bot Platform
- **Telegram Bot API**: Core platform for bot interactions and message handling
- **python-telegram-bot**: Primary library for Telegram integration and webhook/polling support

### Python Dependencies
- **httpx**: HTTP client for Together AI API communications
- **google-genai**: Google's official SDK for Gemini model interactions
- **python-dotenv**: Environment variable management from .env files

### Development and Runtime
- **asyncio**: Asynchronous programming support for concurrent request handling
- **logging**: Built-in Python logging for application monitoring and debugging