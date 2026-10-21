import asyncio
import json
from types import SimpleNamespace

import pytest

import AgenteIA.asistente.reescritura as reescritura
from AgenteIA.asistente.reescritura import construir_frase


INVENTARIO = [
    {"codigo": "ACE-001", "nombre": "Aceite de Motor 5W-30", "marca": "Mobil",
     "categoria": "Aceites", "precio": 749, "existencia": 3},
    {"codigo": "BAL-002", "nombre": "Balatas delanteras Ceramitas", "marca": "Brembo",
     "categoria": "Frenos", "precio": 1249, "existencia": 15,
     "vehiculosCompatibles": ["Nissan Versa 2012-2019"]},
    {"codigo": "BUJ-003", "nombre": "Bujia de encendido", "marca": "NGK",
     "categoria": "Encendido", "precio": 120, "existencia": 40},
    {"codigo": "PRU-012", "nombre": "Banda de accesorios", "marca": "Gates",
     "categoria": "Motor", "precio": 420, "existencia": 10},
]
CODIGOS = [p["codigo"] for p in INVENTARIO]
VIENDO_ACEITE = SimpleNamespace(codigo_seleccionado="ACE-001", codigos_lista=CODIGOS)
SIN_NADA = SimpleNamespace(codigo_seleccionado=None, codigos_lista=[])


@pytest.mark.parametrize("clasificacion, contexto, frase", [
    ({"tipo": "pagina_siguiente"}, VIENDO_ACEITE, "siguientes productos"),
    ({"tipo": "pagina_siguiente"}, SIN_NADA, None),               # no hay lista
    ({"tipo": "posicion", "numero": "3"}, VIENDO_ACEITE, "el producto 3"),
    ({"tipo": "precio", "codigo": "BAL-002"}, SIN_NADA, "¿cuánto cuesta el BAL-002?"),
    ({"tipo": "precio", "codigo": ""}, VIENDO_ACEITE, "¿cuánto cuesta el ACE-001?"),
    ({"tipo": "precio", "codigo": ""}, SIN_NADA, None),           # no hay producto
    ({"tipo": "precio", "codigo": "XYZ-999"}, VIENDO_ACEITE, None),  # código inventado
    ({"tipo": "calcular_venta", "codigo": "", "cantidad": "4", "descuento": "15"},
     VIENDO_ACEITE, "si vendo 4 del ACE-001 con 15% de descuento"),
    ({"tipo": "calcular_venta", "codigo": "BAL-002", "cantidad": ""}, SIN_NADA, None),
    ({"tipo": "listar_categoria", "categoria": "Frenos"}, SIN_NADA, "¿qué tenemos de frenos?"),
    ({"tipo": "listar_categoria", "categoria": "Llantas"}, SIN_NADA, None),  # no existe
    ({"tipo": "recomendar_venta", "categoria": "Encendido"}, SIN_NADA,
     "un cliente quiere encendido, ¿qué le ofrezco?"),
    ({"tipo": "compatibilidad", "codigo": "BAL-002", "vehiculo": "Nissan Versa 2015"},
     SIN_NADA, "¿el BAL-002 es compatible con un Nissan Versa 2015?"),
    ({"tipo": "compatibilidad", "codigo": "BAL-002", "vehiculo": "Versa"}, SIN_NADA, None),
    ({"tipo": "stock_bajo"}, SIN_NADA, "¿qué tiene poco stock?"),
    ({"tipo": "sintoma", "texto": "rechina al frenar"}, SIN_NADA, "rechina al frenar"),
    ({"tipo": "otro"}, VIENDO_ACEITE, None),
    ({"tipo": "no existe"}, VIENDO_ACEITE, None),
    ("esto no es un diccionario", VIENDO_ACEITE, None),
])
def test_construir_frase(clasificacion, contexto, frase):
    # La pregunta nombra los productos que usa cada caso; las de página
    # no nombran productos (si los nombraran, no serían cambio de página).
    if isinstance(clasificacion, dict) and clasificacion.get("tipo") in ("pagina_siguiente", "posicion"):
        pregunta = "pásame los que siguen"
    else:
        pregunta = "precio y existencia de las balatas BAL-002"
    assert construir_frase(clasificacion, INVENTARIO, contexto, pregunta) == frase


