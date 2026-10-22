import re

from AgenteIA.asistente.texto import normalizar, quitar_acentos


# Razonamiento interno de los modelos que "piensan" (qwen3, qwen3.5...).
# Normalmente se apaga con think=False (ver configuracion.py), pero si la
# versión del paquete ollama no lo soporta, llega dentro de la respuesta.
_BLOQUE_RAZONAMIENTO = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)


def quitar_razonamiento(respuesta: str) -> str:
    respuesta = _BLOQUE_RAZONAMIENTO.sub("", respuesta)
    # Bloque cerrado sin abrir ("...razonamiento</think> Respuesta").
    if "</think>" in respuesta.lower():
        respuesta = re.split(r"</think>", respuesta, flags=re.IGNORECASE)[-1]
    # Bloque abierto que nunca se cerró: no hay respuesta útil después.
    if "<think>" in respuesta.lower():
        respuesta = re.split(r"<think>", respuesta, flags=re.IGNORECASE)[0]
    return respuesta.strip()


# Frases del prompt que el modelo a veces copia como si fueran
# consejos para el vendedor ("No confundas este ruido con...").
_FRASES_DE_REGLAS = re.compile(
    r"^(?:no confundas|no recomiendas|no recomiendes|no inventes|"
    r"no menciones|no agregues|no mezcles|no conviertas|no afirmes|"
    r"evita repetir|usa la documentacion|utiliza la documentacion|"
    r"distingue (?:los|las|entre)|responde (?:exactamente|solo|siempre)|"
    r"segun la documentacion|la documentacion)\b"
)


def quitar_reglas_repetidas(respuesta: str) -> str:
    # Quita las oraciones que solo repiten reglas internas.
    # Si quitarlas dejaría la respuesta vacía, se deja como estaba.
    oraciones = re.split(r"(?<=[.!?])\s+", respuesta.strip())
    utiles = [
        o for o in oraciones
        if not _FRASES_DE_REGLAS.search(quitar_acentos(o.strip().lower()))
    ]
    if not utiles:
        return respuesta
    return " ".join(utiles).strip()


# Sistemas donde nunca se debe decir que una falla "no es peligrosa".
_SISTEMAS_DE_SEGURIDAD = re.compile(
    r"\b(?:freno|frenos|frenado|frena|balata|balatas|pastilla|pastillas|"
    r"disco|discos|caliper|mordaza|liquido de frenos|direccion|volante|"
    r"llanta|llantas|neumatico|neumaticos|suspension|amortiguador|"
    r"amortiguadores|rotula|rotulas|terminal de direccion)\b"
)


# Frases que minimizan el riesgo ("no es peligroso", "no hay riesgo").
_MINIMIZA_RIESGO = re.compile(
    r"\bno (?:es|seria|resulta|suele ser) (?:muy |tan |algo )?peligros[oa]\b|"
    r"\bno (?:hay|existe|representa|implica|supone) (?:un |ningun |gran |mayor )?"
    r"(?:riesgo|peligro)\b|"
    r"\bsin (?:riesgo|peligro) (?:inmediato|alguno)\b|"
    r"\b(?:es|son) segur[oa]s? (?:seguir )?(?:manejar|conducir|circular)\b|"
    r"\bno (?:hay|existe) (?:riesgo|peligro) (?:de peligro |de riesgo )?inmediat[oa]\b|"
    r"\bpuedes? seguir (?:manejando|conduciendo|circulando) sin problema\b"
)


_ADVERTENCIAS_SEGURIDAD = (
    (r"\b(?:freno|frenos|frenado|frena|balata|balatas|pastilla|pastillas|"
     r"disco|discos|caliper|mordaza|liquido de frenos)\b",
     "En los frenos, un ruido o desgaste no debe ignorarse: puede "
     "reducir la capacidad de frenado, así que conviene revisarlos pronto "
     "con un mecánico."),
    (r"\b(?:llanta|llantas|neumatico|neumaticos)\b",
     "Una falla en las llantas no debe ignorarse: puede afectar "
     "el agarre y el frenado, así que conviene revisarlas pronto."),
    (r"\b(?:direccion|volante|suspension|amortiguador|amortiguadores|"
     r"rotula|rotulas|terminal de direccion)\b",
     "Una falla en la dirección o la suspensión no debe ignorarse: "
     "puede afectar el control del vehículo, así que conviene revisarla "
     "pronto con un mecánico."),
)


