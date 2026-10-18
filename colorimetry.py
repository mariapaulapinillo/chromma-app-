"""Motor de colorimetría: puntúa Q1-Q24 en temperatura, valor y croma."""
from questionnaire import QUESTIONNAIRE_SCHEMA

# Cada opción aporta (T, V, C):
#   T: + cálido / - frío   V: + claro / - oscuro   C: + brillante / - suave
# Las listas siguen el orden de "options" en QUESTIONNAIRE_SCHEMA.
WEIGHTS = {
    "skin_tone": [(0, 3, 0), (0, 2, 0), (0, 0, 0), (0, -2, 0), (0, -3, 0)],
    "undertone_self": [(-3, 0, 0), (3, 0, 0), (1, 0, -1), (0, 0, 0)],
    "veins": [(-3, 0, 0), (3, 0, 0), (0, 0, 0), (0, 0, 0)],
    "sun_reaction": [(-1, 2, 0), (0, 1, 0), (1, -1, 0), (1, -2, 0)],
    "metal_test": [(-3, 0, 0), (3, 0, 0), (0, 0, 0), (0, 0, 0)],
    "white_test": [(-3, 0, 1), (3, 0, -1), (0, 0, 0), (0, 0, -2)],
    "clothing_colors": [(-2, 1, -2), (2, -2, -2), (0, -1, 3), (2, 2, 2)],
    "hair_natural_color": [(-1, 3, 0), (2, 1, 0), (0, -2, 0), (0, -3, 1)],
    "hair_highlights": [(2, 0, 0), (-2, 0, 0), (0, 0, 0)],
    "eye_color": [(-1, 2, 1), (0, 0, 1), (0, -3, 0), (2, -1, -1)],
    "eye_pattern": [(3, 0, 0), (-2, 0, 1), (0, 0, -2)],
    "contrast_level": [(0, -1, 3), (0, 0, 0), (0, 1, -3)],
    "blush_natural": [(-2, 0, 0), (2, 1, 0), (2, 0, 0), (0, 0, 0)],
    "freckles": [(2, 0, 0), (-2, 0, 0), (0, 0, 0)],
    "lip_natural_tone": [(-2, 1, 0), (2, 1, 0), (1, 0, -1), (0, -2, 0)],
    "bright_vs_muted": [(0, 0, 3), (0, 0, -3), (0, -2, 1)],
    "black_clothing": [(0, -1, 2), (0, 0, -2), (0, 0, 0)],
    "orange_vs_pink": [(3, 0, 0), (-3, 0, 0), (0, 0, 0), (0, 0, 0)],
    "tan_durability": [(1, -1, 0), (-1, 1, 0), (0, 0, 0)],
    "eyebrow_density": [(0, -2, 1), (0, 1, -1), (0, 0, 0)],
    "jewelry_gems": [(0, -1, 2), (3, 0, -1), (-2, 1, -2)],
    "season_known": [(0, 0, 0), (2, 0, 0), (-2, 0, 0)],
    "makeup_dislike": [(-2, 0, 0), (2, 0, 0), (0, 1, 0), (0, -1, 0)],
    "saturations": [(0, 1, 3), (0, 0, -3), (0, -2, 2)],
}

# Estación -> (signo T, signo V, signo C)
SEASON_PROFILES = {
    "Primavera": (1, 1, 1),
    "Verano": (-1, 1, -1),
    "Otoño": (1, -1, -1),
    "Invierno": (-1, -1, 1),
}
DIM_WEIGHTS = (1.5, 1.0, 1.0)  # la temperatura pesa más
NEUTRAL_BAND = 0.15

SEASON_INFO = {
    "Primavera": {
        "description": "Paleta cálida, clara y brillante: colores frescos, luminosos y vivos.",
        "palette": ["#FF7F50", "#FFB347", "#FFD700", "#98D86A", "#40C9A2",
                    "#FF6F61", "#F9A8A0", "#FFE5B4", "#7FD6E8", "#E94B6A"],
    },
    "Verano": {
        "description": "Paleta fría, clara y suave: tonos empolvados, pastel y de aire sereno.",
        "palette": ["#B8C5E3", "#C8A2C8", "#E8B4C8", "#9DB4C0", "#8FA9C9",
                    "#D8BFD8", "#A8C3BC", "#C58C9B", "#778DA9", "#E6D5E0"],
    },
    "Otoño": {
        "description": "Paleta cálida, profunda y suave: tonos terrosos, especiados y naturales.",
        "palette": ["#8B4513", "#B7410E", "#CC7722", "#DAA520", "#6B8E23",
                    "#556B2F", "#A0522D", "#D2691E", "#7B3F00", "#9C6B30"],
    },
    "Invierno": {
        "description": "Paleta fría, profunda y brillante: colores puros, intensos y de alto contraste.",
        "palette": ["#000000", "#FFFFFF", "#C2185B", "#0D47A1", "#6A1B9A",
                    "#B71C1C", "#00695C", "#1A237E", "#E91E63", "#37474F"],
    },
}

