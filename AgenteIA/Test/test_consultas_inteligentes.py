import unittest

from AgenteIA.inventario.consultas_inteligentes import (
    consultar_inventario_inteligente,
)


class TestConsultasInteligentes(unittest.TestCase):

    def setUp(self):
        # Inventario de prueba independiente del real.
        self.productos = [
            {
                "codigo": "AMO-005",
                "nombre": "Amortiguador Delantero",
                "categoria": "Suspensión",
                "precioMXN": 1450,
                "existencia": 7,
                "universal": False,
                "vehiculosCompatibles": [
                    "Toyota Corolla (2014–2019)"
                ],
            },
            {
                "codigo": "BAL-002",
                "nombre": "Balatas delanteras",
                "categoria": "Frenos",
                "precioMXN": 1249,
                "existencia": 15,
                "universal": False,
                "vehiculosCompatibles": [
                    "Nissan Sentra (2013–2019)"
                ],
            },
            {
                "codigo": "ACE-001",
                "nombre": "Aceite de Motor 5W-30",
                "categoria": "Aceites",
                "precioMXN": 749,
                "existencia": 0,
                "universal": True,
                "vehiculosCompatibles": [],
            },
        ]

    def consultar(self, pregunta):
        return consultar_inventario_inteligente(
            pregunta,
            self.productos
        )

    def test_busqueda_categoria(self):
        respuesta = self.consultar(
            "Muéstrame los productos de suspensión"
        )
        self.assertIn("AMO-005", respuesta)
        self.assertNotIn("BAL-002", respuesta)

    def test_producto_mas_barato(self):
        respuesta = self.consultar(
            "¿Cuál es la refacción más barata?"
        )
        self.assertIn("ACE-001", respuesta)
        self.assertIn("749.00", respuesta)

    def test_productos_agotados(self):
        respuesta = self.consultar(
            "Muéstrame los productos agotados"
        )
        self.assertIn("ACE-001", respuesta)
        self.assertNotIn("AMO-005", respuesta)

    def test_vehiculo_compatible(self):
        respuesta = self.consultar(
            "¿Qué refacciones tienes para un Toyota Corolla 2018?"
        )
        self.assertIn("AMO-005", respuesta)
        self.assertNotIn("BAL-002", respuesta)

    def test_anio_fuera_de_rango(self):
        respuesta = self.consultar(
            "¿Qué refacciones tienes para un Toyota Corolla 2024?"
        )
        self.assertIn("Total de coincidencias: 0", respuesta)
        self.assertNotIn("AMO-005", respuesta)

    def test_vehiculo_desconocido(self):
        respuesta = self.consultar(
            "¿Qué refacciones tienes para un Honda Civic 2018?"
        )
        self.assertIn(
            "No pude identificar",
            respuesta
        )

    def test_busqueda_combinada(self):
        respuesta = self.consultar(
            "¿Tienes amortiguadores para un Toyota Corolla 2018?"
        )
        self.assertIn("AMO-005", respuesta)
        self.assertNotIn("ACE-001", respuesta)

    def test_busqueda_combinada_sin_resultados(self):
        respuesta = self.consultar(
            "¿Tienes balatas para un Toyota Corolla 2018?"
        )
        self.assertIn("Total de coincidencias: 0", respuesta)
        self.assertNotIn("AMO-005", respuesta)
        self.assertNotIn("BAL-002", respuesta)

    def test_recomendacion_aceite_segura(self):
        respuesta = self.consultar(
            "¿Qué aceite recomiendas para un Corolla 2018?"
        )
        self.assertIn(
            "verificar las especificaciones",
            respuesta
        )
        self.assertNotIn("ACE-001", respuesta)


if __name__ == "__main__":
    unittest.main()
