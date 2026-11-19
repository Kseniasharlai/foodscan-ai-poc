import httpx
from typing import Dict, Optional
from app.config import settings
from app.models import ProductData, NutrientInfo

DEMO_PRODUCTS_FALLBACK: Dict[str, ProductData] = {
    "3017620422003": ProductData(
        barcode="3017620422003",
        name="Nutella — Горіхова паста з какао",
        brand="Ferrero",
        categories="Солодкі пасти, Шоколадно-горіхові пасти",
        image_url="https://images.openfoodfacts.org/images/products/301/762/042/2003/front_en.633.400.jpg",
        ingredients_text="Цукор, пальмова олія, фундук (13%), сухе знежирене молоко (8.7%), знежирений какао-порошок (7.4%), емульгатор: лецитини (соєві) (E322), ванілін.",
        allergens=["Горіхи (фундук)", "Молоко", "Соя"],
        additives_tags=["en:e322"],
        nutriscore_grade="e",
        nova_group=4,
        nutrients=NutrientInfo(
            energy_kcal=539.0,
            proteins_g=6.3,
            fats_g=30.9,
            saturated_fats_g=10.6,
            carbohydrates_g=57.5,
            sugars_g=56.3,
            fiber_g=3.4,
            salt_g=0.107,
        ),
        source="Open Food Facts (Demo Cache)",
    ),
    "5449000000996": ProductData(
        barcode="5449000000996",
        name="Coca-Cola Classic",
        brand="The Coca-Cola Company",
        categories="Газовані безалкогольні напої, Солодкі напої",
        image_url="https://images.openfoodfacts.org/images/products/544/900/000/0996/front_en.891.400.jpg",
        ingredients_text="Вода питна підготовлена, цукор, діоксид вуглецю (E290), барвник цукровий колер IV (E150d), регулятор кислотності ортофосфорна кислота (E338), натуральні ароматизатори, кофеїн.",
        allergens=[],
        additives_tags=["en:e290", "en:e150d", "en:e338"],
        nutriscore_grade="e",
        nova_group=4,
        nutrients=NutrientInfo(
            energy_kcal=42.0,
            proteins_g=0.0,
            fats_g=0.0,
            saturated_fats_g=0.0,
            carbohydrates_g=10.6,
            sugars_g=10.6,
            fiber_g=0.0,
            salt_g=0.0,
        ),
        source="Open Food Facts (Demo Cache)",
    ),
    "3228857000906": ProductData(
        barcode="3228857000906",
        name="Хліб цільнозерновий з насінням",
        brand="Harry's / Pain Complet",
        categories="Хлібобулочні вироби, Цільнозерновий хліб",
        image_url=None,
        ingredients_text="Цільнозернове пшеничне борошно (62%), вода питна, насіння льону та соняшнику (8%), закваска житня, дріжджі хлібопекарські, олія ріпакова, сіль морська (1.1%).",
        allergens=["Глютен (пшениця, жито)"],
        additives_tags=[],
        nutriscore_grade="a",
        nova_group=3,
        nutrients=NutrientInfo(
            energy_kcal=248.0,
            proteins_g=9.4,
            fats_g=4.2,
            saturated_fats_g=0.6,
            carbohydrates_g=41.0,
            sugars_g=2.8,
            fiber_g=7.5,
            salt_g=1.1,
        ),
        source="Open Food Facts (Demo Cache)",
    ),
    "7622210449283": ProductData(
        barcode="7622210449283",
        name="Печиво сендвіч Oreo Original",
        brand="Mondelez International",
        categories="Солодке печиво, Кондитерські вироби",
        image_url=None,
        ingredients_text="Борошно пшеничне, цукор, олія пальмова, олія ріпакова, какао-порошок зі зниженим вмістом жиру (4.5%), крохмаль пшеничний, глюкозно-фруктозний сироп, розпушувачі (E500, E501, E503), сіль, емульгатор (соєвий лецитин E322), ароматизатор ванілін.",
        allergens=["Глютен (пшениця)", "Соя"],
        additives_tags=["en:e500", "en:e501", "en:e503", "en:e322"],
        nutriscore_grade="d",
        nova_group=4,
        nutrients=NutrientInfo(
            energy_kcal=474.0,
            proteins_g=5.0,
            fats_g=19.0,
            saturated_fats_g=5.4,
            carbohydrates_g=69.0,
            sugars_g=38.0,
            fiber_g=2.7,
            salt_g=0.73,
        ),
        source="Open Food Facts (Demo Cache)",
    ),
}


def _safe_float(nutriments: dict, key: str) -> Optional[float]:
    val = nutriments.get(key)
    if val is None:
        return None
    try:
        return round(float(val), 2)
    except (ValueError, TypeError):
        return None


async def fetch_product_by_barcode(barcode: str) -> Optional[ProductData]:
    clean_barcode = "".join(ch for ch in barcode.strip() if ch.isdigit())
    if not clean_barcode:
        return None

    url = f"{settings.openfoodfacts_base_url}/{clean_barcode}.json"
    headers = {
        "User-Agent": "FoodScanAI-UniversityPoC/1.0 (https://github.com/student/foodscan-ai-poc)"
    }

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                payload = resp.json()
                if payload.get("status") == 1 and "product" in payload:
                    p = payload["product"]
                    nutr = p.get("nutriments", {})

                    ingredients = (
                        p.get("ingredients_text_uk")
                        or p.get("ingredients_text_en")
                        or p.get("ingredients_text")
                        or "Склад не вказано виробником у відкритій базі."
                    )
                    name = (
                        p.get("product_name_uk")
                        or p.get("product_name_en")
                        or p.get("product_name")
                        or f"Продукт #{clean_barcode}"
                    )
                    allergens_raw = p.get("allergens_tags", [])
                    allergens = [
                        a.split(":")[-1].replace("-", " ").capitalize()
                        for a in allergens_raw
                    ]
                    nova = p.get("nova_group")
                    try:
                        nova = int(nova) if nova is not None else None
                    except (ValueError, TypeError):
                        nova = None

                    return ProductData(
                        barcode=clean_barcode,
                        name=name,
                        brand=p.get("brands", "Невідомий бренд"),
                        categories=p.get("categories", "Харчові продукти"),
                        image_url=p.get("image_front_small_url") or p.get("image_url"),
                        ingredients_text=ingredients,
                        allergens=allergens,
                        additives_tags=p.get("additives_tags", []),
                        nutriscore_grade=(p.get("nutriscore_grade") or "").lower() or None,
                        nova_group=nova,
                        nutrients=NutrientInfo(
                            energy_kcal=_safe_float(nutr, "energy-kcal_100g"),
                            proteins_g=_safe_float(nutr, "proteins_100g"),
                            fats_g=_safe_float(nutr, "fat_100g"),
                            saturated_fats_g=_safe_float(nutr, "saturated-fat_100g"),
                            carbohydrates_g=_safe_float(nutr, "carbohydrates_100g"),
                            sugars_g=_safe_float(nutr, "sugars_100g"),
                            fiber_g=_safe_float(nutr, "fiber_100g"),
                            salt_g=_safe_float(nutr, "salt_100g"),
                        ),
                        source="Open Food Facts REST API v2",
                    )
    except httpx.HTTPError:
        pass

    return DEMO_PRODUCTS_FALLBACK.get(clean_barcode)
