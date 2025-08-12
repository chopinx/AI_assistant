#!/usr/bin/env python3
"""
Logging Configuration Module

Centralized logging setup for the AI Assistant project.
"""

import logging
import os


def setup_logging(logger_name: str = 'ai_assistant') -> logging.Logger:
    """
    Setup logging configuration
    
    Args:
        logger_name: Name for the logger (default: 'ai_assistant')
        
    Returns:
        Configured logger instance
    """
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    if debug_mode:
        log_level = 'DEBUG'
    log_level = 'DEBUG'  # Force debug for now
    
    # Only configure if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('ai_assistant.log', mode='a')
            ]
        )
    
    # Set specific loggers to reduce noise
    logging.getLogger('anthropic').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    return logging.getLogger(logger_name)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name, ensuring logging is configured
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    # Ensure logging is configured
    if not logging.getLogger().handlers:
        setup_logging()
    
    return logging.getLogger(name)