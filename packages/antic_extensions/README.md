# Antic Extensions v.0.1.0

Antic Signal의 확장 패키지입니다.

**주요 기능:**

- 주요 Database 접속 및 쿼리 서비스 (PostgreSQL, Redis)

## 빠른 시작

사용하려는 Azure Function, 패키지/모듈 등에서 아래와 같이 사용하세요.

```sh
pip install .

# 혹은
pip install <release-link>

# 예시:
pip install https://github.com/AnticSignal/stock-hyper-visioning-app/releases/download/v0.1.0_antic_ext/antic_extensions-0.1.0-py3-none-any.whl
```

클라우드 환경에서 사용할 경우, `requirements.txt`에 `pip install <release-link>` 와 같이 작성해야 합니다.

**예시:**

```ini
azure-functions
https://github.com/AnticSignal/stock-hyper-visioning-app/releases/download/v0.1.0_antic_ext/antic_extensions-0.1.0-py3-none-any.whl
certifi==2025.7.9
```

**코드 내부:**

```python
# src/main.py
from antic_extensions import PsqlDBClient

# PsqlDBClient내에 자격 증명 정보를 입력합니다.
client = PsqlDBClient(...)
with client.cursor() as cur:
    cur.execute('SELECT * from database LIMIT 100')
    rows = cur.fetchall()

# --------------------------------------- #

from antic_extensions import RedisService

# RedisService내에 자격 증명 정보를 입력합니다.
service = RedisService(...)
service.set('test_name', 'test_value')
service.get('test_name')
service.set_hash('test_hash', {'test': 2323 })
service.get_hash('test_hash')

```

## 개발

```sh
pip install -e .
```

```sh
# Pytest
pytest --log-cli-level=DEBUG -s
```