_CONECTORES = re.compile(r",\s*(?:pero|aunque|sin embargo|aun asi)\s+", re.IGNORECASE)


def _quitar_clausula_que_minimiza(oracion: str) -> str:
    # "Es un indicio de desgaste, pero no es peligroso."  -> "Es un indicio de desgaste."
    # "No hay riesgo inmediato, pero revisa las balatas." -> "Revisa las balatas."
    # Si toda la oración minimiza el riesgo, devuelve "".
    partes = _CONECTORES.split(oracion)
    utiles = [p for p in partes if not _MINIMIZA_RIESGO.search(normalizar(p))]
    if not utiles:
        return ""
    texto = ", ".join(p.strip().rstrip(".") for p in utiles).strip()
    if not texto:
        return ""
    return texto[0].upper() + texto[1:] + "."


def corregir_minimizacion_de_riesgo(respuesta: str, tema: str) -> str:
    # Si el tema es un sistema de seguridad (frenos, llantas, dirección,
    # suspensión) y el modelo dijo que "no es peligroso" o "no hay
    # riesgo", se quita esa parte y se agrega una advertencia al final.
    tema_normal = normalizar(tema)
    if not _SISTEMAS_DE_SEGURIDAD.search(tema_normal):
        return respuesta

    oraciones = re.split(r"(?<=[.!?])\s+", respuesta.strip())
    corregidas = []
    hubo_cambio = False
    quitada_anterior = False

    for oracion in oraciones:
        if _MINIMIZA_RIESGO.search(normalizar(oracion)):
            hubo_cambio = True
            oracion = _quitar_clausula_que_minimiza(oracion)
            quitada_anterior = not oracion
            if not oracion:
                continue
        elif quitada_anterior:
            # "Sin embargo, ..." ya no tiene a qué oponerse.
            oracion = re.sub(
                r"^(?:sin embargo|aun asi|aún así|no obstante),\s*", "",
                oracion, flags=re.IGNORECASE,
            )
            oracion = oracion[:1].upper() + oracion[1:]
            quitada_anterior = False
        corregidas.append(oracion)

    if not hubo_cambio:
        return respuesta

    advertencia = next(
        (texto for patron, texto in _ADVERTENCIAS_SEGURIDAD
         if re.search(patron, tema_normal)),
        _ADVERTENCIAS_SEGURIDAD[0][1],
    )
    corregidas.append(advertencia)
    return " ".join(corregidas).strip()


# "La banda de distribución" -> "la banda o cadena de distribución (según
# el motor)". Muchos motores usan cadena y el modelo no debe afirmar cuál
# lleva un vehículo concreto ("En el Versa 2015, la banda...").
_BANDA_DISTRIBUCION = re.compile(
    r"\b(?P<art>la |una )?(?P<pieza>banda|correa) de distribuci[oó]n\b",
    re.IGNORECASE,
)


def aclarar_banda_o_cadena(respuesta: str) -> str:
    if re.search(r"\bcadena\b", respuesta, re.IGNORECASE):
        return respuesta

    hecho = False

    def cambiar(m: re.Match) -> str:
        nonlocal hecho
        art = m.group("art") or ""
        texto = f"{art}{m.group('pieza')} o cadena de distribución"
        if not hecho:
            hecho = True
            texto += " (según el motor)"
        return texto

    return _BANDA_DISTRIBUCION.sub(cambiar, respuesta)


