import json
import re
import httpx
from typing import List
from app.config import settings
from app.models import ProductData, AIHealthEvaluation, AdditiveAssessment

KNOWN_ADDITIVES = {
    "e150d": ("E150d", "Цукровий колер IV (аміачно-сульфітний)", "moderate", "Синтетичний барвник; у великих дозах небажаний для дітей."),
    "e250": ("E250", "Нітрит натрію", "high", "Консервант і фіксатор кольору в м'ясних виробах; при надмірному споживанні утворює нітрозаміни."),
    "e290": ("E290", "Діоксид вуглецю", "low", "Безпечний газ для газування напоїв."),
    "e322": ("E322", "Лецитини (соєвий/соняшниковий)", "low", "Природний емульгатор, безпечний (увага при алергії на сою)."),
    "e330": ("E330", "Лимонна кислота", "low", "Природний антиоксидант і регулятор кислотності."),
    "e338": ("E338", "Ортофосфорна кислота", "moderate", "Регулятор кислотності; надлишок погіршує засвоєння кальцію."),
    "e500": ("E500", "Карбонати натрію (харчова сода)", "low", "Безпечний розпушувач тіста."),
    "e501": ("E501", "Карбонати калію", "low", "Безпечний розпушувач та стабілізатор."),
    "e503": ("E503", "Карбонати амонію", "low", "Безпечний розпушувач у випічці."),
    "e621": ("E621", "Глутамат натрію", "moderate", "Підсилювач смаку; може стимулювати переїдання ультраобробленої їжі."),
    "e951": ("E951", "Аспартам", "moderate", "Штучний підсолоджувач; протипоказаний при фенілкетонурії."),
}


def _extract_additives(product: ProductData) -> List[AdditiveAssessment]:
    found_codes = set()
    for tag in product.additives_tags:
        code = tag.split(":")[-1].lower().strip()
        found_codes.add(code)

    for match in re.findall(r"\b[eEеЕ][-\s]?(\d{3}[a-zA-Z]?)\b", product.ingredients_text):
        found_codes.add(f"e{match.lower()}")

    results: List[AdditiveAssessment] = []
    for code in sorted(found_codes):
        if code in KNOWN_ADDITIVES:
            c, name, risk, desc = KNOWN_ADDITIVES[code]
            results.append(AdditiveAssessment(code=c, name=name, risk_level=risk, description=desc))
        else:
            results.append(
                AdditiveAssessment(
                    code=code.upper(),
                    name=f"Харчова добавка {code.upper()}",
                    risk_level="moderate",
                    description="Технологічна харчова добавка. Рекомендується помірне споживання.",
                )
            )
    return results


def _rule_based_fallback_evaluation(product: ProductData, reason: str) -> AIHealthEvaluation:
    """Резервний алгоритмічний аналіз за критеріями ВООЗ / Nutri-Score / NOVA."""
    score = 72
    pros: List[str] = []
    cons: List[str] = []
    n = product.nutrients

    if n.sugars_g is not None:
        if n.sugars_g > 22.5:
            score -= 22
            cons.append(f"Високий вміст цукрів ({n.sugars_g} г на 100 г — перевищує норму ВООЗ).")
        elif n.sugars_g > 10.0:
            score -= 10
            cons.append(f"Підвищений вміст цукрів ({n.sugars_g} г на 100 г).")
        elif n.sugars_g <= 5.0:
            score += 6
            pros.append(f"Низький вміст цукрів ({n.sugars_g} г на 100 г).")

    if n.saturated_fats_g is not None:
        if n.saturated_fats_g > 5.0:
            score -= 15
            cons.append(f"Високий вміст насичених жирів ({n.saturated_fats_g} г на 100 г).")
        elif n.saturated_fats_g <= 1.5:
            score += 5
            pros.append("Мінімальна кількість насичених жирів.")

    if n.salt_g is not None:
        if n.salt_g > 1.5:
            score -= 14
            cons.append(f"Надлишок солі ({n.salt_g} г на 100 г).")
        elif n.salt_g <= 0.3:
            score += 4
            pros.append("Низький вміст солі.")

    if n.fiber_g is not None and n.fiber_g >= 5.0:
        score += 10
        pros.append(f"Високий вміст харчових волокон/клітковини ({n.fiber_g} г на 100 г).")

    if n.proteins_g is not None and n.proteins_g >= 8.0:
        score += 7
        pros.append(f"Хороше джерело білка ({n.proteins_g} г на 100 г).")

    if product.nova_group == 4:
        score -= 12
        cons.append("Ультраоброблений продукт (група NOVA 4).")
    elif product.nova_group in (1, 2):
        score += 8
        pros.append("Мінімальний ступінь промислової обробки (NOVA 1–2).")

    if "пальмова олія" in product.ingredients_text.lower() or "palm oil" in product.ingredients_text.lower():
        score -= 8
        cons.append("Містить пальмову олію, багату на насичені жирні кислоти.")

    additives = _extract_additives(product)
    high_risk = [a for a in additives if a.risk_level == "high"]
    if high_risk:
        score -= 12 * len(high_risk)
        cons.append(f"Виявлено добавки підвищеного ризику: {', '.join(a.code for a in high_risk)}.")

    if not pros:
        pros.append("Продукт забезпечує швидке поповнення енергії за потреби.")
    if not cons:
        cons.append("Суттєвих нутриціологічних ризиків у складі не виявлено.")

    score = max(5, min(98, score))

    if score >= 70:
        badge = "Корисний вибір"
        rec = "Продукт підходить для регулярного збалансованого раціону."
    elif score >= 45:
        badge = "Помірне споживання"
        rec = "Вживайте в обмежених порціях та поєднуйте зі свіжими овочами або білком."
    else:
        badge = "Небажаний для частого вживання"
        rec = "Рекомендується обмежити вживання та обрати менш оброблену альтернативу без доданого цукру."

    summary = (
        f"Продукт «{product.name}» отримав {score}/100 балів за нутриціологічним профілем. "
        f"{cons[0] if score < 70 else pros[0]}"
    )

    return AIHealthEvaluation(
        health_score=score,
        verdict_badge=badge,
        summary=summary,
        pros=pros,
        cons=cons,
        additives_analysis=additives,
        recommendation=rec,
        analysis_engine=f"Локальний нутриціологічний рушій ({reason})",
    )


