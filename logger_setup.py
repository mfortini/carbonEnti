import logging
import os

def setup_logger(name):
    """
    Configures a logger with a standard format and file handler.
    
    Args:
        name (str): Name of the logger.

    Returns:
        logging.Logger: Configured logger.
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)  # Ensure log directory exists

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set global logging level (DEBUG, INFO, WARNING, etc.)

    # Formatter for logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # File Handler
    file_handler = logging.FileHandler(f"{log_dir}/{name}.log")
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(formatter)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Show INFO+ messages on console
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
