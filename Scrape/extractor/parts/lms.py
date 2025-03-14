import asyncio
import re

import aiohttp
from bs4 import BeautifulSoup

from Scrape.extractor.decorator import retryOnTimeout
from Scrape.extractor.exception import ErrorType, ExtractorException
from Scrape.extractor.parts.constants import *
from Scrape.extractor.parts.utils import Utils


class LmsExtractor:
    def __init__(self, studentId: str, password: str):
        self.studentId: str = studentId
        self.password: str = password

        self.lmsSession: aiohttp.ClientSession | None = None

    @retryOnTimeout()
    async def _lmsFetch(self, url: str) -> BeautifulSoup:
        """
        GET 요청을 보내고, 응답을 BeautifulSoup 객체로 변환하여 반환합니다.

        인증 세션이 없다면 생성을 시도합니다.

        Parameters:
            url: 요청 url

        Returns:
            content: BeautifulSoup 객체
        """
        try:
            # 세션 검증 및 생성
            if self.lmsSession is None:
                await self._getLmsSession()

            # 페이지 요청 및 변환 후 반환
            async with self.lmsSession.get(url) as response:
                data = await response.text()
                return BeautifulSoup(data, "lxml")

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(errorType=ErrorType.SCRAPE_ERROR) from e

    async def _checkAccess(
        self, content: BeautifulSoup, exception: bool = True
    ) -> bool | Exception:
        """
        페이지 접근 여부를 검증합니다.

        Parameters:
            content: BeautifulSoup 객체
            exception: 예외 발생 여부
        """
        mainContainer = content.find("div", id="region-main")

        # LMS 시스템 경고
        alert = mainContainer.find("div", class_="alert")
        # 접근 제한 메세지
        notify = mainContainer.find("div", class_="panel-heading")
        if alert or notify:
            if exception:
                raise ExtractorException(errorType=ErrorType.INVALID_ACCESS)
            else:
                return False

    @retryOnTimeout()
    async def _getLmsSession(self):
        """
        lmsSession 인스턴스 변수에 LMS 인증 세션을 할당합니다.
        """
        # 세션 요청 헤더
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }

        # 로그인 데이터
        loginData = {"username": self.studentId, "password": self.password}

        # 타임아웃 설정
        timeout = aiohttp.ClientTimeout(total=10)

        # 세션 초기화
        self.lmsSession = aiohttp.ClientSession(headers=headers, timeout=timeout)

        try:
            # LMS 로그인 요청
            async with self.lmsSession.post(
                LMS_LOGIN_URL, data=loginData, allow_redirects=False
            ) as loginResponse:
                # 정상 응답 검증
                if loginResponse.status != 303:
                    raise ExtractorException(errorType=ErrorType.LMS_ERROR)

                # Redirect 링크 추출
                loginRedirectUrl = loginResponse.headers.get("Location", "")

                if loginRedirectUrl == LMS_LOGIN_FAILURE_URL:
                    # 인증 정보가 잘못된 경우
                    raise ExtractorException(errorType=ErrorType.AUTHENTICATION_FAIL)
                elif LMS_LOGIN_SUCCESS_URL in loginRedirectUrl:
                    # 로그인 상태 검증
                    async with self.lmsSession.get(
                        LMS_MAIN_PAGE_URL, allow_redirects=False
                    ) as verifyResponse:
                        # 비정상 응답 검증
                        if verifyResponse.status == 303:
                            raise ExtractorException(errorType=ErrorType.LMS_ERROR)
                    return

                raise ExtractorException(errorType=ErrorType.LMS_ERROR)

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(errorType=ErrorType.SYSTEM_ERROR) from e

    async def verifyAuthentication(self, getUser: bool) -> tuple:
        """
        학교 시스템에 로그인하여 인증 정보를 확인하고, 사용자 정보를 스크래핑합니다.

        Parameters:
            getUser: 사용자 정보 추출 여부

        Returns:
            verification: 인증 여부
            userData: 사용자 정보
            message: 인증 메세지
        """
        try:
            # 인증 세션 생성
            await self._getLmsSession()

            # 사용자 정보 추출
            if getUser:
                userData = await self._getUserData()
                return True, userData, "인증에 성공했어요"
            return True, None, "인증에 성공했어요"

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(errorType=ErrorType.SYSTEM_ERROR) from e

        finally:
            if self.lmsSession:
                await self.lmsSession.close()
                self.lmsSession = None

    async def _getUserData(self) -> dict:
        """
        사용자 정보를 스크래핑합니다.

        Returns:
            userData: 사용자 정보
        """
        try:
            content = await self._lmsFetch(LMS_USER_PAGE_URL)

            userData = {}
            userData["name"] = content.find("input", id="id_firstname").get("value")
            userData["college"] = content.find("input", id="id_institution").get(
                "value"
            )

            # 전공, 학부 판별
            major = content.find("input", id="id_department").get("value")
            department, major = Utils.getDepartment(major=major)
            userData["department"] = department
            userData["major"] = major
            return userData

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(
                errorType=ErrorType.SCRAPE_ERROR, content=content
            ) from e

    async def _getPastCourseList(
        self, year: int, semester: int, close: bool = True
    ) -> list:
        """
        과거 강좌 목록을 스크래핑합니다.

        Parameters:
            year: 연도
            semester: 학기
            close: 세션 종료 여부

        Returns:
            courseList: 강좌 목록
        """
        try:
            # 페이지 요청
            content = await self._lmsFetch(
                LMS_PAST_COURSE_PAGE_URL.format(year, semester * 10)
            )

            courseContainer = content.find("div", class_="course_lists")
            courseTable = courseContainer.find("tbody", class_="my-course-lists")
            courses = courseTable.find_all("tr")

            # 강좌 목록 확인
            if not courses or courses[0].find("td", colspan="5"):
                raise ExtractorException(errorType=ErrorType.COURSE_NOT_EXIST)

            courseList = []
            for course in courses:
                columns = course.find_all("td")
                courseTag = columns[1].find("a")
                courseList.append(
                    {
                        "title": courseTag.text.strip().split("(")[0].strip(),
                        "link": courseTag.get("href"),
                        "identifier": courseTag.text.strip()
                        .split("_")[1]
                        .split(")")[0][-4:],
                        "code": Utils.extractCodeFromUrl(courseTag.get("href"), "id"),
                        "professor": columns[2].text.strip(),
                    }
                )
            return courseList

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(
                errorType=ErrorType.SCRAPE_ERROR, content=content
            ) from e

        finally:
            if close and self.lmsSession:
                await self.lmsSession.close()
                self.lmsSession = None

    async def _getCourseList(self, close: bool = True) -> list:
        """
        강좌 목록을 스크래핑합니다.

        Parameters:
            close: 세션 종료 여부

        Returns:
            courseList: 강좌 목록
        """
        try:
            # 페이지 요청 및 권한 검증
            content = await self._lmsFetch(LMS_MAIN_PAGE_URL)
            await self._checkAccess(content=content)

            courseContainer = content.find("div", class_="course_lists")
            courses = courseContainer.find_all("li", class_="course_label_re")

            # 강좌 목록 확인
            if not courses:
                raise ExtractorException(errorType=ErrorType.COURSE_NOT_EXIST)

            courseList = [
                {
                    "title": course.find("h3").text.strip().split("(")[0].strip(),
                    "link": (
                        courseLink := course.find("a", class_="course_link").get("href")
                    ),
                    "identifier": course.find("h3")
                    .text.strip()
                    .split("_")[1]
                    .split(")")[0][-4:],
                    "code": Utils.extractCodeFromUrl(courseLink, "id"),
                    "professor": course.find("p", class_="prof").text.strip(),
                }
                for course in courses
            ]
            return courseList

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(
                errorType=ErrorType.SCRAPE_ERROR, content=content
            ) from e

        finally:
            if close and self.lmsSession:
                await self.lmsSession.close()
                self.lmsSession = None

    async def getCourseActivites(self, courseCode: str, close: bool = True) -> list:
        """
        강좌의 주차별 활동 목록을 스크래핑합니다.

        Parameters:
            courseCode: 강좌 코드
            close: 세션 종료 여부

        Returns:
            courseActivityList: 강좌 주차별 활동 목록
        """
        try:
            # 페이지 요청 및 권한 검증
            content = await self._lmsFetch(LMS_COURSE_PAGE_URL.format(courseCode))
            await self._checkAccess(content=content)

            sectionContainer = content.find("div", class_="total_sections")
            sections = sectionContainer.find_all(
                "li", id=re.compile(r"section-[1-9]\d*")
            )

            # 활동 목록 스크래핑 비동기 처리
            tasks = [
                self._getActivites(week=index, content=section)
                for index, section in enumerate(sections, start=1)
            ]
            courseActivityList = await asyncio.gather(*tasks)

            # 활동 존재 검증 및 필터링
            return [activity for activity in courseActivityList if activity is not None]

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(
                errorType=ErrorType.SCRAPE_ERROR, content=content
            ) from e

        finally:
            if close and self.lmsSession:
                await self.lmsSession.close()
                self.lmsSession = None

    async def _getActivites(self, week: int, content: BeautifulSoup) -> list:
        """
        해당 주차의 활동들을 스크래핑합니다.

        Parameters:
            content: BeautifulSoup 객체

        Returns:
            activityList: 주차별 활동 목록
        """
        try:
            weekActivities = {"week": week}
            activityList = []
            tasks = []

            # 요소 추출
            activities = content.find_all("li", class_="activity")
            for activity in activities:
                # 활동 존재 여부 필터링
                classList = activity.get("class", [])
                if len(classList) < 1:
                    continue

                # 활동 유형 필터링
                activityType = LMS_ACTIVITY_TYPES.get(classList[1])
                if not activityType:
                    continue

                # 활성 상태
                activityData = {
                    "available": (
                        False if activity.find("div", class_="availability") else True
                    ),
                    "type": activityType,
                }

                # 제목 스크래핑
                titleElement = activity.find("span", class_="instancename")
                if titleElement:
                    # 자식 요소 제거
                    childElement = titleElement.find("span", class_="accesshide")
                    if childElement:
                        childElement.extract()
                    activityData["title"] = titleElement.text.strip()

                # 활동 링크 및 코드 스크래핑
                linkElement = activity.find("a")
                if linkElement:
                    activityLink = linkElement.get("href")
                    activityData["link"] = activityLink
                    activityData["code"] = Utils.extractCodeFromUrl(
                        url=activityLink, paramName="id"
                    )

                # 과제 유형 비동기 작업 추가
                if activityType == "assignment" and activityData["available"] == True:
                    tasks.append((activityData["code"], activityData))

                # 강의 유형 추가 스크래핑
                if activityType == "lecture":
                    deadlineElement = activity.find("span", class_="text-ubstrap")
                    lectureTimeElement = activity.find("span", class_="text-info")
                    if deadlineElement and lectureTimeElement:
                        startAt, deadline = map(
                            str.strip, deadlineElement.text.split("~")
                        )
                        activityData.update(
                            {
                                "startAt": startAt,
                                "deadline": deadline,
                                "lectureTime": lectureTimeElement.text.strip().replace(
                                    ", ", ""
                                ),
                            }
                        )

                # 객체 추가
                activityList.append(activityData)

            # 과제 정보 스크래핑 비동기 작업 처리
            if tasks:
                results = await asyncio.gather(
                    *[
                        self.getCourseAssignment(assignmentCode=code, close=False)
                        for code, _ in tasks
                    ]
                )
                for assignmentData, (_, activityData) in zip(results, tasks):
                    activityData.update(assignmentData)

            # 활동 목록 검증
            if not activityList:
                return None

            weekActivities["activities"] = activityList
            return weekActivities

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(
                errorType=ErrorType.SCRAPE_ERROR, content=content
            ) from e

    async def getCourseAssignment(
        self, assignmentCode: str, close: bool = True
    ) -> dict:
        """
        과제 정보를 스크래핑합니다.

        Parameters:
            assignmentCode: 과제 코드
            close: 세션 종료 여부

        Returns:
            assignmentData: 과제 정보
        """
        try:
            # 페이지 요청 및 권한 검증
            content = await self._lmsFetch(
                LMS_ASSIGNMENT_PAGE_URL.format(assignmentCode)
            )
            await self._checkAccess(content=content)

            assignmentContainer = content.find("div", id="region-main")

            # 과제 설명 스크래핑
            descriptionContainer = assignmentContainer.find("div", id="intro")
            description = Utils.extractContent(container=descriptionContainer)

            # 과제 정보 스크래핑
            table = assignmentContainer.find("table", class_="generaltable").find_all(
                "tr"
            )

            # 팀 필드 존재 검증
            rows = (
                table[2:6]
                if table[0].find_all("td")[0].get_text(strip=True) == "팀"
                else table[1:5]
            )

            keys = ["gradingStatus", "deadline", "timeLeft", "lastModified"]
            values = [row.find_all("td")[1].get_text(strip=True) for row in rows]

            # 과제 정보 객체 생성
            assignmentData = dict(zip(keys, values))
            assignmentData["description"] = description

            # 과제 제출 상태 추가
            timeLeft = assignmentData.get("timeLeft")
            submitStatus = {
                "빨랐습니다": "done",
                "늦었습니다": "late",
                "마감이 지난": "miss",
            }
            assignmentData["submitStatus"] = next(
                (
                    status
                    for keyword, status in submitStatus.items()
                    if keyword in timeLeft
                ),
                "none",
            )

            return assignmentData

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(
                errorType=ErrorType.SCRAPE_ERROR, content=content
            ) from e

        finally:
            if close and self.lmsSession:
                await self.lmsSession.close()
                self.lmsSession = None

    async def getCourseNotice(self, boardCode: str, close: bool = True) -> list:
        """
        강좌 공지사항을 스크래핑합니다.

        Parameters:
            boardCode: 공지사항 게시판 코드
            close: 세션 종료 여부

        Returns:
            noticeList: 전체 공지사항 정보
        """
        try:
            # 페이지 요청 및 권한 검증
            content = await self._lmsFetch(LMS_BOARD_PAGE_URL.format(boardCode))
            await self._checkAccess(content=content)

            container = content.find("tbody")

            # 공지사항 목록 확인
            firstRow = container.find("td") if container else None
            if firstRow and firstRow.get("colspan") == "5":
                return []

            # 공지사항 목록 추출
            notices = container.find_all("tr")

            # 비동기 작업 생성
            tasks = [
                self._getNotice(link=notice.find("a").get("href")) for notice in notices
            ]

            # 비동기 작업 처리
            noticeList = await asyncio.gather(*tasks)

            # 추가 정보 삽입
            for index, notice in enumerate(noticeList):
                notice["index"] = (
                    notices[index].find_all("td")[0].text.strip() or "9999"
                )
                notice["title"] = notices[index].find("a").text.strip()
                notice["professor"] = notices[index].find_all("td")[2].text.strip()
                notice["date"] = notices[index].find_all("td")[3].text.strip()

            return noticeList

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(
                errorType=ErrorType.SCRAPE_ERROR, content=content
            ) from e

        finally:
            if close and self.lmsSession:
                await self.lmsSession.close()
                self.lmsSession = None

    async def _getNotice(self, link: str) -> dict:
        """
        공지사항 내용을 스크래핑하고 공지사항 객체를 반환합니다.

        Parameters:
            link: 공지사항 링크

        Returns:
            noticeData: 공지사항 정보
        """
        try:
            # 페이지 요청 및 권한 검증
            content = await self._lmsFetch(link)
            await self._checkAccess(content=content)

            # 공지사항 객체 생성
            noticeData = {"link": link}

            # 파일 추출
            fileContainer = content.find("ul", class_="files")
            if fileContainer:
                noticeData["files"] = [
                    {
                        "name": file.find("a").text.strip(),
                        "link": file.find("a").get("href"),
                    }
                    for file in fileContainer.find_all("li")
                ]

            # 공지사항 텍스트 추출
            container = content.find("div", class_="text_to_html")
            noticeData["content"] = Utils.extractContent(container=container)

            return noticeData

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(
                errorType=ErrorType.SCRAPE_ERROR, content=content
            ) from e

    async def getLectureAttendance(self, courseCode: str, close: bool = True) -> list:
        """
        온라인 강의 출석 상태를 스크래핑합니다.

        Parameters:
            courseCode: 강좌 코드
            close: 세션 종료 여부

        Returns:
            attendanceData: 온라인 강의 출석 상태 정보
        """

        def extractAttendance(cell):
            return cell.text.strip() == "O"

        try:
            # 페이지 요청 및 권한 검증
            content = await self._lmsFetch(LMS_ATTENDANCE_PAGE_URL.format(courseCode))
            if await self._checkAccess(content=content, exception=False) is False:
                return None

            table = content.select("table.user_progress_table tbody tr")

            attendanceData = []
            for row in table:
                cells = row.find_all("td")
                week = (
                    int(cells[0].text.strip())
                    if cells[0].text.strip().isdigit()
                    else None
                )
                title = cells[1].text.strip() if week else cells[0].text.strip()
                attendance = extractAttendance(cells[-2] if week else cells[-1])

                if title:
                    if week:
                        attendanceData.append(
                            {
                                "week": week,
                                "attendances": [
                                    {"title": title, "attendance": attendance}
                                ],
                            }
                        )
                    else:
                        attendanceData[-1]["attendances"].append(
                            {"title": title, "attendance": attendance}
                        )

            return attendanceData

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(
                errorType=ErrorType.SCRAPE_ERROR, content=content
            ) from e

        finally:
            if close and self.lmsSession:
                await self.lmsSession.close()
                self.lmsSession = None
