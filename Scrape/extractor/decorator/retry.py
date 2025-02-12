import asyncio
from functools import wraps

import aiohttp

from Scrape.extractor.exception import ErrorType, ExtractorException


def retryOnTimeout(
    maxRetries: int = 3, initialDelay: float = 1.0, backoffFactor: float = 2.0
):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initialDelay
            lastException = None
            for attempt in range(maxRetries):
                try:
                    return await func(*args, **kwargs)
                except ExtractorException as e:
                    lastException = e
                    cause = e.__cause__
                    if (
                        attempt < maxRetries - 1
                        and cause
                        and (
                            isinstance(
                                cause, (asyncio.TimeoutError, aiohttp.ClientTimeout)
                            )
                            or (hasattr(cause, "status") and 500 <= cause.status < 600)
                        )
                    ):
                        await asyncio.sleep(delay)
                        delay *= backoffFactor
                        continue
                    raise
            raise ExtractorException(
                errorType=ErrorType.SCHOOL_SYSTEM_ERROR
            ) from lastException

        return wrapper

    return decorator
