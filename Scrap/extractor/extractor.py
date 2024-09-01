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
        try:
            content = await self._lmsFetch(course['courseLink'])

            container = content.find('div', class_='course-content')
            alert = container.find('div', class_='alert')

            if alert is None:
                noticeTask = self._getCourseNotices(content)
                activityTask = self._getCourseActivites(content)
                notices, activities = await asyncio.gather(noticeTask, activityTask)

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