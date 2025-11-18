from fastapi import Depends, APIRouter, HTTPException
from ..services import (
    RealtimeStockInfoCacheService,
    HistoricalStockDataQueryService 
)
from ..core import (
    get_psql_client, 
    get_redis_service_client,
    PsqlDBClient, RedisService
)
from .models import QueryRequest

router = APIRouter()


@router.get("/stock/top10")
def get_stock_top10(
        redis_client: RedisService = Depends(get_redis_service_client)
):
    """[GET] 실시간 주식 TOP10 데이터를 얻을 수 있습니다."""
    service = RealtimeStockInfoCacheService(
        redis_client
    )
    ...


@router.get("/stock/realtime/{unique_id}")
def get_stock_realtime_data(
        unique_id: str,
        redis_client: RedisService = Depends(get_redis_service_client)
):
    """[GET] 실시간으로 해당 종목에 대한 현재 데이터를 받습니다."""
    id = str(unique_id)
    service = RealtimeStockInfoCacheService(
        redis_client
    )
    ...


@router.get("/stock/history/{unique_id}")
def get_stock_history_data(
        unique_id: str,
        sql_client: PsqlDBClient = Depends(get_psql_client)
):
    """[GET] 해당 종목에 대한 주식 히스토리 데이터를 받습니다."""
    id = str(unique_id)
    service = HistoricalStockDataQueryService(
        sql_client
    )
    ...
