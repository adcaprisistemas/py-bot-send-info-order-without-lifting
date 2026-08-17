import unittest

from src.alerts import discover_alerts, get_alert


class DiscoveryTest(unittest.TestCase):
    def test_descubrir_alertas(self):
        alertas = discover_alerts()
        self.assertIsInstance(alertas, list)
        nombres = [a["name"] for a in alertas]
        self.assertIn("ordenes_sin_levante", nombres)

    def test_estructura_alerta(self):
        alertas = discover_alerts()
        self.assertGreater(len(alertas), 0)
        for alerta in alertas:
            self.assertIn("name", alerta)
            self.assertIn("run", alerta)
            self.assertIn("jobs", alerta)
            self.assertTrue(callable(alerta["run"]))

    def test_get_alert_existente(self):
        alerta = get_alert("ordenes_sin_levante")
        self.assertIsNotNone(alerta)
        self.assertEqual(alerta["name"], "ordenes_sin_levante")

    def test_get_alert_inexistente(self):
        alerta = get_alert("modulo_inexistente")
        self.assertIsNone(alerta)


if __name__ == "__main__":
    unittest.main()
