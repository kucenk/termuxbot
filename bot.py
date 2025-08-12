"""
XMPP Bot Implementation using slixmpp
Handles connection, messaging, and MUC operations
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
import slixmpp
from slixmpp.exceptions import IqError, IqTimeout
from commands import CommandHandler
from scheduler import MessageScheduler

class JabberBot(slixmpp.ClientXMPP):
    """Main XMPP Bot class"""
    
    def __init__(self, config):
        """Initialize the bot with configuration"""
        super().__init__(config.jid, config.password)
        
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.command_handler = CommandHandler(self)
        self.scheduler = MessageScheduler(self, config.timezone_offset)
        
        # Track joined rooms and users
        self.joined_rooms = set()
        self.room_users = {}
        
        # Register event handlers
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message_handler)
        self.add_event_handler("muc::presence", self.muc_presence_handler)
        self.add_event_handler("muc::join", self.muc_join_handler)
        self.add_event_handler("disconnected", self.disconnected_handler)
        
        # Enable plugins
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0045')  # Multi-User Chat
        self.register_plugin('xep_0199')  # XMPP Ping
        
        self.logger.info("Bot initialized")
    
    async def session_start(self, event):
        """Handle session start"""
        self.logger.info("Session started")
        
        # Send presence
        self.send_presence()
        
        # Get roster
        try:
            await self.get_roster()
        except IqError as e:
            self.logger.error(f"Error getting roster: {e}")
        
        # Join conference rooms
        for room in self.config.rooms:
            await self.join_room(room)
        
        # Start scheduler
        self.scheduler.start()
        
        self.logger.info("Bot is now online and ready")
    
    async def join_room(self, room_jid):
        """Join a MUC room"""
        try:
            self.logger.info(f"Joining room: {room_jid}")
            self.plugin['xep_0045'].join_muc(
                room_jid, 
                self.config.nickname
            )
            self.joined_rooms.add(room_jid)
            self.room_users[room_jid] = set()
            
            # Send welcome message after joining
            await asyncio.sleep(2)  # Brief delay to ensure join is complete
            welcome_msg = self.config.welcome_message.format(
                nickname=self.config.nickname,
                time=datetime.now(timezone(timedelta(hours=self.config.timezone_offset))).strftime("%H:%M GMT+7")
            )
            self.send_message(mto=room_jid, mbody=welcome_msg, mtype='groupchat')
            
        except Exception as e:
            self.logger.error(f"Error joining room {room_jid}: {e}")
    
    async def message_handler(self, msg):
        """Handle incoming messages"""
        if msg['type'] in ('chat', 'normal'):
            # Private message
            await self.handle_private_message(msg)
        elif msg['type'] == 'groupchat':
            # Group chat message
            await self.handle_group_message(msg)
    
    async def handle_private_message(self, msg):
        """Handle private messages"""
        if msg['from'].bare == self.boundjid.bare:
            return  # Ignore own messages
        
        body = msg['body'].strip()
        self.logger.info(f"Private message from {msg['from']}: {body}")
        
        # Process commands
        response = await self.command_handler.process_command(body, msg['from'], 'chat')
        
        if response:
            msg.reply(response).send()
    
    async def handle_group_message(self, msg):
        """Handle group chat messages"""
        if msg['mucnick'] == self.config.nickname:
            return  # Ignore own messages
        
        body = msg['body'].strip()
        room = msg['from'].bare
        
        self.logger.info(f"Group message in {room} from {msg['mucnick']}: {body}")
        
        # Check if message is directed at bot
        if body.startswith(f"{self.config.nickname}:") or body.startswith("!"):
            command = body.replace(f"{self.config.nickname}:", "").strip()
            if command.startswith("!"):
                command = command[1:]  # Remove ! prefix
            
            response = await self.command_handler.process_command(
                command, msg['from'], 'groupchat', msg['mucnick']
            )
            
            if response:
                self.send_message(mto=room, mbody=response, mtype='groupchat')
    
    async def muc_presence_handler(self, presence):
        """Handle MUC presence changes"""
        room = presence['from'].bare
        nick = presence['from'].resource
        
        if room in self.joined_rooms:
            if nick not in self.room_users.get(room, set()):
                # New user joined
                if nick != self.config.nickname:  # Don't welcome ourselves
                    self.logger.info(f"New user {nick} joined {room}")
                    self.room_users[room].add(nick)
                    
                    # Send welcome message to new user
                    welcome_msg = self.config.user_welcome_message.format(
                        nickname=nick,
                        room=room,
                        bot_nick=self.config.nickname
                    )
                    
                    await asyncio.sleep(1)  # Brief delay
                    self.send_message(mto=room, mbody=welcome_msg, mtype='groupchat')
    
    async def muc_join_handler(self, presence):
        """Handle successful MUC joins"""
        room = presence['from'].bare
        self.logger.info(f"Successfully joined room: {room}")
    
    async def disconnected_handler(self, event):
        """Handle disconnection"""
        self.logger.warning("Disconnected from server")
        self.scheduler.stop()
        
        # Attempt reconnection
        await asyncio.sleep(5)
        self.logger.info("Attempting to reconnect...")
    
    async def send_hourly_message(self):
        """Send hourly time announcement to all rooms"""
        now = datetime.now(timezone(timedelta(hours=self.config.timezone_offset)))
        message = self.config.hourly_message.format(
            time=now.strftime("%H:%M"),
            date=now.strftime("%d/%m/%Y"),
            day=now.strftime("%A")
        )
        
        for room in self.joined_rooms:
            self.send_message(mto=room, mbody=message, mtype='groupchat')
        
        self.logger.info(f"Sent hourly message: {message}")
    
    async def connect_and_run(self):
        """Connect to server and run bot"""
        self.logger.info(f"Connecting to {self.config.server}...")
        
        # Connect to server (blocks until connection established)
        if self.connect():
            self.logger.info("Connection established successfully")
        else:
            raise Exception("Failed to connect to XMPP server")
