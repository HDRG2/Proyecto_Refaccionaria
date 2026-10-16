import unittest
from types import SimpleNamespace

from AgenteIA.contexto_inventario import (
    ContextoInventario,
    crear_contexto_desde_productos,
    seleccionar_producto_contextual,
    obtener_producto_seleccionado,
    resolver_producto_contextual,
    resolver_seleccion_por_nombre,
    resolver_posicion_lista,
)


class TestContextoInventario(unittest.TestCase):

    def setUp(self):
        self.productos = [
            {
                "codigo": "AMO-005",
                "nombre": "Amortiguador Delantero",
                "precioMXN": 1450,
                "existencia": 5,
            },
            {
                "codigo": "ACE-001",
                "nombre": "Aceite de Motor 5W-30",
                "precioMXN": 350,
                "existencia": 3,
            },
        ]

    def mensaje(self, rol, texto):
        return SimpleNamespace(rol=rol, texto=texto)

    def test_no_elegir_producto_ambiguo(self):
        historial = [
            self.mensaje(
                "model",
                "Encontré Amortiguador Delantero "
                "(AMO-005) y Aceite de Motor "
                "(ACE-001)."
            ),
            self.mensaje("user", "¿Cuánto cuesta?"),
            self.mensaje(
                "model",
                "Indícame qué refacción deseas consultar."
            ),
        ]

        producto = resolver_producto_contextual(
            "¿Y cuántos quedan?",
            historial,
            self.productos,
        )

        self.assertIsNone(producto)

    def test_recuperar_producto_unico(self):
        historial = [
            self.mensaje(
                "model",
                "Encontré Amortiguador Delantero (AMO-005)."
            )
        ]

        producto = resolver_producto_contextual(
            "¿Cuánto cuesta?",
            historial,
            self.productos,
        )

        self.assertIsNotNone(producto)
        self.assertEqual(producto["codigo"], "AMO-005")

    def test_seleccion_explicita(self):
        contexto = crear_contexto_desde_productos(
            self.productos
        )

        seleccionado = seleccionar_producto_contextual(
            contexto,
            "AMO-005",
            self.productos,
        )

        self.assertTrue(seleccionado)
        self.assertEqual(
            contexto.codigo_seleccionado,
            "AMO-005",
        )

    def test_consultar_inventario_actualizado(self):
        contexto = ContextoInventario(
            codigo_seleccionado="AMO-005"
        )

        inventario_actualizado = [
            {
                "codigo": "AMO-005",
                "nombre": "Amortiguador Delantero",
                "precioMXN": 1600,
                "existencia": 2,
            }
        ]

        producto = obtener_producto_seleccionado(
            contexto,
            inventario_actualizado,
        )

        self.assertEqual(producto["precioMXN"], 1600)
        self.assertEqual(producto["existencia"], 2)

    def test_producto_eliminado(self):
        contexto = ContextoInventario(
            codigo_seleccionado="AMO-005"
        )

        producto = obtener_producto_seleccionado(
            contexto,
            []
        )

        self.assertIsNone(producto)

    def test_seleccionar_amortiguador_por_nombre(self):
        contexto = ContextoInventario(
            codigos_lista=["AMO-005", "ACE-001"]
        )

        producto = resolver_seleccion_por_nombre(
            "¿Cuánto cuesta el amortiguador?",
            contexto,
            self.productos,
        )

        self.assertIsNotNone(producto)
        self.assertEqual(producto["codigo"], "AMO-005")

    def test_no_seleccionar_sin_nombre(self):
        contexto = ContextoInventario(
            codigos_lista=["AMO-005", "ACE-001"]
        )

        producto = resolver_seleccion_por_nombre(
            "¿Cuánto cuesta?",
            contexto,
            self.productos,
        )

        self.assertIsNone(producto)

    def test_no_seleccionar_producto_fuera_de_lista(self):
        contexto = ContextoInventario(
            codigos_lista=["ACE-001"]
        )

        producto = resolver_seleccion_por_nombre(
            "El amortiguador",
            contexto,
            self.productos,
        )

        self.assertIsNone(producto)
    
    def test_posicion_primero(self):
        contexto = ContextoInventario(
            codigos_lista=["ACE-001", "AMO-005", "BAL-002", "BUJ-003", "FIL-001"]
        )
        productos = [{"codigo": codigo} for codigo in contexto.codigos_lista]
        estado, producto = resolver_posicion_lista(
                "¿Cuánto cuesta el primero?", contexto, productos
            )
    
        self.assertEqual(estado, "encontrado")
        self.assertEqual(producto["codigo"], "ACE-001")
    
    def test_posicion_tercero(self):
        contexto = ContextoInventario(
            codigos_lista=["ACE-001", "AMO-005", "BAL-002", "BUJ-003", "FIL-001"]
        )
        productos = [{"codigo": codigo} for codigo in contexto.codigos_lista]
    
        estado, producto = resolver_posicion_lista(
            "¿Cuánto cuesta el tercero?", contexto, productos
        )
    
        self.assertEqual(estado, "encontrado")
        self.assertEqual(producto["codigo"], "BAL-002")
    
    def test_posicion_quinto(self):
        contexto = ContextoInventario(
            codigos_lista=["ACE-001", "AMO-005", "BAL-002", "BUJ-003", "FIL-001"]
        )
        productos = [{"codigo": codigo} for codigo in contexto.codigos_lista]
    
        estado, producto = resolver_posicion_lista(
            "¿Cuánto cuesta el quinto?", contexto, productos
        )
    
        self.assertEqual(estado, "encontrado")
        self.assertEqual(producto["codigo"], "FIL-001")
    
    def test_posicion_sexto_inexistente(self):
        contexto = ContextoInventario(
            codigos_lista=["ACE-001", "AMO-005", "BAL-002", "BUJ-003", "FIL-001"]
        )
        productos = [{"codigo": codigo} for codigo in contexto.codigos_lista]
    
        estado, producto = resolver_posicion_lista(
            "¿Cuánto cuesta el sexto?", contexto, productos
        )
    
        self.assertEqual(estado, "fuera_de_rango")
        self.assertIsNone(producto)
    
    def test_posicion_sin_lista_previa(self):
        contexto = ContextoInventario()
        productos = [{"codigo": "ACE-001"}]
    
        estado, producto = resolver_posicion_lista(
            "¿Cuánto cuesta el primero?", contexto, productos
        )
    
        self.assertEqual(estado, "sin_lista")
        self.assertIsNone(producto)
    
    def test_posicion_producto_eliminado(self):
        contexto = ContextoInventario(
            codigos_lista=["ACE-001", "AMO-005"]
        )
        productos = [{"codigo": "ACE-001"}]
    
        estado, producto = resolver_posicion_lista(
            "¿Cuánto cuesta el segundo?", contexto, productos
        )
    
        self.assertEqual(estado, "producto_eliminado")
        self.assertIsNone(producto)


if __name__ == "__main__":
    unittest.main()
    
    

