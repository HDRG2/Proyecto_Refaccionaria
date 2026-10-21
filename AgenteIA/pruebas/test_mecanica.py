import pytest

from AgenteIA.mecanica.buscador_mecanico import buscar_conocimiento
from AgenteIA.mecanica.conocimientos_mecanicos import (
    CONOCIMIENTOS_MECANICOS,
    buscar_respuesta_rapida,
)


@pytest.mark.parametrize("pregunta, clave", [
    ("Mi carro rechina al frenar, ¿qué puede ser?", "ruido_al_frenar"),
    ("chillan los frenos", "ruido_al_frenar"),
    ("vibra cuando freno", "vibracion_al_frenar"),
    ("El volante vibra a alta velocidad", "vibracion_en_velocidad"),
    ("¿Es peligroso manejar con las balatas gastadas?", "riesgos_balatas"),
    ("Mi motor se sobrecalienta, ¿qué hago?", "que_hacer_sobrecalentamiento"),
    ("¿Para qué sirve el termostato?", "funcion_termostato"),
    ("mi carro tiene juego en el volante", "juego_volante"),
    ("el volante está muy duro", "volante_duro"),
    ("la dirección se siente pesada", "volante_duro"),
    ("¿para qué sirve el alternador?", "funcion_alternador"),
    ("¿qué hace la marcha?", "funcion_marcha"),
])
def test_respuesta_rapida(pregunta, clave):
    assert buscar_respuesta_rapida(pregunta) == CONOCIMIENTOS_MECANICOS[clave]


@pytest.mark.parametrize("pregunta", [
    "¿cuánto cuestan las balatas?",   # inventario
    "¿tienes balatas?",               # inventario
    "¿cuánto cuesta el volante?",     # pregunta de precio, no de mecánica
])
def test_sin_respuesta_rapida(pregunta):
    assert buscar_respuesta_rapida(pregunta) is None


@pytest.mark.parametrize("pregunta, sistema, no_debe", [
    ("mi carro rechina al frenar", "SISTEMA FRENOS", None),
    ("el volante vibra a alta velocidad", "LLANTAS Y ALINEACION", "SISTEMA DIRECCION"),
    ("el volante está duro", "SISTEMA DIRECCION", None),
    ("mi motor se sobrecalienta en el tráfico", "SISTEMA REFRIGERACION", None),
])
def test_buscar_conocimiento(pregunta, sistema, no_debe):
    documentacion = buscar_conocimiento(pregunta)
    assert documentacion is not None and sistema in documentacion
    if no_debe:
        assert no_debe not in documentacion


def test_sobrecalentamiento_incluye_seguridad():
    # filtros_respuesta necesita el apartado SEGURIDAD para agregar
    # las advertencias que falten.
    documentacion = buscar_conocimiento("mi motor se sobrecalienta")
    assert "SEGURIDAD:" in documentacion


from AgenteIA.asistente.filtros_respuesta import aclarar_banda_o_cadena


@pytest.mark.parametrize("respuesta, esperado", [
    ("En el Versa 2015, la banda de distribución sincroniza el cigüeñal.",
     "En el Versa 2015, la banda o cadena de distribución (según el motor) sincroniza el cigüeñal."),
    ("La banda (o cadena) de distribución sincroniza...",
     "La banda (o cadena) de distribución sincroniza..."),
    ("La banda de accesorios mueve el alternador.",
     "La banda de accesorios mueve el alternador."),
])
def test_aclarar_banda_o_cadena(respuesta, esperado):
    assert aclarar_banda_o_cadena(respuesta) == esperado


@pytest.mark.parametrize("pregunta", [
    "no arranca el carro",
    "el carro no quiere arrancar",
    "no quiere prender",
])
def test_no_arranca_encuentra_sistema_electrico(pregunta):
    documentacion = buscar_conocimiento(pregunta)
    assert documentacion is not None and "SISTEMA ELECTRICO" in documentacion


# ---------------------------------------------------------------------
# Motor que se calienta (respuesta fija con advertencia de seguridad)
# ---------------------------------------------------------------------

from AgenteIA.asistente.filtros_respuesta import hablar_directo
from AgenteIA.asistente.texto import preparar_pregunta
from AgenteIA.mecanica.conocimientos_mecanicos import (
    CONOCIMIENTOS_MECANICOS,
    buscar_respuesta_rapida,
)


@pytest.mark.parametrize("pregunta", [
    "mi carro se calienta",
    "mi nave se calienta",
    "se le sube la aguja",
    "el motor se sobrecalienta",
    "se está calentando mucho el carro",
    "echa vapor el cofre",
])
def test_motor_se_calienta_respuesta_fija(pregunta):
    respuesta = buscar_respuesta_rapida(preparar_pregunta(pregunta))
    assert respuesta == CONOCIMIENTOS_MECANICOS["causas_sobrecalentamiento"]
    assert "No abrir la tapa del radiador" in respuesta


@pytest.mark.parametrize("pregunta", [
    "se calientan mucho los frenos",
    "se calienta la batería",
    "se calienta el aceite",
    "el motor se sobrecalienta, ¿qué hago?",   # usa la de "qué hacer"
])
def test_otras_piezas_calientes_no_usan_esa_respuesta(pregunta):
    respuesta = buscar_respuesta_rapida(preparar_pregunta(pregunta))
    assert respuesta != CONOCIMIENTOS_MECANICOS["causas_sobrecalentamiento"]


@pytest.mark.parametrize("texto, esperado", [
    ("El vendedor debe revisar el nivel de refrigerante.",
     "Conviene revisar el nivel de refrigerante."),
    ("Primero el vendedor debería medir el voltaje.",
     "Primero conviene medir el voltaje."),
    ("El cliente debe llevarlo al taller.", "El cliente debe llevarlo al taller."),
])
def test_hablar_directo(texto, esperado):
    assert hablar_directo(texto) == esperado


