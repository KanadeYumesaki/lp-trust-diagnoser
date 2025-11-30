# lp_trust_diagnoser/logging_config.py
from __future__ import annotations

import logging
from typing import Optional


def configure_logging(level: int = logging.INFO, logger_name: Optional[str] = None) -> None:
    """
    Configure basic logging for the application.

    This function is idempotent: calling it multiple times won't add duplicate handlers.
    """
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        # Already configured
        return

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
