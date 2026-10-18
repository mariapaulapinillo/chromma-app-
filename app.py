import os

from flask import Flask, render_template, jsonify, request
from questionnaire import QUESTIONNAIRE_SCHEMA
from colorimetry import calculate_colorimetry
from recommender import recommend_products
from database import init_db

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
