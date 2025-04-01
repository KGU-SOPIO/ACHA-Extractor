import urllib
import urllib.parse

from bs4 import BeautifulSoup

from Scrape.extractor.exception import ErrorType, ExtractorException


class Utils:
    @staticmethod
    def getDepartment(major: str) -> tuple:
        """
        전공으로 학부를 판별합니다.

        1. 학부, 전공 존재
        2. 가전공으로 학부만 존재
        3. 대학 소속으로 전공만 존재

        Parameters:
            major: 전공

        Returns:
            department: 학부
            major: 전공
        """
        departmentGroup = {
            "글로벌어문학부": {
                "독어독문전공",
                "프랑스어문전공",
                "일어일문전공",
                "중어중문전공",
                "러시아어문전공",
            },
            "디자인비즈학부": {
                "시각정보디자인전공",
                "산업디자인전공",
                "장신구금속디자인전공",
            },
            "Fine Arts학부": {"한국화전공", "서양화전공", "미술경영전공", "서예전공"},
            "스포츠과학부": {"스포츠건강과학전공", "스포츠레저산업전공"},
            "공공안전학부": {"범죄교정심리학전공", "경찰행정학전공"},
            "휴먼서비스학부": {"사회복지학전공", "청소년학전공"},
            "공공인재학부": {"행정학전공", "정치외교학전공"},
            "경제학부": {"경제학전공", "응용통계학전공", "지식재산학전공"},
            "경영학부": {"경영학전공", "회계세무학전공"},
            "AI컴퓨터공학부": {
                "컴퓨터공학전공",
                "인공지능전공",
                "SW안전보안전공",
                "모빌리티SW전공",
            },
            "바이오융합학부": {"생명과학전공", "식품생물공학전공"},
            "전자공학부": {"나노·반도체전공", "정보통신시스템전공"},
            "신소재화학공학부": {"신소재공학전공", "화학공학전공"},
            "스마트시티공학부": {"건축공학전공", "도시·교통공학전공"},
            "호텔외식경영학부": {"호텔경영전공", "외식·조리전공"},
        }

        # 가전공 판별
        if major.endswith("학부"):
            return major, ""

        # 학부 판별
        for department, majors in departmentGroup.items():
            if major in majors:
                return department, major

        # 대학 소속 전공 판별
        return "", major

    @staticmethod
    def extractContent(container: BeautifulSoup) -> str:
        """
        주어진 HTML 요소에서 텍스트를 추출합니다.

        Parameters:
            container: BeautifulSoup 객체

        Returns:
            content: 추출된 텍스트
        """
        for lineBreak in container.find_all("br"):
            lineBreak.replace_with("[BR]")

        contentList = []
        elements = container.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "li"], recursive=True
        )

        if elements:
            for element in elements:
                if element.name == "li":
                    text = element.get_text(separator=" ", strip=True)
                else:
                    text = element.get_text(strip=True)
                if text:
                    contentList.append(text)
        else:
            contentList.append(container.get_text(strip=True))

        content = "\n".join(contentList)
        return content.replace("[BR]", "")

    @staticmethod
    def extractCodeFromUrl(url: str, paramName: str) -> str:
        """
        Url에서 파라미터 값을 추출합니다.
        """
        try:
            parsedUrl = urllib.parse.urlparse(url=url)
            queryParams = urllib.parse.parse_qs(parsedUrl.query)
            return queryParams.get(paramName)[0]
        except Exception as e:
            raise ExtractorException(errorType=ErrorType.EXTRACT_PARAMETER_ERROR) from e
