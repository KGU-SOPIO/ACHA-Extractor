import asyncio

from Scrap.extractor.parts.kutis import KutisExtractor
from Scrap.extractor.parts.lms import LmsExtractor
from Scrap.extractor.parts.utils import Utils

class Extractor(KutisExtractor, LmsExtractor, Utils):
    """
    LMS, KUTIS 스크래핑을 처리하는 클래스입니다.
    """
    def __init__(self, studentId, password):
        KutisExtractor.__init__(self , studentId, password)
        LmsExtractor.__init__(self, studentId, password)


    async def getCourses(self, detail: bool=True):
        try:
            courseList = await self._getCourseList(close=False)
            if detail:
                tasks = [self._getCourseData(course) for course in courseList]
                courseList = await asyncio.gather(*tasks)
            return courseList

        except Exception:
            raise
        
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
            content = await self._lmsFetch(course['courseLink'])
            
            container = content.find('div', class_='course-content')
            alert = container.find('div', class_='alert')

            if alert is not None:
                return course
            
            noticeUrl = content.find('li', id='section-0').find('li', class_='activity').find('a').get('href')           
            noticeBoardCode = Utils.extractCodeFromUrl(url=noticeUrl, paramName="id")

            noticeTask = self.getCourseNotice(boardCode=noticeBoardCode, close=False)
            activityTask = self.getCourseActivites(courseCode=course['courseCode'], close=False)
            attendanceTask = self.getLectureAttendance(courseCode=course['courseCode'], contain=True, flat=True, close=False)
            notices, activities, attendances = await asyncio.gather(noticeTask, activityTask, attendanceTask)

            if attendances['courseCode'] == course['courseCode']:
                attendanceMap = {lecture['title']: lecture['attendance'] for lecture in attendances['attendances']}
                for weekActivities in activities:
                    for activity in weekActivities:
                        if activity.get('activityType') == 'video':
                            try:
                                if activity['available'] == "true":
                                    activity['attendance'] = attendanceMap[activity['activityName']]
                            except KeyError:
                                raise Exception("강의 정보와 출석 정보가 일치하지 않습니다.")

            course.update({
                'notices': notices,
                'activities': activities
            })

            return course
            
        except Exception:
            raise