# Síntomas de sobrecalentamiento en la pregunta. "sobrecal" cubre
# "sobrecalienta", "sobrecalentó" y "sobrecalentamiento" (antes se buscaba
# "sobrecalent", que NO coincide con "se sobrecalienta").
_SINTOMAS_SOBRECALENTAMIENTO = (
    "sobrecal",
    "se calienta mucho",
    "se calento mucho",
    "motor muy caliente",
    "temperatura del motor alta",
    "temperatura alta",
    "se calienta",
    "se calento",
    "se esta calentando",
    "sube la temperatura",
    "sube la aguja",
    "sale vapor",
    "echa vapor",
)


# Frases donde el modelo NIEGA la falla que reportó el vendedor sin poder
# saberlo: "No tienes falla en tu manguera", "no hay ningún problema",
# "tu termostato está bien". Se quita la oración completa.
_NIEGA_FALLA = re.compile(
    r"\b(?:no\s+(?:tienes|tiene|hay|existe|presenta)\s+(?:ningun\s+|ninguna\s+|una\s+)?"
    r"(?:falla|problema|averia|dano)s?|"
    r"no\s+es\s+(?:una\s+)?(?:falla|problema)|"
    r"no\s+hay\s+(?:de\s+)?que\s+preocupar|"
    r"(?:tu|su|el|la)\s+\w+(?:\s+\w+)?\s+(?:esta|estan)\s+(?:bien|en buen estado|funcionando bien))\b",
    re.IGNORECASE,
)


def quitar_diagnostico_negado(respuesta: str) -> str:
    oraciones = re.split(r"(?<=[.!?])\s+|,\s+(?=revisa|conviene|verifica)", respuesta)
    limpias = [o for o in oraciones if not _NIEGA_FALLA.search(quitar_acentos(o))]
    if not limpias or len(limpias) == len(oraciones):
        return respuesta
    texto = " ".join(limpias).strip()
    return texto[0].upper() + texto[1:]


