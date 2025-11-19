from fastapi import Depends, APIRouter, HTTPException
from ..services import (
    RealtimeStockInfoCacheService,
    HistoricalStockDataQueryService 
)
from ..core.clients import (
    get_psql_client, 
    get_redis_service_client,
    PsqlDBClient, RedisService
)
from .models import QueryRequest

router = APIRouter()


## /api/v1/stock/top10
@router.get("/top10")
def get_stock_top10(
        redis_client: RedisService = Depends(get_redis_service_client)
):
    """[GET] 실시간 주식 TOP10 데이터를 얻을 수 있습니다."""
    service = RealtimeStockInfoCacheService(
        redis_client
    )
    ...

## /api/v1/stock/realtime
@router.get("/realtime/{unique_id}")
def get_stock_realtime_data(
        unique_id: str,
        redis_client: RedisService = Depends(get_redis_service_client)
):
    """[GET] 실시간으로 해당 종목에 대한 현재 데이터를 받습니다."""
    uniq_id = str(unique_id)
    service = RealtimeStockInfoCacheService(
        redis_client
    )
    data = service.cache_stock_realtime_data(uniq_id)
    return data

    
## /api/v1/stock/history
@router.get("/history/{unique_id}")
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

