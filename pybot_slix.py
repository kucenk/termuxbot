#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"Talisman (slixmpp) - minimal migration skeleton
Save as pybot_slix.py and edit config.txt (same keys as original pybot: CONNECT_SERVER, PORT, JID, PASSWORD, RESOURCE, DEFAULT_NICK, ADMINS, etc.)
This is an async (slixmpp) based starting point to migrate from xmpppy to slixmpp.
\"\"\"
import os
import sys
import asyncio
import time
import threading
import traceback
from ast import literal_eval as safe_eval

# ensure script dir is current working dir
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

try:
    import slixmpp
    from slixmpp.exceptions import IqError, IqTimeout
except Exception as e:
    print("Missing dependency: slixmpp is required. Install with: pip install slixmpp")
    raise

GENERAL_CONFIG_FILE = 'config.txt'
GROUPCHAT_CACHE_FILE = 'dynamic/chatrooms.list'
PLUGIN_DIR = 'plugins'

# load config (uses same format as original repo which used eval())
if not os.path.exists(GENERAL_CONFIG_FILE):
    print("Missing config file:", GENERAL_CONFIG_FILE)
    sys.exit(1)

with open(GENERAL_CONFIG_FILE, 'r', encoding='utf-8') as f:
    GENERAL_CONFIG = safe_eval(f.read())

CONNECT_SERVER = GENERAL_CONFIG.get('CONNECT_SERVER')
PORT = GENERAL_CONFIG.get('PORT', 5222)
JID = GENERAL_CONFIG.get('JID')
PASSWORD = GENERAL_CONFIG.get('PASSWORD')
RESOURCE = GENERAL_CONFIG.get('RESOURCE', 'talisman')
DEFAULT_NICK = GENERAL_CONFIG.get('DEFAULT_NICK', 'Talisman')
ADMINS = GENERAL_CONFIG.get('ADMINS', [])
AUTO_RESTART = GENERAL_CONFIG.get('AUTO_RESTART', False)

# helpers for file operations
def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, data):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(data)

class TalismanBot(slixmpp.ClientXMPP):
    def __init__(self, jid, password):
        # slixmpp expects full JID optionally with resource set separately
        super().__init__(jid, password)
        self.nick = DEFAULT_NICK
        self.room_configs = {}

        # register plugins we need
        self.register_plugin('xep_0030')  # service discovery
        self.register_plugin('xep_0045')  # multi-user chat
        self.register_plugin('xep_0199')  # XMPP ping

        # event handlers
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("groupchat_message", self.on_groupchat_message)
        self.add_event_handler("message", self.on_message)
        self.add_event_handler("muc::%s::got_online" % self.nick, self.muc_user_online)
        self.add_event_handler("failed_auth", self.on_failed_auth)
        self.add_event_handler("disconnected", self.on_disconnected)
        self.add_event_handler("ssl_invalid_cert", self.on_ssl_invalid_cert)

        # storage for joined rooms
        self.joined_rooms = set()

    async def session_start(self, event):
        """Called when the session is ready: send presence and get roster"""
        try:
            self.send_presence()
            await self.get_roster()
        except (IqError, IqTimeout) as e:
            print("Error getting roster:", e)

        # load groupchats from dynamic/chatrooms.list if exists (compatibility)
        if os.path.exists(GROUPCHAT_CACHE_FILE):
            try:
                gch_db = safe_eval(read_file(GROUPCHAT_CACHE_FILE))
                for room, info in gch_db.items():
                    nick = info.get('nick') or DEFAULT_NICK
                    self.join_muc(room, nick)
                    self.room_configs[room] = info
            except Exception as e:
                print("Failed to parse groupchat cache:", e)

        print("Session started. Joined rooms:", list(self.joined_rooms))

    def join_muc(self, room, nick=None, password=None):
        """Join MUC room using xep_0045 plugin"""
        nick = nick or self.nick
        try:
            self.plugin['xep_0045'].join_muc(room, nick, password=password, wait=True)
            self.joined_rooms.add(room)
            print(f"Joining room {room} as {nick}")
        except Exception as e:
            print("Error joining room", room, e)

    def on_groupchat_message(self, msg):
        """Handle incoming groupchat messages"""
        # msg is a Message stanza dict-like object
        try:
            if msg['mucnick'] == self.nick:
                return  # ignore our own messages
            body = msg['body']
            from_jid = msg['from']
            room = str(from_jid).split('/')[0]
            sender_nick = msg['mucnick']
            print(f"[{room}] {sender_nick}: {body}")
            # here you can call command handlers or plugins
        except Exception:
            traceback.print_exc()

    def on_message(self, msg):
        """Handle direct chat messages (private/direct)"""
        try:
            if msg['type'] in ('chat', 'normal'):
                from_jid = msg['from']
                body = msg['body']
                print(f"[PRIVATE] {from_jid}: {body}")
                # simple auto-reply example for testing
                # self.send_message(mto=str(from_jid), mbody="I got: " + (body or ""), mtype='chat')
        except Exception:
            traceback.print_exc()

    def muc_user_online(self, presence):
        # presence callback when someone (including us) becomes online in MUC
        try:
            room = str(presence['from']).split('/')[0]
            nick = presence['muc']['nick'] if 'muc' in presence else None
            # note: slixmpp uses structured stanzas; inspect presence for details interactively
            print("Presence in", room, "nick:", nick)
        except Exception:
            traceback.print_exc()

    def on_failed_auth(self, event):
        print("Authentication failed - check JID and PASSWORD in config.txt")
        # for safety, stop
        self.disconnect()

    def on_disconnected(self, event):
        print("Disconnected from server")
        if AUTO_RESTART:
            print("AUTO_RESTART enabled - restarting process")
            # note: on Android/Termux this may behave differently
            os.execv(sys.executable, [sys.executable] + sys.argv)

    def on_ssl_invalid_cert(self, cert):
        print("SSL certificate validation failed:", cert)

    # convenience wrappers to mimic old interface
    def msg(self, target, body):
        # if target is a room in joined_rooms, send groupchat
        if target in self.joined_rooms:
            self.send_message(mto=target, mbody=body, mtype='groupchat')
        else:
            self.send_message(mto=target, mbody=body, mtype='chat')

    def leave_room(self, room, reason=''):
        if room in self.joined_rooms:
            try:
                self.plugin['xep_0045'].leave_muc(room, self.nick, reason=reason)
                self.joined_rooms.discard(room)
            except Exception as e:
                print("Error leaving room:", e)

def main():
    # build full JID with resource if provided in config
    jid = JID
    if RESOURCE and '@' in jid and '/' not in jid:
        jid = jid + '/' + RESOURCE

    xmpp = TalismanBot(jid, PASSWORD)

    # Connect using provided CONNECT_SERVER and PORT if available
    connect_args = {}
    if CONNECT_SERVER:
        host = CONNECT_SERVER
        connect_args['host'] = host
        connect_args['port'] = PORT or 5222

    # Note: use use_tls/use_ssl defaults are ok; you can pass use_tls=True if needed
    try:
        # recommended: start the event loop via connect() and process(forever=True)
        xmpp.connect(address=(connect_args.get('host'), connect_args.get('port')) if connect_args else None)
        xmpp.process(forever=True)
    except Exception as e:
        print("Connection error:", e)
        traceback.print_exc()

if __name__ == '__main__':
    main()