@pytest.mark.parametrize("codigo, pregunta, ultima, aceptado", [
    ("BAL-002", "¿y si es un Versa 2015?", "La banda de accesorios mueve el alternador.", False),
    ("BAL-002", "¿las balatas le quedan a un Versa 2015?", "", True),
    ("BAL-002", "¿y si es un Versa 2015?", "Balatas delanteras Ceramitas (BAL-002): $1,249.00", True),
    ("ACE-001", "¿y si es un Versa 2015?", "", True),   # es el producto que se está viendo
])
def test_no_elige_productos_que_nadie_menciono(codigo, pregunta, ultima, aceptado):
    clasificacion = {"tipo": "compatibilidad", "codigo": codigo, "vehiculo": "Nissan Versa 2015"}
    frase = construir_frase(clasificacion, INVENTARIO, VIENDO_ACEITE, pregunta, ultima)
    assert (frase is not None) is aceptado


# ---------------------------------------------------------------------
# Flujo completo del servidor con el modelo simulado
# ---------------------------------------------------------------------

def _conversar(mensajes: list[str], simulado: dict) -> list[str]:
    from AgenteIA.servidor import Consulta, EstadoContexto, MensajeHistorial, consultar

    async def clasificar_falso(mensajes_modelo):
        texto = mensajes_modelo[-1]["content"].split("Mensaje: ")[-1].replace("\nJSON:", "")
        return simulado.get(texto, {"tipo": "otro"})

    original = reescritura._clasificar
    reescritura._clasificar = clasificar_falso
    respuestas, historial, contexto = [], [], {}
    try:
        for mensaje in mensajes:
            datos = Consulta(
                pregunta=mensaje,
                inventario=json.dumps(INVENTARIO),
                historial=historial,
                contexto=EstadoContexto(**contexto),
            )
            resultado = asyncio.run(consultar(datos))
            contexto = resultado["contexto"]
            historial += [
                MensajeHistorial(rol="user", texto=mensaje),
                MensajeHistorial(rol="model", texto=resultado["respuesta"]),
            ]
            respuestas.append(resultado["respuesta"])
    finally:
        reescritura._clasificar = original
    return respuestas


def test_flujo_reescritura_precio_y_venta():
    respuestas = _conversar(
        [
            "¿cuánto cuesta el PRU-012?",
            "me piden cuatro de esos pero quieren rebaja del 15",
            "qué traemos para afinación",
        ],
        {"qué traemos para afinación": {"tipo": "recomendar_venta", "categoria": "Encendido"}},
    )
    assert "Total con IVA: $1,656.48" in respuestas[1]
    assert "BUJ-003" in respuestas[2]


def test_flujo_reescritura_descarta_codigo_inventado():
    respuestas = _conversar(
        ["¿cuánto cuesta el turbo XYZ-999?"],
        {"¿cuánto cuesta el turbo XYZ-999?": {"tipo": "precio", "codigo": "XYZ-999"}},
    )
    assert "XYZ-999" not in respuestas[0] or "No encontré" in respuestas[0]
    assert "$" not in respuestas[0]


from AgenteIA.asistente.reescritura import leer_json_tolerante


@pytest.mark.parametrize("contenido, esperado", [
    ('{"tipo":"precio","codigo":"ACE-001"}', {"tipo": "precio", "codigo": "ACE-001"}),
    # JSON cortado: se rescata lo que sí se cerró.
    ('{"tipo":"recomendar_venta","categoria":"Encendido","texto":"para una afinacion se',
     {"tipo": "recomendar_venta", "categoria": "Encendido"}),
    ('{"tipo":"inventado","codigo":"X"', None),
    ("basura", None),
    ("", None),
])
def test_leer_json_tolerante(contenido, esperado):
    assert leer_json_tolerante(contenido) == esperado


@pytest.mark.parametrize("clasificacion, pregunta", [
    ({"tipo": "pagina_anterior"}, "Motor"),
    ({"tipo": "pagina_siguiente"}, "iluminación"),
    ({"tipo": "posicion", "numero": "1"}, "Suspensión"),
    ({"tipo": "precio", "codigo": ""}, "dímelo sin precios"),
])
def test_reescritura_no_acepta_clasificaciones_absurdas(clasificacion, pregunta):
    assert construir_frase(clasificacion, INVENTARIO, VIENDO_ACEITE, pregunta) is None


