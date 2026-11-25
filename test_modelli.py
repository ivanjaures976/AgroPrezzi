import unittest

from modelli import Coltura, Allevamento
from scenari import Scenario, confronta


class TestColtura(unittest.TestCase):
    def setUp(self):
        # 1000 m2 x 2 kg/m2 = 2000 kg; prezzo 1.50 EUR/kg
        self.c = Coltura("Pomodori", 1000, 2, 1.50)
        self.c.aggiungi_costo("Semi", 400)
        self.c.aggiungi_costo("Manodopera", 1100)

    def test_costi_ricavi_margine(self):
        self.assertEqual(self.c.costi_totali(), 1500)
        self.assertEqual(self.c.ricavi(), 3000)
        self.assertEqual(self.c.margine(), 1500)
        self.assertAlmostEqual(self.c.margine_percentuale(), 50.0)

    def test_prezzo_minimo(self):
        # 1500 EUR / 2000 kg = 0.75 EUR/kg
        self.assertAlmostEqual(self.c.prezzo_minimo(), 0.75)

    def test_produzione_zero(self):
        vuota = Coltura("Vuota", 0, 2, 1.50)
        self.assertIsNone(vuota.prezzo_minimo())
        self.assertEqual(vuota.margine_percentuale(), 0.0)

    def test_valori_non_validi(self):
        with self.assertRaises(ValueError):
            Coltura("", 100, 1, 1)
        with self.assertRaises(ValueError):
            self.c.aggiungi_costo("Errore", -5)


class TestAllevamento(unittest.TestCase):
    def test_animali_persi(self):
        # 100 animali, 10% persi -> 90 x 5 kg = 450 kg
        a = Allevamento("Polli", 100, 10, 5, 4.0)
        self.assertAlmostEqual(a.animali_finali(), 90)
        self.assertAlmostEqual(a.kg_venduti(), 450)
        self.assertAlmostEqual(a.ricavi(), 1800)

    def test_percentuale_fuori_intervallo(self):
        with self.assertRaises(ValueError):
            Allevamento("Polli", 100, 120, 5, 4.0)


class TestScenari(unittest.TestCase):
    def test_confronto_non_modifica_originale(self):
        c = Coltura("Grano", 1000, 1, 1.0)
        c.aggiungi_costo("Costi", 500)
        righe = confronta(c, [Scenario("Prezzo alto", prezzo_kg=2.0)])
        self.assertEqual(c.prezzo_kg, 1.0)
        self.assertEqual(righe[0]["margine"], 500)
        self.assertEqual(righe[1]["margine"], 1500)
        self.assertEqual(righe[1]["diff_base"], 1000)


if __name__ == "__main__":
    unittest.main()