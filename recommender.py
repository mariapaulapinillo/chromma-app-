from database import get_connection

NO_LIMIT = 9999999


def parse_budget_limit(budget_str):
    """Mapea la selección de presupuesto de Q27 a un número máximo en COP."""
    if not budget_str:
        return NO_LIMIT

    # Se evalúa la etiqueta (primera palabra) antes que los montos: el texto de
    # "Medio" también contiene "$50,000" y se confundiría con "Económico".
    label = budget_str.strip().split()[0].lower()
    if label.startswith("econ"):
        return 50000
    if label == "medio":
        return 100000
    if label == "premium":
        return 180000
    return NO_LIMIT  # Sin restricción


def _first_word(text):
    return text.split()[0] if text else ""


def recommend_products(user_profile):
    """
    Filtra productos según:
    - season: Coincidencia con la estación o "Todas"
    - skin_type: Coincidencia con el tipo de piel o "Todas"
    - budget: Límite superior de precio en COP
    y ordena por compatibilidad: acabado preferido ("Todos" cuenta como
    coincidencia) y luego precio ascendente. El acabado es una preferencia
    de orden, no un filtro duro.
    """
    season = user_profile.get("season", "")
    skin_type = _first_word(user_profile.get("skin_type", ""))
    finish = _first_word(user_profile.get("finish", ""))
    max_price = parse_budget_limit(user_profile.get("budget", ""))

    conn = get_connection()
    try:
        rows = conn.execute('''
            SELECT * FROM products
            WHERE price_cop <= ?
              AND (season_compat = ? OR season_compat = 'Todas')
              AND (skin_type_compat = ? OR skin_type_compat = 'Todas')
            ORDER BY
              CASE WHEN season_compat = ? THEN 1 ELSE 2 END,
              CASE WHEN skin_type_compat = ? THEN 1 ELSE 2 END,
              CASE WHEN finish = ? OR finish = 'Todos' THEN 1 ELSE 2 END,
              price_cop ASC
        ''', (max_price, season, skin_type, season, skin_type, finish)).fetchall()
    finally:
        conn.close()

    return [{
        "id": row["id"],
        "brand": row["brand"],
        "name": row["name"],
        "category": row["category"],
        "shade_name": row["shade_name"],
        "hex_color": row["hex_color"],
        "season": row["season_compat"],
        "skin_type": row["skin_type_compat"],
        "finish": row["finish"],
        "price_cop": row["price_cop"],
        "price_formatted": f"${row['price_cop']:,} COP".replace(",", "."),
        "image_url": row["image_url"],
        "description": row["description"],
    } for row in rows]
