document.addEventListener("DOMContentLoaded", () => {
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById(btn.dataset.tab).classList.add("active");
        });
    });

    const barcodeForm = document.getElementById("barcode-form");
    const barcodeInput = document.getElementById("barcode-input");
    const customForm = document.getElementById("custom-form");
    const loader = document.getElementById("loader");
    const errorBox = document.getElementById("error-box");
    const resultSection = document.getElementById("result-section");

    document.querySelectorAll(".sample-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            barcodeInput.value = chip.dataset.barcode;
            runBarcodeAnalysis(chip.dataset.barcode);
        });
    });

    barcodeForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const code = barcodeInput.value.trim();
        if (code) runBarcodeAnalysis(code);
    });

    customForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        showLoading();
        const payload = {
            product_name: document.getElementById("custom-name").value.trim(),
            ingredients_text: document.getElementById("custom-ingredients").value.trim(),
            sugars_g: parseFloat(document.getElementById("custom-sugars").value) || 0,
            saturated_fats_g: parseFloat(document.getElementById("custom-satfat").value) || 0,
            salt_g: parseFloat(document.getElementById("custom-salt").value) || 0,
            proteins_g: parseFloat(document.getElementById("custom-proteins").value) || 0
        };

        try {
            const res = await fetch("/api/analyze-custom", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Помилка аналізу");
            renderResult(data);
        } catch (err) {
            showError(err.message);
        }
    });

    async function runBarcodeAnalysis(barcode) {
        showLoading();
        try {
            const res = await fetch(`/api/analyze/${encodeURIComponent(barcode)}`);
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Продукт не знайдено");
            renderResult(data);
        } catch (err) {
            showError(err.message);
        }
    }

    function showLoading() {
        loader.classList.remove("hidden");
        errorBox.classList.add("hidden");
        resultSection.classList.add("hidden");
    }

    function showError(msg) {
        loader.classList.add("hidden");
        errorBox.textContent = msg;
        errorBox.classList.remove("hidden");
    }

    function renderResult(data) {
        loader.classList.add("hidden");
        errorBox.classList.add("hidden");
        resultSection.classList.remove("hidden");

        const { product, evaluation, api_metadata } = data;

        const imgEl = document.getElementById("prod-img");
        if (product.image_url) {
            imgEl.src = product.image_url;
            imgEl.classList.remove("hidden");
        } else {
            imgEl.classList.add("hidden");
        }

        document.getElementById("prod-barcode").textContent = `Штрихкод: ${product.barcode}`;
        document.getElementById("prod-name").textContent = product.name;
        document.getElementById("prod-brand").textContent = `${product.brand} • ${product.categories}`;

        const nutriBadge = document.getElementById("nutriscore-badge");
        nutriBadge.textContent = product.nutriscore_grade
            ? `Nutri-Score: ${product.nutriscore_grade.toUpperCase()}`
            : "Nutri-Score: н/д";

        const novaBadge = document.getElementById("nova-badge");
        novaBadge.textContent = product.nova_group
            ? `NOVA група: ${product.nova_group}`
            : "NOVA: н/д";

        const scoreCircle = document.getElementById("score-circle");
        scoreCircle.className = "score-circle " + (
            evaluation.health_score >= 70 ? "score-good" :
            evaluation.health_score >= 45 ? "score-warn" : "score-bad"
        );
        document.getElementById("health-score").textContent = evaluation.health_score;
        document.getElementById("verdict-badge").textContent = evaluation.verdict_badge;
        document.getElementById("ai-summary").textContent = evaluation.summary;
        document.getElementById("prod-ingredients").textContent = product.ingredients_text;

        const allergensBox = document.getElementById("allergens-box");
        if (product.allergens && product.allergens.length > 0) {
            document.getElementById("prod-allergens").textContent = product.allergens.join(", ");
            allergensBox.classList.remove("hidden");
        } else {
            allergensBox.classList.add("hidden");
        }

        const n = product.nutrients || {};
        const macroMap = [
            ["Калорії", n.energy_kcal != null ? `${n.energy_kcal} ккал` : "—"],
            ["Білки", n.proteins_g != null ? `${n.proteins_g} г` : "—"],
            ["Жири", n.fats_g != null ? `${n.fats_g} г` : "—"],
            ["Насич. жири", n.saturated_fats_g != null ? `${n.saturated_fats_g} г` : "—"],
            ["Вуглеводи", n.carbohydrates_g != null ? `${n.carbohydrates_g} г` : "—"],
            ["Цукри", n.sugars_g != null ? `${n.sugars_g} г` : "—"],
            ["Клітковина", n.fiber_g != null ? `${n.fiber_g} г` : "—"],
            ["Сіль", n.salt_g != null ? `${n.salt_g} г` : "—"]
        ];
        document.getElementById("nutrients-grid").innerHTML = macroMap
            .map(([label, val]) => `<div class="nutrient-item"><strong>${val}</strong><span>${label}</span></div>`)
            .join("");

        document.getElementById("pros-list").innerHTML = evaluation.pros
            .map(item => `<li>${item}</li>`).join("");
        document.getElementById("cons-list").innerHTML = evaluation.cons
            .map(item => `<li>${item}</li>`).join("");

        const addList = document.getElementById("additives-list");
        if (evaluation.additives_analysis && evaluation.additives_analysis.length > 0) {
            addList.innerHTML = evaluation.additives_analysis.map(a => `
                <div class="additive-item risk-${a.risk_level}">
                    <div><strong>${a.code}</strong> — ${a.name}<br><span class="muted">${a.description}</span></div>
                </div>
            `).join("");
        } else {
            addList.innerHTML = `<span class="muted">Штучних харчових добавок (E-кодів) не виявлено.</span>`;
        }

        document.getElementById("ai-recommendation").textContent = evaluation.recommendation;
        document.getElementById("api-meta").textContent =
            `Джерело даних: ${api_metadata.data_provider} | Аналізатор: ${evaluation.analysis_engine} | Час відповіді: ${api_metadata.processing_time_ms} мс`;
    }
});
