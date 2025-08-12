"""
Command handler for XMPP Bot
Handles ping, help and other bot commands
"""

import asyncio
import subprocess
import logging
import time
from datetime import datetime, timezone, timedelta

class CommandHandler:
    """Handle bot commands"""
    
    def __init__(self, bot):
        """Initialize command handler"""
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        
        # Define available commands
        self.commands = {
            'ping': self.cmd_ping,
            'help': self.cmd_help,
            'time': self.cmd_time,
            'status': self.cmd_status,
            'uptime': self.cmd_uptime,
        }
        
        self.start_time = time.time()
    
    async def process_command(self, command_text, sender, msg_type, sender_nick=None):
        """Process a command and return response"""
        if not command_text:
            return None
        
        # Parse command and arguments
        parts = command_text.strip().split()
        if not parts:
            return None
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        self.logger.info(f"Processing command '{command}' from {sender} (args: {args})")
        
        # Execute command
        if command in self.commands:
            try:
                return await self.commands[command](args, sender, msg_type, sender_nick)
            except Exception as e:
                self.logger.error(f"Error executing command '{command}': {e}")
                return f"❌ Error executing command: {str(e)}"
        else:
            return f"❓ Unknown command '{command}'. Type 'help' for available commands."
    
    async def cmd_ping(self, args, sender, msg_type, sender_nick=None):
        """Ping command - measure network latency"""
        target = args[0] if args else "google.com"
        
        # Sanitize target to prevent command injection
        if not self.is_valid_hostname(target):
            return "❌ Invalid hostname format"
        
        try:
            # Use ping command (works on most Unix-like systems including Termux)
            start_time = time.time()
            process = await asyncio.create_subprocess_exec(
                'ping', '-c', '3', '-W', '5', target,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            end_time = time.time()
            
            if process.returncode == 0:
                # Parse ping output for average time
                output = stdout.decode()
                lines = output.split('\n')
                
                # Look for statistics line
                stats_line = None
                for line in lines:
                    if 'avg' in line and 'ms' in line:
                        stats_line = line
                        break
                
                if stats_line:
                    # Extract average time
                    try:
                        # Parse format like: "rtt min/avg/max/mdev = 12.345/23.456/34.567/5.678 ms"
                        parts = stats_line.split('=')[1].strip().split('/')
                        avg_ms = float(parts[1])
                        return f"🏓 Ping to {target}: {avg_ms:.1f}ms average"
                    except:
                        pass
                
                # Fallback: calculate total time
                total_ms = (end_time - start_time) * 1000
                return f"🏓 Ping to {target}: {total_ms:.0f}ms (total time)"
            
            else:
                error_msg = stderr.decode().strip()
                return f"❌ Ping failed to {target}: {error_msg}"
                
        except FileNotFoundError:
            return "❌ Ping command not available on this system"
        except Exception as e:
            return f"❌ Ping error: {str(e)}"
    
    async def cmd_help(self, args, sender, msg_type, sender_nick=None):
        """Help command - show available commands"""
        help_text = "🤖 Available Commands:\n"
        help_text += "• ping [host] - Ping a host (default: google.com)\n"
        help_text += "• time - Show current time (GMT+7)\n"
        help_text += "• status - Show bot status\n"
        help_text += "• uptime - Show bot uptime\n"
        help_text += "• help - Show this help message\n\n"
        help_text += "💡 Use: !<command> or BotName: <command>"
        
        return help_text
    
    async def cmd_time(self, args, sender, msg_type, sender_nick=None):
        """Time command - show current time"""
        now = datetime.now(timezone(timedelta(hours=self.bot.config.timezone_offset)))
        time_str = now.strftime("%H:%M:%S GMT+7")
        date_str = now.strftime("%A, %d %B %Y")
        
        return f"🕐 Current time: {time_str}\n📅 Date: {date_str}"
    
    async def cmd_status(self, args, sender, msg_type, sender_nick=None):
        """Status command - show bot status"""
        status = "🤖 Bot Status:\n"
        status += f"• Online: ✅ Yes\n"
        status += f"• Connected rooms: {len(self.bot.joined_rooms)}\n"
        status += f"• Server: {self.bot.config.server}\n"
        status += f"• Nickname: {self.bot.config.nickname}\n"
        status += f"• Timezone: GMT+{self.bot.config.timezone_offset}"
        
        return status
    
    async def cmd_uptime(self, args, sender, msg_type, sender_nick=None):
        """Uptime command - show bot uptime"""
        uptime_seconds = int(time.time() - self.start_time)
        
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        
        uptime_str = ""
        if days > 0:
            uptime_str += f"{days}d "
        if hours > 0:
            uptime_str += f"{hours}h "
        if minutes > 0:
            uptime_str += f"{minutes}m "
        uptime_str += f"{seconds}s"
        
        return f"⏱️ Bot uptime: {uptime_str.strip()}"
    
    def is_valid_hostname(self, hostname):
        """Validate hostname format"""
        import re
        # Basic hostname validation
        pattern = r'^[a-zA-Z0-9.-]+$'
        return bool(re.match(pattern, hostname)) and len(hostname) <= 253
