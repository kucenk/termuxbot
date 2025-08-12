#!/usr/bin/env python3
"""
XMPP Bot for jabber.ru - Main Entry Point
Compatible with Termux Android environment
"""

import logging
import asyncio
import signal
import sys
from bot import JabberBot
from config import BotConfig

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bot.log', mode='a')
        ]
    )

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logging.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

async def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Load configuration
        config = BotConfig()
        
        # Create and start bot
        bot = JabberBot(config)
        logger.info("Starting XMPP Bot...")
        
        # Connect and run bot
        await bot.connect_and_run()
        
        # Keep the bot running
        while True:
            await asyncio.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error starting bot: {e}")
        sys.exit(1)
