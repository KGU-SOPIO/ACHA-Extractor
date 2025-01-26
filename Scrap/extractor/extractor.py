import asyncio

from Scrap.extractor.parts import KutisExtractor, LmsExtractor, Utils
from Scrap.extractor.exception import ErrorType, ExtractorException

class Extractor(KutisExtractor, LmsExtractor):
    """
    LMS, KUTIS 스크래핑을 처리하는 클래스입니다.
    """
    def __init__(self, studentId: str, password: str):
        KutisExtractor.__init__(self , studentId=studentId, password=password)
        LmsExtractor.__init__(self, studentId=studentId, password=password)


    async def getCourses(self, year: int | None, semester: int | None, extract: bool) -> list:
        try:
            if (year and semester):
                courseList = await self._getPastCourseList(year=year, semester=semester, close=False)
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
            raise ExtractorException(type=ErrorType.SYSTEM_ERROR, args=e.args) from e
        
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
            content = await self._lmsFetch(course['link'])
            
            # 접근 권한 검증
            container = content.find('div', class_='course-content')
            alert = container.find('div', class_='alert')
            if alert:
                return course
            
            # 공지사항 URL 및 게시판 코드 추출
            noticeUrl = content.find('li', id='section-0').find('li', class_='activity').find('a').get('href')           
            noticeBoardCode = Utils.extractCodeFromUrl(url=noticeUrl, paramName="id")

            # 공지사항, 활동, 출석 비동기 작업 생성 및 실행
            noticeTask = self.getCourseNotice(boardCode=noticeBoardCode, close=False)
            activityTask = self.getCourseActivites(courseCode=course['code'], close=False)
            attendanceTask = self.getLectureAttendance(courseCode=course['code'], contain=True, flat=True, close=False)
            notices, activities, attendances = await asyncio.gather(noticeTask, activityTask, attendanceTask)

            # 추출된 데이터 병합
            if attendances is not None and attendances['code'] == course['code']:
                attendanceMap = {lecture['title']: lecture['attendance'] for lecture in attendances['attendances']}
                for weekActivities in activities:
                    for activity in weekActivities:
                        if activity.get('type') == 'lecture':
                            try:
                                if activity['available'] == True:
                                    activity['attendance'] = attendanceMap[activity['title']]
                            except KeyError:
                                raise ExtractorException(type=ErrorType.SCRAPE_ERROR, message="강의 정보와 출석 정보가 일치하지 않습니다.", args=e.args)

            # 추출된 데이터 추가
            course.update({
                'noticeCode': noticeBoardCode,
                'notices': notices,
                'activities': activities
            })

            return course
        
        except ExtractorException:
            # 스크래핑 문제 예외 처리
            raise
        
        except Exception as e:
            # 시스템 예외 처리
            raise ExtractorException(type=ErrorType.SYSTEM_ERROR, args=e.args) from e