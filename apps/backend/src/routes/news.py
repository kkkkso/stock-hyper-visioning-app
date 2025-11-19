from fastapi import Depends, APIRouter, HTTPException
from ..services import (
    HistoricalStockDataQueryService 
)
from ..core.clients import (
    get_psql_client, 
    PsqlDBClient
)

router = APIRouter()


## /api/v1/news/stock
@router.get("/stock/{unique_id}")
def get_stock_news_data(
        unique_id: str,
        sql_client: PsqlDBClient = Depends(get_psql_client)
):
    """[GET] 해당 주식 종목에 대한 뉴스 감정 분석 데이터를 받도록 합니다."""
    id = str(unique_id)
    service = HistoricalStockDataQueryService(sql_client)
    ...
    