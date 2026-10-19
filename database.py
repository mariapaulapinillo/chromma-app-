import os
import sqlite3

from ingredients import analyze_ingredients

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma.db")
PLACEHOLDER = "https://via.placeholder.com/150"  # valor legado: se reemplaza por imágenes locales
IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "img", "products")
IMG_URL_PREFIX = "/static/img/products/"


def _shade(hex_color, factor):
    """Aclara (factor > 0) u oscurece (factor < 0) un #RRGGBB."""
    channels = [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]
    if factor >= 0:
        channels = [round(c + (255 - c) * factor) for c in channels]
    else:
        channels = [round(c * (1 + factor)) for c in channels]
    return "#%02x%02x%02x" % tuple(channels)


def _product_svg(category, hex_color):
    c, light, dark = hex_color, _shade(hex_color, 0.45), _shade(hex_color, -0.3)
    if category == "Labial":
        art = (f'<rect x="115" y="150" width="70" height="95" rx="6" fill="#2b2b33"/>'
               f'<rect x="125" y="95" width="50" height="62" fill="#b9a36a"/>'
               f'<path d="M127 95 V70 Q150 40 173 62 V95 Z" fill="{c}"/>'
               f'<path d="M140 68 Q150 55 160 62" stroke="{light}" stroke-width="4" fill="none" stroke-linecap="round"/>')
    elif category == "Rubor":
        art = (f'<circle cx="150" cy="150" r="88" fill="#2b2b33"/>'
               f'<circle cx="150" cy="150" r="70" fill="{c}"/>'
               f'<ellipse cx="128" cy="125" rx="22" ry="12" fill="{light}"/>')
    elif category == "Sombras":
        pans = "".join(
            f'<rect x="{62 + col * 62}" y="{100 + row * 58}" width="52" height="48" rx="8" fill="{shade}"/>'
            for row, shades in enumerate(((light, c, dark), (dark, light, c)))
            for col, shade in enumerate(shades))
        art = f'<rect x="48" y="84" width="204" height="132" rx="14" fill="#2b2b33"/>{pans}'
    else:  # Base, Corrector
        art = (f'<rect x="128" y="48" width="44" height="36" rx="5" fill="#2b2b33"/>'
               f'<rect x="108" y="82" width="84" height="150" rx="14" fill="#f4f1ee" stroke="#d6d0ca"/>'
               f'<rect x="114" y="150" width="72" height="76" rx="10" fill="{c}"/>'
               f'<rect x="122" y="104" width="56" height="30" rx="4" fill="#fff" stroke="#e3ded9"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" role="img" aria-label="{category}">'
            f'<rect width="300" height="300" fill="{_shade(hex_color, 0.82)}"/>'
            f'<ellipse cx="150" cy="262" rx="80" ry="10" fill="{_shade(hex_color, 0.65)}"/>{art}</svg>')


