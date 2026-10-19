let questionnaire = null;
let flatQuestions = [];
let currentIndex = 0;
let userAnswers = {};

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('btn-start').addEventListener('click', startQuiz);
    document.getElementById('btn-next').addEventListener('click', nextPage);
    document.getElementById('btn-prev').addEventListener('click', prevPage);
    initTools();
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
                    ${badgesHTML(prod.badges)}
                    <div class="product-price">${esc(prod.price_formatted)}</div>
                    ${prod.is_high_end ? `<button type="button" class="btn-dupe" data-dupe-id="${esc(prod.id)}">🔍 Buscar Dupe Económico</button>` : ''}
                    <div class="availability">Disponible en: ${(prod.is_high_end ? ['Falabella Unicentro', 'Blush Bar', 'Medipiel'] : ['Falabella Unicentro', 'Blush Bar', 'Medipiel', 'Farmatodo']).map(n => `<span class="chip">${n}</span>`).join('')}</div>
                    <details class="store-details" data-product-id="${esc(prod.id)}">
                        <summary>📍 Disponible en Tiendas Cercanas</summary>
                        <div class="store-body"><p class="store-hint">Cargando tiendas…</p></div>
                    </details>
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

    resultsContainer.querySelectorAll('.btn-dupe').forEach(btn => {
        btn.addEventListener('click', () => openDupes(Number(btn.dataset.dupeId)));
    });
    resultsContainer.querySelectorAll('.store-details').forEach(det => {
        det.addEventListener('toggle', () => {
            if (det.open && !det.dataset.loaded) {
                det.dataset.loaded = '1';
                loadStores(Number(det.dataset.productId), det.querySelector('.store-body'));
            }
        });
    });

    // Si la imagen no carga, el contenedor muestra el color del tono
    resultsContainer.querySelectorAll('.product-img').forEach(img => {
        img.addEventListener('error', () => {
            img.remove();
        });
    });
}


// ---------- Sprint 6: badges, dupes, cosmetiquera y tiendas ----------

function badgeClass(text) {
    if (text.includes('Alcohol')) return 'badge-warning-alcohol';
    if (text.includes('Fragancia')) return 'badge-warning-fragrance';
    return 'badge-sensitive-safe';
}

function badgesHTML(badges) {
    if (!badges || !badges.length) return '';
    return `<div class="ingredient-badges">${badges.map(b =>
        `<span class="ing-badge ${badgeClass(b)}">${esc(b)}</span>`).join('')}</div>`;
}

function formatCOP(n) {
    return '$' + Number(n).toLocaleString('es-CO') + ' COP';
}

async function getJSON(url, options) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    return data;
}

function errorHTML(err) {
    return `<p class="error-banner">${esc(err.message || 'Error al conectar con la API.')}</p>`;
}

let catalogCache = null;
async function getCatalog() {
    if (!catalogCache) catalogCache = (await getJSON('/api/catalog')).products;
    return catalogCache;
}

const FLOW_IDS = ['intro-screen', 'quiz-screen', 'loading-screen', 'results-screen'];
let flowScreen = 'intro-screen';

function showView(view) {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.toggle('active', b.dataset.view === view));
    const tools = document.getElementById('tools-screen');
    if (view === 'test') {
        tools.classList.add('hidden');
        document.getElementById(flowScreen).classList.remove('hidden');
        return;
    }
    const visible = FLOW_IDS.find(id => !document.getElementById(id).classList.contains('hidden'));
    if (visible) flowScreen = visible;
    FLOW_IDS.forEach(id => document.getElementById(id).classList.add('hidden'));
    tools.classList.remove('hidden');
    document.getElementById('dupes-screen').classList.toggle('hidden', view !== 'dupes');
    document.getElementById('cosmetic-bag-screen').classList.toggle('hidden', view !== 'bag');
    if (view === 'dupes') loadDupeSelect();
    if (view === 'bag') renderBagList();
}

function initTools() {
    document.querySelectorAll('.nav-btn').forEach(b =>
        b.addEventListener('click', () => showView(b.dataset.view)));
    const search = document.getElementById('dupe-search');
    document.getElementById('btn-find-dupes').addEventListener('click', () => runDupeSearch(search.value));
    search.addEventListener('keydown', e => { if (e.key === 'Enter') runDupeSearch(search.value); });
    document.getElementById('btn-bag-plan').addEventListener('click', runBagPlan);
}

// --- Dupes ---