def hablar_directo(respuesta: str) -> str:
    # El modelo a veces habla del vendedor en tercera persona porque así
    # viene en las instrucciones: "El vendedor debe revisar el nivel..."
    # -> "Conviene revisar el nivel...".
    def cambiar(m: re.Match) -> str:
        return "Conviene" if m.group(1)[0].isupper() else "conviene"

    respuesta = re.sub(
        r"\b([Ee]l vendedor|[Ee]l empleado|[Ee]l usuario)\s+"
        r"(?:debe|deber[ií]a|tiene que|puede|podr[ií]a|necesita)\s+",
        lambda m: cambiar(m) + " ",
        respuesta,
    )
    # "Vendedor, actualmente no hay..." -> "Actualmente no hay..."
    respuesta = re.sub(
        r"^\s*(?:Hola,?\s+)?(?:estimado\s+)?vendedor\s*[,:]\s*(\w)",
        lambda m: m.group(1).upper(),
        respuesta,
        flags=re.IGNORECASE,
    )

    # Primera persona del modelo: "revisaré la presión" -> "conviene
    # revisar la presión"; "no confirmaré" -> "no se debe confirmar".
    verbos = {
        "revisare": "revisar", "verificare": "verificar",
        "comprobare": "comprobar", "inspeccionare": "inspeccionar",
        "medire": "medir", "diagnosticare": "diagnosticar",
        "recomendare": "recomendar", "sugerire": "sugerir",
        "cambiare": "cambiar", "reemplazare": "reemplazar",
        "confirmare": "confirmar", "descartare": "descartar",
        "afirmare": "afirmar",
    }

    def primera_persona(m: re.Match) -> str:
        negado, verbo = m.group(1), m.group(2)
        base = verbos[quitar_acentos(verbo).casefold()]
        texto = f"no se debe {base}" if negado else f"conviene {base}"
        return texto[0].upper() + texto[1:] if (negado or verbo)[0].isupper() else texto

    # Condicional: "necesitaría inspeccionar" -> "conviene inspeccionar";
    # "si detecto" -> "si se detecta"; "te recomendaría que revisaras" ->
    # "conviene revisar"; "lo reemplazaras" -> "reemplazarlo".
    def infinitivo(raiz: str, terminacion: str) -> str:
        return raiz + {"aras": "ar", "eras": "er", "iras": "ir",
                       "ases": "ar", "eses": "er", "ieses": "ir"}[terminacion]

    respuesta = re.sub(r"\b([Nn])ecesitar[ií]a\s+",
                       lambda m: ("C" if m.group(1) == "N" else "c") + "onviene ", respuesta)
    respuesta = re.sub(r"\b([Ss])i\s+(detecto|encuentro|veo|noto)\b",
                       lambda m: m.group(1) + "i se " + {"detecto": "detecta", "encuentro": "encuentra",
                                                         "veo": "ve", "noto": "nota"}[m.group(2)],
                       respuesta)
    respuesta = re.sub(
        r"\b([Tt])e\s+(?:recomendar[ií]a|sugerir[ií]a|recomiendo|sugiero)\s+que\s+(\w+?)(aras|eras|iras|ases|eses|ieses)\b",
        lambda m: ("C" if m.group(1) == "T" else "c") + "onviene " + infinitivo(m.group(2), m.group(3)),
        respuesta,
    )
    # Segunda persona en futuro: "Revisarás los focos" -> "Conviene
    # revisar los focos" (solo con acento: "eras" sin acento es otra cosa).
    respuesta = re.sub(
        r"\b(\w+?)(ar|er|ir)ás\b",
        lambda m: ("Conviene " if m.group(1)[0].isupper() else "conviene ")
        + m.group(1).lower() + m.group(2),
        respuesta,
    )
    def impersonal(m: re.Match) -> str:
        verbo = {"encuentras": "encuentra", "ves": "ve", "notas": "nota",
                 "detectas": "detecta"}[m.group(3)]
        # "si no encuentras fallas" -> "si no se encuentran fallas"
        if m.group(4).endswith("s"):
            verbo += "n"
        return f"{m.group(1)}i {m.group(2) or ''}se {verbo} {m.group(4)}"

    respuesta = re.sub(
        r"\b([Ss])i\s+(no\s+)?(encuentras|ves|notas|detectas)\s+(\w+)",
        impersonal,
        respuesta,
    )

    respuesta = re.sub(r"\blo\s+(\w+?)(aras|eras|iras)\b",
                       lambda m: infinitivo(m.group(1), m.group(2)) + "lo", respuesta)

    respuesta = re.sub(
        r"\b([Nn]o\s+)?(revisar[ée]|verificar[ée]|comprobar[ée]|inspeccionar[ée]|"
        r"medir[ée]|diagnosticar[ée]|recomendar[ée]|sugerir[ée]|cambiar[ée]|"
        r"reemplazar[ée]|confirmar[ée]|descartar[ée]|afirmar[ée])\b",
        primera_persona,
        respuesta,
        flags=re.IGNORECASE,
    )
    return respuesta


def hay_sobrecalentamiento(pregunta: str) -> bool:
    pregunta_normalizada = normalizar(pregunta)
    return any(s in pregunta_normalizada for s in _SINTOMAS_SOBRECALENTAMIENTO)


