from dotenv import load_dotenv
load_dotenv()

from typing import Union
from .modules import *
from .service import *

import logging

try:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s]     [%(asctime)s] [%(name)s] %(message)s",
    )
except Exception as e:
    print(e)


class NewsDataPipelineAPI:
    """뉴스 데이터를 전처리하고 집계/가공할 수 있는 기능을 제공하는 API 클래스.

    >>> api = NewsDataPipelineAPI()
    >>> results = api.fetch_news_from_naver_api('삼성전자')
      
    >>> api.select_top_k_by_date(results)
    
    """
    def __init__(self) -> None:
        pass

    def fetch_news_from_naver_api(
        self,
        query: str,
        sort: str='sim',
        display: int=100,
        web_scrap_content: bool=False,
        preprocess: bool=True,
    ) -> Optional[
            Union[
                list[NaverNewsApiResultTDict],
                list[NaverNewsContentTDict]
            ]
        ]:
        """네이버 API로 부터 뉴스 데이터를 Fetch하고, 옵션에 따라 `전처리` 후 Return한다.

        **전처리 내용:**  
            1. 불필요 HTML 태그, 이스케이프 문자 등
        
        :param query: (str) 검색 문자열
        :param sort: 정렬 방식. 'sim'은 정확도, 'date'는 날짜순.
        :param display: 받아올 표시 개수. (최대 100)
        :param web_scrap_content: (bool) 뉴스 링크를 타고 본문 스크랩 여부. (기본값: False)
        :param preprocess: (bool) 문자열 전처리 여부. 
        """

        fetch_service = NaverNewsFetchService()
        result = fetch_service.fetch_naver_news_api(query, sort, display)

        if web_scrap_content and result:
            scrapper = NewsScrapService()
            result = scrapper.sync_start_news_scrap(result)

        preprocessor = NaverNewsDataProcessorService()
        if preprocess and result:
            preprocessor.clean_news_items(result)
        return result if result else []

    def select_top_k_by_date(
        self,
        data: list[Union[NaverNewsApiResultTDict,
                         NaverNewsContentTDict]],
        k: int,
        sort: TSort
    ):
        """해당 데이터를 날짜 순으로 정렬하되, 상위 k개를 반환시킵니다.
        
        :param data: (str) 뉴스 데이터 리스트

        """
        service = NaverNewsDataProcessorService()
        return service.select_top_k_by_date_from(
            data, k, sort=sort
        )

