import math

from database import get_connection

MAX_DELTA_E = 5.0


def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))


def color_distance(hex1, hex2):
    """Distancia euclidiana RGB entre dos tonos Hex."""
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)
    return math.sqrt((r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2)


def hex_to_lab(hex_str):
    """Convierte Hex (sRGB, D65) a CIELAB."""
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (lin(c) for c in hex_to_rgb(hex_str))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e(hex1, hex2):
    """Diferencia de color perceptual CIE76 (ΔE)."""
    return math.dist(hex_to_lab(hex1), hex_to_lab(hex2))


def find_dupes(product_id_or_shade, max_price=None, max_delta_e=MAX_DELTA_E):
    """Alternativas más económicas con ΔE <= max_delta_e.

    Acepta un id de producto o un texto (nombre de tono/producto/marca,
    ej. "NARS Orgasm"). El % de coincidencia es 100 - 4*ΔE (ΔE 5 -> 80%).
    """
    conn = get_connection()
    try:
        target = None
        if isinstance(product_id_or_shade, int) or str(product_id_or_shade).isdigit():
            target = conn.execute("SELECT * FROM products WHERE id = ?",
                                  (int(product_id_or_shade),)).fetchone()
        else:
            words = str(product_id_or_shade).lower().split()
            if words:
                clause = " AND ".join(
                    "LOWER(brand || ' ' || name || ' ' || shade_name) LIKE ?" for _ in words)
                target = conn.execute(f"SELECT * FROM products WHERE {clause} LIMIT 1",
                                      [f"%{w}%" for w in words]).fetchone()
        if not target:
            return []

        candidates = conn.execute(
            "SELECT * FROM products WHERE id != ? AND category = ? AND price_cop < ?",
            (target['id'], target['category'], target['price_cop'])).fetchall()
    finally:
        conn.close()

    dupes = []
    for cand in candidates:
        if max_price is not None and cand['price_cop'] > max_price:
            continue
        de = delta_e(target['hex_color'], cand['hex_color'])
        if de > max_delta_e:
            continue
        dupes.append({
            "original_product": target['name'],
            "original_brand": target['brand'],
            "dupe_id": cand['id'],
            "dupe_brand": cand['brand'],
            "dupe_name": cand['name'],
            "dupe_shade": cand['shade_name'],
            "hex_color": cand['hex_color'],
            "price_cop": cand['price_cop'],
            "savings_cop": target['price_cop'] - cand['price_cop'],
            "delta_e": round(de, 2),
            "similarity_percentage": max(0, round(100 - 4 * de)),
        })
    return sorted(dupes, key=lambda d: (-d['similarity_percentage'], d['price_cop']))
