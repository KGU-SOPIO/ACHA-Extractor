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
            raise


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
            raise


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
            raise


    def _getDepartment(self, major: str) -> str:
        """
        전공으로 학부를 판별합니다.

        Parameters:
            major: 전공

        Returns:
            department: 학부
        """
        departmentGroup = {
            "교직학부": {"교육학전공"},
            "관광학부": {"관광경영전공", "관광개발전공", "호텔경영전공", "외식·조리전공", "관광이벤트전공"},
            "호텔외식경영학부": {"호텔경영전공", "외식·조리전공"},
            "글로벌어문학부": {"독어독문전공", "프랑스어문전공", "일어일문전공", "중어중문전공", "러시아어문전공"},
            "디자인비즈학부": {"시각정보디자인전공", "산업디자인전공", "장신구금속디자인전공", "한국화전공", "서양화전공", "미술경영전공", "서예전공"},
            "Fine Arts학부": {"한국화전공", "서양화전공", "미술경영전공", "서예전공"},
            "스포츠과학부": {"스포츠건강과학전공", "스포츠레저산업전공"},
            "공공안전학부": {"범죄교정심리학전공", "경찰행정학전공", "법학전공", "사회복지학전공", "범죄교정학전공"},
            "휴먼서비스학부": {"사회복지학전공", "청소년학전공"},
            "공공인재학부": {"행정학전공", "정치외교학전공", "국제학전공"},
            "경제학부": {"경제학전공", "무역학전공", "응용통계학전공", "지식재산학전공"},
            "경영학부": {"경영학전공", "회계세무학전공", "국제산업정보전공"},
            "회계세무·경영정보학부": {"경영정보전공"},
            "AI컴퓨터공학부": {"컴퓨터공학전공", "인공지능전공", "SW안전보안전공"},
            "ICT융합학부": {"산업시스템공학전공", "경영정보전공", "산업경영공학전공"},
            "바이오융합학부": {"생명과학전공", "식품생물공학전공"},
            "전자공학부": {"나노·반도체전공", "정보통신시스템전공"},
            "융합에너지시스템공학부": {"신소재공학전공", "환경에너지공학전공", "화학공학전공"},
            "스마트시티공학부": {"건설시스템공학전공", "건축공학전공", "도시·교통공학전공"},
            "기계시스템공학부": {"기계공학전공", "지능형로봇전공"}
        }

        for department, majors in departmentGroup.items():
            if major in majors:
                return department
        return ""


    async def _getCourseList(self) -> list:
        """
        강좌 목록을 스크래핑합니다.

        Returns:
            courseList: 강좌 목록
        """
        try:
            content = await self._lmsFetch(LMS_MAIN_PAGE_URL)
            courseContainer = content.find('div', class_='course_lists')
            courses = courseContainer.find_all('li', class_='course_label_re')
            
            # 강좌 존재 확인
            if not courses:
                raise Exception("LMS에 강좌가 열리지 않았습니다.")

            courseList = [
                {
                    'courseName': (courseTitle := course.find('h3').text.strip()).split('(')[0].strip(),
                    'courseCode': courseTitle.split('_')[1].split(')')[0].strip(),
                    'courseLink': (courseLink := course.find('a', class_='course_link').get('href')),
                    'lmsCourseCode': courseLink.split('=')[1].strip()
                }
                for course in courses
            ]
            
            return courseList
        
        except Exception as e:
            raise


    async def _getCourseNotices(self, content: BeautifulSoup) -> list:
        """
        강좌의 공지사항을 스크래핑합니다.

        Parameters:
            content: 강좌 메인 페이지 BeautifulSoup

        Returns:
            noticeList: 공지사항 목록
        """
        try:
            # 공지사항 페이지 링크 스크래핑
            noticeUrl = content.find('li', id='section-0').find('li', class_='activity').find('a').get('href')

            content = await self._lmsFetch(noticeUrl)
            container = content.find('tbody')

            # 공지사항 존재 확인
            firstRow = container.find('td') if container else None
            if firstRow and firstRow.get('colspan') == '5':
                return []

            # 비동기 작업 생성
            tasks = [
                self._getNotice(
                    index = notice.find_all('td')[0].text.strip(),
                    title = notice.find('a').text.strip(),
                    date = notice.find_all('td')[3].text.strip(),
                    link = notice.find('a').get('href')
                )
                for notice in container.find_all('tr')
            ]
            
            # 비동기 작업 처리
            noticeList = await asyncio.gather(*tasks)
            return noticeList

        except Exception as e:
            raise


    async def _getNotice(self, index: str, title: str, date: str, link: str) -> dict:
        """
        공지사항 내용을 스크래핑하고 공지사항 객체를 반환합니다.

        Parameters:
            index: 공지사항 번호
            title: 공지사항 제목
            date: 공지사항 날짜
            link: 공지사항 링크
        
        Returns:
            noticeObject: 공지사항 객체
        """
        try:
            content = await self._lmsFetch(link)

            # 공지사항 객체 생성
            noticeObject = {
                'index': index,
                'title': title,
                'date': date,
                'link': link
            }
            
            # 공지사항 첨부 파일 스크래핑
            fileContainer = content.find('ul', class_='files')
            if fileContainer:
                noticeObject['files'] = [
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

            noticeObject['content'] = '\n'.join(contentList)

            return noticeObject

        except Exception as e:
            raise


    async def _getCourseActivites(self, content: BeautifulSoup) -> list:
        """
        강좌의 주차별 활동 목록을 스크래핑합니다.

        Parameters:
            content: 강좌 메인 페이지 BeautifulSoup

        Returns:
            courseActivityList: 강좌 주차별 활동 목록
        """
        try:           
            courseActivityList = []

            sections = content.find_all('li', id=re.compile(r'section-[1-9]\d*'))

            # 활동 목록 스크래핑 비동기 처리
            tasks = [self._getActivites(section) for section in sections]
            courseActivityList = await asyncio.gather(*tasks)

            return courseActivityList
        
        except Exception as e:
            raise


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

            # 활동 요소 추출
            activities = content.find_all('li', class_='activity')
            for activity in activities:
                activityData = {
                    'available': 'false' if activity.find('div', class_='availability') else 'true'
                }
                
                # 활동 이름 스크래핑
                titleElement = activity.find('span', class_='instancename')
                if titleElement:
                    # 자식 요소 제거
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

                    activityData['activityType'] = activityType

                    # 과제 유형 비동기 작업 추가
                    if activityType == 'assignment' and activityData['available'] == 'true':
                        tasks.append((activityData['activityLink'], activityData))
                    
                    # Video 유형 추가 스크래핑
                    if activityType == 'video':
                        deadlineElement = activity.find('span', class_='text-ubstrap')
                        videoTimeElement = activity.find('span', class_='text-info')
                        if deadlineElement and videoTimeElement:
                            activityData['lectureDeadline'] = deadlineElement.text.strip()
                            activityData['lectureTime'] = videoTimeElement.text.strip().replace(", ", "")
                
                # 활동 객체 추가
                activityList.append(activityData)
            
            # 과제 정보 스크래핑 비동기 작업 처리
            if tasks:
                results = await asyncio.gather(*[self._getAssignment(link) for link, _ in tasks])
                for assignmentData, (_, activityData) in zip(results, tasks):
                    activityData.update(assignmentData)
            
            return activityList
        
        except Exception as e:
            raise


    async def _getAssignment(self, url: str) -> dict:
        """
        과제 정보를 스크래핑합니다.

        Parameters:
            url: 과제 url
        
        Returns:
            assignmentData: 과제 정보
        """
        try:
            content = await self._lmsFetch(url)
            assignmentContainer = content.find('div', id='region-main')

            # 과제 설명 스크래핑
            description = assignmentContainer.find('div', id='intro').get_text(separator='\n', strip=True)
            
            # 과제 정보 스크래핑
            table = assignmentContainer.find('table', class_='generaltable').find_all('tr')
            keys = ['submitStatus', 'gradingStatus', 'deadline', 'leftTime', 'lastModified']
            values = [row.find_all('td')[1].get_text(strip=True) for row in table[:5]]

            # 과제 정보 객체 생성
            assignmentData = dict(zip(keys, values))
            assignmentData['description'] = description

            return assignmentData
        
        except Exception as e:
            raise


    async def _getLectureAttendance(self, lmsCourseCode: str, flat=False) -> dict:
        """
        온라인 강의 출석 상태를 스크래핑합니다.

        Parameters:
            lmsCourseCode: LMS 강의 코드

        Returns:
            lectureData: 온라인 강의 출석 상태 정보
        """
        def extractAttendance(cell):
            return cell.text.strip() == 'O'

        try:
            attendanceData = []

            content = await self._lmsFetch(LMS_ATTENDANCE_PAGE_URL.format(lmsCourseCode))
            tableContainer = content.find('table', class_='user_progress_table')
            table = tableContainer.select('tbody tr')

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
            
            return {'lmsCourseCode': lmsCourseCode, 'attendanceData': attendanceData}
        
        except Exception as e:
            raise