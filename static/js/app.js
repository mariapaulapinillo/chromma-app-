let questionnaire = null;
let flatQuestions = [];
let currentIndex = 0;
let userAnswers = {};

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('btn-start').addEventListener('click', startQuiz);
    document.getElementById('btn-next').addEventListener('click', nextPage);
    document.getElementById('btn-prev').addEventListener('click', prevPage);
});

async function startQuiz() {
    try {
        const response = await fetch('/api/questionnaire');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        questionnaire = await response.json();

        // Unificar las 3 secciones en una sola lista plana para navegación
        flatQuestions = [
            ...questionnaire.section_1_colorimetry.map(q => ({ ...q, section: 'Sección 1: Colorimetría' })),
            ...questionnaire.section_2_skin_type.map(q => ({ ...q, section: 'Sección 2: Tipo de Piel' })),
            ...questionnaire.section_3_preferences.map(q => ({ ...q, section: 'Sección 3: Preferencias' }))
        ];

        document.getElementById('intro-screen').classList.add('hidden');
        document.getElementById('quiz-screen').classList.remove('hidden');

        renderQuestion();
    } catch (error) {
        alert("Error al cargar el cuestionario. Verifica que el servidor Flask esté activo.");
    }
}

function renderQuestion() {
    const q = flatQuestions[currentIndex];
    const total = flatQuestions.length;

    // Barra de progreso: 0% al inicio, 100% con las 27 respondidas
    const answered = flatQuestions.filter(item => userAnswers[item.id]).length;
    document.getElementById('progress-bar').style.width = `${(answered / total) * 100}%`;
    document.getElementById('section-title').textContent = q.section;
    document.getElementById('question-counter').textContent = `Pregunta ${currentIndex + 1} de ${total}`;

    // Las opciones se construyen con DOM (textContent) para no interpretar el texto como HTML
    const container = document.getElementById('question-container');
    container.replaceChildren();

    const title = document.createElement('h2');
    title.textContent = q.q;
    container.appendChild(title);

    if (q.has_visual_aid) {
        container.appendChild(buildVeinsAid(q));
    }

    const grid = document.createElement('div');
    grid.className = 'options-grid';
    q.options.forEach(opt => {
        const card = document.createElement('div');
        card.className = 'option-card' + (userAnswers[q.id] === opt ? ' selected' : '');
        card.textContent = opt;
        card.tabIndex = 0;
        card.setAttribute('role', 'button');
        card.addEventListener('click', () => selectOption(q.id, opt));
        card.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                selectOption(q.id, opt);
            }
        });
        grid.appendChild(card);
    });
    container.appendChild(grid);

    // Botones de navegación
    document.getElementById('btn-prev').classList.toggle('hidden', currentIndex === 0);
    document.getElementById('btn-next').textContent = currentIndex === total - 1 ? 'Ver Resultados' : 'Siguiente';
    document.getElementById('btn-next').disabled = !userAnswers[q.id];
}

// Apoyo visual Q3: tarjetas clicables que seleccionan la opción equivalente
function buildVeinsAid(q) {
    const aid = document.createElement('div');
    aid.className = 'veins-visual-aid';

    const boxes = [
        { cls: 'cool', title: 'Frías (Azul/Violeta)', sub: 'Subtono Frío', option: q.options[0] },
        { cls: 'warm', title: 'Cálidas (Verde/Oliva)', sub: 'Subtono Cálido', option: q.options[1] }
    ];
    boxes.forEach(b => {
        const box = document.createElement('div');
        box.className = `vein-box ${b.cls}`;
        box.tabIndex = 0;
        box.setAttribute('role', 'button');
        box.innerHTML = '<div class="vein-lines"><i></i><i></i><i></i></div>';
        const strong = document.createElement('strong');
        strong.textContent = b.title;
        box.append(strong, document.createElement('br'), b.sub);
        box.addEventListener('click', () => selectOption(q.id, b.option));
        box.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                selectOption(q.id, b.option);
            }
        });
        aid.appendChild(box);
    });

    const hint = document.createElement('p');
    hint.className = 'vein-hint';
    hint.textContent = 'Observa tu muñeca con luz natural. Toca el ejemplo que más se parezca o elige abajo.';
    aid.appendChild(hint);
    return aid;
}

function selectOption(questionId, selectedValue) {
    userAnswers[questionId] = selectedValue;
    renderQuestion();
}

function nextPage() {
    if (currentIndex < flatQuestions.length - 1) {
        currentIndex++;
        renderQuestion();
    } else {
        submitQuiz();
    }
}

function prevPage() {
    if (currentIndex > 0) {
        currentIndex--;
        renderQuestion();
    }
}

function backToQuiz(message) {
    document.getElementById('loading-screen').classList.add('hidden');
    document.getElementById('quiz-screen').classList.remove('hidden');
    const banner = document.createElement('div');
    banner.className = 'error-banner';
    banner.textContent = message;
    document.getElementById('question-container').prepend(banner);
}

async function submitQuiz() {
    document.getElementById('quiz-screen').classList.add('hidden');
    document.getElementById('loading-screen').classList.remove('hidden');

    try {
        const response = await fetch('/api/diagnose', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userAnswers)
        });

        const data = await response.json();
        if (response.ok && data.success) {
            window.diagnosticResult = data;
            document.getElementById('loading-screen').classList.add('hidden');
            document.getElementById('results-screen').classList.remove('hidden');
            renderResults(data);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
            backToQuiz('Error: ' + (data.error || 'respuesta inesperada del servidor'));
        }
    } catch (err) {
        backToQuiz('Error al conectar con la API.');
    }
}

