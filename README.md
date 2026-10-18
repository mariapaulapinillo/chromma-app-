# Chroma App

Aplicación web de **colorimetría facial** y recomendación de maquillaje. Un cuestionario de 27 preguntas determina la estación colorimétrica del usuario (Primavera, Verano, Otoño o Invierno), su subtono y su contraste, y la app recomienda productos de un catálogo en pesos colombianos (COP) según estación, tipo de piel, acabado y presupuesto.

- **Backend:** Python + Flask, SQLite (`chroma.db`)
- **Frontend:** HTML5, JavaScript ES6+ (SPA sin frameworks) y CSS3 responsivo
- **Pruebas:** `unittest` (27 pruebas)

> **Estado:** MVP. Los pesos del algoritmo, las paletas, los consejos de vestuario y el catálogo de productos son datos de ejemplo/calibración inicial, **no** están validados por una experta en colorimetría ni verificados contra los fabricantes.

## Requisitos

- Python 3.10 o superior (desarrollado y probado con **Python 3.14.4**, Linux)
- `pip`
- Node.js solo si quieres revisar la sintaxis del JS (opcional)

## Reproducir paso a paso

```bash
# 1. Clonar
git clone <URL-DEL-REPOSITORIO> chroma-app
cd chroma-app

# 2. Entorno virtual (recomendado)
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

# 3. Dependencias (Flask 3.1.3 fijado)
pip install -r requirements.txt

# 4. Ejecutar las pruebas (esperado: "Ran 27 tests ... OK")
python -m unittest discover tests

# 5. Crear y poblar la base de datos (31 productos)
python database.py

# 6. Levantar el servidor
CHROMA_HOST=127.0.0.1 CHROMA_PORT=3020 python app.py
```

Abre <http://127.0.0.1:3020> y responde el cuestionario.

### Atajos

| Sistema | Comando | Qué hace |
|---|---|---|
| Linux / macOS | `./run.sh` | Instala dependencias, inicializa la BD y arranca el servidor |
| Windows | `INICIAR_CHROMA.bat` | Lo mismo, en `http://localhost:3020` |

**Importante:** `run.sh` publica el servidor en `172.30.0.183:3020` por defecto (la IP del servidor de desarrollo original). En cualquier otra máquina esa IP no existe y el arranque fallará: usa

```bash
CHROMA_HOST=127.0.0.1 ./run.sh
```

Variables de entorno: `CHROMA_HOST` (por defecto `172.30.0.183`) y `CHROMA_PORT` (por defecto `3020`).

### Notas de seguridad

`app.py` arranca con `debug=True` (recarga automática) pero con `use_debugger=False`, para no exponer la consola interactiva de Werkzeug cuando el host está abierto en red. Es un servidor de desarrollo: no lo uses tal cual en producción (usa gunicorn/waitress y `debug=False`).

## Estructura

```
app.py              Flask: rutas / , /api/questionnaire , /api/diagnose
questionnaire.py    QUESTIONNAIRE_SCHEMA: 27 preguntas en 3 secciones
colorimetry.py      Motor de colorimetría (pesos, estaciones, paletas, consejos)
database.py         Esquema SQLite + seeder del catálogo (init_db)
recommender.py      Filtrado y ranking de productos
templates/index.html
static/css/style.css
static/js/app.js    SPA del cuestionario y dashboard de resultados
tests/              test_colorimetry.py, test_recommender.py, test_api.py
run.sh / INICIAR_CHROMA.bat
```

## Cómo funciona

### Motor de colorimetría (`colorimetry.py`)
Cada opción de las preguntas Q1–Q24 suma o resta puntos en tres ejes: **Temperatura** (cálido/frío), **Valor** (claro/oscuro) y **Croma** (brillante/suave). Los puntajes se normalizan a [-1, 1] y se comparan con el perfil de cada estación; gana la de mayor afinidad (la temperatura pesa 1,5×):

| Estación | Temperatura | Valor | Croma |
|---|---|---|---|
| Primavera | Cálido | Claro | Brillante |
| Verano | Frío | Claro | Suave |
| Otoño | Cálido | Oscuro | Suave |
| Invierno | Frío | Oscuro | Brillante |

`confidence_score` (0–100) combina qué tan marcado quedó cada eje y cuántas de las 24 preguntas se respondieron. Se aceptan respuestas parciales; una respuesta que no sea una opción válida lanza `ValueError`.

### Recomendador (`recommender.py`)
Filtra por precio máximo (Q27), estación (o "Todas") y tipo de piel (Q25, o "Todas"). Ordena por coincidencia de estación, tipo de piel, acabado preferido (Q26; es una preferencia de orden, no un filtro duro) y precio ascendente.

Presupuestos: Económico ≤ $50.000, Medio ≤ $100.000, Premium ≤ $180.000, sin restricción.

### API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/questionnaire` | Devuelve el cuestionario completo (JSON) |
| POST | `/api/diagnose` | Recibe `{id_pregunta: opción_elegida}`; devuelve `{success, colorimetry, recommendations}`. 400 si el cuerpo no es un objeto JSON, hay una respuesta inválida o no hay respuestas de Q1–Q24 |

Ejemplo:

```bash
curl -s -X POST http://127.0.0.1:3020/api/diagnose \
  -H 'Content-Type: application/json' \
  -d '{"veins":"Azules o violetas","metal_test":"Plata, oro blanco o platino",
       "skin_type":"Mixta (zona T)","finish_preference":"Mate (sin brillo)",
       "budget_range":"Premium ($100,000 - $180,000 COP)"}'
```

## Base de datos

`database.py` crea la tabla `products` en `chroma.db` (junto al código) y siembra el catálogo **solo si la tabla está vacía**. `chroma.db` está en `.gitignore`: se regenera con `python database.py`. Si cambias el catálogo, borra `chroma.db` y vuelve a ejecutarlo.

Las imágenes del catálogo son una URL de marcador de posición que ya no existe; el dashboard muestra un degradado con el color del tono cuando la imagen no carga. Para fotos reales, cambia `image_url` en `database.py`.

## Pruebas

```bash
python -m unittest discover tests -v
```

Resultado esperado: `Ran 27 tests ... OK`. Cubren el motor (perfiles de las 4 estaciones, entradas inválidas), el esquema de 27 preguntas, el recomendador (presupuesto, estación, tipo de piel, orden, formato COP) y la API (códigos 200/400). Las pruebas de colorimetría usan perfiles de ejemplo: **no miden la precisión real** del diagnóstico. El frontend no tiene pruebas automatizadas.

## Metodología

Desarrollado en 4 sprints de Scrum: (1) motor de colorimetría y cuestionario, (2) base de datos y recomendador, (3) API Flask y SPA del cuestionario, (4) dashboard de resultados y scripts de arranque.
