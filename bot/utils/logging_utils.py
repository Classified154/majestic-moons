import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

FORMATTER = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
LOG_DIR = Path("./logs")

if not Path.exists(LOG_DIR):
    Path.mkdir(LOG_DIR)

COLOR_DICT = {
    "GREEN": 0x46FA76,
    "RED": 0xFC3A4E,
    "YELLOW": 0xFCF765,
}


def get_console_handler() -> logging.StreamHandler:
    """Return a console handler."""
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter())
    return console_handler


def ensure_dir(directory: Path) -> None:
    """Ensure the directory exists."""
    if not Path.exists(directory):
        Path.mkdir(directory)


def get_file_handler(logger_name: str) -> logging.FileHandler:
    """Return a file handler."""
    log_folder = Path.joinpath(LOG_DIR, logger_name)
    ensure_dir(log_folder)
    log_file = Path.joinpath(log_folder, f"{logger_name}.log")
    file_handler = TimedRotatingFileHandler(log_file, when="W0", utc=True, encoding="utf-8")
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(logger_name: str) -> logging.Logger:
    """Return a logger."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler(logger_name))
    # with this pattern, it's rarely necessary to propagate the error up to parent

    if not logger.handlers:
        print(f"No handlers found for logger: {logger_name}")
    else:
        print(f"Handlers for logger {logger_name}: {logger.handlers}")

    logger.propagate = False
    return logger


LOGGER = get_logger("main")


def log(user_id: int, log_type: str, text: str, level: str = "INFO", logger: logging.Logger = LOGGER) -> None:
    """Log a message."""
    text = str(user_id) + " | " + log_type + " | " + text

    if level == "INFO":
        logger.info(text)

    elif level == "WARN":
        logger.warning(text)

    elif level == "ERROR":
        logger.error(text)

    else:
        logger.debug(text)