// ---------- Dashboard de resultados (Sprint 4) ----------

// Todo texto que viene de la API se escapa antes de insertarse como HTML
function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, c => (
        { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
}

// Solo se aceptan colores #RRGGBB para usarlos en estilos
function safeHex(value) {
    return /^#[0-9a-fA-F]{6}$/.test(value) ? value : '#cccccc';
}

function renderResults(data) {
    const { colorimetry, recommendations } = data;
    const resultsContainer = document.getElementById('results-screen');

    const jewelry = colorimetry.jewelry || {};
    const clothing = colorimetry.clothing || { best: [], avoid: [] };
    const isWarm = colorimetry.temperature === 'Cálida';
    const bestMetals = isWarm ? '✨ Metales Cálidos' : '❄️ Metales Fríos';
    const chips = (items, cls) => items.map(i => `<span class="chip ${cls}">${esc(i)}</span>`).join('');

    const paletteHTML = colorimetry.palette.map(hex => `
        <button type="button" class="color-swatch-item" data-hex="${esc(safeHex(hex))}" title="Copiar ${esc(hex)}">
            <span class="swatch-circle" style="background-color: ${safeHex(hex)};"></span>
            <span class="swatch-hex">${esc(hex)}</span>
        </button>
    `).join('');

    let productsHTML;
    if (recommendations && recommendations.length > 0) {
        productsHTML = recommendations.map(prod => `
            <div class="product-card">
                <div class="product-img-container" style="--fallback: ${safeHex(prod.hex_color)};">
                    <img src="${esc(prod.image_url)}" alt="${esc(prod.name)}" class="product-img" loading="lazy"/>
                    <span class="badge-category">${esc(prod.category)}</span>
                </div>
                <div class="product-details">
                    <span class="product-brand">${esc(prod.brand)}</span>
                    <h4 class="product-name">${esc(prod.name)}</h4>
                    <div class="product-shade">
                        <span class="shade-dot" style="background-color: ${safeHex(prod.hex_color)};"></span>
                        <span>${esc(prod.shade_name)} <small>${esc(prod.hex_color)}</small></span>
                    </div>
                    <div class="product-tags">
                        <span class="tag">${esc(prod.finish)}</span>
                        <span class="tag">Piel ${esc(prod.skin_type)}</span>
                    </div>
                    <div class="product-price">${esc(prod.price_formatted)}</div>
                </div>
            </div>
        `).join('');
    } else {
        productsHTML = '<p class="no-products">No se encontraron productos exactos para estos filtros. Intenta ajustar tu presupuesto o tipo de piel.</p>';
    }

    resultsContainer.innerHTML = `
        <div class="card result-header-card">
            <span class="season-badge">${esc(colorimetry.temperature)}</span>
            <h1 class="season-title">Tu Estación: <span>${esc(colorimetry.season)}</span></h1>
            <p class="confidence-text">Certeza del diagnóstico: <strong>${esc(colorimetry.confidence_score)}%</strong></p>
            <p class="season-desc">${esc(colorimetry.palette_description || 'Tu armonía cromática resalta tus rasgos naturales con equilibrio perfecto.')}</p>
            <p class="result-meta">Subtono <strong>${esc(colorimetry.subtone)}</strong> · Contraste <strong>${esc(colorimetry.contrast)}</strong> · ${esc(colorimetry.value)} y ${esc(colorimetry.chroma)}</p>

            <hr class="divider">

            <div class="result-details-grid">
                <div class="detail-box">
                    <h3>🎨 Tu Paleta de Colores</h3>
                    <div class="palette-swatches-grid">${paletteHTML}</div>
                    <p class="swatch-feedback" id="swatch-feedback" aria-live="polite">Toca un color para copiar su código.</p>
                </div>
                <div class="detail-box">
                    <h3>💍 Joyería y Accesorios</h3>
                    <p><strong>${bestMetals}:</strong> Te favorecen ${esc(jewelry.metals || '')}.</p>
                    <p><strong>Mejor evitar:</strong> ${esc(jewelry.avoid || '')}.</p>
                    <h3>👗 Ropa</h3>
                    <p class="chip-label">Colores estrella</p>
                    <div class="chip-row">${chips(clothing.best, 'chip-best')}</div>
                    <p class="chip-label">Colores a evitar</p>
                    <div class="chip-row">${chips(clothing.avoid, 'chip-avoid')}</div>
                </div>
            </div>

            <div class="text-center mt-3">
                <button type="button" id="btn-restart" class="btn-secondary">Repetir Test</button>
            </div>
        </div>

        <div class="recommendations-section">
            <h2>💄 Productos Recomendados Para Ti</h2>
            <p class="sub-heading">Seleccionados según tu estación (${esc(colorimetry.season)}), tipo de piel y presupuesto. ${recommendations ? recommendations.length : 0} resultado(s).</p>
            <div class="products-grid">${productsHTML}</div>
        </div>
    `;

    document.getElementById('btn-restart').addEventListener('click', () => location.reload());

    resultsContainer.querySelectorAll('.color-swatch-item').forEach(btn => {
        btn.addEventListener('click', async () => {
            const hex = btn.dataset.hex;
            let msg = `Color ${hex}`;
            try {
                await navigator.clipboard.writeText(hex);
                msg = `${hex} copiado`;
            } catch (e) { /* sin permiso de portapapeles: solo se muestra el código */ }
            document.getElementById('swatch-feedback').textContent = msg;
        });
    });

    // Si la imagen no carga, el contenedor muestra el color del tono
    resultsContainer.querySelectorAll('.product-img').forEach(img => {
        img.addEventListener('error', () => {
            img.remove();
        });
    });
}
