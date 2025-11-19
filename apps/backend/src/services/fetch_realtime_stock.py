"""실시간 주식 데이터를 Redis에 접속하여 캐시합니다.
"""
import json
import pprint
from typing import Optional
from antic_extensions import RedisService
from .schema_enums import (
    REDIS_STOCK_CURRENT_PRICE,
)
from ..settings import api_settings
import logging

__all__ = (
    'RealtimeStockInfoCacheService',
    'RedisService'
)

class RealtimeStockInfoCacheService:
    """실시간 주식 데이터를 Redis로 부터 캐시한다. 
    """
    def __init__(self, redis_service: Optional[RedisService]=None) -> None:
        """실시간 주식 데이터를 Redis로 부터 캐시하는 헬퍼 클래스를 생성.  

        >>> service = RealtimeStockInfoCacheService()
            data = service.cache_stock_realtime_data("505050")
            ...

        Args:
            redis_service (RedisService, optional): redis_service 입력할 경우 해당 REDIS 연결 풀을 이용합니다. 
                                        `None`으로 미기입시 자동으로 내부적으로 새로운 연결 풀을 생성합니다. 
                                        이때 ``settings.api_settings``의 설정 값에 따라 자동으로 생성합니다. 
                                        (`REDIS_HOST`, `REDIS_PORT`... 등)   
        """
        if api_settings.REDIS_PASSWORD is None:
            raise EnvironmentError("REDIS_PASSWORD is not provided.")
        self._rservice = redis_service
        if not self._rservice:
            self._rservice = RedisService(
                api_settings.REDIS_HOST, 
                api_settings.REDIS_PORT,
                api_settings.REDIS_PASSWORD,
                api_settings.REDIS_DATABASE
            )

    @property
    def redis_client(self):
        if not self._rservice:
            raise RuntimeError("Redis client is not provided!")
        return self._rservice
    
    def cache_current_top_10_stock(self):
        """현재 TOP10 주식 데이터를 Redis로 부터 가져옵니다.  

        """
        ...
        
    def cache_stock_realtime_data(self, stock_unique_id: str):
        """특정 주식 종목에 대한 현재 실시간 주식 데이터를 Redis로 부터 받아옵니다.
        
        :param stock_unique_id: (str) 주식 종목 코드 입력.  

        """
        FILTER_TARGETS = (
            "hts_kor_isnm", "stck_shrn_iscd", "rprs_mrkt_kor_name",
            "bstp_kor_isnm", "stck_prpr", "prdy_vrss_sign",
            "prdy_vrss", "prdy_ctrt", "stck_oprc",
            "stck_sdpr", "stck_hgpr", "stck_lwpr",
            "acml_vol", "acml_tr_pbmn", "w52_hgpr",
            "w52_lwpr"
        )
        data = None
        try:
            data = self.redis_client.get(
                REDIS_STOCK_CURRENT_PRICE.format(id=stock_unique_id)
            )
            data = json.loads(data) # type: ignore
        except TypeError as e:
            logging.warning(e)
        except Exception as e:
            logging.error(e)
        if isinstance(data, dict):
            # 필터링
            data = {k: v 
                    for k, v in data.items()
                    if k in FILTER_TARGETS}
        return data



