from typing import Tuple
from asyncio import sleep

from logger import AppLogger


def retry(exceptions: Tuple, logger: AppLogger, attempts: int = 3, wait_sec: int = 1):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            exc = None
            for attempt in range(1, attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as error:
                    logger.exception('Call http query error', func=func.__name__, attempt=attempt, retriable=True)
                    await sleep(wait_sec)
                    exc = error
                except Exception:
                    logger.exception('Call http query error', func=func.__name__, attempt=attempt, retriable=False)
                    raise
            raise exc

        return wrapper

    return decorator
