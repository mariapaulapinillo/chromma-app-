import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, get_connection
from ingredients import analyze_ingredients
from dupes import color_distance, hex_to_rgb, delta_e, find_dupes


class TestDupesAndIngredients(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def test_ingredient_warnings(self):
        incis = "Water, Alcohol Denat, Fragrance, Glycerin"
        result = analyze_ingredients(incis)
        self.assertTrue(result["has_alcohol"])
        self.assertTrue(result["has_fragrance"])
        self.assertFalse(result["is_safe_sensitive"])
        self.assertIn("⚠️ Contiene Alcohol", result["badges"])
        self.assertIn("⚠️ Contiene Fragancia", result["badges"])

    def test_safe_sensitive_badges(self):
        result = analyze_ingredients("Water, Glycerin, Cetearyl Alcohol, Dimethicone")
        self.assertFalse(result["has_alcohol"])  # alcohol graso no irrita
        self.assertEqual(result["badges"], ["🌿 Apto Piel Sensible", "🚫 No Comedogénico"])
        self.assertEqual(result["warnings"], [])

    def test_comedogenic_and_empty(self):
        self.assertTrue(analyze_ingredients("Isopropyl Myristate, Water")["is_comedogenic"])
        empty = analyze_ingredients(None)
        self.assertFalse(empty["has_alcohol"])
        self.assertTrue(empty["is_safe_sensitive"])

    def test_color_distance_exact(self):
        self.assertEqual(color_distance("#FFFFFF", "#FFFFFF"), 0)
        self.assertEqual(hex_to_rgb("#FF0080"), (255, 0, 128))
        self.assertEqual(delta_e("#E8907E", "#E8907E"), 0)

    def test_db_has_dermatological_columns_and_dupes(self):
        conn = get_connection()
        cols = {r[1] for r in conn.execute("PRAGMA table_info(products)")}
        grouped = conn.execute(
            "SELECT COUNT(*) FROM products WHERE dupes_group_id IS NOT NULL").fetchone()[0]
        missing = conn.execute(
            "SELECT COUNT(*) FROM products WHERE ingredients_list IS NULL").fetchone()[0]
        conn.close()
        self.assertTrue({"ingredients_list", "contains_alcohol", "contains_fragrance",
                         "is_sensitive_safe", "is_comedogenic", "dupes_group_id"} <= cols)
        self.assertGreaterEqual(grouped, 10)
        self.assertEqual(missing, 0)

    def test_find_dupes_by_shade_name(self):
        dupes = find_dupes("NARS Orgasm")
        self.assertGreaterEqual(len(dupes), 1)
        for d in dupes:
            self.assertLessEqual(d["delta_e"], 5)
            self.assertGreater(d["savings_cop"], 0)
        self.assertEqual(dupes, sorted(dupes, key=lambda d: -d["similarity_percentage"]))

    def test_find_dupes_max_price_and_unknown(self):
        self.assertTrue(all(d["price_cop"] <= 30000 for d in find_dupes("NARS Orgasm", max_price=30000)))
        self.assertEqual(find_dupes("producto inexistente xyz"), [])
        self.assertEqual(find_dupes(999999), [])


if __name__ == "__main__":
    unittest.main()