def ensure_product_image(category, hex_color):
    """Crea (si falta) la ilustración local del producto y devuelve su URL."""
    name = f"{category.lower()}-{hex_color.lstrip('#').lower()}.svg"
    path = os.path.join(IMG_DIR, name)
    if not os.path.exists(path):
        os.makedirs(IMG_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(_product_svg(category, hex_color))
    return IMG_URL_PREFIX + name


def assign_local_images(cursor):
    """Reemplaza URLs vacías o de placeholder por imágenes locales."""
    rows = cursor.execute(
        "SELECT id, category, hex_color FROM products "
        "WHERE image_url IS NULL OR image_url NOT LIKE ?", (IMG_URL_PREFIX + "%",)).fetchall()
    for row in rows:
        cursor.execute("UPDATE products SET image_url = ? WHERE id = ?",
                       (ensure_product_image(row[1], row[2]), row[0]))


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,         -- Base, Labial, Rubor, Sombras, Corrector
            shade_name TEXT NOT NULL,
            hex_color TEXT NOT NULL,
            season_compat TEXT NOT NULL,    -- Primavera, Verano, Otoño, Invierno, Todas
            skin_type_compat TEXT NOT NULL, -- Grasa, Mixta, Seca, Normal, Sensible, Todas
            finish TEXT NOT NULL,           -- Mate, Satinado, Luminoso, Todos
            price_cop INTEGER NOT NULL,     -- Precio en COP
            image_url TEXT,
            description TEXT,
            ingredients_list TEXT,          -- INCI (datos ilustrativos)
            contains_alcohol BOOLEAN DEFAULT 0,
            contains_fragrance BOOLEAN DEFAULT 0,
            is_sensitive_safe BOOLEAN DEFAULT 1,
            is_comedogenic BOOLEAN DEFAULT 0,
            dupes_group_id TEXT             -- productos equivalentes comparten grupo
        )
    ''')
    migrate_products_table(cursor)

    # Comprobar si ya existen datos para evitar duplicados
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        seed_products(cursor)
    seed_dupes(cursor)
    backfill_ingredients(cursor)
    assign_local_images(cursor)

    conn.commit()
    conn.close()


NEW_COLUMNS = {
    "ingredients_list": "TEXT",
    "contains_alcohol": "BOOLEAN DEFAULT 0",
    "contains_fragrance": "BOOLEAN DEFAULT 0",
    "is_sensitive_safe": "BOOLEAN DEFAULT 1",
    "is_comedogenic": "BOOLEAN DEFAULT 0",
    "dupes_group_id": "TEXT",
}

# INCI ilustrativos (no son las fórmulas reales de cada marca).
INCI_FRAGRANCE_FREE = "Water, Glycerin, Dimethicone, Cyclopentasiloxane, Talc, Tocopheryl Acetate, Phenoxyethanol"
INCI_ALCOHOL = "Water, Alcohol Denat, Cyclopentasiloxane, Glycerin, Fragrance, Phenoxyethanol"
INCI_FRAGRANCE = "Water, Dimethicone, Glycerin, Parfum, Linalool, Tocopheryl Acetate"
INCI_COMEDOGENIC = "Ricinus Communis Seed Oil, Isopropyl Myristate, Ethylhexyl Palmitate, Cera Alba, Parfum"
INCI_BASIC = "Talc, Mica, Dimethicone, Zinc Stearate, Cetearyl Alcohol, Tocopherol"

INGREDIENTS_BY_CATEGORY = {
    "Base": INCI_ALCOHOL,
    "Corrector": INCI_FRAGRANCE,
    "Labial": INCI_COMEDOGENIC,
    "Rubor": INCI_BASIC,
    "Sombras": INCI_BASIC,
}
INGREDIENTS_BY_BRAND = {"Clinique": INCI_FRAGRANCE_FREE}


def migrate_products_table(cursor):
    """Agrega las columnas nuevas a bases chroma.db creadas antes del Sprint 5."""
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(products)")}
    for column, ddl in NEW_COLUMNS.items():
        if column not in existing:
            cursor.execute(f"ALTER TABLE products ADD COLUMN {column} {ddl}")


def backfill_ingredients(cursor):
    rows = cursor.execute(
        "SELECT id, brand, category FROM products WHERE ingredients_list IS NULL").fetchall()
    for row in rows:
        inci = INGREDIENTS_BY_BRAND.get(row[1]) or INGREDIENTS_BY_CATEGORY.get(row[2], INCI_BASIC)
        set_ingredients(cursor, row[0], inci)


def set_ingredients(cursor, product_id, inci):
    a = analyze_ingredients(inci)
    cursor.execute(
        """UPDATE products SET ingredients_list = ?, contains_alcohol = ?, contains_fragrance = ?,
           is_sensitive_safe = ?, is_comedogenic = ? WHERE id = ?""",
        (inci, a["has_alcohol"], a["has_fragrance"], a["is_safe_sensitive"],
         a["is_comedogenic"], product_id))


def seed_products(cursor):
    P = PLACEHOLDER
    sample_products = [
        # BASES & CORRECTORES
        ("Maybelline", "Fit Me Matte + Poreless", "Base", "120 Classic Ivory", "#E8C5A5", "Verano", "Grasa", "Mate", 45000, P, "Base líquida mate control de brillo."),
        ("L'Oréal", "Infallible Fresh Wear", "Base", "140 Golden Beige", "#D4A373", "Otoño", "Mixta", "Satinado", 78000, P, "Larga duración con acabado natural."),
        ("NARS", "Light Reflecting Foundation", "Base", "Fiji - Light 5", "#E5C19A", "Primavera", "Seca", "Luminoso", 165000, P, "Maquillaje con tratamiento iluminador."),
        ("MAC", "Studio Fix Fluid SPF 15", "Base", "NC25", "#D8B088", "Otoño", "Grasa", "Mate", 142000, P, "Control de grasa de alta cobertura."),
        ("Clinique", "Even Better Makeup", "Base", "CN 28 Cream Chamois", "#E2BC96", "Verano", "Sensible", "Satinado", 135000, P, "Fórmula dermatológica para piel sensible."),
        ("Maybelline", "Super Stay Active Wear", "Base", "310 Sun Beige", "#D9AE80", "Otoño", "Grasa", "Mate", 49000, P, "Cobertura media-alta de hasta 30 horas."),
        ("Ruby Rose", "HB-8100 Base Líquida", "Base", "Rose Ivory", "#EBCBBB", "Invierno", "Normal", "Satinado", 30000, P, "Base accesible con subtono rosado frío."),
        ("L'Oréal", "True Match", "Base", "N2 Vanilla", "#EAC9A9", "Primavera", "Normal", "Satinado", 62000, P, "Tonos que se adaptan al subtono de la piel."),
        ("Fenty Beauty", "Soft'lit Naturally Luminous", "Base", "180 Neutral Deep", "#8D5B3E", "Invierno", "Mixta", "Satinado", 160000, P, "Acabado luminoso suave y cobertura media."),
        ("Maybelline", "Instant Age Rewind Corrector", "Corrector", "Light Neutral", "#E6C3A0", "Todas", "Todas", "Satinado", 38000, P, "Corrector de ojeras con esponja aplicadora."),
        ("Clinique", "Even Better Glow Light Reflecting", "Base", "WN 46 Golden Neutral", "#D6AC83", "Primavera", "Seca", "Luminoso", 150000, P, "Hidratación y brillo saludable."),

        # LABIALES
        ("Rare Beauty", "Kind Words Matte Lipstick", "Labial", "Humble (Rose Nude)", "#B86B77", "Verano", "Todas", "Mate", 98000, P, "Labial cremoso mate suave."),
        ("Fenty Beauty", "Gloss Bomb Universal", "Labial", "Fenty Glow", "#C87D55", "Otoño", "Todas", "Luminoso", 115000, P, "Brillo labial nutritivo de alto impacto."),
        ("Vogue", "Colorissimo Duración 8h", "Labial", "Amaranto / Fucsia Frío", "#A62B56", "Invierno", "Todas", "Mate", 18000, P, "Labial de larga duración económico."),
        ("Ame Cosmetics", "Labial Liquido Mate", "Labial", "Coral Warm", "#E06D53", "Primavera", "Todas", "Mate", 32000, P, "Tono coral cálido y vibrante."),
        ("Charlotte Tilbury", "Matte Revolution", "Labial", "Pillow Talk Medium", "#A45A52", "Otoño", "Todas", "Satinado", 175000, P, "Icónico labial rosa cálido amarronado."),
        ("Kiko Milano", "Gossamer Emotion", "Labial", "104 Vintage Rose", "#C47B89", "Verano", "Todas", "Satinado", 58000, P, "Labial cremoso de alto confort."),
        ("NYX", "Soft Matte Lip Cream", "Labial", "Monte Carlo (Deep Red)", "#8B1E2B", "Invierno", "Todas", "Mate", 42000, P, "Rojo profundo y vibrante frío."),
        ("NYX", "Butter Gloss", "Labial", "Peach Cobbler", "#E9967A", "Primavera", "Todas", "Luminoso", 36000, P, "Gloss cremoso color durazno."),
        ("Maybelline", "Superstay Vinyl Ink", "Labial", "Cheeky (Coral)", "#EE6C5C", "Primavera", "Todas", "Luminoso", 47000, P, "Tinta líquida de acabado brillante."),
        ("Mac", "Lipstick Satin", "Labial", "Brick-o-la", "#8E3B2F", "Otoño", "Todas", "Satinado", 105000, P, "Terracota ladrillo de alta pigmentación."),

        # RUBORES
        ("Milani", "Baked Blush", "Rubor", "Luminoso", "#E27D60", "Primavera", "Todas", "Luminoso", 52000, P, "Rubor horneado tono melocotón dorado."),
        ("Ame Cosmetics", "Rubor Individual", "Rubor", "Rosa Frío Soft", "#E88B9E", "Verano", "Todas", "Satinado", 28000, P, "Rosa delicado para subtonos fríos."),
        ("Rare Beauty", "Soft Pinch Liquid Blush", "Rubor", "Love (Terracotta)", "#B24C39", "Otoño", "Todas", "Luminoso", 118000, P, "Rubor líquido de alta pigmentación terrosa."),
        ("NARS", "Blush", "Rubor", "Exhibit A (Red)", "#D1342B", "Invierno", "Todas", "Mate", 155000, P, "Rojo intenso y radiante para alto contraste."),
        ("Wet n Wild", "Color Icon Blush", "Rubor", "Mellow Wine", "#B0546A", "Invierno", "Todas", "Mate", 22000, P, "Rubor en polvo berry de gran duración."),

        # PALETAS DE SOMBRAS
        ("Beauty Creations", "Tease Me Palette", "Sombras", "Warm Neutrals", "#8C533E", "Otoño", "Todas", "Satinado", 65000, P, "Sombras en tonos cálidos y tierra."),
        ("Urban Decay", "Naked Reloaded", "Sombras", "Neutral Cool/Warm", "#A38573", "Primavera", "Todas", "Satinado", 180000, P, "Paleta neutra versátil de alta gama."),
        ("Too Faced", "Born This Way Sunset", "Sombras", "Warm Gold/Coral", "#D48C46", "Primavera", "Todas", "Luminoso", 178000, P, "Tonos cálidos y veraniegos."),
        ("Colourpop", "Mauve Mood Palette", "Sombras", "Cool Mauves", "#9A7B9B", "Verano", "Todas", "Satinado", 85000, P, "Malvas y rosados fríos suaves."),
        ("Huda Beauty", "Obsessions Midnight Blue", "Sombras", "Navy & Silver", "#27355E", "Invierno", "Todas", "Mate", 98000, P, "Azules profundos y plateados."),
    ]

    cursor.executemany('''
        INSERT INTO products (brand, name, category, shade_name, hex_color, season_compat, skin_type_compat, finish, price_cop, image_url, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_products)


