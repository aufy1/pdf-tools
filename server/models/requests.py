# models/requests.py
from pydantic import BaseModel
from typing import List, Optional

class MergeRequest(BaseModel):
    filenames: List[str]

class SplitRequest(BaseModel):
    filename: str
    pages: Optional[str] = None  # np. "1-5, 8, 11-13"