SEASON_ADVICE = {
    "Primavera": {
        "jewelry": {"metals": "Oro amarillo, oro rosado y cobre brillante", "avoid": "Plata muy fría y platino"},
        "clothing": {
            "best": ["Coral", "Durazno", "Turquesa", "Verde manzana", "Amarillo dorado"],
            "avoid": ["Negro absoluto", "Gris oscuro", "Borgoña apagado"],
        },
    },
    "Verano": {
        "jewelry": {"metals": "Plata, oro blanco y platino", "avoid": "Oro amarillo intenso y cobre"},
        "clothing": {
            "best": ["Rosa empolvado", "Lavanda", "Azul cielo", "Gris azulado", "Malva"],
            "avoid": ["Naranja", "Mostaza", "Negro absoluto"],
        },
    },
    "Otoño": {
        "jewelry": {"metals": "Oro amarillo, bronce y cobre", "avoid": "Plata brillante y platino"},
        "clothing": {
            "best": ["Terracota", "Verde oliva", "Mostaza", "Marrón chocolate", "Calabaza"],
            "avoid": ["Rosa fucsia", "Azul hielo", "Blanco óptico"],
        },
    },
    "Invierno": {
        "jewelry": {"metals": "Plata, oro blanco y platino", "avoid": "Oro amarillo opaco y bronce"},
        "clothing": {
            "best": ["Negro", "Blanco puro", "Azul rey", "Rojo verdadero", "Fucsia"],
            "avoid": ["Beige", "Mostaza", "Colores terrosos apagados"],
        },
    },
}


def _max_abs():
    return {qid: tuple(max(abs(w[d]) for w in ws) for d in range(3))
            for qid, ws in WEIGHTS.items()}


def _validate_weights():
    questions = {q["id"]: q for q in QUESTIONNAIRE_SCHEMA["section_1_colorimetry"]}
    assert set(WEIGHTS) == set(questions), "WEIGHTS no coincide con Q1-Q24"
    for qid, ws in WEIGHTS.items():
        assert len(ws) == len(questions[qid]["options"]), f"pesos desalineados en {qid}"


_validate_weights()
_MAX_ABS = _max_abs()
_QUESTIONS = {q["id"]: q for q in QUESTIONNAIRE_SCHEMA["section_1_colorimetry"]}


def calculate_colorimetry(answers):
    """Calcula estación, temperatura, contraste y paleta a partir de Q1-Q24.

    Acepta respuestas parciales (ignora ids que no sean de Q1-Q24); lanza
    ValueError si una respuesta no es una opción válida o no hay ninguna.
    """
    raw = [0.0, 0.0, 0.0]
    max_possible = [0.0, 0.0, 0.0]
    answered = 0

    for qid, answer in answers.items():
        if qid not in _QUESTIONS:
            continue
        options = _QUESTIONS[qid]["options"]
        if answer not in options:
            raise ValueError(f"Respuesta inválida para '{qid}': {answer!r}")
        weights = WEIGHTS[qid][options.index(answer)]
        for d in range(3):
            raw[d] += weights[d]
            max_possible[d] += _MAX_ABS[qid][d]
        answered += 1

    if answered == 0:
        raise ValueError("No se recibió ninguna respuesta válida de Q1-Q24")

    # Puntajes normalizados a [-1, 1]
    norm = [raw[d] / max_possible[d] if max_possible[d] else 0.0 for d in range(3)]

    fits = {
        season: sum(DIM_WEIGHTS[d] * signs[d] * norm[d] for d in range(3))
        for season, signs in SEASON_PROFILES.items()
    }
    season = max(fits, key=fits.get)

    t_norm, v_norm, c_norm = norm
    if t_norm > NEUTRAL_BAND:
        temperature = "Cálida"
    elif t_norm < -NEUTRAL_BAND:
        temperature = "Fría"
    else:
        temperature = "Neutro"

    contrast_answer = answers.get("contrast_level")
    if contrast_answer is not None:
        contrast = ["Alto", "Medio", "Bajo"][_QUESTIONS["contrast_level"]["options"].index(contrast_answer)]
    else:
        contrast = "Alto" if abs(v_norm) + max(c_norm, 0) > 1 else "Medio"

    # Certeza: claridad de cada eje (saturada en 50% del máximo) y cobertura de preguntas
    clarity = sum(min(1.0, abs(n) / 0.5) for n in norm) / 3
    coverage = answered / len(_QUESTIONS)
    confidence = round(100 * (0.5 + 0.5 * clarity) * (0.7 + 0.3 * coverage), 1)

    info = SEASON_INFO[season]
    return {
        "season": season,
        "temperature": temperature,
        "subtone": temperature,
        "value": "Claro" if v_norm >= 0 else "Oscuro",
        "chroma": "Brillante" if c_norm >= 0 else "Suave",
        "contrast": contrast,
        "palette": list(info["palette"]),
        "palette_description": info["description"],
        "jewelry": dict(SEASON_ADVICE[season]["jewelry"]),
        "clothing": {k: list(v) for k, v in SEASON_ADVICE[season]["clothing"].items()},
        "confidence_score": confidence,
        "scores": {"temperature": raw[0], "value": raw[1], "chroma": raw[2]},
    }
