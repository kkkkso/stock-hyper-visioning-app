import json
from typing import Generator, Any, Union
import logging

__all__ = (
    'JSONLoader',
    'FileHandler'
)


class FileHandler:
    @staticmethod
    def save_to_json(data: Union[dict, list[dict]], path: str='./news.json'):
        if not data:
            raise ValueError(f"Empty or unexpeceted type of data: {type(data)}")
        with open(path, encoding='utf-8', mode='w') as f:
            f.write(json.dumps(data, indent=4, ensure_ascii=False))
            logging.info(f'Saved result txt file to {path}')


class JSONLoader:
    """제너레이터를 반환하는 JSONLoader.
    
    ```python
    # Example
    loader = JSONLoader()
    for item in loader("data.json"):
        print(item)
    ```
    """
    def __init__(self):
        self._data = None
    
    def __call__(self, path: str) -> Generator[Any, None, None]:
        with open(path, 'r', encoding='utf-8') as f:
            self._data = json.load(f)
        
        if isinstance(self._data, list):
            for item in self._data:
                yield item
        elif isinstance(self._data, dict):
            for key, value in self._data.items():
                yield {
                    key: value
                }
                # yield key, value
        else:
            yield self._data

