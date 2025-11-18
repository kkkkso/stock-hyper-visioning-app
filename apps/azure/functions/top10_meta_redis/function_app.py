import json
import logging
import os
from typing import Iterable, List, Sequence

import azure.functions as func
from antic_extensions import RedisService

# FunctionApp 인스턴스 생성
app = func.FunctionApp()

# RedisService 설정
REDIS_TOP10_KEY = os.environ.get("REDIS_TOP10_KEY", "volume_rank:top10")

# RedisService 인스턴스 생성
redis_service = RedisService(
    host=os.environ["REDIS_HOST"],
    port=int(os.environ.get("REDIS_PORT", "6380")),
    password=os.environ.get("REDIS_PASSWORD"),
    database=int(os.environ.get("REDIS_DB", "0")),
    ssl=True,
    decode_responses=True,
)
logging.info("Initialized RedisService for TOP10 meta cache.")

# Helper 함수
def build_top10_meta(rows: List[dict]) -> List[dict]:
    """거래량 순위 원본 리스트에서 TOP10 메타 정보만 추출한다. /[todo] event hub 확인해서 필드명 수정하기"""
    top10: List[dict] = []

    for i, row in enumerate(rows[:10], start=1):
        if not isinstance(row, dict):
            continue

        meta = {
            "rank": i,
            "code": row.get("mksc_shrn_iscd") or row.get("stck_shrn_iscd"),
            "name": row.get("hts_kor_isnm"),
            "volume": row.get("acml_vol"),
            "volume_ratio": row.get("prdy_vrss_vol_rate"),
            # 필요하면 추가: 현재가, 등락률 등
            "price": row.get("stck_prpr"),
            "change_rate": row.get("prdy_ctrt"),
        }
        top10.append(meta)

    return top10

def extract_rows_from_event(payload_str: str) -> List[dict]:
    """
    Event Hub 메시지에서 순위 리스트(list[dict])를 꺼낸다.
    - payload 가 list 면 그대로 사용
    - dict 이고 'output' 키 안에 list 가 있으면 그걸 사용
    """
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        logging.warning("Invalid JSON payload, skip: %s", payload_str[:200])
        return []

    # 케이스 1: 바로 리스트
    if isinstance(payload, list):
        rows = payload
    # 케이스 2: {"output": [...]} 형태
    elif isinstance(payload, dict):
        rows = payload.get("output") or payload.get("data") or payload.get("items")
    else:
        logging.warning("Unexpected payload type: %s", type(payload))
        return []

    if not isinstance(rows, list):
        logging.warning("Expected list for rows, but got: %s", type(rows))
        return []

    # dict 아닌 건 필터링
    return [r for r in rows if isinstance(r, dict)]



# EventHub Trigger 함수
@app.function_name(name="top10_meta_redis") 
@app.event_hub_message_trigger(arg_name="events", event_hub_name=os.environ["AnticSignalEventHubName"],
                               connection="AnticSignalEventHubConnectionString",
                               consumer_group="antic-signal-top10-redis_kis-vol_consumer_group") 
def top10_meta_redis(events: Sequence[func.EventHubEvent]) -> None:  # type: ignore
    """Event Hub 에서 거래량 순위 데이터를 읽어 TOP10 메타를 Redis 에 캐시한다."""
    if not isinstance(events, Sequence):
        events = [events]
    logging.info("Received %d event(s) from EventHub.", len(events))

    for event in events:
        try:
            raw = event.get_body().decode("utf-8")
        except Exception:
            logging.exception("Failed to decode EventHubEvent body, skip event.")
            continue

        rows = extract_rows_from_event(raw)
        if not rows:
            logging.info("No rows extracted from payload: %s", raw[:200])
            continue

        top10_meta = build_top10_meta(rows)
        if not top10_meta:
            logging.info("No TOP10 meta built from rows, skip.")
            continue

        try:
            payload_str = json.dumps(
                {"items": top10_meta},
                ensure_ascii=False,
                default=str,
            )
            # antic_extensions.RedisService 사용
            redis_service.set(REDIS_TOP10_KEY, payload_str)
            logging.info(
                "Saved TOP10 meta to Redis key=%s (count=%d, seq=%s)",
                REDIS_TOP10_KEY,
                len(top10_meta),
                getattr(event, "sequence_number", None),
            )
        except Exception:
            logging.exception("Failed to save TOP10 meta to Redis.")

