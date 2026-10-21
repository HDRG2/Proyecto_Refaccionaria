import re

from AgenteIA.asistente.texto import normalizar


def detectar_inyeccion_instrucciones(pregunta: str) -> bool:
    texto = normalizar(pregunta)

    patrones = (
        # Intentos de ignorar instrucciones.
        r"\bignora (?:todas? )?(?:tus |las )?instrucciones\b",
        r"\bolvida (?:todas? )?(?:tus |las )?instrucciones\b",
        r"\bignora (?:todas? )?(?:tus |las )?reglas\b",

        # Intentos de cambiar el comportamiento.
        r"\bactua como si no tuvieras restricciones\b",
        r"\bdesactiva (?:tus |las )?restricciones\b",
        r"\bno sigas (?:tus |las )?instrucciones\b",

        # Intentos de revelar instrucciones internas.
        r"\bmuestra (?:tu |tus |el )?(?:prompt|instrucciones internas)\b",
        r"\brevela (?:tu |tus |el )?(?:prompt|instrucciones internas)\b",
    )

    return any(
        re.search(patron, texto) is not None
        for patron in patrones
    )


# Verbos que siempre significan "modifica el inventario".
_VERBOS_MODIFICAR = (
    r"cambia|cambiale|cambialo|cambiala|modifica|modificale|modificalo|"
    r"actualiza|actualizale|actualizalo|edita|editale|editalo|establece|"
    r"elimina|eliminalo|eliminala|eliminalos|borra|borralo|borrala|borralos|"
    r"ajusta|ajustale|ajustalo"
)
_INFINITIVOS_MODIFICAR = r"cambiar|modificar|actualizar|editar|establecer|eliminar|borrar|ajustar"

# Verbos que también se usan para PREGUNTAR ("¿cuánto aumenta el precio?",
# "¿me pones el precio?"): solo cuentan como orden si dan un número.
_VERBOS_AMBIGUOS = (
    r"pon|ponle|ponlo|ponla|sube|subele|subelo|baja|bajale|bajalo|"
    r"aumenta|aumentale|aumentalo|disminuye|disminuyele|quita|quitale|"
    r"agrega|agregale"
)
# Nota: "suma" y "resta" NO están aquí: son de la calculadora
# ("suma el ACE-001 y el FIL-001").
_INFINITIVOS_AMBIGUOS = r"poner|subir|bajar|aumentar|disminuir|quitar|agregar"

_CAMPOS_INVENTARIO = (
    r"precio|precios|costo|costos|stock|existencia|existencias|inventario|"
    r"producto|productos|refaccion|refacciones|cantidad|cantidades"
)

# Palabras antes del verbo que lo convierten en pregunta, no en orden:
# "¿cuánto cambia...?", "¿qué pasa si baja...?", "¿cada cuánto se cambia...?"
_ANTES_DE_PREGUNTA = {
    "cuanto", "cuanta", "cuando", "como", "si", "se", "que", "porque",
    "por", "tanto", "le", "me", "nos", "lo", "la",
}

# Antes de un infinitivo, piden que el asistente lo haga.
_PIDE_HACER = (
    r"quiero|quisiera|necesito|puedes|podrias|pudieras|ayudame a|me ayudas a|"
    r"vamos a|deseo|hay forma de|como puedo"
)

_NUMERO_DESTINO = r"(?:\ba\s+|\ben\s+|\$\s*|\b)\d+(?:[.,]\d+)?\s*(?:%|pesos|piezas?|unidades?|mxn)?"
_CODIGO = r"\b[a-z]{2,5}-\d{2,5}\b"


def _palabra_anterior(texto: str, posicion: int) -> str:
    antes = re.findall(r"[a-z]+", texto[:posicion])
    return antes[-1] if antes else ""


