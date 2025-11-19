"""
네이버 뉴스 API - 실시간 뉴스 수집
https://developers.naver.com/docs/serviceapi/search/news/news.md#%EB%89%B4%EC%8A%A4



"""
from typing import Optional, Union, Any
from os import getenv
import logging
from ..modules.http import HttpClient
from .news_preprocess import NaverNewsApiResultTDict


__all__ = (
    'NaverNewsFetchService',
)


class NaverApiClient(HttpClient):
    NAVER_API_SEARCH_ENDPOINT_VAR = "https://openapi.naver.com/v1/search/{service_id}"

    def __init__(self, service: str='news') -> None:
        super().__init__(self.NAVER_API_SEARCH_ENDPOINT_VAR.format(
            service_id=f"{service}.json"
        ))

    def get(self, params: Optional[dict] = None, **kwargs) -> dict | None:
        """
        Args:
            params (dict, optional): 요청 파라미터.
            **kwargs: HttpClient.get에 전달할 추가 인자.
        """
        params = params or {}
        default_headers = {
            'X-Naver-Client-Id': getenv('NAVER_API_CLIENT_ID'),
            'X-Naver-Client-Secret': getenv('NAVER_API_CLIENT_SECRET')
        }
        user_headers = kwargs.get('headers', {})
        kwargs['headers'] = {
            **default_headers, 
            **user_headers
        }
        response = super().get(
            params=params, **kwargs
        )
        return response


class NaverNewsFetchService:
    _SERVICE_NAME = 'news'

    def __init__(self) -> None:
        self._client = NaverApiClient(service=self._SERVICE_NAME)

    def fetch_naver_news_api(
            self, 
            query: str, 
            sort: str='date', 
            display: int=100,
    ) -> Optional[list[NaverNewsApiResultTDict]]:
        """네이버 뉴스 검색

        >>> result = search_naver_news(query, sort='sim')

        :param query: 검색어
        :param sort: 정렬 방식. 'sim'은 정확도, 'date'는 날짜순.
        :param display: 받아올 표시 개수. (최대 100)
        """
        # 뉴스 검색
        if isinstance(query, str):
            q = query.encode('utf-8')
        if not sort in {'sim', 'date'}:
            raise ValueError("Invalid sort parameter. expected 'date' or 'sim'")
        if display < 0 or display > 100:
            raise ValueError("display must be lower than 100 or higher than 0.")
        res = self._client.get(
            params={
                "query": q,
                "display": display,
                "sort": sort
            }
        )
        if res:
            try:
                return res['items']
            except KeyError as e:
                logging.error(e)
        return None
