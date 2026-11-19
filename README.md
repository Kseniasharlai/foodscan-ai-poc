# FoodScan AI — Вебсервіс для аналізу складу харчових продуктів за штрихкодом та оцінки їхньої корисності

**Proof of Concept (PoC)** вебсервіс на базі **Python (FastAPI)**, що інтегрує:
1. **Google Cloud Platform — Generative Language (Gemini) API** (`gemini-2.5-flash`) для інтелектуального нутриціологічного аналізу інгредієнтів, виявлення ризиків харчових добавок (E-кодів) та формування персоналізованих рекомендацій.
2. **Open Food Facts REST API v2** для отримання інформації про харчовий продукт, його склад, поживну цінність, класифікацію **Nutri-Score** та групу обробки **NOVA** за штрихкодом (EAN-13 / UPC).

---

## Структура проєкту

```text
foodscan-ai-poc/
├── app/
│   ├── main.py                  # Головний FastAPI-додаток (Web UI + REST API)
│   ├── config.py                # Конфігурація та змінні середовища
│   ├── models.py                # Pydantic-моделі запитів та відповідей
│   └── services/
│       ├── barcode_service.py   # Інтеграція з Open Food Facts API v2 (+ демо-кеш)
│       └── ai_analyzer.py       # Інтеграція з Google Gemini API (+ алгоритмічний fallback)
├── templates/
│   └── index.html               # Вебінтерфейс користувача
├── static/
│   ├── css/style.css            # Стилізація інтерфейсу
│   └── js/app.js                # Клієнтська логіка взаємодії з API
├── tests/
│   └── test_api.py              # Автоматичні тести (pytest)
├── presentation/
│   ├── FoodScan_AI_Presentation.pptx  # Презентація для захисту семінарської роботи
│   └── SPEAKER_NOTES.md               # Текст доповіді та відповіді на запитання
├── .env.example                 # Шаблон налаштування API-ключа
├── .gitignore                   # Ігнорування .env, .venv, .idea, __pycache__
├── requirements.txt             # Залежності Python
├── run_mac.sh                   # Скрипт швидкого запуску для macOS
└── README.md                    # Документація проєкту
```

---

## Покрокова інструкція запуску у PyCharm на macOS

### Крок 1. Відкриття проєкту в PyCharm
1. Розпакуйте архів `foodscan-ai-poc.zip` у зручну папку (наприклад, `~/Projects/foodscan-ai-poc`).
2. Запустіть **PyCharm** на macOS → **Open** → виберіть папку `foodscan-ai-poc`.
3. PyCharm автоматично запропонує створити віртуальне середовище (`Virtualenv` / `.venv`) на базі Python 3.10+ та встановити пакети з `requirements.txt`. Погодьтеся (**OK**).
   - *Або через вбудований термінал PyCharm (`⌥F12`):*
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     pip install -r requirements.txt
     ```

### Крок 2. Отримання та підключення Google Gemini API Key
1. Перейдіть у **Google Cloud Console** (`https://console.cloud.google.com/apis/library`) та увімкніть **Generative Language API**, або отримайте безкоштовний ключ у **Google AI Studio**: `https://aistudio.google.com/apikey`.
2. Скопіюйте `.env.example` у `.env`:
   ```bash
   cp .env.example .env
   ```
3. Відкрийте `.env` у PyCharm та вставте ваш ключ:
   ```env
   GEMINI_API_KEY=AIzaSy...ваш_ключ...
   GEMINI_MODEL=gemini-2.5-flash
   ```
   > **Примітка:** Якщо ключ не вказано, сервіс автоматично працює у гібридному демо-режимі (використовуючи локальний нутриціологічний рушій), тому демонстрація працюватиме без збоїв у будь-якому разі.

### Крок 3. Запуск вебсервісу
У терміналі PyCharm виконайте:
```bash
uvicorn app.main:app --reload
```
або просто запустіть скрипт:
```bash
./run_mac.sh
```
Після запуску відкрийте у браузері:
- **Вебінтерфейс:** http://127.0.0.1:8000
- **Інтерактивна документація API (Swagger UI):** http://127.0.0.1:8000/docs

### Крок 4. Запуск тестів
```bash
pytest -v
```

---

## Завантаження проєкту на GitHub (через PyCharm або термінал macOS)

1. Створіть новий порожній репозиторій на [github.com](https://github.com/new) з назвою `foodscan-ai-poc` (без додавання README, оскільки він вже є).
2. У терміналі PyCharm виконайте:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: FoodScan AI PoC web service and presentation"
   git branch -M main
   git remote add origin https://github.com/<ВАШ_ЛОГІН>/foodscan-ai-poc.git
   git push -u origin main
   ```
   *(Файл `.env` із секретним ключем автоматично виключено через `.gitignore` і не потрапить у публічний репозиторій).*
