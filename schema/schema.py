
# api/schemas.py
from typing import List, Any, Union
from pydantic import BaseModel, HttpUrl, Field, validator

from typing import Optional, Dict
from pydantic import BaseModel


class NutritionInfoItem(BaseModel):
    nama: str
    nilai: Union[int, float]
    type: str
    status: str

class AnalyzeRequest(BaseModel):
    session_id: str
    nutrition_info: HttpUrl

class AnalyzeResponse(BaseModel):
    status: str
    data: Dict[str, List]
