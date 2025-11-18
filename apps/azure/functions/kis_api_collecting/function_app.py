import json
import logging
import os
from typing import Iterable, List, Sequence

import azure.functions as func
from kis_api import KISClient, fetch_inquire_price, fetch_volume_rank


app = func.FunctionApp()  # type: ignore

client = KISClient(
    app_key=os.environ["KIS_APP_KEY"],
    app_secret=os.environ["KIS_APP_SECRET"],
    request_interval=0.5,
)


def _build_volume_rank_schedule() -> str:
    """환경 변수에 정의된 초 단위 주기를 Azure Functions CRON 식으로 변환한다."""
    raw_value = os.environ.get("VOLUME_RANK_PULLING_INTERVAL", "300")
    try:
        interval = max(1, int(raw_value))
    except ValueError:
        logging.warning("VOLUME_RANK_PULLING_INTERVAL=%s 값이 잘못되어 300초로 대체합니다.", raw_value)
        interval = 300

    if interval < 60:
        return f"*/{interval} * * * * *"

    minutes, seconds = divmod(interval, 60)
    if seconds == 0 and minutes < 60:
        return f"0 */{minutes} * * * *"

    hours, minutes = divmod(minutes, 60)
    if seconds == 0 and minutes == 0 and hours < 24:
        return f"0 0 */{hours} * * *"

    logging.warning("지원하지 않는 interval=%s 값이 입력되어 5분 주기로 대체합니다.", interval)
    return "0 */5 * * * *"


VOLUME_RANK_SCHEDULE = _build_volume_rank_schedule()


@app.function_name(name="kis_volume_rank_collect_interval")
@app.event_hub_output(
    arg_name="kis_volume_rank",
    event_hub_name=os.environ["AnticSignalEventHubName"],
    connection="AnticSignalEventConnectionString",
)
@app.timer_trigger(schedule=VOLUME_RANK_SCHEDULE, arg_name="myTimer", run_on_startup=True, use_monitor=False)
def volume_rank_collect_interval(myTimer: func.TimerRequest, kis_volume_rank: func.Out[str]) -> None:  # type: ignore
    if myTimer.past_due:
        logging.info("The timer is past due!")

    data = fetch_volume_rank(client)
    kis_volume_rank.set(json.dumps(data, default=str))
    logging.info("Volume rank timer function executed.")


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
        candidates = (item.get("mksc_shrn_iscd") for item in data if isinstance(item, dict))
    elif isinstance(data, dict):
        candidates = [data.get("mksc_shrn_iscd") or data.get("stck_shrn_iscd")]
    else:
        logging.info("Unsupported payload type for extracting stock codes: %s", type(data))
        return []

    codes = [code for code in candidates if code]
    return codes[:30]


@app.function_name(name="kis_inquire_price_from_event")
@app.event_hub_message_trigger(
    arg_name="events",
    event_hub_name=os.environ["AnticSignalEventHubName"],
    connection="AnticSignalEventConnectionString",
    consumer_group="$Default",
)
def inquire_price_from_event(events: Sequence[func.EventHubEvent]) -> None:  # type: ignore
    """Event Hub 메시지를 받아 주식 현재가 시세를 조회한다."""
    if not isinstance(events, Sequence):
        events = [events]

    for event in events:
        raw = event.get_body().decode("utf-8")
        stock_codes = _extract_stock_codes(raw)
        if not stock_codes:
            logging.info("No stock codes found in message: %s", raw)
            continue

        enriched_payloads = []
        for code in stock_codes:
            try:
                enriched_payloads.append(fetch_inquire_price(client, fid_input_iscd=code))
            except Exception as exc:  # pylint: disable=broad-except
                logging.exception("Failed to fetch current price for %s: %s", code, exc)

        logging.info(
            "Fetched %d current price rows for event sequence=%s",
            len(enriched_payloads),
            getattr(event, "sequence_number", None),
        )


def _persist_snapshot(payloads: List[dict]) -> None:
    """현재가 응답 목록을 JSON 파일로 저장한다."""
    output_path = os.environ.get("CURRENT_PRICE_SNAPSHOT_PATH", "/tmp/current_price_snapshot.json")
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fp:
            json.dump(payloads, fp, default=str, ensure_ascii=False, indent=2)
        logging.info("Saved %d rows to %s", len(payloads), output_path)
    except OSError as exc:
        logging.exception("Failed to persist current price snapshot to %s: %s", output_path, exc)
