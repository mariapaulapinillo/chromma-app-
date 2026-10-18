import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma.db")
PLACEHOLDER = "https://via.placeholder.com/150"


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
            description TEXT
        )
    ''')

    # Comprobar si ya existen datos para evitar duplicados
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        seed_products(cursor)

    conn.commit()
    conn.close()


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


if __name__ == '__main__':
    init_db()
    print("Base de datos inicializada y poblada correctamente con catálogo en COP.")
