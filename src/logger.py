# coding=utf-8

import logging
from .config import config

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# Prepare logs directory
config.log.path.mkdir(parents=True, exist_ok=True)


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
    logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT)

    # Log to file
    file_handler = logging.FileHandler(config.log.path / f"{name}.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # No need to add console handler here, as we set up basicConfig with StreamHandler if echo is True
    # if echo:
    #     # Log to console
    #     stream_handler = logging.StreamHandler()
    #     stream_handler.setFormatter(formatter)
    #     logger.addHandler(stream_handler)

    return logger


# Setup basic logging for libraries
logging.basicConfig(
    level="INFO",
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler()] if config.log.echo else [],
)

# Initialize loggers
base_logger = setup_logger("base")
dim_ria_logger = setup_logger("dim_ria")
olx_logger = setup_logger("olx")
telegram_logger = setup_logger("telegram")
bot_logger = setup_logger("bot")
