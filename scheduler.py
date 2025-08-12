"""
Message scheduler for hourly announcements
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

class MessageScheduler:
    """Handle scheduled messages"""
    
    def __init__(self, bot, timezone_offset=7):
        """Initialize scheduler"""
        self.bot = bot
        self.timezone_offset = timezone_offset
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.task = None
    
    def start(self):
        """Start the scheduler"""
        if not self.running:
            self.running = True
            self.task = asyncio.create_task(self._schedule_loop())
            self.logger.info("Message scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.task:
            self.task.cancel()
        self.logger.info("Message scheduler stopped")
    
    async def _schedule_loop(self):
        """Main scheduling loop"""
        try:
            while self.running:
                # Calculate time until next hour
                now = datetime.now(timezone(timedelta(hours=self.timezone_offset)))
                next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                wait_seconds = (next_hour - now).total_seconds()
                
                self.logger.info(f"Next hourly message in {wait_seconds:.0f} seconds at {next_hour.strftime('%H:%M')}")
                
                # Wait until next hour
                await asyncio.sleep(wait_seconds)
                
                if self.running:  # Check if still running after sleep
                    await self.bot.send_hourly_message()
                
        except asyncio.CancelledError:
            self.logger.info("Scheduler task cancelled")
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")
            # Restart scheduler after error
            if self.running:
                await asyncio.sleep(60)  # Wait 1 minute before restarting
                self.task = asyncio.create_task(self._schedule_loop())
