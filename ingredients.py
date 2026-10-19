import re

SENSITIVE_INGREDIENTS = {
    "alcohol": ["alcohol denat", "sd alcohol", "isopropyl alcohol", "alcohol"],
    "fragrance": ["fragrance", "parfum", "linalool", "limonene", "citronellol"],
    "comedogenic": ["isopropyl myristate", "coconut oil", "ethylhexyl palmitate"],
}

# Alcoholes grasos: emolientes no irritantes, no deben activar la alerta de alcohol.
FATTY_ALCOHOLS = ("cetyl alcohol", "cetearyl alcohol", "stearyl alcohol",
                  "behenyl alcohol", "lauryl alcohol", "myristyl alcohol")

BADGE_ALCOHOL = "⚠️ Contiene Alcohol"
BADGE_FRAGRANCE = "⚠️ Contiene Fragancia"
BADGE_SENSITIVE = "🌿 Apto Piel Sensible"
BADGE_NON_COMEDOGENIC = "🚫 No Comedogénico"


def _tokens(ingredients_text):
    """Divide el INCI por comas y descarta alcoholes grasos."""
    parts = [p.strip() for p in re.split(r"[,;]", ingredients_text.lower())]
    return [p for p in parts if p and p not in FATTY_ALCOHOLS]


def _contains(tokens, keywords):
    return any(k in t for t in tokens for k in keywords)


def analyze_ingredients(ingredients_text):
    tokens = _tokens(ingredients_text) if ingredients_text else []

    has_alcohol = _contains(tokens, SENSITIVE_INGREDIENTS["alcohol"])
    has_fragrance = _contains(tokens, SENSITIVE_INGREDIENTS["fragrance"])
    has_comedogenic = _contains(tokens, SENSITIVE_INGREDIENTS["comedogenic"])
    is_safe_sensitive = not (has_alcohol or has_fragrance)

    badges = []
    if has_alcohol:
        badges.append(BADGE_ALCOHOL)
    if has_fragrance:
        badges.append(BADGE_FRAGRANCE)
    if is_safe_sensitive:
        badges.append(BADGE_SENSITIVE)
    if not has_comedogenic:
        badges.append(BADGE_NON_COMEDOGENIC)

    warnings = [
        "Contiene Alcohol Denat" if has_alcohol else None,
        "Contiene Fragancia/Parfum" if has_fragrance else None,
        "Ingredientes Comedogénicos" if has_comedogenic else None,
    ]

    return {
        "has_alcohol": has_alcohol,
        "has_fragrance": has_fragrance,
        "is_comedogenic": has_comedogenic,
        "is_safe_sensitive": is_safe_sensitive,
        "warnings": [w for w in warnings if w],
        "badges": badges,
    }
