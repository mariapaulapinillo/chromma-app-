import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import get_connection
from cosmetic_bag import plan_for_occasion
from stores import find_stores, haversine_km
from recommender import recommend_products


def product_id(brand, shade):
    conn = get_connection()
    row = conn.execute("SELECT id FROM products WHERE brand = ? AND shade_name LIKE ?",
                       (brand, f"{shade}%")).fetchone()
    conn.close()
    return row["id"]


class TestSprint6(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def post(self, url, payload):
        return self.client.post(url, data=json.dumps(payload), content_type='application/json')

    def test_dupes_endpoint(self):
        pid = product_id("NARS", "Orgasm")
        data = self.client.get(f'/api/dupes/{pid}').get_json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["dupes"]), 1)
        cheap = self.client.get(f'/api/dupes/{pid}?max_price=30000').get_json()
        self.assertTrue(all(d["price_cop"] <= 30000 for d in cheap["dupes"]))

    def test_analyze_ingredients_endpoint(self):
        r = self.post('/api/analyze-ingredients', {"ingredients": "Water, Parfum"})
        self.assertIn("⚠️ Contiene Fragancia", r.get_json()["analysis"]["badges"])
        self.assertEqual(self.post('/api/analyze-ingredients', {"ingredients": 5}).status_code, 400)
        self.assertEqual(self.client.post('/api/analyze-ingredients', data="x",
                                          content_type='application/json').status_code, 400)

    def test_catalog_has_badges(self):
        products = self.client.get('/api/catalog').get_json()["products"]
        self.assertTrue(all("badges" in p for p in products))
        self.assertTrue(any(p["is_high_end"] for p in products))

    def test_sensitive_skin_only_safe_products(self):
        profile = {"season": "Primavera", "skin_type": "Sensible (tendencia a rojeces)",
                   "finish": "", "budget": ""}
        results = recommend_products(profile)
        conn = get_connection()
        for p in results:
            safe = conn.execute("SELECT is_sensitive_safe FROM products WHERE id = ?",
                                (p["id"],)).fetchone()[0]
            self.assertEqual(safe, 1)
        conn.close()

    def test_bag_plan_message(self):
        plan = plan_for_occasion([product_id("Maybelline", "120"), product_id("NARS", "Exhibit")], "oficina", "Invierno")
        self.assertEqual(plan["completion"], 50)
        self.assertIn("Te faltan", plan["message"])
        self.assertEqual(sorted(plan["missing"]), ["Labial", "Sombras"])
        owned_steps = [s for s in plan["steps"] if s["status"] == "Ya lo tienes"]
        self.assertEqual(len(owned_steps), 2)

    def test_bag_plan_single_missing_and_complete(self):
        ids = [product_id("Maybelline", "120"), product_id("Maybelline", "Light Neutral"),
               product_id("NARS", "Exhibit")]
        plan = plan_for_occasion(ids, "dia", "Invierno")
        self.assertEqual(plan["completion"], 100)
        self.assertIn("100%", plan["message"])
        plan = plan_for_occasion(ids[:2], "dia", "Invierno")
        self.assertEqual(plan["message"], "¡Kit 67% completo! Solo te falta un rubor frío para tu look de día.")

    def test_bag_plan_endpoint_validation(self):
        ok = self.post('/api/bag-plan', {"bag": [], "occasion": "fiesta"})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(self.post('/api/bag-plan', {"bag": ["x"], "occasion": "dia"}).status_code, 400)
        self.assertEqual(self.post('/api/bag-plan', {"bag": [], "occasion": "boda"}).status_code, 400)

    def test_stores_endpoint(self):
        pid = product_id("NARS", "Orgasm")
        online = self.client.get(f'/api/stores/{pid}').get_json()["stores"]
        self.assertEqual(online["physical"], [])
        self.assertTrue(online["online"][0]["best_price"])
        prices = [s["price_cop"] for s in online["online"]]
        self.assertEqual(prices, sorted(prices))
        near = self.client.get(f'/api/stores/{pid}?lat=4.70&lon=-74.04').get_json()["stores"]
        self.assertEqual(near["physical"][0]["city"], "Bogotá")
        self.assertLessEqual(len(near["physical"]), 4)
        self.assertEqual(self.client.get(f'/api/stores/{pid}?lat=4.7').status_code, 400)
        self.assertEqual(self.client.get('/api/stores/999999').status_code, 404)

    def test_haversine_and_farmatodo_high_end(self):
        self.assertAlmostEqual(haversine_km(4.7, -74.0, 4.7, -74.0), 0)
        names = {s["retailer"] for s in find_stores(product_id("NARS", "Orgasm"))["online"]}
        self.assertNotIn("Farmatodo", names)

    def test_diagnose_includes_badges(self):
        r = self.client.get('/api/questionnaire').get_json()
        answers = {q["id"]: q["options"][0] for s in r.values() for q in s}
        data = self.post('/api/diagnose', answers).get_json()
        self.assertTrue(all("badges" in p and "is_high_end" in p for p in data["recommendations"]))


if __name__ == "__main__":
    unittest.main()
