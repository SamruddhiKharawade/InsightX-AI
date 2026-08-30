"""
Shared logger setup. Every script in the pipeline calls get_logger(__name__)
so all log messages share consistent formatting and go to both the console
and a single logs/pipeline.log file.
"""

import logging
import sys
from pathlib import Path

# Make the project root importable so "from config.settings import ..." works
# no matter which subfolder this file is called from.
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from config.settings import LOG_DIR


def get_logger(name: str) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if this is called more than once
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_DIR / "pipeline.log")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger