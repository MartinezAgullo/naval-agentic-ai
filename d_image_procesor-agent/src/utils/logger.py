"""
Centralized logging configuration using Python's standard logging library.
Provides hierarchical loggers for different modules with file and console handlers.
"""

import os
import logging
import sys
from pathlib import Path
from typing import Optional


# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = "threat_detection_agent.log",
    console_level: Optional[str] = None
) -> None:
    """
    Configure logging for the entire application.
    
    Args:
        level: Default logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               If None, reads from LOG_LEVEL environment variable (default: INFO)
        log_file: Name of the log file (placed in logs/ directory)
        console_level: Console logging level (defaults to same as level)
    """
    # Read from environment variable if not specified
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    console_numeric_level = getattr(logging, console_level.upper(), numeric_level) if console_level else numeric_level
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Console handler with color-friendly format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_numeric_level)
    console_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with detailed format
    if log_file:
        file_handler = logging.FileHandler(
            LOGS_DIR / log_file,
            mode='a',
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Configure third-party loggers based on main LOG_LEVEL
    third_party_level = logging.WARNING if numeric_level >= logging.INFO else logging.INFO
    
    logging.getLogger("httpx").setLevel(third_party_level)
    logging.getLogger("httpcore").setLevel(third_party_level)
    logging.getLogger("openai").setLevel(third_party_level)
    logging.getLogger("anthropic").setLevel(third_party_level)
    logging.getLogger("urllib3").setLevel(third_party_level)
    logging.getLogger("LiteLLM").setLevel(third_party_level)
    
    root_logger.info(f"Logging initialized - Console: {level}, File: {level}")
    root_logger.debug(f"Third-party loggers set to: {logging.getLevelName(third_party_level)}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__ from calling module)
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing threat detection")
    """
    return logging.getLogger(name)


# Module-level convenience loggers
tools_logger = get_logger("threat_detection.tools")
agents_logger = get_logger("threat_detection.agents")
crew_logger = get_logger("threat_detection.crew")
gradio_logger = get_logger("threat_detection.gradio")
