# KIS API Collector Function


## 개요
- 위치: `apps/azure/functions/kis_api_collecting`
- 목적: KIS 오픈 API에서 거래량 상위 30개 종목을 5분마다 수집해 Azure Event Hub (`AnticSignalEventHubName`)로 전송합니다.
- Swift timer 설정: `0 */5 * * * *` (5분 마다 실행, `function_app.py` 참조).

## 주요 파일
- `function_app.py`: 최신 Python Programming Model 기반 엔트리 포인트 (`FunctionApp`)와 타이머 트리거 정의.
- `host.json`: Functions 호스트 전역 구성.
- `requirements.txt`: 함수 앱 종속성 목록.
- `local.settings.json`: 로컬 개발용 환경 변수. **실제 키/시크릿은 저장소에 커밋하지 않는 것을 권장합니다.**

## 공유 패키지 빌드
`requirements.txt`가 `dist/kis_api-<버전>.whl`을 참조하므로, 개발/배포 전에 루트에서 wheel을 생성해야 합니다.
```bash
pip install -U build
./scripts/build_kis_shared.sh        # Linux/Mac
# 또는 PowerShell
powershell -ExecutionPolicy Bypass -File scripts/build_kis_shared.ps1
```
`packages/kis_api`를 수정할 때마다 wheel을 재생성해 주세요.

## 로컬 실행 방법
1. Azure Functions Core Tools와 Python 3.12 환경을 준비합니다 (위 wheel 생성 완료 가정).
2. 필요 시 가상환경 생성 후 의존성 설치:
   ```bash
   cd apps/azure/functions/kis_api_collecting
   python -m venv .venv && source .venv/Scripts/activate  # Linux/Mac: source .venv/bin/activate
   pip install -r requirements.dev.txt
   ```
   `requirements.dev.txt`는 `requirements.txt` + `-e ../../../../packages/kis_api`를 포함해 공유 모듈을 editable 상태로 로드합니다.
3. `local.settings-default.json`에 KIS API Key/Secret, Event Hub 연결 문자열 등을 설정하고, `local.settings.json`으로 복사 후 수정합니다.
4. Functions 실행:
   ```bash
   func start
   ```

## 배포 시 의존성 포함 방법
1. wheel이 최신인지 확인 후 함수 폴더에서 `.python_packages`를 준비:
   ```bash
   cd apps/azure/functions/kis_api_collecting
   python -m pip install -r requirements.txt
   ```
   `requirements.txt`는 `../../../../dist/kis_api-<버전>.whl`을 참조하므로, 해당 wheel이 존재하지 않으면 위 “공유 패키지 빌드” 단계를 먼저 수행해야 합니다.
2. 이후 `func azure functionapp publish <함수앱>`을 실행하면 `.python_packages` 디렉터리가 함께 업로드되어 공유 모듈을 사용할 수 있습니다.

## 비고
- 폴더 내 `__azurite*` 파일 및 `__blobstorage__`, `__queuestorage__` 디렉터리는 Azurite 로컬 에뮬레이터가 생성한 개발용 데이터입니다. 필요 시 삭제 후 `func start` 실행 시 다시 생성할 수 있습니다.
- 배포 시에는 `local.settings.json`의 값을 Azure Functions App의 Application Settings로 이전하세요.

## 함수별 트리거, 입력, 저장 데이터
아래 표는 `function_app.py`에 정의된 각 함수의 트리거, API 입력값, 역할, 결과 저장 위치를 요약한 것입니다.

