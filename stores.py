"""Tiendas físicas y virtuales en Colombia con comparativa de precios.

Las sedes y coordenadas son aproximadas y los precios por tienda son una
estimación (factor por retailer sobre el precio de catálogo): no hay
integración con inventarios reales.
"""
import math

from database import get_connection
from recommender import HIGH_END_MIN_PRICE

# retailer -> (factor de precio, vende gama alta, URL online)
RETAILERS = {
    "Mercado Libre": (0.92, True, "https://www.mercadolibre.com.co"),
    "Farmatodo": (0.97, False, "https://www.farmatodo.com.co"),
    "Falabella": (1.00, True, "https://www.falabella.com.co"),
    "Blush Bar": (1.03, True, "https://www.blushbar.co"),
    "Medipiel": (1.05, True, "https://www.medipiel.com.co"),
}

# (retailer, sede, ciudad, lat, lon)
BRANCHES = [
    ("Falabella", "Falabella Unicentro", "Bogotá", 4.7017, -74.0419),
    ("Blush Bar", "Blush Bar Andino", "Bogotá", 4.6669, -74.0537),
    ("Medipiel", "Medipiel Zona T", "Bogotá", 4.6665, -74.0546),
    ("Farmatodo", "Farmatodo Calle 85", "Bogotá", 4.6686, -74.0560),
    ("Falabella", "Falabella Santafé", "Medellín", 6.1960, -75.5740),
    ("Medipiel", "Medipiel El Poblado", "Medellín", 6.2093, -75.5679),
    ("Farmatodo", "Farmatodo Laureles", "Medellín", 6.2442, -75.5896),
    ("Falabella", "Falabella Chipichape", "Cali", 3.4745, -76.5297),
    ("Farmatodo", "Farmatodo Granada", "Cali", 3.4590, -76.5340),
    ("Falabella", "Falabella Buenavista", "Barranquilla", 11.0165, -74.8236),
    ("Blush Bar", "Blush Bar Buenavista", "Barranquilla", 11.0170, -74.8230),
]

MAX_PHYSICAL = 4


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * 6371 * math.asin(math.sqrt(a))


def estimated_price(product_id, base_price, retailer):
    """Precio estimado y estable por producto/tienda, redondeado a 100 COP."""
    factor = RETAILERS[retailer][0]
    jitter = ((product_id * 7 + len(retailer)) % 5 - 2) / 100
    return round(base_price * (factor + jitter) / 100) * 100


def _carries(retailer, base_price):
    return RETAILERS[retailer][1] or base_price < HIGH_END_MIN_PRICE


def find_stores(product_id, lat=None, lon=None):
    """Devuelve None si el producto no existe."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT id, price_cop FROM products WHERE id = ?",
                           (product_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    base = row["price_cop"]

    online = [{
        "retailer": name,
        "url": RETAILERS[name][2],
        "price_cop": estimated_price(product_id, base, name),
    } for name in RETAILERS if _carries(name, base)]
    online.sort(key=lambda s: s["price_cop"])
    if online:
        online[0]["best_price"] = True

    physical = []
    if lat is not None and lon is not None:
        for retailer, branch, city, blat, blon in BRANCHES:
            if not _carries(retailer, base):
                continue
            physical.append({
                "retailer": retailer,
                "name": branch,
                "city": city,
                "distance_km": round(haversine_km(lat, lon, blat, blon), 1),
                "price_cop": estimated_price(product_id, base, retailer),
            })
        physical.sort(key=lambda s: s["distance_km"])
        physical = physical[:MAX_PHYSICAL]

    for store in online + physical:
        store["price_formatted"] = f"${store['price_cop']:,} COP".replace(",", ".")
    return {"estimated": True, "online": online, "physical": physical}
