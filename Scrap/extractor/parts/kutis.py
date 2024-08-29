import aiohttp
from bs4 import BeautifulSoup

class KutisExtractor:
    def __init__(self, studentId: str, password: str):
        self.studentId: str = studentId
        self.password: str = password

        self.kutisSession: aiohttp.ClientSession | None = None

        self.kutisLoginUrl: str = "https://kutis.kyonggi.ac.kr/webkutis/view/hs/wslogin/loginCheck.jsp"
        self.kutisMainUrl: str = "https://kutis.kyonggi.ac.kr/webkutis/view/main/mypage.jsp?flag=2"
        self.kutisTimetableUrl: str = "https://kutis.kyonggi.ac.kr/webkutis/view/hs/wssu3/wssu330s.jsp?m_menu=wsco1s05&s_menu=wssu330s"


    async def getKutisSession(self):
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
            async with self.kutisSession.post(self.kutisLoginUrl, data=loginData, allow_redirects=False) as loginResponse:
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
            raise str(e)


    async def fetch(self, url):
        """
        GET 요청을 보내고, 응답을 문자열로 변환하여 반환합니다.

        인증 세션이 없다면 얻기를 시도합니다.

        Parameters:
            url (str): 요청 Url
        
        Returns:
            response (str): 응답 데이터
        """
        try:
            if self.kutisSession == None:
                await self.getKutisSession()
            async with self.kutisSession.get(url) as response:
                return await response.text()
        except Exception as e:
            raise str(e)


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

            data = await self.fetch(self.kutisTimetableUrl)
            content = BeautifulSoup(data, 'lxml')
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
            raise str(e)