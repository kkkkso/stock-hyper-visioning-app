"""뉴스 링크를 통해 뉴스 데이터를 웹 스크랩한다."""

from bs4 import BeautifulSoup
import logging
from typing import TypedDict, Optional
import requests

__all__ = (
    'NaverNewsWebScrapClient',
    'NewsWebScrapResultTDict'
)

class NewsWebScrapResultTDict(TypedDict):
    title: str
    body: str


class NaverNewsWebScrapClient:

    @staticmethod
    def filter_naver_news(url: str):
        """정상적인 네이버 뉴스 링크인지 확인"""
        prefixes = [
            "https://n.news.naver.com",
            "https://sports.news.naver.com"
        ]
        return any(url.startswith(p) for p in prefixes)

    def scrap_naver_news_content(
            self,
            url: str, 
            stop_if_abnormal_news_link: bool=False
    ) -> Optional[NewsWebScrapResultTDict]:
        """
        주어진 네이버 뉴스 URL에서 제목과 본문 내용을 스크랩합니다.
        일반 뉴스, 연예, 스포츠 뉴스 등 다양한 섹션의 구조를 처리합니다.

        Args:
            url (str): 스크랩할 네이버 뉴스 기사의 URL
            stop_if_abnormal_news_link (bool): 예상되지 않은 뉴스 링크는 수집하지 않습니다.  
                                            ``filter_naver_news()`` 함수를 사용합니다.

        Returns:
            ``NewsWebScrapResultTDict`` dict[str, str]
        """
        if stop_if_abnormal_news_link:
            if not self.filter_naver_news(url):
                logging.warning(f"예상되지 않은 뉴스 링크: {url}")
                return None

        headers = {
            # 일부 언론사는 헤더를 검사하므로 일반적인 브라우저 헤더를 추가합니다.
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            return None
        
        logging.info(f"Scrapping url: {url}")

        soup = BeautifulSoup(response.text, 'html.parser')
        try:
            title = ""
            content = None
            # 1. 기사 제목 찾기 (일반, 연예, 스포츠 공통 시도)
            title_tag = soup.select_one('h2#title_area span, h4.title, h2.end_tit')
            if title_tag:
                title = title_tag.get_text(strip=True)
            # 2. 기사 본문 찾기 (여러 선택자를 순서대로 시도)
            #   - 일반 뉴스: #dic_area
            #   - 연예 뉴스: #articeBody
            #   - 스포츠 뉴스: #newsEndContents
            content_selectors = ['#dic_area', '#articeBody', '#newsEndContents']
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    break
            if not content:
                raise Exception(f"Cannot find body text on url: {url}")
            
            # 3. 본문 내용에서 불필요한 요소 제거 (광고, 기자 정보 등)
            #    - decompose() 메서드는 해당 태그를 파싱 트리에서 완전히 제거합니다.
            unnecessary_tags = [
                'script', 'style', 'div.byline', 'div.reporter_area', 
                'span.end_photo_org', 'p.source', 'div.highlight-editor',
                'div.ad_body_2020x150'
            ]
            for tag_selector in unnecessary_tags:
                for tag in content.select(tag_selector):
                    tag.decompose()
            # 4. 텍스트 추출 및 정리
            #    - get_text()를 사용하여 텍스트만 추출합니다.
            #    - separator='\n' : 태그와 태그 사이를 줄바꿈으로 연결합니다.
            #    - strip=True : 텍스트 앞뒤의 공백을 제거합니다.
            body_text = content.get_text(separator='\n', strip=True)
        except Exception as e:
            logging.error(e)
            return None
        return {
            'title': title, 
            'body': body_text
        }

