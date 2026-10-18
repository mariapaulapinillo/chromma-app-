import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from colorimetry import calculate_colorimetry
from questionnaire import QUESTIONNAIRE_SCHEMA


class TestColorimetryEngine(unittest.TestCase):

    def test_winter_profile(self):
        answers = {
            "skin_tone": "Clara",
            "undertone_self": "Rosado / Rojizo / Azulado",
            "veins": "Azules o violetas",
            "sun_reaction": "Se quema muy fácil, casi nunca se broncea",
            "metal_test": "Plata, oro blanco o platino",
            "white_test": "Blanco puro / Blanco óptico radiante",
            "hair_natural_color": "Negro azabache / Negro profundo",
            "eye_color": "Café oscuro, marrón profundo o negro",
            "contrast_level": "Alto contraste (ej. piel clara y cabello/ojos muy oscuros)"
        }
        result = calculate_colorimetry(answers)
        self.assertEqual(result["season"], "Invierno")
        self.assertEqual(result["temperature"], "Fría")
        self.assertGreater(result["confidence_score"], 60)

    def test_autumn_profile(self):
        answers = {
            "skin_tone": "Morena / Olival",
            "undertone_self": "Dorado / Amarillento / Durazno",
            "veins": "Verdes u oliváceas",
            "sun_reaction": "Se broncea intensamente sin quemarse",
            "metal_test": "Oro amarillo, bronce o cobre",
            "white_test": "Blanco marfil / Blanco crema / Hueso",
            "hair_natural_color": "Rubio dorado / Cobrizo / Castaño claro cálido",
            "eye_color": "Verde oliva, miel o ámbar",
            "contrast_level": "Bajo contraste (todos mis rasgos son de intensidad similar)"
        }
        result = calculate_colorimetry(answers)
        self.assertEqual(result["season"], "Otoño")
        self.assertEqual(result["temperature"], "Cálida")

    def test_spring_profile(self):
        answers = {
            "skin_tone": "Clara",
            "undertone_self": "Dorado / Amarillento / Durazno",
            "veins": "Verdes u oliváceas",
            "metal_test": "Oro amarillo, bronce o cobre",
            "white_test": "Blanco marfil / Blanco crema / Hueso",
            "hair_natural_color": "Rubio dorado / Cobrizo / Castaño claro cálido",
            "eye_color": "Azul claro, gris o verde claro",
            "saturations": "Luminosos y puros (Alta saturación)",
        }
        result = calculate_colorimetry(answers)
        self.assertEqual(result["season"], "Primavera")
        self.assertEqual(result["temperature"], "Cálida")

    def test_summer_profile(self):
        answers = {
            "skin_tone": "Clara",
            "undertone_self": "Rosado / Rojizo / Azulado",
            "veins": "Azules o violetas",
            "metal_test": "Plata, oro blanco o platino",
            "white_test": "Gris claro o beige preferiblemente",
            "hair_natural_color": "Rubio muy claro / Platino / Ceniza",
            "eye_color": "Azul claro, gris o verde claro",
            "saturations": "Opacos, grises o empolvados (Baja saturación)",
        }
        result = calculate_colorimetry(answers)
        self.assertEqual(result["season"], "Verano")
        self.assertEqual(result["temperature"], "Fría")

    def test_result_shape(self):
        result = calculate_colorimetry({"veins": "Azules o violetas"})
        for key in ("season", "temperature", "subtone", "contrast", "palette", "confidence_score"):
            self.assertIn(key, result)
        self.assertTrue(all(c.startswith("#") and len(c) == 7 for c in result["palette"]))
        self.assertTrue(0 <= result["confidence_score"] <= 100)

    def test_advice_per_season(self):
        for season, answers in {
            "Invierno": {"veins": "Azules o violetas", "hair_natural_color": "Negro azabache / Negro profundo",
                         "saturations": "Luminosos y puros (Alta saturación)"},
            "Otoño": {"veins": "Verdes u oliváceas", "skin_tone": "Morena / Olival",
                      "saturations": "Opacos, grises o empolvados (Baja saturación)"},
        }.items():
            result = calculate_colorimetry(answers)
            self.assertEqual(result["season"], season)
            self.assertTrue(result["jewelry"]["metals"])
            self.assertTrue(result["clothing"]["best"])
            self.assertTrue(result["clothing"]["avoid"])

    def test_invalid_answer_raises(self):
        with self.assertRaises(ValueError):
            calculate_colorimetry({"skin_tone": "Verde marciana"})

    def test_empty_answers_raises(self):
        with self.assertRaises(ValueError):
            calculate_colorimetry({"skin_type": "Grasa (brillo en todo el rostro, poros dilatados)"})


class TestQuestionnaireSchema(unittest.TestCase):

    def test_structure_has_27_questions(self):
        s = QUESTIONNAIRE_SCHEMA
        self.assertEqual(len(s["section_1_colorimetry"]), 24)
        self.assertEqual(len(s["section_2_skin_type"]), 1)
        self.assertEqual(len(s["section_3_preferences"]), 2)
        ids = [q["id"] for sec in s.values() for q in sec]
        self.assertEqual(len(ids), 27)
        self.assertEqual(len(set(ids)), 27)


if __name__ == "__main__":
    unittest.main()
