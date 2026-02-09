# backend/core/logging.py
"""Logging configuration for the application."""
import sys
from loguru import logger

# Configure Loguru to output to stdout
logger.configure(handlers=[{"sink": sys.stdout, "level": "INFO"}])


def get_logger(name: str):
    """Get a logger instance with the given name."""
    return logger.bind(name=name)
