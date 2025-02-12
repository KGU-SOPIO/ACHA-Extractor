import aiohttp
from bs4 import BeautifulSoup

from Scrape.extractor.exception import ErrorType, ExtractorException
from Scrape.extractor.parts.constants import *


class KutisExtractor:
    def __init__(self, studentId: str, password: str):
        self.studentId: str = studentId
        self.password: str = password

        self.kutisSession: aiohttp.ClientSession | None = None

    async def _kutisPostFetch(self, url: str, data: dict[str, int]) -> BeautifulSoup:
        """
        POST 요청을 보내고, 응답을 BeautifulSoup 객체로 변환하여 반환합니다.

        인증 세션이 없다면 생성을 시도합니다.

        Parameters:
            url: 요청 Url

        Returns:
            content: BeautifulSoup 객체
        """
        try:
            # 세션 검증 및 생성
            if self.kutisSession is None:
                await self._getKutisSession()

            # 페이지 요청 및 변환 후 반환
            async with self.kutisSession.post(url, data=data) as response:
                response.raise_for_status()
                data = await response.text()
                return BeautifulSoup(data, "lxml")

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(errorType=ErrorType.SCRAPE_ERROR) from e

    async def _kutisFetch(self, url: str) -> BeautifulSoup:
        """
        GET 요청을 보내고, 응답을 BeautifulSoup 객체로 변환하여 반환합니다.

        인증 세션이 없다면 생성을 시도합니다.

        Parameters:
            url: 요청 Url

        Returns:
            content: BeautifulSoup 객체
        """
        try:
            # 세션 검증 및 생성
            if self.kutisSession is None:
                await self._getKutisSession()

            # 페이지 요청 및 변환 후 반환
            async with self.kutisSession.get(url) as response:
                response.raise_for_status()
                data = await response.text()
                return BeautifulSoup(data, "lxml")

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(errorType=ErrorType.SCRAPE_ERROR) from e

    async def _getKutisSession(self):
        """
        kutisSession 인스턴스 변수에 KUTIS 인증 세션을 할당합니다.
        """
        # 세션 요청 헤더
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }

        # 로그인 데이터
        loginData = {"id": self.studentId, "pw": self.password}

        # 세션 초기화
        self.kutisSession = aiohttp.ClientSession(headers=headers)

        try:
            # KUTIS 로그인 페이지 GET 요청
            async with self.kutisSession.get(
                KUTIS_LOGIN_PAGE_URL, allow_redirects=False
            ) as formResponse:
                if formResponse.status != 200:
                    raise ExtractorException(errorType=ErrorType.KUTIS_ERROR)

            # KUTIS 로그인 POST 요청
            async with self.kutisSession.post(
                KUTIS_LOGIN_URL, data=loginData, allow_redirects=False
            ) as loginResponse:
                if loginResponse.status != 302:
                    raise ExtractorException(errorType=ErrorType.AUTHENTICATION_FAIL)

                loginRedirectUrl = loginResponse.headers.get("Location")
                if not loginRedirectUrl:
                    raise ExtractorException(errorType=ErrorType.KUTIS_ERROR)

            # SSO GET 요청
            async with self.kutisSession.get(
                loginRedirectUrl, allow_redirects=False
            ) as ssoResponse:
                if ssoResponse.status != 302:
                    raise ExtractorException(errorType=ErrorType.KUTIS_ERROR)

                ssoRedirectUrl = ssoResponse.headers.get("Location")
                if not ssoRedirectUrl:
                    raise ExtractorException(errorType=ErrorType.KUTIS_ERROR)

            # SSO Redirect URL GET 요청
            async with self.kutisSession.get(
                ssoRedirectUrl, allow_redirects=True
            ) as verifyResponse:
                if verifyResponse.status != 200:
                    raise ExtractorException(errorType=ErrorType.KUTIS_ERROR)

            # 로그인 상태 검증
            async with self.kutisSession.get(
                KUTIS_MAIN_PAGE_URL, allow_redirects=True
            ) as mainPageResponse:
                if mainPageResponse.status != 200:
                    raise ExtractorException(errorType=ErrorType.KUTIS_ERROR)
            return

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(errorType=ErrorType.SYSTEM_ERROR) from e

    async def getTimetable(
        self, year: int | None, semester: int | None, close: bool = True
    ) -> list:
        """
        KUTIS에서 시간표를 스크래핑합니다.

        ! rowspan으로 인한 비정확한 요일 수집 가능성, 문제 해결 필요
            -> 1 ~ 3교시(오전), 4 ~ 5교시, 6 ~ 7교시(오후) 시간대 외 수업 시간이 존재하는지 확인 필요
                : 존재하지 않으면 해결 필요 없음

        Parameters:
            close: 세션 종료 여부

        Returns:
            classes: 시간표 정보
        """
        try:
            # 과거 또는 현재 시간표 페이지 요청
            if year and semester:
                content = await self._kutisPostFetch(
                    KUTIS_TIMETABLE_PAGE_URL,
                    data={"hyear": year, "hakgi": semester * 10},
                )
            else:
                content = await self._kutisFetch(KUTIS_TIMETABLE_PAGE_URL)

            tables = content.find_all("table", class_="list06")
            timetable = tables[1]

            # 시간표 존재 여부 검증
            if timetable.find("p", class_="caution"):
                raise ExtractorException(errorType=ErrorType.TIMETABLE_NOT_EXIST)

            classes = []
            days = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일"]
            period = 0

            rows = timetable.find_all("tr")
            for rowIndex in range(1, len(rows), 2):
                period += 1

                columns = rows[rowIndex].find_all(["th", "td"])
                for colIndex, col in enumerate(columns):
                    if col.name == "th":
                        classTime = int(col.get("rowspan")) // 2
                        title, identifier, professor, lectureRoom = col.get_text(
                            separator="<br>", strip=True
                        ).split("<br>")
                        classes.append(
                            {
                                "title": title,
                                "identifier": identifier,
                                "professor": professor,
                                "lectureRoom": lectureRoom,
                                "day": days[colIndex - 1],
                                "classTime": classTime,
                                "startAt": period,
                                "endAt": period + classTime - 1,
                            }
                        )

            return classes

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(
                errorType=ErrorType.SCRAPE_ERROR, content=content
            ) from e

        finally:
            if close and self.kutisSession:
                await self.kutisSession.close()
                self.kutisSession = None
