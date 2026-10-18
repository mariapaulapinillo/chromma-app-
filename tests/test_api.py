import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def post(self, payload):
        return self.app.post('/api/diagnose', data=json.dumps(payload),
                             content_type='application/json')

    def test_index_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Chroma'.encode(), response.data)

    def test_get_questionnaire(self):
        response = self.app.get('/api/questionnaire')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('section_1_colorimetry', data)
        self.assertIn('section_2_skin_type', data)
        self.assertIn('section_3_preferences', data)
        self.assertEqual(sum(len(s) for s in data.values()), 27)

    def test_diagnose_endpoint(self):
        sample_answers = {
            "skin_tone": "Clara",
            "undertone_self": "Rosado / Rojizo / Azulado",
            "veins": "Azules o violetas",
            "sun_reaction": "Se quema muy fácil, casi nunca se broncea",
            "metal_test": "Plata, oro blanco o platino",
            "white_test": "Blanco puro / Blanco óptico radiante",
            "hair_natural_color": "Negro azabache / Negro profundo",
            "eye_color": "Café oscuro, marrón profundo o negro",
            "contrast_level": "Alto contraste (ej. piel clara y cabello/ojos muy oscuros)",
            "skin_type": "Grasa (brillo en todo el rostro, poros dilatados)",
            "finish_preference": "Mate (sin brillo, control de grasa)",
            "budget_range": "Medio ($50,000 - $100,000 COP)"
        }
        response = self.post(sample_answers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['colorimetry']['season'], "Invierno")
        self.assertIsInstance(data['recommendations'], list)
        self.assertTrue(len(data['recommendations']) > 0)
        for item in data['recommendations']:
            self.assertLessEqual(item['price_cop'], 100000)
            self.assertIn(item['season'], ["Invierno", "Todas"])

    def test_diagnose_returns_dashboard_fields(self):
        data = json.loads(self.post({"veins": "Verdes u oliváceas", "metal_test": "Oro amarillo, bronce o cobre",
                                     "budget_range": "Sin restricción de presupuesto"}).data)
        c = data['colorimetry']
        for key in ("season", "temperature", "contrast", "palette", "confidence_score", "jewelry", "clothing"):
            self.assertIn(key, c)
        for item in data['recommendations']:
            for key in ("image_url", "brand", "name", "shade_name", "hex_color", "skin_type", "finish", "price_formatted"):
                self.assertIn(key, item)

    def test_diagnose_empty_body_is_400(self):
        response = self.app.post('/api/diagnose', data='{}', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_diagnose_malformed_json_is_400(self):
        response = self.app.post('/api/diagnose', data='no es json', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_diagnose_non_object_is_400(self):
        self.assertEqual(self.post(["Clara"]).status_code, 400)

    def test_diagnose_invalid_answer_is_400(self):
        response = self.post({"skin_tone": "Verde marciana"})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', json.loads(response.data))

    def test_diagnose_without_colorimetry_answers_is_400(self):
        response = self.post({"skin_type": "Grasa (brillo en todo el rostro, poros dilatados)"})
        self.assertEqual(response.status_code, 400)

    def test_diagnose_non_string_preference_is_400(self):
        response = self.post({"veins": "Azules o violetas", "budget_range": 5})
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
