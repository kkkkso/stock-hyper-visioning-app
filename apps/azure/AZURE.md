# Azure 인프라 구축

## Azure Event Hub

## Azure Stream Analytics

## Azure Function

- `apps/azure/functions/kis_api_collecting`
  - 5분 간격으로 KIS 거래량 상위 30개 종목을 수집하여 Event Hub 로 전송하는 타이머 기반 Azure Function.
    - TODO: 추후 수집 대상 API 추가 예정

## Azure Managed Redis

캐시 기능 구현을 위해 Redis를 필요로 합니다.  

다음 링크를 참조하여 REDIS 인스턴스를 생성하세요: [azure_redis](./redis/AZ_REDIS.md)
