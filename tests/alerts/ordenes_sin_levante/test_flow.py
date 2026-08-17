import http.server
import json
import os
import socketserver
import threading
import unittest

os.environ["LEVANTE_API_GET_URL"] = "http://127.0.0.1:8899/ordenes"
os.environ["LEVANTE_API_POST_URL"] = "http://127.0.0.1:8899/enviar"
os.environ["MAX_REINTENTOS"] = "1"
os.environ["EJECUTAR_AL_INICIAR"] = "false"

from src.alerts.ordenes_sin_levante import module as levante_module  # noqa: E402


class _Handler(http.server.BaseHTTPRequestHandler):
    get_status = 200
    get_body = []
    post_status = 200
    post_bodies = []

    def do_GET(self):
        body = json.dumps(self.get_body).encode()
        self.send_response(self.get_status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(length)
        _Handler.post_bodies.append(json.loads(payload))
        self.send_response(self.post_status)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, fmt, *args):
        pass


class FlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = socketserver.TCPServer(("127.0.0.1", 8899), _Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def setUp(self):
        _Handler.get_status = 200
        _Handler.get_body = [
            {
                "id": 1,
                "codigo": "A",
                "COD_USU_JEFE": 10,
                "CORREO_JEFE": "jefe@x.com",
                "COD_USU_SECTORISTA": 20,
                "CORREO_SECTORISTA": "sec@x.com",
                "COD_USU_APERTURA": 30,
                "CORREO_USU_APERTURA": "ap@x.com",
                "CODIGO_DESPACHO": "1-0",
                "FECHA_NUMERACION": "2024-01-01",
            },
            {
                "id": 2,
                "codigo": "B",
                "COD_USU_JEFE": 10,
                "CORREO_JEFE": "jefe@x.com",
                "COD_USU_SECTORISTA": 21,
                "CORREO_SECTORISTA": "sec2@x.com",
                "COD_USU_APERTURA": 30,
                "CORREO_USU_APERTURA": "ap@x.com",
                "CODIGO_DESPACHO": "0-0",
                "FECHA_NUMERACION": "2024-01-02",
            },
        ]
        _Handler.post_status = 200
        _Handler.post_bodies = []

    def test_modulo_expone_run_y_schedule(self):
        self.assertTrue(callable(levante_module.run))
        self.assertTrue(callable(levante_module.schedule))

    def test_ejecuta_modulo(self):
        metricas = levante_module.run()
        self.assertIsInstance(metricas, dict)
        self.assertGreaterEqual(len(_Handler.post_bodies), 1)

    def test_sin_ordenes_no_envia_nada(self):
        _Handler.get_body = []
        levante_module.run()
        self.assertEqual(len(_Handler.post_bodies), 0)

    def test_orden_fallida_no_detiene_las_demas(self):
        _Handler.post_status = 500
        levante_module.run()
        self.assertGreaterEqual(len(_Handler.post_bodies), 0)

    def test_error_al_obtener_ordenes_no_lanza_excepcion(self):
        _Handler.get_status = 500
        levante_module.run()
        self.assertEqual(len(_Handler.post_bodies), 0)


if __name__ == "__main__":
    unittest.main()
