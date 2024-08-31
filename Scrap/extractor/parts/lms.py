import re
import asyncio
import aiohttp
from bs4 import BeautifulSoup

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
            
        except Exception as e:
            raise Exception(str(e))


    async def _getLmsSession(self):
        """
        lmsSession 인스턴스 변수에 LMS 인증 세션을 할당합니다.
        """
        # 세션 요청 헤더
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # 로그인 데이터
        loginData = {
            'username': self.studentId,
            'password': self.password
        }

        self.lmsSession = aiohttp.ClientSession(headers=headers)

        try:
            async with self.lmsSession.post(LMS_LOGIN_URL, data=loginData, allow_redirects=False) as loginResponse:
                if loginResponse.status != 303:
                    raise Exception("LMS Authentication Fail")

                loginRedirectUrl = loginResponse.headers.get('Location', '')

                if loginRedirectUrl == LMS_LOGIN_FAILURE_URL:
                    raise Exception("학번 또는 비밀번호를 잘못 입력했습니다.")
                elif LMS_LOGIN_SUCCESS_URL in loginRedirectUrl:
                    return
                
                raise Exception("LMS Authentication Fail")

        except Exception as e:
            await self.lmsSession.close()
            self.lmsSession = None
            raise Exception(str(e))


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
            userData['phonenumber'] = content.find('input', id='id_phone').get('value')
            userData['email'] = content.find('input', id='id_email').get('value')
            userData['college'] = content.find('input', id='id_institution').get('value')
            userData['major'] = content.find('input', id='id_department').get('value')
            userData['department'] = self._getDepartment(userData['major'])
            return userData

        except Exception as e:
            await self.lmsSession.close()
            self.lmsSession = None
            raise Exception(str(e))


    def _getDepartment(self, major: str) -> str:
        """
        전공으로 학부를 판별합니다.

        Parameters:
            major: 전공

        Returns:
            department: 학부
        """
        departmentGroup = {
            "교직학부": ["교육학전공"],
            "관광학부": ["관광경영전공", "관광개발전공", "호텔경영전공", "외식·조리전공", "관광이벤트전공"],
            "호텔외식경영학부": ["호텔경영전공", "외식·조리전공"],
            "글로벌어문학부": ["독어독문전공", "프랑스어문전공", "일어일문전공", "중어중문전공", "러시아어문전공"],
            "디자인비즈학부": ["시각정보디자인전공", "산업디자인전공", "장신구금속디자인전공", "한국화전공", "서양화전공", "미술경영전공", "서예전공"],
            "Fine Arts학부": ["한국화전공", "서양화전공", "미술경영전공", "서예전공"],
            "스포츠과학부": ["스포츠건강과학전공", "스포츠레저산업전공"],
            "공공안전학부": ["범죄교정심리학전공", "경찰행정학전공", "법학전공", "사회복지학전공", "범죄교정학전공"],
            "휴먼서비스학부": ["사회복지학전공", "청소년학전공"],
            "공공인재학부": ["행정학전공", "정치외교학전공", "국제학전공"],
            "경제학부": ["경제학전공", "무역학전공", "응용통계학전공", "지식재산학전공"],
            "경영학부": ["경영학전공", "회계세무학전공", "국제산업정보전공"],
            "회계세무·경영정보학부": ["경영정보전공"],
            "AI컴퓨터공학부": ["컴퓨터공학전공", "인공지능전공", "SW안전보안전공"],
            "ICT융합학부": ["산업시스템공학전공", "경영정보전공", "산업경영공학전공"],
            "바이오융합학부": ["생명과학전공", "식품생물공학전공"],
            "전자공학부": ["나노·반도체전공", "정보통신시스템전공",],
            "융합에너지시스템공학부": ["신소재공학전공", "환경에너지공학전공", "화학공학전공"],
            "스마트시티공학부": ["건설시스템공학전공", "건축공학전공", "도시·교통공학전공"],
            "기계시스템공학부": ["기계공학전공", "지능형로봇전공"]
        }

        for department, majors in departmentGroup.items():
            if major in majors:
                return department
        return ""


    async def _getCourseList(self) -> list:
        """
        강좌 목록을 스크래핑합니다.

        Returns:
            courseData: 강좌 목록
        """
        try:
            courseList = []

            content = await self._lmsFetch(LMS_MAIN_PAGE_URL)
            courseContainer = content.find('div', class_='course_lists')
            courses = courseContainer.find_all('li', class_='course_label_re')

            for course in courses:
                linkTag = course.find('a', class_='course_link')
                courseLink = linkTag.get('href')
                lmsCourseCode = courseLink.split('=')[1].strip()

                titleTag = course.find('h3')
                courseTitle = titleTag.text.strip()

                courseName = courseTitle.split('(')[0].strip()
                courseCode = courseTitle.split('_')[1].split(')')[0].strip()

                courseData = {
                    'courseName': courseName,
                    'courseCode': courseCode,
                    'courseLink': courseLink,
                    'lmsCourseCode': lmsCourseCode
                }
                courseList.append(courseData)
            
            return courseList
        
        except Exception as e:
            await self.lmsSession.close()
            self.lmsSession = None
            raise Exception(str(e))


    async def _getCourseActivites(self, url: str) -> list:
        """
        강좌의 주차별 활동 목록을 스크래핑합니다.

        Parameters:
            url: 강좌 url

        Returns:
            courseActivityList: 강좌 주차별 활동 목록
        """
        try:
            courseActivityList = []

            content = await self._lmsFetch(url)
            sections = content.find_all('li', id=re.compile(r'section-[1-9]\d*'))

            # 활동 목록 스크래핑 비동기 처리
            tasks = [self._getActivites(section) for section in sections]
            courseActivityList = await asyncio.gather(*tasks)

            return courseActivityList
        
        except Exception as e:
            raise Exception(str(e))


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

            # 활동 요소 추출
            activities = content.find_all('li', class_='activity')
            for activity in activities:
                activityData = {}

                # 활동 이름, 링크 스크래핑
                titleElement = activity.find('span', class_='instancename')
                if titleElement:
                    # 활동 이름 스크래핑
                    childElement = titleElement.find('span', class_='accesshide')
                    if childElement:
                        childElement.extract()
                    activityData['activityName'] = titleElement.text.strip()

                    # 활동 링크 스크래핑
                    linkElement = activity.find('a')
                    if linkElement:
                        activityData['activityLink'] = linkElement.get('href')

                # 활동 유형 스크래핑
                classList = activity.get('class', [])
                if len(classList) > 1:
                    activityType = LMS_ACTIVITY_TYPES.get(classList[1], classList[1])
                    # text 유형(텍스트) 무시
                    if activityType == 'text':
                        continue
                    else:
                        activityData['activityType'] = activityType
                    
                    # Video 유형 추가 스크래핑
                    if activityType == 'video':
                        deadlineElement = activity.find('span', class_='text-ubstrap')
                        videoTimeElement = activity.find('span', class_='text-info')
                        if deadlineElement and videoTimeElement:
                            activityData['lectureDeadline'] = deadlineElement.text.strip()
                            activityData['lectureTime'] = videoTimeElement.text.strip().replace(", ", "")
                
                # 활동 객체 추가
                activityList.append(activityData)
            
            return activityList
        
        except Exception as e:
            raise Exception(str(e))


    async def _getAssignment(self, url: str) -> dict:
        """
        과제 정보를 스크래핑합니다.

        Parameters:
            url: 과제 url
        
        Returns:
            assignmentData: 과제 정보
        """
        try:
            assignmentData = {}

            content = await self._lmsFetch(url)
            assignmentContainer = content.find('div', id='region-main')

            # 과제 제목 스크래핑
            title = assignmentContainer.find('h2').get_text(strip=True)
            assignmentData['title'] = title

            # 과제 설명 스크래핑
            descriptionContainer = assignmentContainer.find('div', id='intro')
            assignmentData['description'] = descriptionContainer.get_text(separator='\n', strip=True)
            
            # 과제 정보 스크래핑
            table = assignmentContainer.find('table', class_='generaltable').find_all('tr')
            keys = ['submitStatus', 'gradingStatus', 'deadline', 'leftTime', 'lastModified']
            for key, row in zip(keys, table[:5]):
                assignmentData[key] = row.find_all('td')[1].get_text(strip=True)

            return assignmentData
        
        except Exception as e:
            raise Exception(str(e))


    async def _getLectureAttendance(self, url: str) -> dict:
        """
        온라인 강의 출석 상태를 스크래핑합니다.

        Parameters:
            url: 온라인 출석부 url

        Returns:
            lectureData: 온라인 강의 출석 상태 정보
        """
        def extractAttendance(cell):
            return cell.text.strip() == 'O'

        try:
            attendanceData = {}

            content = await self._lmsFetch(url)
            tableContainer = content.find('table', class_='user_progress_table')
            table = tableContainer.select('tbody tr')

            for row in table:
                cells = row.find_all('td')
                # 주차 셀 확인
                if cells[0].text.strip().isdigit():
                    currentWeek = cells[0].text.strip()
                    title = cells[1].text.strip()
                    weekAttendance = extractAttendance(cells[-1])
                    attendance = extractAttendance(cells[-2])

                    if title:
                        attendanceData[currentWeek] = {}
                        attendanceData[currentWeek]['attendance'] = str(weekAttendance).lower()
                        attendanceData[currentWeek]['lectures'] = []
                        attendanceData[currentWeek]['lectures'].append({
                            'title': title,
                            'attendance': str(attendance).lower()
                        })
                # 주차 내부 셀 확인
                else:
                    title = cells[0].text.strip()
                    attendance = extractAttendance(cells[-1])
                    attendanceData[currentWeek]['lectures'].append({
                        'title': title,
                        'attendance': str(attendance).lower()
                    })
                
            return attendanceData
        
        except Exception as e:
            raise Exception(e)