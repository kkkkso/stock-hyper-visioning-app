import pytest
from news_analysis.core import NewsDataPipelineAPI
from news_analysis.modules import FileHandler
from pathlib import Path
import json


def test_integration():
    api = NewsDataPipelineAPI()
    result = api.fetch_news_from_naver_api(
        '삼성전자',
        web_scrap_content=True
    )
    print(result)
    if result:
        FileHandler.save_to_json(
            result, str(Path("./news_test.json"))
        )

