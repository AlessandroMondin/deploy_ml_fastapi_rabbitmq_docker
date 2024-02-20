import logging


def get_logger(logger_name: str, logger_level: int = logging.DEBUG) -> logging.Logger:
    # Configure logger
    logger = logging.getLogger(logger_name)  # Use the provided logger_name
    logger.setLevel(logger_level)  # Use the provided logger_level

    # Check if logger already has handlers
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logger_level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger
