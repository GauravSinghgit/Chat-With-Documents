import os
import sys

from loguru import logger

os.makedirs("data/logs", exist_ok=True)

# Remove default handler
logger.remove()

# Console handler — colored, readable
_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.add(
    sys.stderr,
    format=_CONSOLE_FORMAT,
    level="INFO",
    colorize=True,
)

# File handler — full debug logs, rotated
logger.add(
    "data/logs/app.log",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} - {message}",
)

__all__ = ["logger"]
