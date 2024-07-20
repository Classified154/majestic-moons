import logging
import os
from logging.handlers import TimedRotatingFileHandler


FORMATTER = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
LOG_DIR = "./logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

COLOR_DICT = {
  "GREEN": 0x46fa76,
  "RED": 0xfc3a4e,
  "YELLOW": 0xfcf765
}


class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def get_console_handler():
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(CustomFormatter())
    return console_handler


def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_file_handler(logger_name):
    log_folder = os.path.join(LOG_DIR, logger_name)
    ensure_dir(log_folder)
    log_file = os.path.join(log_folder, f"{logger_name}.log")
    file_handler = TimedRotatingFileHandler(log_file, when='W0', utc=True, encoding="utf-8")
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(logger_name):
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


def log(user_id, log_type, text, level="INFO", logger=LOGGER):
    text = str(user_id) + " | " + log_type + " | " + text

    if level == "INFO":
        logger.info(text)

    elif level == "WARN":
        logger.warning(text)

    elif level == "ERROR":
        logger.error(text)

    else:
        logger.debug(text)