async def evaluate_product_with_ai(product: ProductData) -> AIHealthEvaluation:
    """
    Інтеграція з Google Cloud Generative Language (Gemini) REST API.
    Повертає структуровану JSON-оцінку корисності продукту українською мовою.
    """
    api_key = settings.gemini_api_key.strip()
    if not api_key or api_key == "your_google_gemini_api_key_here":
        return _rule_based_fallback_evaluation(
            product, "ключ GEMINI_API_KEY не задано у .env — працює демо-режим"
        )

    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent?key={api_key}"
    )

    prompt = f"""Ти — професійний нутриціолог та експерт із харчової безпеки.
Проаналізуй склад харчового продукту та оціни його корисність для здоров'я людини.
Відповідь надай виключно українською мовою у форматі суворого JSON.

Дані продукту:
- Назва: {product.name}
- Бренд: {product.brand}
- Категорія: {product.categories}
- Склад (інгредієнти): {product.ingredients_text}
- Алергени: {', '.join(product.allergens) if product.allergens else 'не вказано'}
- Харчові добавки (теги): {', '.join(product.additives_tags) if product.additives_tags else 'немає'}
- Nutri-Score: {product.nutriscore_grade or 'невідомо'}, NOVA група: {product.nova_group or 'невідомо'}
- Поживна цінність на 100 г: {product.nutrients.model_dump_json()}

Поверни JSON такої структури:
{{
  "health_score": <ціле число від 0 до 100>,
  "verdict_badge": "<одне з: Корисний вибір | Помірне споживання | Небажаний для частого вживання>",
  "summary": "<2-3 речення стислого експертного висновку>",
  "pros": ["<перевага 1>", "<перевага 2>"],
  "cons": ["<недолік або ризик 1>", "<недолік 2>"],
  "additives_analysis": [
    {{
      "code": "E...",
      "name": "<назва добавки>",
      "risk_level": "<low | moderate | high>",
      "description": "<коротке пояснення впливу>"
    }}
  ],
  "recommendation": "<конкретна порада споживачу щодо вживання або заміни>"
}}"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
            if response.status_code != 200:
                return _rule_based_fallback_evaluation(
                    product, f"HTTP {response.status_code} від Gemini API"
                )

            data = response.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(raw_text)

            additives = [
                AdditiveAssessment(**item)
                for item in parsed.get("additives_analysis", [])
            ]
            if not additives:
                additives = _extract_additives(product)

            return AIHealthEvaluation(
                health_score=max(0, min(100, int(parsed.get("health_score", 50)))),
                verdict_badge=parsed.get("verdict_badge", "Помірне споживання"),
                summary=parsed.get("summary", "Аналіз виконано моделлю Gemini."),
                pros=parsed.get("pros", []),
                cons=parsed.get("cons", []),
                additives_analysis=additives,
                recommendation=parsed.get("recommendation", "Дотримуйтесь збалансованого раціону."),
                analysis_engine=f"Google Cloud / Gemini API ({settings.gemini_model})",
            )
    except Exception as exc:
        return _rule_based_fallback_evaluation(product, f"резерв після помилки API: {type(exc).__name__}")
