
# api/schemas.py
from typing import List, Any, Union
from pydantic import BaseModel, HttpUrl, Field, validator

from typing import Optional, Dict
from pydantic import BaseModel

class IngredientItem(BaseModel):
    nama: str
    status: str
    detail: str

class NutritionInfoItem(BaseModel):
    nama: str
    nilai: Union[int, float]
    type: str
    status: str


class NutritionItem(BaseModel):
    nama: str
    nilai: Union[int, float]
    type: str
    status: str
    input: Optional[Any] = None
    data: Dict[str, Any] = Field(default_factory=dict)

# class NutritionItem(BaseModel):
#     nama: Optional[str] = None
#     nilai: Optional[int] = 0
#     input: Optional[str] = None
#     type: Optional[str] = None
#     data: Optional[Dict[str, str]] = None  # <<< ini untuk nyimpan dict asli


class RecommendationResponse(BaseModel):
    nama: Optional[str]
    status: str
    data: List[dict]
    detail: Optional[str] = None


class AnalyzeRequest(BaseModel):
    composition: HttpUrl
    nutrition_info: HttpUrl

class AnalyzeResponse(BaseModel):
    status: str
    data: Dict[str, List]


class RecognitionFoodRequest(BaseModel):
    foods: HttpUrl

class RecognitionFoodResponse(BaseModel):
    status: str
    foods_detected: List[str]



class RawIngredient(BaseModel):
    nama: str
    status: str
    detail: str

class RawNutritionInfo(BaseModel):
    nama: str
    nilai: Union[int, float, str]
    type: str
    status: str
    data: Optional[Dict[str, Any]] = None  # no longer required

    # if downstream logic needs nilai as string, coerce here:
    @validator("nilai", pre=True)
    def coerce_nilai_to_str(cls, v):
        return str(v)


class MakeSummaryFoodRequest(BaseModel):
    ingredients: List[RawIngredient]
    nutrition_info: List[RawNutritionInfo]


class MakeSummaryFoodResponse(BaseModel):
    ingredients: List[str]
    nutrition_info: List[str]


class MakeRecommendationRequest(BaseModel):
    name: str
    status: str
    detail: str
    ingredients: List[IngredientItem]
    nutrition_info: List[NutritionInfoItem]

class RecommendationDataItem(BaseModel):
    name: str
    status: str
    detail: str
    ingredients: List[IngredientItem]
    nutrition_info: List[NutritionInfoItem]

class RecommendationResponse(BaseModel):
    status: str
    data: List[RecommendationDataItem]