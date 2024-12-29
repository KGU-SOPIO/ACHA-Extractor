import re
import asyncio
import aiohttp
from bs4 import BeautifulSoup

from Scrap.extractor.parts.utils import Utils
from Scrap.extractor.parts.constants import *

class LmsExtractor:
    def __init__(self, studentId: str, password: str):
        self.studentId: str = studentId
        self.password: str = password

        self.lmsSession: aiohttp.ClientSession | None = None


    async def _lmsFetch(self, url: str) -> BeautifulSoup:
        """
        GET 요청을 보내고, 응답을 BeautifulSoup로 변환하여 반환합니다.

        인증 세션이 없다면 생성을 시도합니다.

        Parameters:
            url (str): 요청 Url
        
        Returns:
            response (str): 응답 데이터
        """
        try:
            if self.lmsSession is None:
                await self._getLmsSession()
            
            async with self.lmsSession.get(url) as response:
                data = await response.text()
                return BeautifulSoup(data, 'lxml')
            
        except Exception:
            raise

 
    async def _getLmsSession(self):
        """
        lmsSession 인스턴스 변수에 LMS 인증 세션을 할당합니다.
        """
        # 세션 요청 헤더
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }

        # 로그인 데이터
        loginData = {
            "username": self.studentId,
            "password": self.password
        }

        self.lmsSession = aiohttp.ClientSession(headers=headers)

        try:
            async with self.lmsSession.post(LMS_LOGIN_URL, data=loginData, allow_redirects=False) as loginResponse:
                if loginResponse.status != 303:
                    raise Exception("LMS 인증에 실패했습니다.")

                loginRedirectUrl = loginResponse.headers.get("Location", "")

                if loginRedirectUrl == LMS_LOGIN_FAILURE_URL:
                    raise Exception("학번 또는 비밀번호를 잘못 입력했습니다.")
                elif LMS_LOGIN_SUCCESS_URL in loginRedirectUrl:
                    async with self.lmsSession.get(LMS_MAIN_PAGE_URL, allow_redirects=False) as verifyResponse:
                        if verifyResponse.status == 303:
                            raise Exception("로그인에 실패했습니다.")
                    return
                
                raise Exception("LMS 인증에 실패했습니다.")

        except Exception:
            raise


    async def verifyAuthentication(self):
        """
        학교 시스템 인증을 확인합니다.

        Returns:
            verification: 인증 여부
        """
        try:
            await self._getLmsSession()
            return "true"
        except Exception:
            return "false"


    async def getUserData(self) -> dict:
        """
        사용자 정보를 스크래핑합니다.

        Returns:
            userData: 사용자 정보
        """
        try:
            content = await self._lmsFetch(LMS_USER_PAGE_URL)

            userData = {}
            userData['name'] = content.find('input', id='id_firstname').get('value')
            userData['college'] = content.find('input', id='id_institution').get('value')
            userData['major'] = content.find('input', id='id_department').get('value')
            userData['department'] = Utils.getDepartment(userData['major'])
            return userData

        except Exception:
            raise


    async def _getCourseList(self, close: bool=True) -> list:
        """
        강좌 목록을 스크래핑합니다.

        Returns:
            courseList: 강좌 목록
        """
        try:
            content = await self._lmsFetch(LMS_MAIN_PAGE_URL)
            courseContainer = content.find('div', class_='course_lists')
            courses = courseContainer.find_all('li', class_='course_label_re')
            
            # 강좌 목록 확인
            if not courses:
                raise Exception("강좌가 존재하지 않습니다.")

            courseList = [
                {
                    "courseName": course.find('h3').text.strip().split('(')[0].strip(),
                    "courseLink": (courseLink := course.find('a', class_='course_link').get('href')),
                    "courseCode": courseLink.split('=')[1].strip(),
                    "professor": course.find('p', class_='prof').text.strip()
                }
                for course in courses
            ]
            return courseList
        
        except Exception:
            raise

        finally:
            if close and self.lmsSession:
                await self.lmsSession.close()
                self.lmsSession = None


    async def getCourseActivites(self, courseCode: str, close: bool=True) -> list:
        """
        강좌의 주차별 활동 목록을 스크래핑합니다.

        Parameters:
            courseCode: 강좌 코드

        Returns:
            courseActivityList: 강좌 주차별 활동 목록
        """
        try:
            content = await self._lmsFetch(LMS_COURSE_PAGE_URL.format(courseCode))
            sections = content.find_all('li', id=re.compile(r'section-[1-9]\d*'))

            # 활동 목록 스크래핑 비동기 처리
            tasks = [self._getActivites(content=section) for section in sections]
            courseActivityList = await asyncio.gather(*tasks)

            return courseActivityList
        
        except Exception:
            raise

        finally:
            if close and self.lmsSession:
                await self.lmsSession.close()
                self.lmsSession = None


    async def _getActivites(self, content: BeautifulSoup) -> list:
        """
        해당 주차의 활동들을 스크래핑합니다.

        Parameters:
            content: 주차별 BeautifulSoup
        
        Returns:
            activityList: 주차별 활동 목록
        """
        try:
            activityList = []
            tasks = []

            # 요소 추출
            activities = content.find_all('li', class_='activity')
            for activity in activities:
                # 활성 상태
                activityData = {
                    'available': 'false' if activity.find('div', class_='availability') else 'true'
                }
                
                # 제목 스크래핑
                titleElement = activity.find('span', class_='instancename')
                if titleElement:
                    # 자식 요소 제거
                    childElement = titleElement.find('span', class_='accesshide')
                    if childElement:
                        childElement.extract()
                    activityData['activityName'] = titleElement.text.strip()

                # 코드 스크래핑
                linkElement = activity.find('a')
                if linkElement:
                    activityLink = linkElement.get('href')
                    activityData['activityLink'] = activityLink
                    activityData['activityCode'] = Utils.extractCodeFromUrl(url=activityLink, paramName="id")

                # 유형 스크래핑
                classList = activity.get('class', [])
                if len(classList) > 1:
                    activityType = LMS_ACTIVITY_TYPES.get(classList[1], classList[1])

                    # text 유형(텍스트) 무시
                    if activityType == 'text':
                        continue

                    activityData['activityType'] = activityType

                    # 과제 유형 비동기 작업 추가
                    if activityType == 'assignment' and activityData['available'] == 'true':
                        tasks.append((activityData['activityCode'], activityData))
                    
                    # Video 유형 추가 스크래핑
                    if activityType == 'video':
                        deadlineElement = activity.find('span', class_='text-ubstrap')
                        videoTimeElement = activity.find('span', class_='text-info')
                        if deadlineElement and videoTimeElement:
                            activityData['lectureDeadline'] = deadlineElement.text.strip()
                            activityData['lectureTime'] = videoTimeElement.text.strip().replace(", ", "")
                
                # 객체 추가
                activityList.append(activityData)
            
            # 과제 정보 스크래핑 비동기 작업 처리
            if tasks:
                results = await asyncio.gather(*[self.getCourseAssignment(assignmentCode=code, close=False) for code, _ in tasks])
                for assignmentData, (_, activityData) in zip(results, tasks):
                    activityData.update(assignmentData)
            
            return activityList
        
        except Exception:
            raise


    async def getCourseAssignment(self, assignmentCode: str, close: bool=True) -> dict:
        """
        과제 정보를 스크래핑합니다.

        Parameters:
            assignmentCode: 과제 코드
            close: 세션 종료 여부
        
        Returns:
            assignmentData: 과제 정보
        """
        try:
            content = await self._lmsFetch(LMS_ASSIGNMENT_PAGE_URL.format(assignmentCode))
            assignmentContainer = content.find('div', id='region-main')

            # 과제 설명 스크래핑
            description = assignmentContainer.find('div', id='intro').get_text(separator='\n', strip=True)
            
            # 과제 정보 스크래핑
            table = assignmentContainer.find('table', class_='generaltable').find_all('tr')
            keys = ["gradingStatus", "deadline", "timeLeft", "lastModified"]
            values = [row.find_all('td')[1].get_text(strip=True) for row in table[1:5]]

            # 과제 정보 객체 생성
            assignmentData = dict(zip(keys, values))
            assignmentData['description'] = description

            # 과제 제출 상태 추가
            timeLeft = assignmentData.get("timeLeft")
            submitStatus = {
                "빨랐습니다": "done",
                "늦었습니다": "late",
                "마감이 지난": "miss"
            }
            assignmentData["submitStatus"] = next((status for keyword, status in submitStatus.items() if keyword in timeLeft), "none")

            return assignmentData
        
        except Exception:
            raise
    
        finally:
            if close and self.lmsSession:
                await self.lmsSession.close()
                self.lmsSession = None


    async def getCourseNotice(self, boardCode: str, close: bool=True) -> list:
        """
        강좌 공지사항을 스크래핑합니다.

        Parameters:
            boardCode: 공지사항 게시판 코드
            close: 세션 종료 여부

        Returns:
            noticeList: 전체 공지사항 정보
        """
        try:
            content = await self._lmsFetch(LMS_BOARD_PAGE_URL.format(boardCode))
            container = content.find('tbody')

            # 공지사항 목록 확인
            firstRow = container.find('td') if container else None
            if firstRow and firstRow.get('colspan') == '5':
                return []
            
            # 공지사항 목록 추출
            notices = container.find_all('tr')

            # 비동기 작업 생성
            tasks = [
                self._getNotice(link=notice.find('a').get('href'))
                for notice in notices
            ]
            
            # 비동기 작업 처리
            noticeList = await asyncio.gather(*tasks)

            # 추가 정보 삽입
            for index, notice in enumerate(noticeList):
                notice["index"] = notices[index].find_all('td')[0].text.strip() or "중요"
                notice["title"] = notices[index].find('a').text.strip()
                notice["date"] = notices[index].find_all('td')[3].text.strip()

            return noticeList

        except Exception:
            raise

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
            content = await self._lmsFetch(link)

            # 공지사항 객체 생성
            noticeData = {
                "link": link
            }
            
            # 공지사항 첨부 파일 스크래핑
            fileContainer = content.find('ul', class_='files')
            if fileContainer:
                noticeData['files'] = [
                    {
                        'fileName': file.find('a').text.strip(),
                        'fileLink': file.find('a').get('href')
                    }
                    for file in fileContainer.find_all('li')
                ]

            # 공지사항 내용 스크래핑
            contentList = []
            container = content.find('div', class_='text_to_html')
            for element in container.children:
                if element.name is None:
                    contentList.append(element.strip())
                elif element.name == 'p':
                    contentList.append(element.get_text(strip=True))
                elif element.name is not None:
                    allowedAttrs = {'src', 'href'}
                    element.attrs = {key: value for key, value in element.attrs.items() if key in allowedAttrs}
                    contentList.append(str(element))

            noticeData['content'] = '\n'.join(contentList)

            return noticeData

        except Exception:
            raise


    async def getLectureAttendance(self, courseCode: str, contain: bool=False, flat: bool=False, close: bool=True) -> dict:
        """
        온라인 강의 출석 상태를 스크래핑합니다.

        Parameters:
            courseCode: 강의 코드
            contain: 강의 코드 포함 여부
            flat: 주차별 데이터 그룹화
            close: 세션 종료 여부

        Returns:
            attendanceData: 온라인 강의 출석 상태 정보
        """
        def extractAttendance(cell):
            return cell.text.strip() == "O"

        try:
            content = await self._lmsFetch(LMS_ATTENDANCE_PAGE_URL.format(courseCode))
            tableContainer = content.find('table', class_='user_progress_table')
            table = tableContainer.select('tbody tr')

            attendanceData = []

            for row in table:
                cells = row.find_all('td')
                title = cells[1].text.strip() if cells[0].text.strip().isdigit() else cells[0].text.strip()
                attendance = extractAttendance(cells[-2] if cells[0].text.strip().isdigit() else cells[-1])

                if title:
                    if flat:
                        attendanceData.append({
                            'title': title,
                            'attendance': attendance
                        })
                    else:
                        if cells[0].text.strip().isdigit():
                            attendanceData.append([{
                                'title': title,
                                'attendance': attendance
                            }])
                        else:
                            attendanceData[-1].append({
                                'title': title,
                                'attendance': attendance
                            })
                elif not flat and cells[0].text.strip().isdigit():
                    attendanceData.append([])
            
            return {"courseCode": courseCode, "attendances": attendanceData} if contain else attendanceData

        except Exception:
            raise

        finally:
            if close and self.lmsSession:
                await self.lmsSession.close()
                self.lmsSession = None