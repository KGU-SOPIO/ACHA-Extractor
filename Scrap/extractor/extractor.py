import time

import asyncio
import aiohttp

from Scrap.extractor.parts.kutis import KutisExtractor
from Scrap.extractor.parts.lms import LmsExtractor

class Extractor(KutisExtractor, LmsExtractor):
    """
    LMS, KUTIS 스크래핑을 처리하는 클래스입니다.
    """
    def __init__(self, studentId, password):
        KutisExtractor.__init__(self , studentId, password)
        LmsExtractor.__init__(self, studentId, password)


    async def _getCourseDetail(self, course: dict) -> dict:
        """
        해당 강좌의 데이터를 스크래핑합니다.

        Parameters:
            course: 강좌 기본 정보
        
        Returns:
            course: 스크래핑 데이터 추가된 강좌 정보
        """
        try:
            content = await self._lmsFetch(course['courseLink'])

            container = content.find('div', class_='course-content')
            alert = container.find('div', class_='alert')

            if alert is not None:
                return course

            noticeTask = self._getCourseNotices(content)
            activityTask = self._getCourseActivites(content)
            attendanceTask = self._getLectureAttendance(course['lmsCourseCode'], flat=True)
            notices, activities, attendances = await asyncio.gather(noticeTask, activityTask, attendanceTask)

            if attendances['lmsCourseCode'] == course['lmsCourseCode']:
                attendanceMap = {lecture['title']: lecture['attendance'] for lecture in attendances['attendanceData']}
                for weekActivities in activities:
                    for activity in weekActivities:
                        if activity.get('activityType') == 'video':
                            try:
                                activity['attendance'] = attendanceMap[activity['activityName']]
                            except KeyError:
                                raise Exception("강의 정보와 출석 정보가 일치하지 않습니다.")

            course.update({
                'notices': notices,
                'activities': activities
            })

            return course
            
        except Exception as e:
            raise


    async def extractCourse(self):
        try:
            courseList = await self._getCourseList()
            tasks = [self._getCourseDetail(course) for course in courseList]
            courseDetails = await asyncio.gather(*tasks)

            return courseDetails

        except Exception as e:
            raise Exception("Extract Failure")
        
        finally:
            if self.lmsSession:
                await self.lmsSession.close()