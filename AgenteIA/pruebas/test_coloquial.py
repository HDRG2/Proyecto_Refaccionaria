import pytest

from AgenteIA.asistente import coloquial
from AgenteIA.asistente.coloquial import corregir_ortografia, traducir_coloquial
from AgenteIA.asistente.texto import preparar_pregunta


INVENTARIO = [
    {"codigo": "BAL-002", "nombre": "Balatas delanteras Ceramitas", "marca": "Brembo",
     "categoria": "Frenos", "precio": 1249, "existencia": 15,
     "vehiculosCompatibles": ["Nissan Versa 2012-2019", "Toyota Corolla 2014-2019"]},
    {"codigo": "AMO-005", "nombre": "Amortiguador Delantero", "marca": "Monroe",
     "categoria": "Suspensión", "precio": 1450, "existencia": 7},
    {"codigo": "BUJ-003", "nombre": "Bujia de encendido", "marca": "NGK",
     "categoria": "Encendido", "precio": 120, "existencia": 40},
    {"codigo": "PRU-008", "nombre": "Batería de 12V", "marca": "LTH",
     "categoria": "Sistema eléctrico", "precio": 2100, "existencia": 8},
    {"codigo": "PRU-006", "nombre": "Filtro de aire", "marca": "Gonher",
     "categoria": "Filtros", "precio": 180, "existencia": 15},
    {"codigo": "PRU-014", "nombre": "Termostato de Motor", "marca": "Motorad",
     "categoria": "Enfriamiento", "precio": 450, "existencia": 5},
]


@pytest.mark.parametrize("entrada, debe_contener", [
    # Precio
    ("a cómo las pastillas", "cual es el precio de las balatas"),
    ("q precio trae el aceite", "cual es el precio de"),
    ("cuanta lana el alternador", "cuanto cuesta el alternador"),
    ("cuanto le cobro por la pila", "cual es el precio de la bateria"),
    ("cuánto por el radiador", "cual es el precio de el radiador"),
    ("kuanto kuesta", "cuanto cuesta"),
    # Existencia
    ("¿traes balatas?", "tienes balatas"),
    ("tendrás amortis", "tienes amortiguadores"),
    ("me consigues un filtro del aire", "tienes un filtro de aire"),
    ("ay bujias?", "hay bujias"),
    # Refacciones
    ("kuanto kuesta el filtro de gas", "filtro de combustible"),
    ("la banda del tiempo", "banda de distribucion"),
    ("se prendió el foquito del motor", "check engine"),
    ("el chicote del cloch", "el cable del clutch"),
    # Vehículo
    ("algo pa mi vocho", "para mi volkswagen sedan"),
    ("mi nave", "mi carro"),
    ("la troca", "la camioneta"),
    # Síntomas
    ("se le sube la aguja", "sube la temperatura"),
    ("traga mucha gasolina", "gasta mucha gasolina"),
    ("chorrea aceite", "tira aceite"),
    ("se me murió la pila", "se descarga la bateria"),
    ("no tiene jalón", "pierde potencia"),
    ("avienta aire caliente", "no enfria"),
    # Cálculos
    ("con todo e iva", "con iva"),
    ("hazme un descuentito", "descuento"),
    ("500 varos", "500 pesos"),
    # Abreviaturas
    ("nomás dime el nombre", "solo dime el nombre"),
    ("xq rechina", "por que rechina"),
])
def test_traducir_coloquial(entrada, debe_contener):
    assert debe_contener in traducir_coloquial(entrada).casefold()


@pytest.mark.parametrize("entrada", [
    "¿cuánto cuesta el BAL-002?",
    "si me llevo un par",           # "par" no es "pa"
    "para un versa 2015",
    "hay que revisar los frenos",
    "a cómo está el filtro",        # lo resuelve texto.py, no se rompe
    "ay no, me equivoqué",
])
def test_no_cambia_lo_que_ya_se_entiende(entrada):
    resultado = preparar_pregunta(entrada).casefold()
    assert "parar" not in resultado and "hay no" not in resultado
    assert "precio de esta" not in resultado


@pytest.mark.parametrize("entrada, esperado", [
    ("tienes valatas", "tienes balatas"),
    ("hay vujias", "hay bujias"),
    ("tienes amortigador", "tienes amortiguador"),
    ("balatas para corrolla 2016", "balatas para corolla 2016"),
    ("filtor de aire", "filtro de aire"),
    ("cuanto cuesta la bateira", "cuanto cuesta la bateria"),
    ("termostatoo", "termostato"),
    ("embrage", "embrague"),
    ("acete de motor", "aceite de motor"),
])
def test_corregir_errores_de_dedo(entrada, esperado):
    assert corregir_ortografia(entrada, INVENTARIO) == esperado


@pytest.mark.parametrize("entrada", [
    # Palabras reales que se parecen a una refacción: NO se tocan.
    "borra el producto BAL-002",
    "el patrón quiere el reporte",
    "el turbo truena",
    "el carro tuvo una falla",
    "quiere tapetes para su carro",
    "explicación corta",
    "acepte la venta",
    "hace un chillido cuando frena",
    "buenaas tardes",
])
def test_no_corrige_palabras_reales(entrada):
    assert corregir_ortografia(entrada, INVENTARIO) == entrada


def test_registrar_no_entendida():
    import tempfile
    from pathlib import Path

    carpeta = Path(tempfile.mkdtemp())
    import os

    anterior = (coloquial.CARPETA_REGISTRO, coloquial.ARCHIVO_NO_ENTENDIDAS)
    apagado = os.environ.pop("PISTON_SIN_REGISTRO", None)
    coloquial.CARPETA_REGISTRO = carpeta
    coloquial.ARCHIVO_NO_ENTENDIDAS = carpeta / "no_entendidas.txt"
    try:
        coloquial.registrar_no_entendida("¿tienes la cosa esa?", "sin respuesta")
        coloquial.registrar_no_entendida("pásame lo que falta", "reescrita", "siguientes productos")
        lineas = coloquial.ARCHIVO_NO_ENTENDIDAS.read_text(encoding="utf-8").splitlines()
    finally:
        coloquial.CARPETA_REGISTRO, coloquial.ARCHIVO_NO_ENTENDIDAS = anterior
        if apagado is not None:
            os.environ["PISTON_SIN_REGISTRO"] = apagado

    assert len(lineas) == 2
    assert "sin respuesta\t¿tienes la cosa esa?" in lineas[0]
    assert lineas[1].endswith("-> siguientes productos")


@pytest.mark.parametrize("texto, esperado", [
    ("tr4nsmision", "transmision"),
    ("b4l4t4s", "balatas"),
    ("fr3nos", "frenos"),
    ("t3rmost4to", "termostato"),
    ("b0mba de agu4", "bomba de agua"),
])
def test_numeros_en_lugar_de_letras(texto, esperado):
    assert corregir_ortografia(texto, INVENTARIO) == esperado


@pytest.mark.parametrize("texto", [
    "ace001", "precio ace001", "aceite 5w30", "bal002", "4 balatas",
    "205/55 r16", "h4", "llanta r15", "sensor o2", "versa 2015",
])
def test_codigos_y_medidas_no_se_tocan(texto):
    assert corregir_ortografia(texto, INVENTARIO) == texto


