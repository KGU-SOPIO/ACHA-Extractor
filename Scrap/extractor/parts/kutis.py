import aiohttp
from bs4 import BeautifulSoup

from Scrap.extractor.parts.constants import *

class KutisExtractor:
    def __init__(self, studentId: str, password: str):
        self.studentId: str = studentId
        self.password: str = password

        self.kutisSession: aiohttp.ClientSession | None = None


    async def _kutisFetch(self, url: str) -> BeautifulSoup:
        """
        GET 요청을 보내고, 응답을 BeautifulSoup로로 변환하여 반환합니다.

        인증 세션이 없다면 예외를 발생시킵니다.
            - 비동기 요청 시 발생하는 문제 예방

        Parameters:
            url (str): 요청 Url
        
        Returns:
            response (str): 응답 데이터
        """
        try:
            if self.kutisSession == None:
                raise Exception("인증 세션이 생성되지 않았습니다.")

            async with self.kutisSession.get(url) as response:
                data = await response.text()
                return BeautifulSoup(data, 'lxml')
        except Exception as e:
            raise str(e)


    async def _getKutisSession(self):
        """
        kutisSession 인스턴스 변수에 Kutis 인증 세션을 할당합니다.
        """
        # 세션 요청 헤더
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # 로그인 데이터
        loginData = {
            'id': self.studentId,
            'pw': self.password
        }

        self.kutisSession = aiohttp.ClientSession(headers=headers)

        try:
            async with self.kutisSession.post(KUTIS_LOGIN_URL, data=loginData, allow_redirects=False) as loginResponse:
                if loginResponse.status != 302:
                    raise Exception("KUTIS Authentication Fail")
                
                loginRedirectUrl = loginResponse.headers.get('Location')
                if not loginRedirectUrl:
                    raise Exception("KUTIS Authentication Fail")
            
            async with self.kutisSession.get(loginRedirectUrl, allow_redirects=False) as ssoResponse:
                if ssoResponse.status != 302:
                    raise Exception("KUTIS Authentication Fail")
            return
            
        except Exception as e:
            await self.kutisSession.close()
            self.kutisSession = None
            raise Exception(str(e))


    async def getTimetable(self):
        """
        Kutis에서 시간표를 스크래핑합니다.

        ! rowspan으로 인한 비정확한 요일 수집 가능성 문제 해결 필요
            -> 1 ~ 3교시(오전), 4 ~ 5교시, 6 ~ 7교시(오후) 시간대 외 수업 시간이 존재하는지 확인 필요
                : 존재하지 않으면 해결 필요 없음
        """
        try:
            classes = []
            days = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일']
            period = 0

            content = await self._kutisFetch(KUTIS_TIMETABLE_PAGE_URL)
            tables = content.find_all('table', class_='list06')
            timetable = tables[1]

            rows = timetable.find_all('tr')
            for rowIndex in range(1, len(rows), 2):
                period += 1
                
                columns = rows[rowIndex].find_all(['th', 'td'])
                for colIndex, col in enumerate(columns):
                    if col.name == 'th':
                        classTime = int(col.get('rowspan')) // 2
                        courseName, courseCode, professor, classroom = col.get_text(separator="<br>", strip=True).split("<br>")
                        classes.append({
                            'courseName': courseName,
                            'courseCode': courseCode,
                            'professor': professor,
                            'classroom': classroom,
                            'day': days[colIndex-1],
                            'classTime': classTime,
                            'startAt': period,
                            'endAt': period + classTime - 1
                        })

        except Exception as e:
            await self.kutisSession.close()
            self.kutisSession = None
            raise Exception(str(e))