| 함수명 | 실행 트리거 | 주요 입력값 | 역할 | 저장 데이터 |
| --- | --- | --- | --- | --- |
| `kis_volume_rank_collect_interval` | Timer (`_build_volume_rank_schedule`로 계산) | 없음 (환경변수 KIS 인증 정보만 사용) | 5분 등 주기마다 `fetch_volume_rank` 호출 후 결과를 Event Hub에 전송 | Event Hub `AnticSignalEventHubName`에 volume rank JSON 메시지 |
| `kis_inquire_price_from_event` | Event Hub 메시지 (거래량 순위) | `mksc_shrn_iscd` (volume rank payload에서 추출) | 각 종목의 현재가 정보를 `fetch_inquire_price`로 조회 | Redis `stock:{code}:current_price`, `stock:{code}:current_price_fields` |
| `kis_inquire_time_itemconclusion_from_event` | Event Hub 메시지 | `mksc_shrn_iscd` | 현재 시각(초 단위)을 `fid_input_hour_1`으로 사용해 `fetch_inquire_time_itemconclusion` 호출 | Redis `stock:{code}:intraday_ticks` |
| `kis_investor_trade_by_stock_daily_from_event` | Event Hub 메시지 | `fid_input_iscd`, `fid_input_date` (당일 KST) | 종목별 투자자 매매동향(일별) 조회 후 별도 Event Hub로 forward | Event Hub `INVESTOR_TRADE_EVENT_HUB_NAME` |
| `kis_inquire_daily_chartprice_from_event` | Event Hub 메시지 | `fid_input_iscd`, `fid_period_div_code`=`D`, 기간(`fetch_inquire_daily_itemchartprice` 기본값) | 1년치 일봉 데이터 조회 후 PostgreSQL 업서트 | PostgreSQL `DAILY_PRICE_TABLE_NAME` (예: `anticsignal.stock_history`) |

### 데이터 흐름 다이어그램
```mermaid
flowchart LR
    Timer[kis_volume_rank_collect_interval<br/>Timer Trigger] --> EH[Event Hub<br/>kis-volume-rank-5min]
    EH --> Price[kis_inquire_price_from_event]
    EH --> TimeItem[kis_inquire_time_itemconclusion_from_event]
    EH --> Investor[kis_investor_trade_by_stock_daily_from_event]
    EH --> Daily[kis_inquire_daily_chartprice_from_event]

    Price -->|현재가 JSON| Redis1[(Redis<br/>stock:{code}:current_price)]
    Price -->|요약 해시| Redis2[(Redis<br/>stock:{code}:current_price_fields)]
    TimeItem -->|intraday ticks| Redis3[(Redis<br/>stock:{code}:intraday_ticks)]
    Investor --> EH2[Event Hub<br/>INVESTOR_TRADE_EVENT_HUB_NAME]
    Daily --> PG[(PostgreSQL<br/>stock_history)]
```

## 저장 데이터 샘플

### Redis 캐시 예시
```jsonc
// stock:005930:current_price
{
  "stck_prpr": "78000",
  "prdy_vrss": "500",
  "acml_vol": "2550032",
  "collected_at": "2025-03-19T14:05:00+09:00",
  "requested_fid_input_iscd": "005930",
  "mksc_shrn_iscd": "005930"
}

// stock:005930:current_price_fields
{
  "stck_prpr": "78000",
  "prdy_vrss": "500",
  "acml_vol": "2550032",
  "collected_at": "2025-03-19T14:05:00+09:00"
}

// stock:005930:intraday_ticks
[
  {
    "stck_cntg_hour": "140000",
    "stck_prpr": "78000",
    "cntg_vol": "1200",
    "requested_fid_input_iscd": "005930"
  },
  {
    "stck_cntg_hour": "140100",
    "stck_prpr": "78100",
    "cntg_vol": "800",
    "requested_fid_input_iscd": "005930"
  }
]
```

### PostgreSQL (stock_history) 업서트 예시
`DAILY_PRICE_TABLE_NAME`을 `anticsignal.stock_history`로 설정했을 때 적재되는 레코드는 아래와 같습니다.

```sql
INSERT INTO anticsignal.stock_history
    (fid_input_iscd, fid_period_div_code, stck_bsop_date, stck_clpr, stck_oprc)
VALUES
    ('005930', 'D', '2025-03-19', 58500, 57400)
ON CONFLICT (fid_input_iscd, fid_period_div_code, stck_bsop_date)
    DO UPDATE SET
        stck_clpr = EXCLUDED.stck_clpr,
        stck_oprc = EXCLUDED.stck_oprc;
```

> `fetch_inquire_daily_itemchartprice` 응답 중 `requested_fid_input_iscd`, `requested_fid_period_div_code`, `stck_bsop_date`, `stck_clpr`, `stck_oprc`만 추려서 Numeric 컬럼에 저장합니다.
