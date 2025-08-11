"""
Entry point for AstroGeminiBot
Handles application startup and graceful shutdown
"""

import asyncio
import logging
import signal
import sys
from bot import AstroGeminiBot
from utils.logging_config import setup_logging

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    sys.exit(0)

async def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize and start the bot
        bot = AstroGeminiBot()
        bot.start_info()
        
        # Start the bot
        await bot.application.initialize()
        await bot.application.start()
        await bot.application.updater.start_polling()
        
        logger.info("Bot is running. Press Ctrl+C to stop.")
        
        # Keep the application running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    finally:
        # Cleanup
        if 'bot' in locals():
            try:
                await bot.application.updater.stop()
                await bot.application.stop()
                await bot.application.shutdown()
                logger.info("Bot shutdown complete.")
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
