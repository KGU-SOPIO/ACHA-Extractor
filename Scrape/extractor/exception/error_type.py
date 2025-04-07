from enum import Enum

from rest_framework import status


class ErrorType(Enum):
    LMS_ERROR = (
        "LMS 오류",
        "LMS에 문제가 발생하여 요청을 처리하지 못했습니다.",
        status.HTTP_406_NOT_ACCEPTABLE,
    )
    KUTIS_ERROR = (
        "KUTIS 오류",
        "KUTIS에 문제가 발생하여 요청을 처리하지 못했습니다.",
        status.HTTP_406_NOT_ACCEPTABLE,
    )
    KUTIS_PASSWORD_ERROR = (
        "KUTIS 비밀번호 변경 필요 오류",
        "KUTIS 비밀번호 변경이 필요합니다.",
        status.HTTP_401_UNAUTHORIZED,
    )
    SCHOOL_SYSTEM_ERROR = (
        "학교 시스템 오류",
        "학교 시스템에 문제가 발생하여 요청을 처리하지 못했습니다.",
        status.HTTP_406_NOT_ACCEPTABLE,
    )
    SCRAPE_ERROR = (
        "스크래핑 오류",
        "스크래핑에 실패했습니다.",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    EXTRACT_PARAMETER_ERROR = (
        "파라미터 추출 오류",
        "링크에서 파라미터를 추출하지 못했습니다.",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    SYSTEM_ERROR = (
        "시스템 오류",
        "시스템에 문제가 발생했습니다.",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    AUTHENTICATION_FAIL = (
        "인증 실패",
        "학번 또는 비밀번호를 잘못 입력했습니다.",
        status.HTTP_400_BAD_REQUEST,
    )
    INVALID_ACCESS = (
        "잘못된 접근",
        "강좌에 접근할 수 없습니다.",
        status.HTTP_400_BAD_REQUEST,
    )
    COURSE_NOT_EXIST = (
        "강좌 미존재",
        "강좌가 존재하지 않습니다.",
        status.HTTP_400_BAD_REQUEST,
    )
    TIMETABLE_NOT_EXIST = (
        "시간표 미존재",
        "시간표가 존재하지 않습니다.",
        status.HTTP_404_NOT_FOUND,
    )

    def __init__(self, title: str, message: str, httpStatus: status):
        self.title = title
        self.message = message
        self.httpStatus = httpStatus
