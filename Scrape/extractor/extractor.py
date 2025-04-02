import asyncio

from Scrape.extractor.exception import ErrorType, ExtractorException
from Scrape.extractor.parts import KutisExtractor, LmsExtractor, Utils


class Extractor(KutisExtractor, LmsExtractor):
    """
    LMS, KUTIS 스크래핑을 처리하는 클래스입니다.
    """

    def __init__(self, studentId: str, password: str):
        KutisExtractor.__init__(self, studentId=studentId, password=password)
        LmsExtractor.__init__(self, studentId=studentId, password=password)

    async def getCourses(
        self, year: int | None, semester: int | None, extract: bool
    ) -> list:
        """
        모든 강좌의 데이터를 스크래핑합니다.

        Parameters:
            year: 추출 연도
            semester: 추출 학기
            extract: 개별 강좌 데이터 추출 여부

        Returns:
            courseList: 모든 강좌 데이터
        """
        try:
            # 과거 또는 현재 강좌 목록 요청
            if year and semester:
                courseList = await self._getPastCourseList(
                    year=year, semester=semester, close=False
                )
            else:
                courseList = await self._getCourseList(close=False)

            if extract:
                tasks = [self._getCourseData(course) for course in courseList]
                courseList = await asyncio.gather(*tasks)
            return courseList

        except ExtractorException:
            # 스크래핑 문제 예외 처리
            raise

        except Exception as e:
            # 시스템 예외 처리
            raise ExtractorException(errorType=ErrorType.SYSTEM_ERROR) from e

        finally:
            if self.lmsSession:
                await self.lmsSession.close()
                self.lmsSession = None

    async def _getCourseData(self, course: dict) -> dict:
        """
        해당 강좌의 데이터를 스크래핑합니다.

        Parameters:
            course: 강좌 정보

        Returns:
            course: 스크래핑 데이터 추가된 강좌 정보
        """
        try:
            # 페이지 요청
            content = await self._lmsFetch(course["link"])

            # 접근 권한 검증
            container = content.find("div", class_="course-content")
            alert = container.find("div", class_="alert")
            if alert:
                return course

            # 공지사항 URL 및 게시판 코드 추출
            noticeUrl = (
                content.find("li", id="section-0")
                .find("li", class_="activity")
                .find("a")
                .get("href")
            )
            noticeBoardCode = Utils.extractCodeFromUrl(url=noticeUrl, paramName="id")

            # 공지사항, 활동, 출석 비동기 작업 생성 및 실행
            noticeTask = self.getCourseNotice(boardCode=noticeBoardCode, close=False)
            activityTask = self.getCourseActivites(
                courseCode=course["code"], close=False
            )
            attendanceTask = self.getLectureAttendance(
                courseCode=course["code"], close=False
            )
            noticeData, activityData, attendanceData = await asyncio.gather(
                noticeTask, activityTask, attendanceTask
            )

            # 추출된 데이터 병합
            if attendanceData is not None:
                # 출석 데이터 튜플 map 생성
                attendanceMap = {}
                for weekAttendances in attendanceData:
                    week = weekAttendances["week"]
                    for lecture in weekAttendances["attendances"]:
                        title = lecture["title"]
                        attendance = lecture["attendance"]
                        attendanceMap[(week, title)] = attendance

                # 활동 데이터에 출석 정보 추가
                for weekActivities in activityData:
                    week = weekActivities["week"]
                    for activity in weekActivities["activities"]:
                        if activity.get("type") == "lecture":
                            key = (week, activity["title"])
                            if key in attendanceMap:
                                activity["attendance"] = attendanceMap[key]
                            else:
                                raise ExtractorException(
                                    errorType=ErrorType.SCRAPE_ERROR,
                                    message="강의 정보와 출석 정보가 일치하지 않습니다.",
                                    data=f"[Activity] - {activityData}\n[Attendance] - {attendanceData}",
                                )

            # 추출된 데이터 추가
            course.update(
                {
                    "noticeCode": noticeBoardCode,
                    "notices": noticeData,
                    "activities": activityData,
                }
            )

            return course

        except ExtractorException:
            # 스크래핑 문제 예외 처리
            raise

        except Exception as e:
            # 시스템 예외 처리
            raise ExtractorException(errorType=ErrorType.SCRAPE_ERROR) from e