def detectar_modificacion_inventario(pregunta: str) -> bool:
    # Detecta ÓRDENES de modificar el inventario ("cambia el precio del
    # BAL-001 a 10 pesos", "borra el producto FIL-001"), no preguntas que
    # usan los mismos verbos ("¿cuánto cambia el precio con IVA?").
    texto = normalizar(pregunta)

    # 1. Imperativo: "cambia el precio", "borra el producto",
    #    "ponle 5 piezas al stock", "cambia el BAL-001 a 10 pesos".
    for verbos, necesita_numero in ((_VERBOS_MODIFICAR, False), (_VERBOS_AMBIGUOS, True)):
        for m in re.finditer(r"\b(?:" + verbos + r")\b", texto):
            if _palabra_anterior(texto, m.start()) in _ANTES_DE_PREGUNTA:
                continue
            resto = texto[m.end():m.end() + 60]
            # Los números de un código ("BAL-001") no son una cantidad.
            resto_sin_codigos = re.sub(_CODIGO, " ", resto)
            sobre_campo = re.search(
                r"^(?:\s+[\w$%.,-]+){0,4}?\s+(?:el |la |los |las |al |del |su |sus )?"
                r"(?:" + _CAMPOS_INVENTARIO + r")\b", resto
            ) is not None
            sobre_codigo = re.search(r"^(?:\s+\S+){0,3}?\s+" + _CODIGO, resto) is not None
            con_numero = re.search(_NUMERO_DESTINO, resto_sin_codigos) is not None
            if necesita_numero:
                if (sobre_campo or sobre_codigo) and con_numero:
                    return True
            elif sobre_campo or (sobre_codigo and con_numero):
                return True

    # 2. Pedido con infinitivo: "quiero cambiar el precio del BAL-001",
    #    "¿puedes poner el precio del ACE-001 en 100?".
    for infinitivos, necesita_numero in ((_INFINITIVOS_MODIFICAR, False), (_INFINITIVOS_AMBIGUOS, True)):
        m = re.search(
            r"\b(?:" + _PIDE_HACER + r")\s+(?:(?:le|lo|la|me)\s+)?(?:" + infinitivos + r")"
            r"(?:le|lo|la)?\b(?:\s+\S+){0,3}?\s+(?:el |la |los |las |al |del |su )?"
            r"(?:" + _CAMPOS_INVENTARIO + r")\b(?P<resto>.{0,60})",
            texto,
        )
        if m and (
            not necesita_numero
            or re.search(_NUMERO_DESTINO, re.sub(_CODIGO, " ", m.group("resto")))
        ):
            return True

    return False


_PATRONES_INYECCION = (
    # Ignorar u olvidar instrucciones (español)
    r"\b(?:ignora|ignore|ignorar|olvida|olvidate|olvidar|omite|omitir|"
    r"descarta|salta|saltate|borra|desobedece)\b.{0,40}\b(?:instrucciones|"
    r"reglas|indicaciones|restricciones|ordenes|normas|prompt|"
    r"lineamientos|configuracion|programacion)\b",
    # Cambio de identidad o de rol
    r"\ba partir de (?:ahora|este momento)\b.{0,30}\b(?:eres|seras|actua|"
    r"actuaras|responde|responderas|habla|hablaras|finge)\b",
    r"\bahora (?:eres|seras|vas a ser|te llamas|actuaras)\b",
    # "finge que eres...", "imagina que eres...", "simula que no tienes reglas".
    # "Imagina que mi carro hace un ruido" es una pregunta normal.
    r"\b(?:finge|fingir|finjas|pretende|simula|simular|imagina|imaginate|"
    r"haz de cuenta|hagamos de cuenta|supongamos)\s+(?:que\s+)?(?:tu\s+)?"
    r"(?:eres|seas|fueras|ser|te llamas|no tienes|no hay reglas|estas libre)\b",
    # "Actúa como mi abogado" (orden al asistente). "¿El aditivo actúa como
    # limpiador?" es una pregunta normal.
    r"(?:^|[¿¡]\s*|\b(?:quiero|necesito|puedes|podrias|ahora|ya|tu)\s+(?:que\s+)?)"
    r"(?:actua|actues|actue|actuar|comportate|te comportes)\s+como\b",
    r"\b(?:juega a ser|hazte pasar|responde como si (?:fueras|eras|no))\b",
    r"\bjuego de rol\b|\brole ?play\b|\broleplay\b",
    r"\bmodo (?:desarrollador|developer|dios|admin|administrador|"
    r"sin restricciones|sin filtro|libre|dan|debug|prueba)\b",
    r"\b(?:jailbreak|dan mode|do anything now|sin filtros|sin censura|"
    r"sin limites|eres libre)\b",
    # Revelar instrucciones internas
    r"\b(?:muestra|muestrame|revela|revelame|dime|ensename|repite|"
    r"escribe|imprime|copia|cual es|cuales son|que dicen)\b.{0,30}\b(?:"
    r"tu prompt|el prompt|tus instrucciones|tus reglas|tus indicaciones|"
    r"tus restricciones|tu configuracion|tu programacion|reglas internas|"
    r"instrucciones internas|mensaje del sistema|system message)\b",
    r"\bsystem ?prompt\b|\bmensaje del sistema\b|\binstrucciones del sistema\b",
    # Inglés
    r"\b(?:ignore|disregard|forget|bypass|override)\b.{0,30}\b(?:instructions|"
    r"rules|prompt|previous|above|guidelines)\b",
    r"\byou are now\b|\bact as\b|\bpretend\b|\bfrom now on\b",
    r"\bdeveloper mode\b|\bnew instructions\b",
    # Etiquetas falsas de sistema
    r"<\s*/?\s*(?:system|sistema|admin|instrucciones)\s*>",
    r"\[\s*(?:system|sistema|admin)\s*\]",
    r"^\s*(?:system|sistema|admin|assistant|asistente|usuario|user)\s*:",
    r"#{2,}\s*(?:system|sistema|instrucciones)",
)


def detectar_inyeccion_ampliada(pregunta: str) -> bool:
    texto = normalizar(pregunta)
    return any(
        re.search(patron, texto) is not None
        for patron in _PATRONES_INYECCION
    )