# Grupos de equivalencias: el primer elemento es el producto original ya existente (o nuevo).
DUPE_ORIGINALS_NEW = [
    ("NARS", "Blush", "Rubor", "Orgasm", "#E8907E", "Primavera", "Todas", "Luminoso", 155000,
     "El rubor durazno con destellos dorados más icónico."),
]
DUPE_GROUPS = [
    # (group_id, (marca, tono) del original, [dupes económicos])
    ("blush-peach-gold", ("NARS", "Orgasm"), [
        ("Ame Cosmetics", "Rubor Individual", "Rubor", "Durazno Rosado", "#E58F80", "Primavera", "Todas", "Luminoso", 28000, "Durazno rosado con brillo sutil."),
        ("Milani", "Baked Blush", "Rubor", "Coral Glow", "#E3957F", "Primavera", "Todas", "Luminoso", 52000, "Rubor horneado coral suave."),
    ]),
    ("lip-rose-nude", ("Rare Beauty", "Humble (Rose Nude)"), [
        ("Vogue", "Colorissimo Duración 8h", "Labial", "Rosa Nude", "#BA6D78", "Verano", "Todas", "Mate", 18000, "Rosa nude mate económico."),
    ]),
    ("lip-terracotta", ("Mac", "Brick-o-la"), [
        ("NYX", "Soft Matte Lip Cream", "Labial", "Rome (Terracota)", "#8F3C31", "Otoño", "Todas", "Mate", 42000, "Terracota ladrillo cremoso."),
        ("Ame Cosmetics", "Labial Liquido Mate", "Labial", "Terracota", "#8C3A30", "Otoño", "Todas", "Mate", 32000, "Terracota profundo de larga duración."),
    ]),
    ("lip-pillow-talk", ("Charlotte Tilbury", "Pillow Talk Medium"), [
        ("Vogue", "Colorissimo Duración 8h", "Labial", "Rosa Cacao", "#A65B54", "Otoño", "Todas", "Satinado", 18000, "Rosa cálido amarronado."),
    ]),
    ("gloss-fenty-glow", ("Fenty Beauty", "Fenty Glow"), [
        ("NYX", "Butter Gloss", "Labial", "Praline", "#C97F57", "Otoño", "Todas", "Luminoso", 36000, "Gloss cremoso color praliné."),
    ]),
    ("base-mac-nc25", ("MAC", "NC25"), [
        ("Ruby Rose", "HB-8100 Base Líquida", "Base", "Beige Medio", "#D9B28A", "Otoño", "Normal", "Satinado", 30000, "Base accesible beige medio."),
        ("Maybelline", "Fit Me Matte + Poreless", "Base", "230 Natural Buff", "#D7AF86", "Otoño", "Grasa", "Mate", 45000, "Control de brillo en beige natural."),
    ]),
    ("shadow-naked", ("Urban Decay", "Neutral Cool/Warm"), [
        ("Beauty Creations", "Nude Mood Palette", "Sombras", "Neutral Mood", "#A58774", "Primavera", "Todas", "Satinado", 65000, "Paleta neutra versátil económica."),
    ]),
]
INSERT_PRODUCT = '''
    INSERT INTO products (brand, name, category, shade_name, hex_color, season_compat,
                          skin_type_compat, finish, price_cop, image_url, description, dupes_group_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
'''


