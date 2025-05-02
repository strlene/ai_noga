
# api/schemas.py
from typing import List, Any, Union
from pydantic import BaseModel, HttpUrl, Field, validator

from typing import Optional, Dict
from pydantic import BaseModel

class IngredientItem(BaseModel):
    nama: str
    status: str
    detail: str

class AnalyzeRequest(BaseModel):
    session_id: str
    composition: HttpUrl

class AnalyzeResponse(BaseModel):
    status: str
    data: Dict[str, List]
