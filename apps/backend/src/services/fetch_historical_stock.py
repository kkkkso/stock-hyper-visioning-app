"""SQL DB로 부터 누적 주식 데이터를 `Query`합니다.
"""
from antic_extensions import PsqlDBClient
from typing import Optional
from ..settings import api_settings

__all__ = (
    'HistoricalStockDataQueryService',
    'PsqlDBClient'
)

class HistoricalStockDataQueryService:
    """실시간 주식 데이터를 Redis로 부터 캐시한다.
    """
    def __init__(self, sql_client: Optional[PsqlDBClient]) -> None:
        """실시간 주식 데이터를 Redis로 부터 캐시하는 헬퍼 클래스를 생성.  

        >>> client = PsqlDBClient(...)
            service = HistoricalStockDataQueryService(client)
            data = service.query_historical_stock_data("505050")
            ...

        Args:
            sql_client (PsqlDBClient, optional): sql_client를 입력할 경우 해당 클라이언트를 이용합니다.
                                                `None`으로 미기입시 자동으로 내부적으로 새로운 클라이언트를 
                                                생성합니다. 
        """
        if api_settings.SQL_PASSWORD is None:
            raise EnvironmentError("SQL_PASSWORD is not provided.")
        self._sql_client = sql_client
        if not self._sql_client:
            self._sql_client = PsqlDBClient(
                api_settings.SQL_HOST, 
                api_settings.SQL_USER,
                api_settings.SQL_PASSWORD,
                api_settings.SQL_DATABASE
            )

    def query_historical_stock_data(
            self,
            stock_unique_id: str
    ):
        """해당 종목의 주식 누적 데이터를 Psql로 부터 받아온다.  
        
        :param stock_unique_id: (str) 주식 종목 코드 입력.  

        """
        ...


    def query_stock_news_data(
            self,
            stock_unique_id: str
    ):
        """해당 종목에 대한 뉴스 기분석 데이터를 Query해서 받아온다.  
        
        :param stock_unique_id: (str) 주식 종목 코드 입력.  

        """
        ...


