from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class NutrientInfo(BaseModel):
    energy_kcal: Optional[float] = Field(None, description="Калорійність на 100 г (ккал)")
    proteins_g: Optional[float] = Field(None, description="Білки на 100 г (г)")
    fats_g: Optional[float] = Field(None, description="Жири на 100 г (г)")
    saturated_fats_g: Optional[float] = Field(None, description="Насичені жири на 100 г (г)")
    carbohydrates_g: Optional[float] = Field(None, description="Вуглеводи на 100 г (г)")
    sugars_g: Optional[float] = Field(None, description="Цукри на 100 г (г)")
    fiber_g: Optional[float] = Field(None, description="Клітковина на 100 г (г)")
    salt_g: Optional[float] = Field(None, description="Сіль на 100 г (г)")


class AdditiveAssessment(BaseModel):
    code: str
    name: str
    risk_level: str  # "low", "moderate", "high"
    description: str


class ProductData(BaseModel):
    barcode: str
    name: str
    brand: str
    categories: str
    image_url: Optional[str] = None
    ingredients_text: str
    allergens: List[str] = []
    additives_tags: List[str] = []
    nutriscore_grade: Optional[str] = None
    nova_group: Optional[int] = None
    nutrients: NutrientInfo
    source: str = "Open Food Facts API"


class AIHealthEvaluation(BaseModel):
    health_score: int = Field(..., ge=0, le=100, description="Інтегральна оцінка корисності (0-100)")
    verdict_badge: str = Field(..., description="Категорія: Корисний / Помірний / Небажаний")
    summary: str = Field(..., description="Короткий висновок про склад продукту")
    pros: List[str] = Field(default_factory=list, description="Позитивні аспекти складу")
    cons: List[str] = Field(default_factory=list, description="Недоліки та ризики")
    additives_analysis: List[AdditiveAssessment] = Field(default_factory=list)
    recommendation: str = Field(..., description="Практична порада споживачу")
    analysis_engine: str = Field(..., description="Джерело аналізу (Google Gemini API або Fallback)")


class AnalysisResponse(BaseModel):
    product: ProductData
    evaluation: AIHealthEvaluation
    api_metadata: Dict[str, Any] = Field(default_factory=dict)


class CustomIngredientsRequest(BaseModel):
    product_name: str = Field(..., min_length=2, max_length=120)
    ingredients_text: str = Field(..., min_length=3, max_length=2000)
    sugars_g: Optional[float] = 0.0
    salt_g: Optional[float] = 0.0
    saturated_fats_g: Optional[float] = 0.0
    proteins_g: Optional[float] = 0.0
