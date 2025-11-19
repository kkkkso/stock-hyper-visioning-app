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
    port=int(os.environ.get("REDIS_PORT", "10000")),
    password=os.environ.get("REDIS_PASSWORD"),
    database=int(os.environ.get("REDIS_DB", "0")),
)
logging.info("Initialized RedisService for TOP10 meta cache.")

# volume_rank_fields 정의
# 맨 위 어딘가에 필드 리스트 정의해 두면 좋아
VOLUME_RANK_FIELDS = [
    "hts_kor_isnm",
    "mksc_shrn_iscd",
    "data_rank",
    "stck_prpr",
    "prdy_vrss_sign",
    "prdy_vrss",
    "prdy_ctrt",
    "acml_vol",
    "prdy_vol",
    "lstn_stcn",
    "avrg_vol",
    "n_befr_clpr_vrss_prpr_rate",
    "vol_inrt",
    "vol_tnrt",
    "nday_vol_tnrt",
    "avrg_tr_pbmn",
    "tr_pbmn_tnrt",
    "nday_tr_pbmn_tnrt",
    "acml_tr_pbmn",
]


# Helper 함수
def build_top10_meta(rows: List[dict]) -> List[dict]:
    """
    거래량 순위 원본 리스트에서 TOP10 메타 정보만 추출한다.
    Event Hub Payload의 필드명을 기준으로 함.
    """
    top10: List[dict] = []

    for i, row in enumerate(rows[:10], start=1):
        if not isinstance(row, dict):
            continue

        meta:dict = {}
        # 컬럼명 그대로 사용
        for field in VOLUME_RANK_FIELDS:
            meta[field] = row.get(field)

        # data_rank 숫자로 쓰기 위해 캐스팅
        try:
            if meta.get("data_rank") is not None:
                meta["data_rank"] = int(meta["data_rank"])
        except (ValueError, TypeError):
            pass

        top10.append(meta)

    # 🔍 여기서 TOP10 전체 요약 찍기
    logging.info(
        "build_top10_meta: built %d items, ranks=%s, codes=%s",
        len(top10),
        [m.get("data_rank") for m in top10],
        [m.get("mksc_shrn_iscd") for m in top10],
    )

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

        # 🔍 여기 추가: 샘플 한 개 찍어보기
        # sample = rows[0]
        # logging.info("Sample row keys: %s", list(sample.keys()))
        # logging.info("Sample row: %s", json.dumps(sample, ensure_ascii=False)[:1000])

        top10_meta = build_top10_meta(rows)
        if not top10_meta:
            logging.info("No TOP10 meta built from rows, skip.")
            continue

        # 🔍 TOP10 전체 JSON 프리뷰 로그
        try:
            preview_str = json.dumps(top10_meta, ensure_ascii=False, default=str)
            logging.info("TOP10 meta full preview (truncated): %s", preview_str[:1500])
        except Exception:
            logging.exception("Failed to serialize TOP10 meta for preview log.")


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

@app.route(route="top10_meta_preview", methods=["GET"])
def top10_meta_preview(req: func.HttpRequest) -> func.HttpResponse:
    value = redis_service.get(REDIS_TOP10_KEY)
    return func.HttpResponse(
        value or '{"items":[]}',
        status_code=200,
        mimetype="application/json"
    )
