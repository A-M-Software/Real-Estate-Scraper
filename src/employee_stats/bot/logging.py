import logging
import sys


def setup_logging() -> None:
    """
    Configure application-wide logging.

    - INFO level by default
    - readable format
    - logs to stdout (important for Docker)
    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
