# coding=utf-8

import logging
from .config import config


# Prepare logs directory
config.log.path.mkdir(parents=True, exist_ok=True)

# TODO: Setup logs from libraries


def setup_logger(
        name: str,
        level: str | int = config.log.level,
        echo: bool = config.log.echo,
) -> logging.Logger:
    """
    Create and return a logger that writes to file and console.
    """

    # Get logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # Not found => create
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

        # Log to file
        file_handler = logging.FileHandler(config.log.path / f"{name}.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        if echo:
            # Log to console
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

    return logger


# Initialize loggers
base_logger = setup_logger("base")
dim_ria_logger = setup_logger("dim_ria")
olx_logger = setup_logger("olx")
telegram_logger = setup_logger("telegram")
