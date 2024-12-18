import logging
from logging.handlers import RotatingFileHandler

class Logger:
    def __init__(self, name: str, func_name: str):
        self.name = name
        self.func_name = func_name

    def get_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s ")

        if not logger.hasHandlers():
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

            file_handler = logging.FileHandler("app.log")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            rotating_file_handler = RotatingFileHandler("app_rotating.log", maxBytes=5 * 1024 * 1024, backupCount=3)
            rotating_file_handler.setLevel(logging.ERROR)
            rotating_file_handler.setFormatter(formatter)
            logger.addHandler(rotating_file_handler)

        return logger