async function loadDupeSelect() {
    const list = document.getElementById('dupe-options');
    if (list.options.length) return;
    try {
        (await getCatalog()).filter(p => p.is_high_end).forEach(p => {
            list.appendChild(new Option(`${p.brand} ${p.name} ${p.shade_name} (${p.price_formatted})`, `${p.brand} ${p.shade_name}`));
        });
    } catch (err) {
        document.getElementById('dupes-results').innerHTML = errorHTML(err);
    }
}

async function openDupes(productId) {
    showView('dupes');
    await loadDupeSelect();
    const product = (await getCatalog()).find(p => p.id === productId);
    if (product) document.getElementById('dupe-search').value = `${product.brand} ${product.shade_name}`;
    runDupes(`/api/dupes/${productId}`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function runDupeSearch(text) {
    const query = text.trim();
    if (!query) {
        document.getElementById('dupes-results').innerHTML = '<p class="no-products">Escribe un producto o tono de alta gama para buscar.</p>';
        return;
    }
    runDupes(`/api/dupes/search?q=${encodeURIComponent(query)}`);
}

async function runDupes(url) {
    const box = document.getElementById('dupes-results');
    box.innerHTML = '<p class="store-hint">Buscando equivalentes…</p>';
    try {
        const { dupes } = await getJSON(url);
        if (!dupes.length) {
            box.innerHTML = '<p class="no-products">No encontramos dupes más económicos con un tono tan cercano (o no reconocimos ese producto). Prueba con marca y tono, ej. «NARS Orgasm».</p>';
            return;
        }
        box.innerHTML = `<div class="dupes-list">${dupes.map(d => `
            <div class="dupe-card">
                <span class="shade-dot big" style="background-color: ${safeHex(d.hex_color)};"></span>
                <div class="dupe-info">
                    <span class="product-brand">${esc(d.dupe_brand)}</span>
                    <strong>${esc(d.dupe_name)}</strong>
                    <small>${esc(d.dupe_shade)} · ${esc(d.hex_color)}</small>
                </div>
                <div class="dupe-numbers">
                    <span class="similarity">${esc(d.similarity_percentage)}% similar</span>
                    <span class="product-price">${esc(formatCOP(d.price_cop))}</span>
                    <span class="savings">Ahorras ${esc(formatCOP(d.savings_cop))}</span>
                </div>
            </div>`).join('')}</div>
            <p class="store-hint">Referencia: ${esc(dupes[0].original_brand)} ${esc(dupes[0].original_product)}.</p>`;
    } catch (err) {
        box.innerHTML = errorHTML(err);
    }
}

// --- Mi Cosmetiquera ---

function loadBag() {
    try {
        const ids = JSON.parse(localStorage.getItem('chroma_bag') || '[]');
        return new Set(Array.isArray(ids) ? ids.filter(Number.isInteger) : []);
    } catch (e) { return new Set(); }
}

function saveBag(bag) {
    try { localStorage.setItem('chroma_bag', JSON.stringify([...bag])); } catch (e) { /* sin almacenamiento */ }
}

async function renderBagList() {
    const list = document.getElementById('bag-list');
    try {
        const products = await getCatalog();
        const bag = loadBag();
        const byCategory = {};
        products.forEach(p => (byCategory[p.category] ||= []).push(p));
        list.innerHTML = Object.entries(byCategory).map(([category, items]) => `
            <fieldset class="bag-group"><legend>${esc(category)}</legend>
            ${items.map(p => `
                <label class="bag-item">
                    <input type="checkbox" value="${esc(p.id)}" ${bag.has(p.id) ? 'checked' : ''}>
                    <span class="shade-dot" style="background-color: ${safeHex(p.hex_color)};"></span>
                    <span>${esc(p.brand)} ${esc(p.name)} – ${esc(p.shade_name)}</span>
                </label>`).join('')}
            </fieldset>`).join('');
        list.querySelectorAll('input[type=checkbox]').forEach(cb =>
            cb.addEventListener('change', () => {
                const current = loadBag();
                cb.checked ? current.add(Number(cb.value)) : current.delete(Number(cb.value));
                saveBag(current);
            }));
    } catch (err) {
        list.innerHTML = errorHTML(err);
    }
}

async function runBagPlan() {
    const box = document.getElementById('bag-plan');
    const bag = [...loadBag()];
    const result = window.diagnosticResult;
    const payload = {
        bag,
        occasion: document.getElementById('occasion-select').value,
        season: result ? result.colorimetry.season : '',
        skin_type: userAnswers.skin_type ? userAnswers.skin_type.split(' ')[0] : ''
    };
    try {
        const { plan } = await getJSON('/api/bag-plan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        box.innerHTML = `
            <div class="bag-summary">
                <p class="bag-message">${esc(plan.message)}</p>
                <div class="progress-bar-background"><div class="progress-bar-fill" style="width: ${Number(plan.completion)}%"></div></div>
            </div>
            <ul class="bag-steps">${plan.steps.map(s => `
                <li class="bag-step ${s.status === 'Ya lo tienes' ? 'owned' : 'missing'}">
                    <strong>${esc(s.category)}</strong>
                    <span class="step-status ${s.status === 'Ya lo tienes' ? 'badge-owned' : ''}">${s.status === 'Ya lo tienes' ? '✅' : '🛒'} ${esc(s.status)}</span>
                    ${s.product ? `<span>${esc(s.product.brand)} ${esc(s.product.name)} – ${esc(s.product.shade_name)}
                        ${s.status === 'Te falta' ? `· ${esc(s.product.price_formatted)}` : ''}</span>${badgesHTML(s.product.badges)}` : '<span>Sin sugerencia disponible.</span>'}
                </li>`).join('')}</ul>
            ${result ? '' : '<p class="store-hint">Tip: haz el test para que las sugerencias respeten tu estación y tu piel.</p>'}`;
    } catch (err) {
        box.innerHTML = errorHTML(err);
    }
    runKitRecommendation(bag, result);
}

// Con diagnóstico hecho, cruza la cosmetiquera con las recomendaciones del perfil
async function runKitRecommendation(bag, result) {
    const box = document.getElementById('bag-kit');
    if (!result) { box.innerHTML = ''; return; }
    const profile = {
        season: result.colorimetry.season,
        skin_type: userAnswers.skin_type || '',
        finish: userAnswers.finish_preference || '',
        budget: userAnswers.budget_range || ''
    };
    try {
        const data = await getJSON('/api/cosmetic-bag/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_profile: profile, owned_product_ids: bag })
        });
        const item = (p, cls) => `<li class="bag-step"><span class="step-status ${cls}">${esc(p.status)}</span>
            <span>${esc(p.brand)} ${esc(p.name)} – ${esc(p.shade_name)} · ${esc(p.price_formatted)}</span>${badgesHTML(p.badges)}</li>`;
        box.innerHTML = `<h3>Tu kit ideal según tu perfil: ${esc(data.completion_percentage)}% completo</h3>
            <ul class="bag-steps">${data.owned_items.map(p => item(p, 'badge-owned')).join('')}
            ${data.missing_items.slice(0, 6).map(p => item(p, '')).join('')}</ul>`;
    } catch (err) {
        box.innerHTML = errorHTML(err);
    }
}

// --- Tiendas cercanas ---

function storesHTML(stores) {
    const row = s => `<li class="store-row${s.best_price ? ' best' : ''}">
        <span><strong>${esc(s.name || s.retailer)}</strong>${s.city ? ` <small>${esc(s.city)} · ${esc(s.distance_km)} km</small>` : ''}</span>
        <span>${esc(s.price_formatted)}${s.best_price ? ' 🏷️ mejor precio' : ''}</span></li>`;
    const online = stores.online.map(s => row({ ...s, name: `${s.retailer} (online)` })).join('');
    const physical = stores.physical.length
        ? `<h5>Tiendas físicas más cercanas</h5><ul class="store-list">${stores.physical.map(row).join('')}</ul>` : '';
    return `${physical}<h5>Tiendas virtuales</h5><ul class="store-list">${online}</ul>
        <p class="store-hint">Precios estimados; confirma en la tienda.</p>`;
}

async function loadStores(productId, body, coords) {
    const query = coords ? `?lat=${coords.latitude}&lon=${coords.longitude}` : '';
    try {
        const { stores } = await getJSON(`/api/stores/${productId}${query}`);
        body.innerHTML = storesHTML(stores);
        if (!coords && navigator.geolocation) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn-secondary btn-small';
            btn.textContent = '📍 Usar mi ubicación';
            btn.addEventListener('click', () => {
                btn.disabled = true;
                navigator.geolocation.getCurrentPosition(
                    pos => loadStores(productId, body, pos.coords),
                    () => { btn.disabled = false; btn.textContent = 'No pudimos obtener tu ubicación'; },
                    { timeout: 8000 });
            });
            body.prepend(btn);
        }
    } catch (err) {
        body.innerHTML = errorHTML(err);
    }
}
