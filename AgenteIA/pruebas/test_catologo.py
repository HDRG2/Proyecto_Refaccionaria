import contextlib
import io
import json

import pytest

from AgenteIA.servidor import ETAPAS, Consulta, EstadoConsulta
from .test_estres import INVENTARIO


CATALOGO = {
    "marcas": ["Bosch", "Mobil", "NGK", "Ultra 8"],
    "categorias": ["Aceites", "Clutch", "Frenos"],
    "autos": [
        {"marca": "Nissan", "modelo": "Versa", "anio_inicio": 2012, "anio_fin": 2019},
        {"marca": "Ford", "modelo": "Focus", "anio_inicio": 2015, "anio_fin": 2020},
        {"marca": "Yamaha", "modelo": "Banshee", "anio_inicio": 1987, "anio_fin": 2006},
    ],
}


def _turno(pregunta, catalogo=CATALOGO):
    datos = Consulta(pregunta=pregunta, inventario=json.dumps(INVENTARIO), catalogo=catalogo)
    estado = EstadoConsulta(datos=datos)
    with contextlib.redirect_stdout(io.StringIO()):
        for etapa in ETAPAS:
            respuesta = etapa(estado)
            if respuesta is not None:
                return respuesta["respuesta"]
    return "<MODELO>"


@pytest.mark.parametrize("pregunta, empieza", [
    ("ultra 8", "La marca Ultra 8 está registrada, pero todavía no tiene productos"),
    ("ultra8", "La marca Ultra 8 está registrada"),
    ("marca ultra 8", "La marca Ultra 8 está registrada"),
    ("mobil", "Productos de la marca Mobil"),
    ("que productos hay de bosch", "Productos de la marca Bosch"),
    ("clutch", "La categoría Clutch está registrada, pero todavía no tiene productos"),
    ("focus", "El Ford Focus (2015-2020) está registrado"),
    ("fokus", "El Ford Focus (2015-2020) está registrado"),
    ("ford focus 2023", "El Ford Focus (2015-2020) está registrado"),
    ("yamaha", "Modelos de Yamaha registrados"),
    ("nissan versa 2015", "Refacciones con compatibilidad registrada para Nissan Versa 2015"),
])
def test_reconoce_el_catalogo(pregunta, empieza):
    texto = _turno(pregunta)
    assert texto.startswith(empieza), texto


def test_anio_fuera_de_rango():
    assert "fuera del rango registrado" in _turno("ford focus 2023")


@pytest.mark.parametrize("pregunta", ["balatas", "termostato", "hola", "categorias"])
def test_lo_demas_no_cambia(pregunta):
    assert _turno(pregunta) == _turno(pregunta, catalogo={})


def test_sin_catalogo_funciona_como_antes():
    # Una versión de la app que no manda el catálogo no debe fallar.
    assert _turno("mobil", catalogo={}).startswith("Productos de la marca Mobil")
