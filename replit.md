# Python XMPP Bot for jabber.ru

## Overview

A lightweight XMPP bot designed for Termux Android environment that connects to jabber.ru server. The bot provides ping functionality, welcome messages for conference rooms and new users, and hourly time announcements in GMT+7 timezone. The application is built using the slixmpp library and follows a modular architecture with separate components for command handling, scheduling, and configuration management.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Application Structure

The bot follows a modular design pattern with clear separation of concerns:

- **Main Entry Point (`main.py`)**: Handles application startup, logging configuration, signal handling for graceful shutdown, and bot lifecycle management
- **Bot Core (`bot.py`)**: Implements the main XMPP client using slixmpp, manages connections, handles events, and coordinates between different modules
- **Command System (`commands.py`)**: Provides a pluggable command handler with support for ping, help, time, status, and uptime commands
- **Scheduling (`scheduler.py`)**: Manages hourly automated announcements using asyncio for non-blocking operations
- **Configuration (`config.py`)**: Handles configuration loading from both INI files and environment variables with validation

### XMPP Protocol Implementation

The bot uses slixmpp as the core XMPP library with these key plugins:
- **XEP-0030**: Service Discovery for server capability detection
- **XEP-0045**: Multi-User Chat (MUC) support for conference room functionality
- **XEP-0199**: XMPP Ping for network latency testing and connection health monitoring

### Event-Driven Architecture

The system implements an event-driven model handling:
- Session start events for initial connection setup
- Message events for command processing
- MUC presence and join events for user tracking and welcome messages
- Disconnection events for connection recovery

### Asynchronous Processing

The bot leverages asyncio for:
- Non-blocking XMPP connection management
- Concurrent command processing
- Scheduled message delivery without blocking main operations
- Graceful shutdown handling

### Configuration Management

Supports flexible configuration through:
- INI file-based configuration with default fallbacks
- Environment variable overrides for deployment flexibility
- Validation of required settings before startup
- Customizable messages and timezone settings

### Error Handling and Logging

Implements comprehensive error handling with:
- Structured logging to both console and file
- Exception handling in command processing
- Connection recovery mechanisms
- Signal-based graceful shutdown

## External Dependencies

### Core XMPP Library
- **slixmpp**: Python XMPP library for protocol implementation and connection management

### Target Platform
- **Termux Android**: Optimized for Android terminal environment
- **jabber.ru**: Configured for jabber.ru XMPP server connectivity

### Python Standard Libraries
- **asyncio**: Asynchronous programming support
- **logging**: Application logging and debugging
- **configparser**: Configuration file parsing
- **datetime**: Time handling for scheduling and announcements
- **signal**: Graceful shutdown handling
- **subprocess**: System command execution for ping functionality