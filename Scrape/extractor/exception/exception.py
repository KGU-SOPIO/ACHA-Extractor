import logging

from bs4 import BeautifulSoup

from Scrape.extractor.exception import ErrorType

EXCEPT_ERROR_TYPES = (
    ErrorType.AUTHENTICATION_FAIL,
    ErrorType.INVALID_ACCESS,
    ErrorType.COURSE_NOT_EXIST,
    ErrorType.TIMETABLE_NOT_EXIST,
    ErrorType.KUTIS_PASSWORD_ERROR,
)


class ExtractorException(Exception):
    def __init__(
        self,
        errorType: ErrorType,
        message: str | None = None,
        content: BeautifulSoup | None = None,
        data: str | None = None,
        *args
    ):
        self.type = errorType
        self.message = message or errorType.message
        self.content = content or None
        self.data = data or None
        super().__init__(self.message, *args)

    def logError(self):
        if self.type in EXCEPT_ERROR_TYPES:
            return
        logger = logging.getLogger("watchmen")
        logger.error(
            self.message,
            extra={
                "type": self.type.title,
                "content": (
                    self.content.prettify() if self.content is not None else None
                ),
                "data": self.data,
            },
            exc_info=True,
        )

    def logWarning(self):
        if self.type in EXCEPT_ERROR_TYPES:
            return
        logger = logging.getLogger("watchmen")
        logger.warning(
            self.message,
            extra={
                "type": self.type.title,
                "content": (
                    self.content.prettify() if self.content is not None else None
                ),
                "data": self.data,
            },
            exc_info=True,
        )
