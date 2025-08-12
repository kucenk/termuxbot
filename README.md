# Python XMPP Bot for jabber.ru

A lightweight XMPP bot designed for Termux Android environment that connects to jabber.ru server with ping functionality, welcome messages, and hourly time announcements.

## Features

- 🌐 XMPP connection to jabber.ru server
- 🏓 Ping command for network latency testing  
- 👋 Welcome messages for conference rooms and new users
- ⏰ Hourly automated time announcements (GMT+7)
- 🤖 Basic command handling system
- 🔄 Stable connection management with auto-reconnect
- 📱 Termux Android compatibility

## Installation

### Prerequisites

Install Python and required packages in Termux:

```bash
pkg update
pkg install python
pip install slixmpp
