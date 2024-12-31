import logging
from enum import Enum
from bs4 import BeautifulSoup

class ErrorType(Enum):
    LMS_ERROR = ("LMS 오류", "LMS에 문제가 발생하여 요청을 처리하지 못했습니다.")
    KUTIS_ERROR = ("KUTIS 오류", "KUTIS에 문제가 발생하여 요청을 처리하지 못했습니다.")
    SCRAPE_ERROR = ("스크래핑 오류", "스크래핑에 실패했습니다.")
    SYSTEM_ERROR = ("시스템 오류", "시스템에 문제가 발생했습니다.")
    AUTHENTICATION_FAIL = ("인증 실패", "학번 또는 비밀번호를 잘못 입력했습니다.")

    def __init__(self, title: str, message: str):
        self.title = title
        self.message = message

class ExtractorException(Exception):
    def __init__(self, type: ErrorType, message: str | None = None, content: BeautifulSoup | None = None, *args, **kwargs):
        self.type = type
        self.message = message or type.message
        self.content = content
        super().__init__(self.type, *args, **kwargs)

    @staticmethod
    def logError(exception: Exception):
        logger = logging.getLogger("watchmen")
        logger.error(f"{exception.message}")

    @staticmethod
    def logWarning(exception: Exception):
        logger = logging.getLogger("watchmen")
        logger.warning(f"{exception.message}")