def _ensure_product(cursor, row, group_id):
    """Inserta el producto si no existe (brand+name+shade) y le asigna su grupo de dupes."""
    found = cursor.execute(
        "SELECT id FROM products WHERE brand = ? AND name = ? AND shade_name = ?",
        (row[0], row[1], row[3])).fetchone()
    if found:
        cursor.execute("UPDATE products SET dupes_group_id = ? WHERE id = ?", (group_id, found[0]))
    else:
        cursor.execute(INSERT_PRODUCT, (*row[:9], PLACEHOLDER, row[9], group_id))


def seed_dupes(cursor):
    """Agrega originales de gama alta y sus alternativas económicas (idempotente)."""
    for row in DUPE_ORIGINALS_NEW:
        _ensure_product(cursor, row, None)
    for group_id, (brand, shade), dupes in DUPE_GROUPS:
        original = cursor.execute(
            "SELECT id FROM products WHERE LOWER(brand) = LOWER(?) AND shade_name LIKE ?",
            (brand, f"{shade}%")).fetchone()
        if original:
            cursor.execute("UPDATE products SET dupes_group_id = ? WHERE id = ?", (group_id, original[0]))
        for row in dupes:
            _ensure_product(cursor, row, group_id)


if __name__ == '__main__':
    init_db()
    print("Base de datos inicializada y poblada correctamente con catálogo en COP.")
