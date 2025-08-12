"""
Configuration management for XMPP Bot
"""

import os
import configparser
import logging

class BotConfig:
    """Bot configuration handler"""
    
    def __init__(self, config_file='config.ini'):
        """Load configuration from file and environment"""
        self.logger = logging.getLogger(__name__)
        
        # Default values
        self.jid = None
        self.password = None
        self.server = "jabber.ru"
        self.port = 5222
        self.nickname = "PyBot"
        self.rooms = []
        self.timezone_offset = 7  # GMT+7
        
        # Messages
        self.welcome_message = "🤖 PyBot is now online! Time: {time}"
        self.user_welcome_message = "👋 Welcome {nickname}! I'm {bot_nick}, your friendly bot assistant."
        self.hourly_message = "⏰ Time update: {time} GMT+7 | Date: {date} ({day})"
        
        # Load from config file
        self.load_config(config_file)
        
        # Override with environment variables
        self.load_env_config()
        
        # Validate required settings
        self.validate_config()
    
    def load_config(self, config_file):
        """Load configuration from INI file"""
        if not os.path.exists(config_file):
            self.logger.warning(f"Config file {config_file} not found, using defaults")
            return
        
        try:
            config = configparser.ConfigParser()
            config.read(config_file)
            
            # Account settings
            if config.has_section('account'):
                self.jid = config.get('account', 'jid', fallback=self.jid)
                self.password = config.get('account', 'password', fallback=self.password)
                self.nickname = config.get('account', 'nickname', fallback=self.nickname)
            
            # Server settings
            if config.has_section('server'):
                self.server = config.get('server', 'host', fallback=self.server)
                self.port = config.getint('server', 'port', fallback=self.port)
            
            # Room settings
            if config.has_section('rooms'):
                rooms_str = config.get('rooms', 'join', fallback='')
                if rooms_str:
                    self.rooms = [room.strip() for room in rooms_str.split(',') if room.strip()]
            
            # Bot settings
            if config.has_section('bot'):
                self.timezone_offset = config.getint('bot', 'timezone_offset', fallback=self.timezone_offset)
            
            # Messages
            if config.has_section('messages'):
                self.welcome_message = config.get('messages', 'welcome', fallback=self.welcome_message)
                self.user_welcome_message = config.get('messages', 'user_welcome', fallback=self.user_welcome_message)
                self.hourly_message = config.get('messages', 'hourly', fallback=self.hourly_message)
            
            self.logger.info(f"Loaded configuration from {config_file}")
            
        except Exception as e:
            self.logger.error(f"Error loading config file: {e}")
    
    def load_env_config(self):
        """Load configuration from environment variables"""
        self.jid = os.getenv('XMPP_JID', self.jid)
        self.password = os.getenv('XMPP_PASSWORD', self.password)
        self.server = os.getenv('XMPP_SERVER', self.server)
        self.nickname = os.getenv('XMPP_NICKNAME', self.nickname)
        
        # Port
        try:
            self.port = int(os.getenv('XMPP_PORT', str(self.port)))
        except ValueError:
            self.logger.warning("Invalid XMPP_PORT in environment, using default")
        
        # Timezone
        try:
            self.timezone_offset = int(os.getenv('TIMEZONE_OFFSET', str(self.timezone_offset)))
        except ValueError:
            self.logger.warning("Invalid TIMEZONE_OFFSET in environment, using default")
        
        # Rooms
        env_rooms = os.getenv('XMPP_ROOMS', '')
        if env_rooms:
            self.rooms = [room.strip() for room in env_rooms.split(',') if room.strip()]
    
    def validate_config(self):
        """Validate required configuration"""
        if not self.jid:
            raise ValueError("XMPP JID is required (set in config.ini or XMPP_JID environment variable)")
        
        if not self.password:
            raise ValueError("XMPP password is required (set in config.ini or XMPP_PASSWORD environment variable)")
        
        self.logger.info(f"Configuration validated - JID: {self.jid}, Server: {self.server}:{self.port}")