def ajustar_respuesta_mecanica(respuesta: str, pregunta: str, tema: str, conocimiento: str | None) -> str:
    # Correcciones a la respuesta de MECÁNICA del modelo (no se usa en
    # consultas de inventario):
    #   - quita reglas internas que el modelo repitió,
    #   - no deja decir "no es peligroso" en frenos, llantas, etc.,
    #   - quita advertencias de emergencia que no corresponden,
    #   - en sobrecalentamiento, agrega las precauciones que falten.
    # Evitar una advertencia genérica de emergencia
    # en consultas mecánicas sin riesgo de sobrecalentamiento.
    respuesta = quitar_reglas_repetidas(respuesta)
    respuesta = hablar_directo(respuesta)
    respuesta = quitar_diagnostico_negado(respuesta)
    respuesta = corregir_minimizacion_de_riesgo(respuesta, tema)
    respuesta = aclarar_banda_o_cadena(respuesta)
    sobrecalentamiento = hay_sobrecalentamiento(pregunta)

    if not sobrecalentamiento:
        advertencia_generica = (
            "Si hay una falla, puede haber problemas de "
            "seguridad, por lo que es importante detenerse "
            "de inmediato en un lugar seguro."
        )

        respuesta = respuesta.replace(
            advertencia_generica,
            ""
        ).strip()

        # Corregir una expresión incorrecta detectada.
        respuesta = re.sub(
            r"\bel tardor en arrancar\b",
            "La dificultad para arrancar",
            respuesta,
            flags=re.IGNORECASE,
        )

        # Eliminar únicamente la advertencia injustificada
        # identificada en la prueba del sistema eléctrico.
        respuesta = re.sub(
            r"Si hay una falla, podría haber un riesgo de "
            r"sobrecalentamiento o daño a otros componentes "
            r"si no se soluciona\.",
            "",
            respuesta,
            flags=re.IGNORECASE,
        ).strip()

    # Validación conservadora de respuestas mecánicas.
    # No afecta las consultas del inventario.
    if conocimiento is not None:

        respuesta_normalizada = normalizar(respuesta)

        expresiones_no_confiables = (
            "definitivamente es",
            "sin duda es",
            "seguramente tienes que cambiar",
            "debes reemplazar",
            "tienes que reemplazar",
            "es necesario reemplazar",
        )

        respuesta_no_confiable = any(
            expresion in respuesta_normalizada
            for expresion in expresiones_no_confiables
        )

        if respuesta_no_confiable:
            respuesta = (
                "No es posible confirmar una falla específica "
                "sin revisar el vehículo. "
                "Estas son las referencias técnicas disponibles:\n\n"
                f"{conocimiento}"
            )


        # Verificar advertencias de seguridad documentadas.
        # Solo se aplica a consultas mecánicas.

        conocimiento_normalizado = normalizar(conocimiento)
        respuesta_normalizada = normalizar(respuesta)

        seguridad_refrigeracion = (
            "sistema refrigeracion" in conocimiento_normalizado
            and "seguridad:" in conocimiento_normalizado
        )

        if sobrecalentamiento and seguridad_refrigeracion:

            menciona_detenerse = any(
                expresion in respuesta_normalizada
                for expresion in (
                    "detente",
                    "detenerse",
                    "detenga",
                    "deten el vehiculo",
                    "detener el vehiculo",
                    "detenga el vehiculo",
                    "deten tu vehiculo",
                )
            )

            menciona_apagar = any(
                expresion in respuesta_normalizada
                for expresion in (
                    "apaga el motor",
                    "apagar el motor",
                    "apague el motor",
                    "apagarlo",
                )
            )

            menciona_tapa_caliente = (
                any(
                    expresion in respuesta_normalizada
                    for expresion in (
                        "tapa del radiador",
                        "tapa del deposito",
                        "tapa del sistema de refrigeracion",
                    )
                )
                and any(
                    expresion in respuesta_normalizada
                    for expresion in (
                        "no abras",
                        "no abrir",
                        "nunca abrir",
                        "no abra",
                    )
                )
                and any(
                    expresion in respuesta_normalizada
                    for expresion in (
                        "caliente",
                        "presurizado",
                    )
                )
            )

            advertencias_faltantes = []

            if not menciona_detenerse:
                advertencias_faltantes.append(
                    "Detente en un lugar seguro"
                )

            if not menciona_apagar:
                advertencias_faltantes.append(
                    "apaga el motor"
                )

            if not menciona_tapa_caliente:
                advertencias_faltantes.append(
                    "no abras la tapa del sistema de "
                    "refrigeración mientras esté caliente, "
                    "debido al riesgo de quemaduras"
                )

            if advertencias_faltantes:
                texto_advertencia = (
                    "Por seguridad: "
                    + "; ".join(advertencias_faltantes)
                    + "."
                )

                respuesta = (
                    texto_advertencia
                    + "\n\n"
                    + respuesta
                )

    return respuesta
