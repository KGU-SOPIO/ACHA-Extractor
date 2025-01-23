import re
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import traceback

from Scrap.extractor.exception import ErrorType, ExtractorException
from Scrap.extractor.parts.utils import Utils
from Scrap.extractor.parts.constants import *

class LmsExtractor:
    def __init__(self, studentId: str, password: str):
        self.studentId: str = studentId
        self.password: str = password

        self.lmsSession: aiohttp.ClientSession | None = None


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
                return BeautifulSoup(data, 'lxml')
            
        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(type=ErrorType.SCRAPE_ERROR, args=e.args) from e


    async def _checkAccess(self, content: BeautifulSoup):
        """
        페이지 접근 여부를 검증합니다.

        Parameters:
            content: BeautifulSoup 객체
        """
        mainContainer = content.find('div', id='region-main')

        # LMS 시스템 경고
        alert = mainContainer.find('div', class_='alert')
        # 접근 제한 메세지
        notify = mainContainer.find('div', class_='panel-heading')
        if alert or notify :
            raise ExtractorException(type=ErrorType.INVALID_ACCESS)


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

        # 세션 초기화
        self.lmsSession = aiohttp.ClientSession(headers=headers)

        try:
            # LMS 로그인 요청
            async with self.lmsSession.post(LMS_LOGIN_URL, data=loginData, allow_redirects=False) as loginResponse:
                # 정상 응답 검증
                if loginResponse.status != 303:
                    raise ExtractorException(type=ErrorType.LMS_ERROR)

                # Redirect 링크 추출
                loginRedirectUrl = loginResponse.headers.get("Location", "")

                if loginRedirectUrl == LMS_LOGIN_FAILURE_URL:
                    # 인증 정보가 잘못된 경우
                    raise ExtractorException(type=ErrorType.AUTHENTICATION_FAIL)
                elif LMS_LOGIN_SUCCESS_URL in loginRedirectUrl:
                    # 로그인 상태 검증
                    async with self.lmsSession.get(LMS_MAIN_PAGE_URL, allow_redirects=False) as verifyResponse:
                        # 비정상 응답 검증
                        if verifyResponse.status == 303:
                            raise ExtractorException(type=ErrorType.LMS_ERROR)
                    return
                
                raise ExtractorException(type=ErrorType.LMS_ERROR)

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(type=ErrorType.SYSTEM_ERROR, args=e.args) from e


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
                return True, userData, "인증에 성공했습니다."
            return True, None, "인증에 성공했습니다."
        
        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(type=ErrorType.SYSTEM_ERROR, args=e.args) from e
        
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
            userData['name'] = content.find('input', id='id_firstname').get('value')
            userData['college'] = content.find('input', id='id_institution').get('value')
            
            major = content.find('input', id='id_department').get('value')
            department, major = Utils.getDepartment(major=major)
            userData['department'] = department
            userData['major'] = major
            return userData
        
        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(type=ErrorType.SCRAPE_ERROR, content=content) from e


    async def _getCourseList(self, close: bool=True) -> list:
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

            courseContainer = content.find('div', class_='course_lists')
            courses = courseContainer.find_all('li', class_='course_label_re')
            
            # 강좌 목록 확인
            if not courses:
                raise ExtractorException(type=ErrorType.COURSE_NOT_EXIST)

            courseList = [
                {
                    "name": course.find('h3').text.strip().split('(')[0].strip(),
                    "link": (courseLink := course.find('a', class_='course_link').get('href')),
                    "identifier": course.find('h3').text.strip().split('_')[1].split(')')[0][-4:],
                    "code": Utils.extractCodeFromUrl(courseLink, "id"),
                    "professor": course.find('p', class_='prof').text.strip()
                }
                for course in courses
            ]
            return courseList
        
        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(type=ErrorType.SCRAPE_ERROR, content=content, args=e.args) from e

        finally:
            if close and self.lmsSession:
                await self.lmsSession.close()
                self.lmsSession = None


    async def getCourseActivites(self, courseCode: str, close: bool=True) -> list:
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
            
            sections = content.find_all('li', id=re.compile(r'section-[1-9]\d*'))

            # 활동 목록 스크래핑 비동기 처리
            tasks = [self._getActivites(week=index, content=section) for index, section in enumerate(sections, start=1)]
            courseActivityList = await asyncio.gather(*tasks)

            return courseActivityList
        
        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(type=ErrorType.SCRAPE_ERROR, content=content, args=e.args) from e

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
            activityList = []
            tasks = []

            # 요소 추출
            activities = content.find_all('li', class_='activity')
            for activity in activities:
                # 활성 상태
                activityData = {
                    # 활동에 주차 정보 추가: 필요시 사용
                    # 'week': week,
                    'available': False if activity.find('div', class_='availability') else True
                }
                
                # 제목 스크래핑
                titleElement = activity.find('span', class_='instancename')
                if titleElement:
                    # 자식 요소 제거
                    childElement = titleElement.find('span', class_='accesshide')
                    if childElement:
                        childElement.extract()
                    activityData['name'] = titleElement.text.strip()

                # 활동 링크 및 코드 스크래핑
                linkElement = activity.find('a')
                if linkElement:
                    activityLink = linkElement.get('href')
                    activityData['link'] = activityLink
                    activityData['code'] = Utils.extractCodeFromUrl(url=activityLink, paramName="id")

                # 유형 스크래핑
                classList = activity.get('class', [])
                if len(classList) > 1:
                    activityType = LMS_ACTIVITY_TYPES.get(classList[1])
                    if not activityType:
                        continue

                    # 과제 유형 추가
                    activityData['type'] = activityType

                    # 과제 유형 비동기 작업 추가
                    if activityType == 'assignment' and activityData['available'] == 'true':
                        tasks.append((activityData['code'], activityData))
                    
                    # 강의 유형 추가 스크래핑
                    if activityType == 'lecture':
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
        
        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(type=ErrorType.SCRAPE_ERROR, content=content, args=e.args) from e


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
            # 페이지 요청 및 권한 검증
            content = await self._lmsFetch(LMS_ASSIGNMENT_PAGE_URL.format(assignmentCode))
            await self._checkAccess(content=content)
            
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
        
        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(type=ErrorType.SCRAPE_ERROR, content=content, args=e.args) from e
    
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
            # 페이지 요청 및 권한 검증
            content = await self._lmsFetch(LMS_BOARD_PAGE_URL.format(boardCode))
            await self._checkAccess(content=content)

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
                notice["professor"] = notices[index].find_all('td')[2].text.strip()
                notice["date"] = notices[index].find_all('td')[3].text.strip()

            return noticeList

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(type=ErrorType.SCRAPE_ERROR, content=content, args=e.args) from e

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
            noticeData = {
                "link": link
            }
            
            # 공지사항 첨부 파일 스크래핑
            fileContainer = content.find('ul', class_='files')
            if fileContainer:
                noticeData['files'] = [
                    {
                        'name': file.find('a').text.strip(),
                        'link': file.find('a').get('href')
                    }
                    for file in fileContainer.find_all('li')
                ]

            # 공지사항 내용 스크래핑
            contentList = []
            container = content.find('div', class_='text_to_html')

            # 줄바꿈 br 태그 변경
            for lineBreak in container.find_all('br'):
                lineBreak.replace_with('\n')

            # 텍스트 추출
            for element in container.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'], recursive=True):
                text = element.get_text()
                if text:
                    contentList.append(text)

            noticeData['content'] = '\n'.join(contentList)

            return noticeData

        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(type=ErrorType.SCRAPE_ERROR, content=content, args=e.args) from e


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
            # 페이지 요청 및 권한 검증
            content = await self._lmsFetch(LMS_ATTENDANCE_PAGE_URL.format(courseCode))
            await self._checkAccess(content=content)

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
                            'name': title,
                            'attendance': attendance
                        })
                    else:
                        if cells[0].text.strip().isdigit():
                            attendanceData.append([{
                                'name': title,
                                'attendance': attendance
                            }])
                        else:
                            attendanceData[-1].append({
                                'name': title,
                                'attendance': attendance
                            })
                elif not flat and cells[0].text.strip().isdigit():
                    attendanceData.append([])
            
            return {"courseCode": courseCode, "attendances": attendanceData} if contain else attendanceData
        
        except ExtractorException:
            raise
        except Exception as e:
            raise ExtractorException(type=ErrorType.SCRAPE_ERROR, content=content, args=e.args) from e

        finally:
            if close and self.lmsSession:
                await self.lmsSession.close()
                self.lmsSession = None