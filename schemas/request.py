from typing import List, Optional

from pydantic import BaseModel


class RequestModel(BaseModel):
    id: int
    query: str


class ResponseModel(BaseModel):
    id: int
    answer: Optional[int] = None
    reasoning: str
    sources: List[str]
