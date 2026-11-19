import time
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.models import (
    AnalysisResponse,
    CustomIngredientsRequest,
    ProductData,
    NutrientInfo,
)
from app.services.barcode_service import fetch_product_by_barcode, DEMO_PRODUCTS_FALLBACK
from app.services.ai_analyzer import evaluate_product_with_ai

BASE_PATH = Path(__file__).resolve().parent.parent

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="PoC-вебсервіс для аналізу складу харчових продуктів за штрихкодом та оцінки корисності за допомогою Google Gemini API та Open Food Facts API.",
)

app.mount("/static", StaticFiles(directory=str(BASE_PATH / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_PATH / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    samples = [
        {"barcode": p.barcode, "name": p.name, "brand": p.brand}
        for p in DEMO_PRODUCTS_FALLBACK.values()
    ]
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.app_name,
            "samples": samples,
            "gemini_configured": bool(
                settings.gemini_api_key
                and settings.gemini_api_key != "your_google_gemini_api_key_here"
            ),
        },
    )


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "gemini_model": settings.gemini_model,
        "gemini_api_key_configured": bool(
            settings.gemini_api_key
            and settings.gemini_api_key != "your_google_gemini_api_key_here"
        ),
    }


@app.get("/api/analyze/{barcode}", response_model=AnalysisResponse)
async def analyze_barcode(barcode: str):
    t0 = time.perf_counter()
    product = await fetch_product_by_barcode(barcode)
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Продукт зі штрихкодом '{barcode}' не знайдено у базі Open Food Facts. Спробуйте інший код або ручний аналіз складу.",
        )

    evaluation = await evaluate_product_with_ai(product)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    return AnalysisResponse(
        product=product,
        evaluation=evaluation,
        api_metadata={
            "cloud_platform": "Google Cloud Platform (Generative Language / Gemini API)",
            "data_provider": product.source,
            "processing_time_ms": elapsed_ms,
        },
    )


@app.post("/api/analyze-custom", response_model=AnalysisResponse)
async def analyze_custom_ingredients(payload: CustomIngredientsRequest):
    t0 = time.perf_counter()
    product = ProductData(
        barcode="CUSTOM-INPUT",
        name=payload.product_name,
        brand="Користувацький ввід",
        categories="Ручна перевірка етикетки",
        ingredients_text=payload.ingredients_text,
        nutrients=NutrientInfo(
            sugars_g=payload.sugars_g,
            salt_g=payload.salt_g,
            saturated_fats_g=payload.saturated_fats_g,
            proteins_g=payload.proteins_g,
        ),
        source="Ручне введення складу користувачем",
    )
    evaluation = await evaluate_product_with_ai(product)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    return AnalysisResponse(
        product=product,
        evaluation=evaluation,
        api_metadata={
            "cloud_platform": "Google Cloud Platform (Generative Language / Gemini API)",
            "data_provider": "Manual Label Input",
            "processing_time_ms": elapsed_ms,
        },
    )
