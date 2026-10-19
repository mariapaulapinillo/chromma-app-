"""Cosmetiquera: qué tiene el usuario y qué le falta para cada ocasión."""
from database import get_connection
from recommender import recommend_products, product_to_dict

OCCASIONS = {
    "dia": {"label": "Día", "categories": ["Corrector", "Base", "Rubor"]},
    "oficina": {"label": "Oficina", "categories": ["Base", "Rubor", "Labial", "Sombras"]},
    "fiesta": {"label": "Fiesta", "categories": ["Base", "Corrector", "Rubor", "Labial", "Sombras"]},
}

# categoría -> (artículo, género, plural)
CATEGORY_GRAMMAR = {
    "Base": ("una", "base", "f"),
    "Corrector": ("un", "corrector", "m"),
    "Labial": ("un", "labial", "m"),
    "Rubor": ("un", "rubor", "m"),
    "Sombras": ("unas", "sombras", "fp"),
}
WARM_SEASONS = ("Primavera", "Otoño")
COOL_SEASONS = ("Verano", "Invierno")


def _tone_word(season, gender):
    if season in WARM_SEASONS:
        word = "cálid"
    elif season in COOL_SEASONS:
        word = "fri"
    else:
        return ""
    if word == "fri":
        return {"m": "frío", "f": "fría", "fp": "frías"}[gender]
    return word + {"m": "o", "f": "a", "fp": "as"}[gender]


def _describe_missing(category, season):
    article, noun, gender = CATEGORY_GRAMMAR[category]
    return " ".join(p for p in (article, noun, _tone_word(season, gender)) if p)


def _suggest(category, owned_ids, profile):
    """Mejor producto faltante: compatible con el perfil o, si no hay, el más barato."""
    candidates = [p for p in recommend_products(profile)
                  if p["category"] == category and p["id"] not in owned_ids]
    if candidates:
        return candidates[0]
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM products WHERE category = ? ORDER BY price_cop", (category,)).fetchall()
    finally:
        conn.close()
    rows = [product_to_dict(r) for r in rows if r["id"] not in owned_ids]
    return rows[0] if rows else None


def plan_for_occasion(bag_ids, occasion, season="", skin_type=""):
    """Devuelve None si la ocasión no existe."""
    spec = OCCASIONS.get(occasion)
    if not spec:
        return None

    conn = get_connection()
    try:
        marks = ",".join("?" * len(bag_ids))
        rows = conn.execute(f"SELECT * FROM products WHERE id IN ({marks})", bag_ids).fetchall() \
            if bag_ids else []
    finally:
        conn.close()
    owned = [product_to_dict(r) for r in rows]
    owned_ids = {p["id"] for p in owned}
    owned_by_category = {}
    for p in owned:
        owned_by_category.setdefault(p["category"], p)

    profile = {"season": season, "skin_type": skin_type, "finish": "", "budget": ""}
    needed = spec["categories"]
    steps, missing = [], []
    for category in needed:
        have = owned_by_category.get(category)
        if have:
            steps.append({"category": category, "status": "Ya lo tienes", "product": have})
        else:
            suggestion = _suggest(category, owned_ids, profile)
            missing.append(category)
            steps.append({"category": category, "status": "Te falta", "product": suggestion})

    completion = round(100 * (len(needed) - len(missing)) / len(needed))
    look = spec["label"].lower()
    if not missing:
        message = f"¡Kit 100% completo para tu look de {look}! No necesitas comprar nada."
    else:
        items = [_describe_missing(c, season) for c in missing]
        if len(items) == 1:
            falta = f"Solo te falta {items[0]}"
        else:
            falta = "Te faltan " + ", ".join(items[:-1]) + " y " + items[-1]
        message = f"¡Kit {completion}% completo! {falta} para tu look de {look}."

    return {
        "occasion": spec["label"],
        "completion": completion,
        "message": message,
        "steps": steps,
        "missing": missing,
    }
