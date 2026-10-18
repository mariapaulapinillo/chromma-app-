import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, get_connection
from recommender import recommend_products, parse_budget_limit


class TestRecommender(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def test_parse_budget(self):
        self.assertEqual(parse_budget_limit("Económico (Hasta $50,000 COP)"), 50000)
        self.assertEqual(parse_budget_limit("Medio ($50,000 - $100,000 COP)"), 100000)
        self.assertEqual(parse_budget_limit("Premium ($100,000 - $180,000 COP)"), 180000)
        self.assertEqual(parse_budget_limit("Sin restricción de presupuesto"), 9999999)
        self.assertEqual(parse_budget_limit(""), 9999999)

    def test_seed_size(self):
        conn = get_connection()
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        conn.close()
        self.assertGreaterEqual(count, 20)

    def test_init_db_is_idempotent(self):
        conn = get_connection()
        before = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        conn.close()
        init_db()
        conn = get_connection()
        after = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        conn.close()
        self.assertEqual(before, after)

    def test_recommendations_season_and_budget(self):
        user_profile = {
            "season": "Otoño",
            "skin_type": "Grasa (brillo en todo el rostro)",
            "finish": "Mate (sin brillo)",
            "budget": "Medio ($50,000 - $100,000 COP)"
        }
        recs = recommend_products(user_profile)
        self.assertTrue(len(recs) > 0)

        for item in recs:
            self.assertLessEqual(item["price_cop"], 100000)
            self.assertIn(item["season"], ["Otoño", "Todas"])

    def test_skin_type_excludes_incompatible(self):
        recs = recommend_products({"season": "Primavera", "skin_type": "Seca (tirantez)",
                                   "finish": "Luminoso / Dewy", "budget": "Sin restricción"})
        self.assertTrue(len(recs) > 0)
        for item in recs:
            self.assertIn(item["skin_type"], ["Seca", "Todas"])

    def test_budget_economico_limit(self):
        recs = recommend_products({"season": "Invierno", "skin_type": "Normal",
                                   "finish": "Mate", "budget": "Económico (Hasta $50,000 COP)"})
        self.assertTrue(len(recs) > 0)
        self.assertTrue(all(r["price_cop"] <= 50000 for r in recs))

    def test_finish_ranked_first(self):
        recs = recommend_products({"season": "Otoño", "skin_type": "Grasa",
                                   "finish": "Mate", "budget": "Sin restricción"})
        finishes = [r["finish"] == "Mate" for r in recs]
        # Dentro de un mismo nivel de season/skin, los Mate van antes; el primero debe ser Mate
        self.assertTrue(finishes[0])

    def test_price_format(self):
        recs = recommend_products({"season": "Verano", "skin_type": "Grasa", "budget": "Sin restricción"})
        item = next(r for r in recs if r["price_cop"] == 45000)
        self.assertEqual(item["price_formatted"], "$45.000 COP")


if __name__ == "__main__":
    unittest.main()
