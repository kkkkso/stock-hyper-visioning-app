from typing import Iterable, TYPE_CHECKING, Optional, Union
from ..modules import NaverNewsWebScrapClient
if TYPE_CHECKING:
    from .news_preprocess import NaverNewsApiResultTDict, NaverNewsContentTDict
import time

class NewsScrapService:

    def sync_start_news_scrap(
            self,
            news_results: "Iterable[NaverNewsApiResultTDict]",
            drop_if_failed: bool = False,
            force_latency: float=0.8
    ) -> "list[NaverNewsContentTDict]":
        """(Sync) 뉴스 스크랩을 시작합니다. (for Test)

        Args:
            news_results (Iterable[NaverNewsApiResultTDict]): _description_
            drop_if_failed (bool, optional): 스크랩 실패하거나 본문이 인식되지 않는 경우 버립니다.  
                                            해당 기능이 비활성화된 경우 원본 데이터를 유지합니다.  
            force_latency (float): 강제 지연시간 
        """
        client = NaverNewsWebScrapClient()
        
        result = []
        for i, item in enumerate(news_results):
            scrapped = client.scrap_naver_news_content(
                item['link'],
                stop_if_abnormal_news_link=True
            )
            if drop_if_failed and not scrapped:
                continue
            result.append(
                {
                    'index': i,
                    'link': item['link'],
                    'originallink': item['originallink'],
                    'title': scrapped['title'] if scrapped else item['title'],
                    'content': scrapped['body'] if scrapped else item['description'],
                    'pubDate': item['pubDate']
                }
            )
            time.sleep(force_latency)
        return result
