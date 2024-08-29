import aiohttp
from bs4 import BeautifulSoup

class LmsExtractor:
    def __init__(self, studentId: str, password: str):
        self.studentId: str = studentId
        self.password: str = password

        self.lmsSession: aiohttp.ClientSession | None = None

        self.lmsLoginUrl: str = "https://lms.kyonggi.ac.kr/login/index.php"
        self.lmsLoginSuccessUrl: str = "https://lms.kyonggi.ac.kr/login/index.php?testsession="
        self.lmsLoginFailUrl: str = "https://lms.kyonggi.ac.kr/login.php?errorcode=3"
        self.lmsUserPageUrl: str = "https://lms.kyonggi.ac.kr/user/user_edit.php"


    async def getLmsSession(self):
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
            async with self.lmsSession.post(self.lmsLoginUrl, data=loginData, allow_redirects=False) as loginResponse:
                if loginResponse.status != 303:
                    raise Exception("LMS Authentication Fail")

                loginRedirectUrl = loginResponse.headers.get('Location', '')

                if loginRedirectUrl == self.lmsLoginFailUrl:
                    raise Exception("학번 또는 비밀번호를 잘못 입력했습니다.")
                elif self.lmsLoginSuccessUrl in loginRedirectUrl:
                    return
                
                raise Exception("LMS Authentication Fail")

        except Exception as e:
            await self.lmsSession.close()
            self.lmsSession = None
            raise str(e)