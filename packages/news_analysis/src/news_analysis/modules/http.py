from typing import Optional
import requests
import logging

__all__ = (
    'HttpClient',
)


class HttpClient:
    def __init__(
            self, 
            endpoint: str
    ) -> None:
        self._endpoint = f"{endpoint}"

    def get(self, params: Optional[dict]=None, **kwargs) -> Optional[dict]:
        try:
            res = requests.get(
                self._endpoint, params=params or {}, **kwargs
            )
            res.raise_for_status()
            logging.info(
                f"Retrived GET({self._endpoint}): {str(res.json())[:100]}"
            )
            return res.json()
        except requests.HTTPError as e:
            logging.warning(e)
        return None
    
    