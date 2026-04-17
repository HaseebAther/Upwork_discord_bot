"""Logging configuration for Upwork Discord bot."""

import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
import os


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[41m",   # Red background
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        levelname = record.levelname
        color = self.COLORS.get(levelname, "")
        
        # Format the message
        log_msg = super().format(record)
        
        # Add color to level name only
        if color:
            record.levelname = f"{color}[{levelname}]{self.RESET}"
        
        return log_msg


def setup_logging(
    log_level: str = "INFO",
    log_file: Path | str | None = None,
    console_output: bool = True,
    cleanup_retention_days: int = 10,
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging
        console_output: Whether to log to console
        cleanup_retention_days: Delete logs older than this many days (default: 10)
    
    Returns:
        Configured logger instance
    """
    # Clean up old logs
    cleanup_stats = cleanup_old_logs(retention_days=cleanup_retention_days)
    
    level = getattr(logging, log_level.upper())
    logger = logging.getLogger("upwork_bot")
    logger.setLevel(level)
    logger.propagate = False

    # Also configure root logger so module loggers (e.g. "discord_bot") emit to same handlers.
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    
    # Clear existing handlers on named logger
    logger.handlers.clear()
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        formatter = ColoredFormatter(
            fmt="%(levelname)s [%(name)s] %(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        
        file_formatter = logging.Formatter(
            fmt="%(levelname)s [%(name)s] %(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        root_logger.addHandler(file_handler)
    
    return logger


def cleanup_old_logs(logs_dir: Path = Path("logs"), retention_days: int = 10) -> dict:
    """
    Clean up log files older than retention_days.
    
    Args:
        logs_dir: Directory containing log files
        retention_days: Keep logs newer than this many days (default: 10)
    
    Returns:
        Dictionary with cleanup stats: {deleted_count, deleted_size_mb, remaining_size_mb}
    """
    logs_dir = Path(logs_dir)
    if not logs_dir.exists():
        return {"deleted_count": 0, "deleted_size_mb": 0, "remaining_size_mb": 0}
    
    cutoff_time = datetime.now() - timedelta(days=retention_days)
    deleted_count = 0
    deleted_size = 0
    remaining_size = 0
    
    try:
        for log_file in logs_dir.glob("*.log"):
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            file_size = log_file.stat().st_size
            
            if file_mtime < cutoff_time:
                # Delete old log file
                log_file.unlink()
                deleted_count += 1
                deleted_size += file_size
            else:
                # Count remaining logs
                remaining_size += file_size
    except Exception as e:
        logger = logging.getLogger("upwork_bot")
        logger.warning(f"Error cleaning up logs: {e}")
    
    return {
        "deleted_count": deleted_count,
        "deleted_size_mb": round(deleted_size / (1024 * 1024), 2),
        "remaining_size_mb": round(remaining_size / (1024 * 1024), 2),
    }


def get_log_size_estimate(
    polling_interval: int = 40,
    num_queries: int = 1,
    lines_per_poll: int = 8,
    bytes_per_line: int = 150,
    retention_days: int = 10,
) -> dict:
    """
    Estimate log file sizes based on polling parameters.
    
    Args:
        polling_interval: Seconds between polls (default: 40)
        num_queries: Number of active queries (default: 1)
        lines_per_poll: Log lines per poll cycle (default: 8)
        bytes_per_line: Bytes per log line (default: 150)
        retention_days: Retention period in days (default: 10)
    
    Returns:
        Dictionary with size estimates
    """
    # Calculate polls per day
    polls_per_day = (24 * 60 * 60) / polling_interval
    
    # Calculate daily size per query
    bytes_per_day_per_query = polls_per_day * lines_per_poll * bytes_per_line
    mb_per_day_per_query = bytes_per_day_per_query / (1024 * 1024)
    
    # Total estimates
    total_mb_per_day = mb_per_day_per_query * num_queries
    total_mb_retention = total_mb_per_day * retention_days
    
    return {
        "polls_per_day": int(polls_per_day),
        "mb_per_day_per_query": round(mb_per_day_per_query, 2),
        "mb_per_day_total": round(total_mb_per_day, 2),
        "mb_per_retention_period": round(total_mb_retention, 2),
        "retention_days": retention_days,
    }


def get_logger(name: str = "upwork_bot") -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)
