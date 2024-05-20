import logging


def configure_logger(log_level=logging.INFO, log_file=None):
    """
    Configure the logger for the application.

    Args:
        log_level (int, optional): The log level to set for the logger.
        Defaults to logging.INFO.
        log_file (str, optional): The path to the log file. If provided,
        logs will be written to this file.
            If not provided, logs will be written to the console.

    Returns:
        logging.Logger: The configured logger instance.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
