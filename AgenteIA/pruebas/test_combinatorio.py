import re
import unicodedata

import pytest

from AgenteIA.mecanica.documentacion_automotriz import DOCUMENTACION_AUTOMOTRIZ
from .test_estres import INVENTARIO, _cumple, _turno


def _sin_acentos(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


# ---------------------------------------------------------------------
# Cómo se nombra cada producto
# ---------------------------------------------------------------------

def _formas_de_nombrar(producto: dict) -> list[str]:
    nombre = producto["nombre"]
    codigo = producto["codigo"]
    prefijo, numero = codigo.split("-")
    formas = [nombre.lower(), codigo, f"{prefijo.lower()}{numero}", f"{prefijo.lower()} {numero}"]

    # La primera palabra sola ("termostato") si ningún otro producto la usa.
    primera = _sin_acentos(nombre.split()[0].lower())
    otros = [p for p in INVENTARIO if p is not producto]
    if not any(_sin_acentos(p["nombre"].lower()).startswith(primera[:5]) for p in otros):
        formas.append(primera)
    return formas


PRECIO = [
    "cuanto cuesta {n}", "precio de {n}", "{n} precio", "cuanto vale {n}",
    "que precio tiene {n}", "en cuanto sale {n}", "cuanto le cobro por {n}",
    "me das el precio de {n}", "{n} cuanto", "cuanto el {n}",
]
EXISTENCIA = [
    "cuantas piezas de {n} quedan", "existencia de {n}", "stock de {n}",
    "cuantas unidades hay de {n}", "cuantos {n} quedan",
]
CALCULO = [
    "si vendo 3 {n}", "me llevo 2 {n}", "cuanto son 4 {n}", "vendo 5 de {n}",
    "2 {n} con iva",
]
FICHA = ["{n}", "{n} en inventario", "busco {n}", "tienes {n}?", "info de {n}"]


def _casos_inventario():
    casos = []
    for producto in INVENTARIO:
        codigo = producto["codigo"]
        for n in _formas_de_nombrar(producto):
            casos += [(t.format(n=n), "$" + codigo) for t in PRECIO]
            casos += [(t.format(n=n), "#" + codigo) for t in EXISTENCIA]
            casos += [(t.format(n=n), "=" + codigo) for t in CALCULO]
            casos += [(t.format(n=n), codigo) for t in FICHA]
    return casos


# ---------------------------------------------------------------------
# Mecánica: cada pieza y cada síntoma de la documentación
# ---------------------------------------------------------------------

FALLA_PIEZA = [
    "falla mi {p}", "no sirve el {p}", "mi {p} anda mal", "tengo problemas con el {p}",
    "el cliente dice que le falla el {p}",
]
SINTOMA = ["mi carro {e}", "el cliente dice que {e}", "{e}, que reviso?"]

# Palabras clave que no son piezas sino conceptos ("servicio", "viaje").
_NO_PIEZA = {
    "servicio", "carretera", "viaje", "mantenimiento", "fluidos", "verificacion",
    "emisiones", "corriente", "voltaje", "frenado", "rebote", "rebotes",
    "golpeteo", "golpeteos", "baches", "topes", "chirrido", "rechinido",
    "sobrecalentamiento", "sobrecalienta", "lubricacion", "viscosidad",
    "afinacion", "encendido", "arranque", "tablero", "indicador", "testigo",
    "testigos", "escaner", "humo", "chispa", "clima", "calefaccion",
    "ventilacion", "combustible", "gasolina", "transmision", "suspension",
    "direccion", "alineacion", "balanceo", "ponchadura", "cableado", "mil",
    "abs", "cvt", "led", "xenon", "halogeno", "intermitentes", "estabilizadora",
}


def _casos_mecanica():
    casos = []
    for datos in DOCUMENTACION_AUTOMOTRIZ.values():
        for clave in datos["palabras_clave"]:
            pieza = _sin_acentos(clave)
            if " " in pieza or len(pieza) < 4 or pieza in _NO_PIEZA:
                continue
            casos += [(t.format(p=pieza), "MEC") for t in FALLA_PIEZA]
        for expresion in datos["expresiones"]:
            casos += [(t.format(e=_sin_acentos(expresion)), "MEC") for t in SINTOMA]
    return casos


CASOS_INVENTARIO = _casos_inventario()
CASOS_MECANICA = _casos_mecanica()


@pytest.mark.parametrize("pregunta, esperado", CASOS_INVENTARIO)
def test_inventario_combinado(pregunta, esperado):
    texto, _ = _turno(pregunta)
    assert _cumple(esperado, texto, pregunta), f"{pregunta!r} -> {texto[:160]!r}"


@pytest.mark.parametrize("pregunta, esperado", CASOS_MECANICA)
def test_mecanica_combinada(pregunta, esperado):
    texto, _ = _turno(pregunta)
    assert _cumple(esperado, texto, pregunta), f"{pregunta!r} -> {texto[:160]!r}"
