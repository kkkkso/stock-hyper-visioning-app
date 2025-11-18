from typing import Optional, Literal
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str

