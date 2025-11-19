import json
import logging
import os
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional, Sequence

import azure.functions as func
from antic_extensions import PsqlDBClient, RedisService
from kis_api import (
    KISClient,
    fetch_inquire_daily_itemchartprice,
    fetch_inquire_price,
    fetch_inquire_time_itemconclusion,
    fetch_investor_trade_by_stock_daily,
    fetch_volume_rank,
)
from kis_api.client import KST


app = func.FunctionApp()  # type: ignore

# 공통으로 사용할 KIS API 클라이언트. request_interval로 호출 간격을 조절한다.
client = KISClient(
    app_key=os.environ["KIS_APP_KEY"],
    app_secret=os.environ["KIS_APP_SECRET"],
    request_interval=float(os.environ.get("KIS_REQUEST_INTERVAL", 0.5) or 0.5),
)

_redis_service: Optional[RedisService] = None
_psql_client: Optional[PsqlDBClient] = None


def _build_volume_rank_schedule() -> str:
    """환경 변수에 정의된 초 단위 주기를 Azure Functions CRON 식으로 변환한다."""
    raw_value = os.environ.get("VOLUME_RANK_PULLING_INTERVAL", "300")
    try:
        interval = max(1, int(raw_value))
    except ValueError:
        logging.warning(
            "VOLUME_RANK_PULLING_INTERVAL=%s 값이 잘못되어 300초로 대체합니다.",
            raw_value,
        )
        interval = 300

    if interval < 60:
        return f"*/{interval} * * * * *"

    minutes, seconds = divmod(interval, 60)
    if seconds == 0 and minutes < 60:
        return f"0 */{minutes} * * * *"

    hours, minutes = divmod(minutes, 60)
    if seconds == 0 and minutes == 0 and hours < 24:
        return f"0 0 */{hours} * * *"

    logging.warning(
        "지원하지 않는 interval=%s 값이 입력되어 5분 주기로 대체합니다.", interval
    )
    return "0 */5 * * * *"


def _resolve_investor_trade_date() -> str:
    """투자자 매매동향 조회일(YYYYMMDD)을 당일로 고정한다."""
    return datetime.now(KST).strftime("%Y%m%d")


def _resolve_time_itemconclusion_hour() -> str:
    """시간대별 체결 조회에서 사용할 기준 시각을 (초 단위) 반환한다."""
    return datetime.now(KST).strftime("%H%M%S")


def _ensure_event_sequence(
    events: Sequence[func.EventHubEvent] | func.EventHubEvent,
) -> List[func.EventHubEvent]:
    """Event Hub 트리거 입력을 항상 리스트 형태로 정규화한다."""
    if isinstance(events, list):
        return events
    if isinstance(events, tuple):
        return list(events)
    return [events]


def _extract_stock_codes(payload: str) -> List[str]:
    """volume-rank 메시지에서 종목코드를 추출한다."""
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        logging.warning("Skip message, invalid JSON: %s", payload)
        return []

    data = parsed.get("output", parsed)

    candidates: Iterable[str] = []
    if isinstance(data, list):
        candidates = (
            item.get("mksc_shrn_iscd") for item in data if isinstance(item, dict)
        )
    elif isinstance(data, dict):
        candidates = [data.get("mksc_shrn_iscd") or data.get("stck_shrn_iscd")]
    else:
        logging.info(
            "Unsupported payload type for extracting stock codes: %s", type(data)
        )
        return []

    codes = [code for code in candidates if code]
    return codes[:30]


