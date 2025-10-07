"""
Python IL STS logger module.
"""

import datetime
import logging
import os
import platform
import sys

from . import __about__

# Ensure log directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Date and time for logging
dt = datetime.datetime.now()
dt = dt.strftime("%Y%m%d")

# Configure the logger
LOG_FILE = os.path.join(LOG_DIR, f"output_{dt}.log")

# Logging Level
LOGGING_LEVEL = logging.INFO

# Initialize root logger
root_logger = logging.getLogger()
if not root_logger.hasHandlers():
    logging.basicConfig(
        level=LOGGING_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, mode="w"),
            # logging.StreamHandler()
        ],
    )

# Log the project version
logging.info(f"Project Version: {__about__.__version__}")


def _log_run_info():
    """Log environment information."""
    info = [
        f"Python Version: {sys.version}",
        f"Python Implementation: {platform.python_implementation()}",
        f"Architecture: {platform.architecture()[0]}",
        f"Operating System: {platform.system()} {platform.release()}",
        f"Platform ID: {platform.platform()}",
        f"Machine: {platform.machine()}",
        f"Processor: {platform.processor()}",
    ]
    for line in info:
        logging.info(line)


def log_to_stream(stream_output, level=logging.DEBUG) -> None:
    """Log messages to a specified output stream.

    Parameters:
        stream_output: The output stream for logging (e.g., console).
        level (int): The logging level for the stream output.
    """
    root_logger.setLevel(level)
    ch = logging.StreamHandler(stream_output)
    ch.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    root_logger.addHandler(ch)


def log_to_screen(level=logging.DEBUG) -> None:
    """Log messages to the console at the specified level.

    Parameters:
        level (int): The logging level for console output.
    """
    log_to_stream(None, level)


# Log the environment information
_log_run_info()


# Return the logger
def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)