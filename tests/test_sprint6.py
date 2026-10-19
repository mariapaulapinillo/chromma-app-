import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


class TestSprint6API(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def post(self, url, payload):
        return self.app.post(url, data=json.dumps(payload), content_type='application/json')

    def test_dupes_endpoint(self):
        response = self.app.get('/api/dupes/search?q=NARS Orgasm')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIsInstance(data['dupes'], list)
        self.assertGreaterEqual(len(data['dupes']), 1)

    def test_dupes_search_requires_query_and_unknown_is_empty(self):
        self.assertEqual(self.app.get('/api/dupes/search').status_code, 400)
        self.assertEqual(self.app.get('/api/dupes/search?q=zzzz').get_json()['dupes'], [])

    def test_cosmetic_bag_recommendation(self):
        payload = {
            "user_profile": {"season": "Otoño", "skin_type": "Grasa", "finish": "Mate", "budget": "Medio"},
            "owned_product_ids": [1, 2],
        }
        response = self.post('/api/cosmetic-bag/recommend', payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('completion_percentage', data)
        owned_ids = {p['id'] for p in data['owned_items']}
        missing_ids = {p['id'] for p in data['missing_items']}
        self.assertFalse(owned_ids & missing_ids)
        self.assertTrue(owned_ids <= {1, 2})
        self.assertTrue(all(p['status'] == "Ya lo tienes en tu cosmetiquera" for p in data['owned_items']))
        self.assertTrue(all(p['status'] == "Sugerido para completar tu kit" for p in data['missing_items']))

    def test_cosmetic_bag_validation(self):
        self.assertEqual(self.post('/api/cosmetic-bag/recommend', {"owned_product_ids": ["a"]}).status_code, 400)
        self.assertEqual(self.post('/api/cosmetic-bag/recommend', {"user_profile": []}).status_code, 400)
        self.assertEqual(self.app.post('/api/cosmetic-bag/recommend', data="x",
                                       content_type='application/json').status_code, 400)

    def test_ui_has_new_sections(self):
        html = self.app.get('/').get_data(as_text=True)
        for marker in ('id="dupes-screen"', 'id="cosmetic-bag-screen"', 'Test Colorimetría'):
            self.assertIn(marker, html)


if __name__ == '__main__':
    unittest.main()
