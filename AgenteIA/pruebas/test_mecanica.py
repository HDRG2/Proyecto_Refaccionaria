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


# ---------------------------------------------------------------------
# Mangueras y respuestas que niegan la falla reportada
# ---------------------------------------------------------------------

from AgenteIA.asistente.filtros_respuesta import quitar_diagnostico_negado


@pytest.mark.parametrize("pregunta", [
    "falla mi manguera", "mi manguera falla", "se rompió la manguera del radiador",
    "gotea la manguera",
])
def test_falla_manguera_respuesta_fija(pregunta):
    respuesta = buscar_respuesta_rapida(preparar_pregunta(pregunta))
    assert respuesta == CONOCIMIENTOS_MECANICOS["falla_manguera"]


@pytest.mark.parametrize("texto, esperado", [
    ("No tienes falla en tu manguera, revisa el nivel de refrigerante.",
     "Revisa el nivel de refrigerante."),
    ("Tu termostato está bien. Conviene revisar el ventilador.",
     "Conviene revisar el ventilador."),
    ("Revisa las balatas. No hay ningún problema con los discos.",
     "Revisa las balatas."),
    ("Conviene revisar el nivel.", "Conviene revisar el nivel."),
])
def test_quitar_diagnostico_negado(texto, esperado):
    assert quitar_diagnostico_negado(texto) == esperado


# ---------------------------------------------------------------------
# "Falla mi X" sin síntoma: se pregunta el síntoma, no se inventa
# ---------------------------------------------------------------------

from AgenteIA.mecanica.conocimientos_mecanicos import respuesta_falla_sin_sintoma


@pytest.mark.parametrize("pregunta, debe_contener", [
    ("falla mi volante", "en la dirección"),
    ("falla mi mofle", "en el escape"),
    ("no sirven los frenos", "en los frenos"),
    ("fallan mis luces", "fallan las luces"),
    ("la transmision falla", "falla la transmisión"),
    ("mi carro tiene falla en la suspension", "en la suspensión"),
    ("falla el alternador", "en el sistema eléctrico"),
])
def test_falla_sin_sintoma_pide_el_sintoma(pregunta, debe_contener):
    respuesta = respuesta_falla_sin_sintoma(preparar_pregunta(pregunta))
    assert respuesta is not None and debe_contener in respuesta


@pytest.mark.parametrize("pregunta", [
    "el volante vibra",              # ya trae síntoma
    "falla mi volante cuando giro y hace ruido",
    "precio del volante",
    "falla el sistema de la computadora del banco",
])
def test_falla_con_sintoma_o_sin_pieza_no_aplica(pregunta):
    assert respuesta_falla_sin_sintoma(preparar_pregunta(pregunta)) is None


# ---------------------------------------------------------------------
# Validador de respuestas de mecánica: no aceptar síntomas inventados
# ---------------------------------------------------------------------

from AgenteIA.mecanica.validador_mecanica import (
    respuesta_desde_documentacion,
    terminos_inventados,
)


@pytest.mark.parametrize("pregunta, respuesta, inventado", [
    ("falla mi volante",
     "El ruido de rechinar al volante puede ser causado por la banda de dirección.", "rechinar"),
    ("el carro vibra en carretera",
     "La vibración puede deberse a balatas desgastadas.", "balatas"),
])
def test_detecta_terminos_inventados(pregunta, respuesta, inventado):
    assert inventado in terminos_inventados(respuesta, pregunta, buscar_conocimiento(pregunta))


@pytest.mark.parametrize("pregunta, respuesta", [
    ("fallan mis luces", "Conviene revisar focos, fusibles, relevadores, conectores y cables."),
    ("rechinan los frenos", "Puede deberse a pastillas desgastadas o discos rayados."),
    ("el clutch patina", "El disco puede estar desgastado; las revoluciones suben sin avanzar."),
    ("sale humo blanco", "El humo blanco con olor dulce puede ser refrigerante; revisa la junta de culata."),
    ("no arranca el carro", "Puede ser la batería, las terminales o el motor de arranque."),
])
def test_acepta_respuestas_correctas(pregunta, respuesta):
    assert terminos_inventados(respuesta, pregunta, buscar_conocimiento(pregunta)) == []


def test_respuesta_desde_documentacion():
    texto = respuesta_desde_documentacion(buscar_conocimiento("falla mi volante")) or ""
    assert texto.startswith("Síntomas comunes:")
    assert "Qué revisar:" in texto


@pytest.mark.parametrize("pregunta, debe_contener", [
    ("falla mi rifle", "No tengo información técnica sobre «rifle»"),
    ("falla mi carro", "¿Qué le pasa al vehículo"),
    ("falla", "¿Qué le pasa al vehículo"),
    ("falla el motor", "¿Qué le pasa al vehículo"),
    ("mi camioneta anda mal", "¿Qué le pasa al vehículo"),
])
def test_falla_sin_pieza_reconocible(pregunta, debe_contener):
    respuesta = respuesta_falla_sin_sintoma(preparar_pregunta(pregunta))
    assert respuesta is not None and debe_contener in respuesta