def _get_int_env(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        logging.warning(
            "%s 값을 정수로 변환할 수 없어 기본값 %s을 사용합니다.", key, default
        )
        return default


def _get_redis_service() -> RedisService:
    """실시간 데이터를 저장할 RedisService 인스턴스를 생성/재사용한다."""
    global _redis_service
    if _redis_service is None:
        host = os.environ["REDIS_HOST"]
        port = _get_int_env("REDIS_PORT", 6380)
        password = os.environ.get("REDIS_PASSWORD")
        database = _get_int_env("REDIS_DB", 0)
        _redis_service = RedisService(
            host=host, port=port, password=password, database=database
        )
        logging.info("Redis service initialized for %s:%s/%s", host, port, database)
    return _redis_service


def _get_psql_client() -> PsqlDBClient:
    """1년치 시세 데이터를 적재할 PostgreSQL 클라이언트를 생성/재사용한다."""
    global _psql_client
    if _psql_client is None:
        _psql_client = PsqlDBClient(
            host=os.environ["POSTGRES_HOST"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            database=os.environ["POSTGRES_DB"],
            minconn=_get_int_env("POSTGRES_MIN_CONN", 1),
            maxconn=_get_int_env("POSTGRES_MAX_CONN", 5),
        )
        logging.info(
            "PostgreSQL client initialized for %s/%s",
            os.environ["POSTGRES_HOST"],
            os.environ["POSTGRES_DB"],
        )
    return _psql_client


def _get_daily_price_table() -> str:
    schema = os.environ.get("DAILY_PRICE_SCHEMA_NAME", "anticsignal")
    table = os.environ.get("DAILY_PRICE_TABLE_NAME", "stock_history")
    table_name = f"{schema}.{table}"
    if not table_name or not all(ch.isalnum() or ch == "_" for ch in table):
        raise ValueError(
            "DAILY_PRICE_TABLE_NAME 환경 변수에는 영문/숫자/언더스코어만 사용할 수 있습니다."
        )
    return table_name


def _cache_current_prices(payloads: List[Dict[str, Any]]) -> None:
    """주식 현재가 데이터를 Redis에 캐시한다."""
    if not payloads:
        return
    service = _get_redis_service()
    for payload in payloads:
        code = (
            payload.get("mksc_shrn_iscd")
            or payload.get("stck_shrn_iscd")
            or payload.get("requested_fid_input_iscd")
        )
        if not code:
            continue
        service.set(f"stock:{code}:current_price", json.dumps(payload, default=str))
        summary = {
            "stck_prpr": str(payload.get("stck_prpr", "")),
            "prdy_vrss": str(payload.get("prdy_vrss", "")),
            "acml_vol": str(payload.get("acml_vol", "")),
            "collected_at": str(payload.get("collected_at", "")),
        }
        service.set_hash(f"stock:{code}:current_price_fields", summary)


def _cache_time_itemconclusion(rows: List[Dict[str, Any]]) -> None:
    """당일 시간대별 체결 데이터를 Redis에 캐시한다."""
    if not rows:
        return
    service = _get_redis_service()
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        code = (
            row.get("requested_fid_input_iscd")
            or row.get("mksc_shrn_iscd")
            or row.get("stck_shrn_iscd")
        )
        if not code:
            continue
        grouped[code].append(row)
    for code, items in grouped.items():
        service.set(f"stock:{code}:intraday_ticks", json.dumps(items, default=str))


def _cache_investor_trade(rows: List[Dict[str, Any]]) -> None:
    """투자자 매매동향(일별) 데이터를 Redis에 캐시한다."""
    if not rows:
        return
    service = _get_redis_service()
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        code = (
            row.get("requested_fid_input_iscd")
            or row.get("mksc_shrn_iscd")
            or row.get("stck_shrn_iscd")
        )
        if not code:
            continue
        grouped[code].append(row)
    for code, items in grouped.items():
        service.set(
            f"stock:{code}:investor_trade_daily", json.dumps(items, default=str)
        )


def _safe_decimal(value: Any) -> Optional[Decimal]:
    """문자열/숫자를 Decimal 로 변환한다."""
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        logging.warning("Cannot convert value=%s to Decimal", value)
        return None


def _persist_daily_chartprice(rows: List[Dict[str, Any]]) -> None:
    """기간별 시세 데이터를 PostgreSQL 테이블에 upsert한다."""
    if not rows:
        return
    table_name = _get_daily_price_table()
    client = _get_psql_client()
    insert_sql = (
        f"INSERT INTO {table_name} (fid_input_iscd, fid_period_div_code, stck_bsop_date, stck_clpr, stck_oprc, acml_vol) "
        "VALUES (%s, %s, %s::date, %s, %s, %s) "
        "ON CONFLICT (fid_input_iscd, fid_period_div_code, stck_bsop_date) "
        "DO UPDATE SET stck_clpr = EXCLUDED.stck_clpr, stck_oprc = EXCLUDED.stck_oprc, acml_vol = EXCLUDED.acml_vol"
    )
    inserted = 0
    skipped = 0
    try:
        with client.cursor() as cur:
            for row in rows:
                code = (
                    row.get("requested_fid_input_iscd")
                    or row.get("mksc_shrn_iscd")
                    or row.get("stck_shrn_iscd")
                )
                trade_date = row.get("stck_bsop_date")
                period_code = row.get("requested_fid_period_div_code")
                close_price = _safe_decimal(row.get("stck_clpr"))
                open_price = _safe_decimal(row.get("stck_oprc"))
                volume = _safe_decimal(row.get("acml_vol"))
                missing_fields = [
                    name
                    for name, value in [
                        ("fid_input_iscd", code),
                        ("stck_bsop_date", trade_date),
                        ("fid_period_div_code", period_code),
                        ("stck_clpr", close_price),
                        ("stck_oprc", open_price),
                        ("acml_vol", volume),
                    ]
                    if value in (None, "")
                ]
                if missing_fields:
                    skipped += 1
                    logging.warning(
                        "Skip chartprice row due to missing fields %s. raw=%s",
                        ",".join(missing_fields),
                        row,
                    )
                    continue
                cur.execute(
                    insert_sql,
                    (code, period_code, trade_date, close_price, open_price, volume),
                )
                inserted += 1
    except Exception as exc:
        logging.exception(
            "Failed to upsert daily chart price rows into %s: %s", table_name, exc
        )
        raise
    logging.info(
        "Persisted %d chart price rows into %s (skipped=%d, incoming=%d)",
        inserted,
        table_name,
        skipped,
        len(rows),
    )


# Function 별 스케줄과 Event Hub를 환경 변수 기반으로 계산한다.
VOLUME_RANK_SCHEDULE = _build_volume_rank_schedule()
DEFAULT_EVENT_HUB_NAME = os.environ["AnticSignalEventHubName"]
VOLUME_RANK_EVENT_HUB_NAME = os.environ.get(
    "VolumeRankEventHubName", DEFAULT_EVENT_HUB_NAME
)
EVENT_HUB_CONSUMER_GROUP = os.environ.get("EventHubConsumerGroup", "$Default")
INVESTOR_TRADE_EVENT_HUB = os.environ.get(
    "INVESTOR_TRADE_EVENT_HUB_NAME", DEFAULT_EVENT_HUB_NAME
)
STOCK_HISTORICAL_DATA_EVENT_HUB = os.environ.get(
    "StockHistoricalDataHubName", "StockHistoricalDataHubName"
)


# 거래량 순위 데이터
@app.function_name(name="kis_volume_rank_collect_interval")
@app.event_hub_output(
    arg_name="kis_volume_rank_default",
    event_hub_name=DEFAULT_EVENT_HUB_NAME,
    connection="AnticSignalEventConnectionString",
)
@app.event_hub_output(
    arg_name="kis_volume_rank_interval",
    event_hub_name=VOLUME_RANK_EVENT_HUB_NAME,
    connection="AnticSignalEventConnectionString",
)
@app.timer_trigger(
    schedule=VOLUME_RANK_SCHEDULE,
    arg_name="myTimer",
    run_on_startup=True,
    use_monitor=False,
)
def volume_rank_collect_interval(
    myTimer: func.TimerRequest,
    kis_volume_rank_default: func.Out[str],
    kis_volume_rank_interval: func.Out[str],
) -> None:  # type: ignore
    """거래량 순위 데이터를 주기적으로 조회해 Event Hub로 전송한다."""
    if myTimer.past_due:
        logging.info("The timer is past due!")

    data = fetch_volume_rank(client)
    payload = json.dumps(data, default=str)
    kis_volume_rank_default.set(payload)
    kis_volume_rank_interval.set(payload)
    logging.info("Volume rank timer function executed.")


# 주식 현재가 시세
@app.function_name(name="kis_inquire_price_from_event")
@app.event_hub_message_trigger(
    arg_name="events",
    event_hub_name=VOLUME_RANK_EVENT_HUB_NAME,
    connection="AnticSignalEventConnectionString",
    consumer_group=EVENT_HUB_CONSUMER_GROUP,
)
def inquire_price_from_event(events: Sequence[func.EventHubEvent]) -> None:  # type: ignore
    """거래량 순위 이벤트를 받아 종목 현재가를 실시간 조회하고 Redis에 저장한다."""
    normalized_events = _ensure_event_sequence(events)

    for event in normalized_events:
        raw = event.get_body().decode("utf-8")
        stock_codes = _extract_stock_codes(raw)
        if not stock_codes:
            logging.info("No stock codes found in message: %s", raw)
            continue

        enriched_payloads = []
        for code in stock_codes:
            try:
                enriched_payloads.append(
                    fetch_inquire_price(client, fid_input_iscd=code)
                )
            except Exception as exc:  # pylint: disable=broad-except
                logging.exception("Failed to fetch current price for %s: %s", code, exc)

        _cache_current_prices(enriched_payloads)
        logging.info(
            "Fetched %d current price rows for event sequence=%s",
            len(enriched_payloads),
            getattr(event, "sequence_number", None),
        )


# 당일 시간대별 체결
@app.function_name(name="kis_inquire_time_itemconclusion_from_event")
@app.event_hub_message_trigger(
    arg_name="events",
    event_hub_name=VOLUME_RANK_EVENT_HUB_NAME,
    connection="AnticSignalEventConnectionString",
    consumer_group=EVENT_HUB_CONSUMER_GROUP,
)
def inquire_time_itemconclusion_from_event(events: Sequence[func.EventHubEvent]) -> None:  # type: ignore
    """Event Hub 메시지를 받아 당일 시간대별 체결 데이터를 조회하고 Redis에 저장한다."""
    normalized_events = _ensure_event_sequence(events)
    hour = _resolve_time_itemconclusion_hour()

    for event in normalized_events:
        raw = event.get_body().decode("utf-8")
        stock_codes = _extract_stock_codes(raw)
        if not stock_codes:
            logging.info("No stock codes found in message for time conclusion: %s", raw)
            continue

        aggregated: List[Dict[str, Any]] = []
        for code in stock_codes:
            try:
                aggregated.extend(
                    fetch_inquire_time_itemconclusion(
                        client,
                        fid_input_iscd=code,
                        fid_input_hour_1=hour,
                    )
                )
            except Exception as exc:  # pylint: disable=broad-except
                logging.exception(
                    "Failed to fetch time conclusion for %s: %s", code, exc
                )

        _cache_time_itemconclusion(aggregated)
        logging.info(
            "Fetched %d time-item conclusion rows for event sequence=%s",
            len(aggregated),
            getattr(event, "sequence_number", None),
        )


# 투자자 매매동향
@app.function_name(name="kis_investor_trade_by_stock_daily_from_event")
@app.event_hub_message_trigger(
    arg_name="events",
    event_hub_name=VOLUME_RANK_EVENT_HUB_NAME,
    connection="AnticSignalEventConnectionString",
    consumer_group=EVENT_HUB_CONSUMER_GROUP,
)
def investor_trade_by_stock_daily_from_event(
    events: Sequence[func.EventHubEvent],
) -> None:  # type: ignore
    """Event Hub 메시지를 받아 종목별 투자자 매매동향(일별)을 수집한다."""
    normalized_events = _ensure_event_sequence(events)
    input_date = _resolve_investor_trade_date()

    for event in normalized_events:
        raw = event.get_body().decode("utf-8")
        stock_codes = _extract_stock_codes(raw)
        if not stock_codes:
            logging.info("No stock codes found in message for investor trade: %s", raw)
            continue

        aggregated: List[Dict[str, Any]] = []
        for code in stock_codes:
            try:
                aggregated.extend(
                    fetch_investor_trade_by_stock_daily(
                        client,
                        fid_input_iscd=code,
                        fid_input_date=input_date,
                    )
                )
            except Exception as exc:  # pylint: disable=broad-except
                logging.exception(
                    "Failed to fetch investor trade data for %s: %s", code, exc
                )

        if aggregated:
            _cache_investor_trade(aggregated)
            logging.info(
                "Fetched %d investor trade rows for event sequence=%s",
                len(aggregated),
                getattr(event, "sequence_number", None),
            )


@app.function_name(name="kis_inquire_daily_chartprice_from_event")
@app.event_hub_output(
    arg_name="stock_history_output",
    event_hub_name=STOCK_HISTORICAL_DATA_EVENT_HUB,
    connection="AnticSignalEventConnectionString",
)
@app.event_hub_message_trigger(
    arg_name="events",
    event_hub_name=VOLUME_RANK_EVENT_HUB_NAME,
    connection="AnticSignalEventConnectionString",
    consumer_group=EVENT_HUB_CONSUMER_GROUP,
)
def inquire_daily_chartprice_from_event(
    events: Sequence[func.EventHubEvent],
    stock_history_output: func.Out[str],
) -> None:  # type: ignore
    """Event Hub 메시지를 받아 1년치 시세 데이터를 조회하고 PostgreSQL에 저장한다."""
    normalized_events = _ensure_event_sequence(events)

    for event in normalized_events:
        raw = event.get_body().decode("utf-8")
        stock_codes = _extract_stock_codes(raw)
        if not stock_codes:
            logging.info("No stock codes found in message for chart price: %s", raw)
            continue

        aggregated: List[Dict[str, Any]] = []
        for code in stock_codes:
            try:
                aggregated.extend(
                    fetch_inquire_daily_itemchartprice(
                        client,
                        fid_input_iscd=code,
                    )
                )
            except Exception as exc:  # pylint: disable=broad-except
                logging.exception(
                    "Failed to fetch daily chart price for %s: %s", code, exc
                )

        if aggregated:
            logging.info(f"historical data {aggregated}")
            stock_history_output.set(json.dumps(aggregated, default=str))
            logging.info(
                "Emitted %d chart price rows to %s",
                len(aggregated),
                STOCK_HISTORICAL_DATA_EVENT_HUB,
            )
            _persist_daily_chartprice(aggregated)
            logging.info(
                "Fetched %d chart price rows for event sequence=%s",
                len(aggregated),
                getattr(event, "sequence_number", None),
            )
