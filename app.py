import os

from flask import Flask, render_template, jsonify, request
from questionnaire import QUESTIONNAIRE_SCHEMA
from colorimetry import calculate_colorimetry
from recommender import recommend_products
from database import init_db, get_connection
from dupes import find_dupes
from ingredients import analyze_ingredients
from cosmetic_bag import plan_for_occasion
from stores import find_stores
from recommender import product_to_dict, recommend_products

app = Flask(__name__)

# Asegurar que la base de datos esté lista al arrancar
init_db()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/questionnaire', methods=['GET'])
def get_questionnaire():
    return jsonify(QUESTIONNAIRE_SCHEMA)


@app.route('/api/diagnose', methods=['POST'])
def diagnose():
    answers = request.get_json(silent=True)
    if not answers or not isinstance(answers, dict):
        return jsonify({"error": "Se requieren las respuestas en formato JSON de las preguntas Q1-Q27."}), 400

    try:
        # 1. Diagnóstico colorimétrico (ValueError si hay respuestas inválidas)
        colorimetry_result = calculate_colorimetry(answers)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # 2. Perfil de búsqueda para recomendación
    user_profile = {
        "season": colorimetry_result["season"],
        "skin_type": answers.get("skin_type"),
        "finish": answers.get("finish_preference"),
        "budget": answers.get("budget_range")
    }
    if not all(v is None or isinstance(v, str) for v in user_profile.values()):
        return jsonify({"error": "skin_type, finish_preference y budget_range deben ser texto."}), 400

    # 3. Productos recomendados
    recommended_products = recommend_products(user_profile)

    return jsonify({
        "success": True,
        "colorimetry": colorimetry_result,
        "recommendations": recommended_products
    })


@app.route('/api/catalog', methods=['GET'])
def get_catalog():
    """Catálogo completo (para el buscador de dupes y Mi Cosmetiquera)."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM products ORDER BY category, brand, name").fetchall()
    finally:
        conn.close()
    return jsonify({"success": True, "products": [product_to_dict(r) for r in rows]})


@app.route('/api/dupes/<int:product_id>', methods=['GET'])
def get_dupes(product_id):
    max_price = request.args.get('max_price', type=int)
    results = find_dupes(product_id, max_price)
    return jsonify({"success": True, "dupes": results})


@app.route('/api/dupes/search', methods=['GET'])
def search_dupes_by_name():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"error": "Escribe el producto o tono a buscar (parámetro q)."}), 400
    max_price = request.args.get('max_price', type=int)
    return jsonify({"success": True, "dupes": find_dupes(query, max_price)})


@app.route('/api/cosmetic-bag/recommend', methods=['POST'])
def recommend_with_cosmetic_bag():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Se requiere un JSON con 'user_profile' y 'owned_product_ids'."}), 400
    user_profile = data.get("user_profile", {})
    owned_ids = data.get("owned_product_ids", [])
    if not isinstance(user_profile, dict) or not all(
            v is None or isinstance(v, str) for v in user_profile.values()):
        return jsonify({"error": "user_profile debe ser un objeto con valores de texto."}), 400
    if not isinstance(owned_ids, list) or not all(
            isinstance(i, int) and not isinstance(i, bool) for i in owned_ids):
        return jsonify({"error": "owned_product_ids debe ser una lista de ids."}), 400

    recommendations = recommend_products({k: v or "" for k, v in user_profile.items()})
    owned_items, missing_items = [], []
    for item in recommendations:
        if item["id"] in owned_ids:
            item["status"] = "Ya lo tienes en tu cosmetiquera"
            owned_items.append(item)
        else:
            item["status"] = "Sugerido para completar tu kit"
            missing_items.append(item)

    completion = round(len(owned_items) / max(1, len(recommendations)) * 100)
    return jsonify({
        "success": True,
        "completion_percentage": completion,
        "owned_items": owned_items,
        "missing_items": missing_items,
    })


@app.route('/api/analyze-ingredients', methods=['POST'])
def check_ingredients():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("ingredients", ""), str):
        return jsonify({"error": "Se requiere un JSON con el campo 'ingredients' (texto)."}), 400
    analysis = analyze_ingredients(data.get("ingredients", ""))
    return jsonify({"success": True, "analysis": analysis})


@app.route('/api/bag-plan', methods=['POST'])
def bag_plan():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Se requiere un JSON con 'bag' y 'occasion'."}), 400
    bag = data.get("bag", [])
    if not isinstance(bag, list) or not all(isinstance(i, int) and not isinstance(i, bool) for i in bag):
        return jsonify({"error": "'bag' debe ser una lista de ids de producto."}), 400
    season, skin_type = data.get("season", ""), data.get("skin_type", "")
    if not isinstance(season, str) or not isinstance(skin_type, str):
        return jsonify({"error": "season y skin_type deben ser texto."}), 400

    plan = plan_for_occasion(bag, data.get("occasion"), season, skin_type)
    if plan is None:
        return jsonify({"error": "Ocasión no válida. Usa: dia, oficina o fiesta."}), 400
    return jsonify({"success": True, "plan": plan})


@app.route('/api/stores/<int:product_id>', methods=['GET'])
def get_stores(product_id):
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    if (lat is None) != (lon is None) or \
            (lat is not None and not (-90 <= lat <= 90 and -180 <= lon <= 180)):
        return jsonify({"error": "lat y lon deben enviarse juntos y ser coordenadas válidas."}), 400
    result = find_stores(product_id, lat, lon)
    if result is None:
        return jsonify({"error": "Producto no encontrado."}), 404
    return jsonify({"success": True, "stores": result})


if __name__ == '__main__':
    # Mismo esquema que SeguimientoRNDC/run.sh: se publica en la IP de la máquina.
    # use_debugger=False: con el host expuesto en red no se habilita la consola
    # interactiva de Werkzeug (ejecuta código); el reloader sigue activo.
    app.run(
        host=os.environ.get("CHROMA_HOST", "172.30.0.183"),
        port=int(os.environ.get("CHROMA_PORT", "3020")),
        debug=True,
        use_debugger=False,
    )
