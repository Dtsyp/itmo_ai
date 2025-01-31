import sys

from aiologger import Logger
from aiologger.formatters.base import Formatter
from aiologger.handlers.files import AsyncFileHandler
from aiologger.handlers.streams import AsyncStreamHandler
from aiologger.levels import LogLevel


async def setup_logger():
    logger = Logger(name="api_logger")

    formatter = Formatter(
        fmt="{asctime} | {levelname} | {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
    )

    file_handler = AsyncFileHandler(
        filename="logs/api.log",
        mode="a",
        encoding="utf-8",
    )
    stream_handler = AsyncStreamHandler(stream=sys.stdout)
    file_handler.formatter = formatter
    stream_handler.formatter = formatter
    logger.add_handler(file_handler)
    logger.add_handler(stream_handler)

    logger.level = LogLevel.INFO

    return logger
