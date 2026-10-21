import re

from AgenteIA.asistente.texto import normalizar


MENSAJE_AYUDA = (
    "Soy el asistente virtual de El Pistón. Puedo ayudarte con:\n"
    "• Inventario: \"¿qué tenemos en inventario?\", \"¿qué hay de frenos?\"\n"
    "• Productos: \"dame el filtro de aceite\", \"¿cuánto cuesta el ACE-001?\"\n"
    "• Existencias: \"¿cuántas piezas quedan del ACE-001?\"\n"
    "• Cálculos: \"súmalo si lo vendo todo\", \"si vendo 3\", "
    "\"con IVA\", \"suma el ACE-001 y el FIL-001\", \"cuánto es 150 por 4\"\n"
    "• Compatibilidad: \"¿el ACE-001 es compatible con un Nissan Versa 2015?\"\n"
    "• Mecánica: \"¿qué pasa si no cambio las balatas?\""
)


_SALUDOS = {
    "hola", "holi", "holis", "buenas", "buenos dias", "buen dia",
    "buenas tardes", "buenas noches", "que onda", "q onda",
    "quiubo", "quiubole", "que hubo", "que tal", "hola que tal",
    "que paso", "que pex", "hey", "saludos", "hello", "hi",
    "hola buenos dias", "hola buenas tardes", "hola buenas noches",
    "hola buenas", "que onda que tal", "hola que onda",
}


_GRACIAS = {
    "gracias", "muchas gracias", "mil gracias", "grax", "thx",
    "thanks", "thank you", "te pasaste", "gracias crack",
    "ok gracias", "va gracias", "sale gracias", "perfecto gracias",
    "muy amable", "se agradece", "chido gracias",
}


_DESPEDIDAS = {
    "adios", "bye", "nos vemos", "hasta luego", "chao", "chau",
    "hasta pronto", "sale bye", "me voy", "hasta manana",
    "bye bye", "nos vidrios",
}


_CONFIRMACIONES = {
    "ok", "okay", "okey", "va", "sale", "vale", "si", "no", "bien",
    "entendido", "de acuerdo", "ya", "listo", "perfecto", "chido",
    "excelente", "orale", "simon", "nel", "ajam", "aja", "mmm",
    "ah", "oh", "ok va", "sale va",
}


_IDENTIDAD = (
    r"\b(?:quien eres|que eres|como te llamas|cual es tu nombre|"
    r"tu nombre|eres (?:una )?ia|eres humano|eres un robot|"
    r"eres chatgpt|eres gemini|que modelo eres|quien te creo|"
    r"quien te hizo|eres real)\b"
)


_AYUDA = (
    r"\b(?:ayuda|ayudame|que puedes hacer|que sabes hacer|"
    r"como funcionas|en que me ayudas|en que me puedes ayudar|"
    r"menu|opciones|instrucciones de uso|como te uso|"
    r"que haces|para que sirves)\b"
)


MENSAJE_FUERA_DE_TEMA = (
    "Solo puedo ayudarte con refacciones, inventario, precios, cálculos "
    "de ventas y mecánica automotriz. ¿Qué necesitas consultar?"
)

# Pedidos creativos o de entretenimiento. Si se PIDEN ("escríbeme un poema
# sobre balatas", "cuéntame un chiste") se rechazan aunque mencionen una
# refacción. "El motor hace un ruido como de canción" no es un pedido.
_PEDIDO_CREATIVO = (
    r"\b(?:poema|poemas|poesia|verso|versos|rima|rimas|cancion|canciones|"
    r"rap|cuento|cuentos|chiste|chistes|adivinanza|adivinanzas|receta|"
    r"recetas|horoscopo|trabalenguas|novela|ensayo|carta de amor|"
    r"historia inventada|chisme|piropo)\b"
)

# Verbos con los que se PIDE algo: "escríbeme", "cuéntame", "dame"...
_PIDE = (
    r"\b(?:escribe|escribeme|escribir|cuenta|cuentame|contar|dime|dame|"
    r"hazme|haz|inventa|inventame|canta|cantame|recita|recitame|quiero|"
    r"me das|me cuentas|me escribes|me haces|pasame|sabes|conoces|"
    r"tienes|otro|otra)\b"
)

# Temas generales: se rechazan si la pregunta no habla de autos.
_TEMA_GENERAL = (
    r"\b(?:mundial|futbol|partido de futbol|liga mx|equipo de futbol|"
    r"beisbol|basquetbol|capital de|presidente|presidenta|politica|"
    r"elecciones|partido politico|gobierno|pelicula|peliculas|serie|"
    r"series|actor|actriz|cantante|musica|tarea|examen|escuela|novia|"
    r"novio|amor|dios|religion|como me veo|que hora es|que dia es|"
    r"bitcoin|criptomoneda|historia de mexico)\b"
)

_TEMA_AUTOMOTRIZ = (
    r"\b(?:carro|carros|auto|autos|coche|coches|vehiculo|vehiculos|"
    r"camioneta|motor|freno|frenos|balata|balatas|aceite|llanta|llantas|"
    r"refaccion|refacciones|pieza|piezas|bateria|suspension|"
    r"transmision|clutch|mecanic[oa]|taller|inventario|producto|productos|"
    r"volante|direccion|estereo|autoestereo|radio|bocina|bocinas|tablero)\b"
)


def es_fuera_de_tema(texto_normalizado: str) -> bool:
    creativo = re.search(_PEDIDO_CREATIVO, texto_normalizado)
    if creativo and (
        re.search(_PIDE, texto_normalizado[:creativo.start()])
        or not re.search(_TEMA_AUTOMOTRIZ, texto_normalizado)
    ):
        return True
    return bool(
        re.search(_TEMA_GENERAL, texto_normalizado)
        and not re.search(_TEMA_AUTOMOTRIZ, texto_normalizado)
        # "tarea" con números ("¿cuánto es 5 por 3? es para mi tarea")
        # se deja pasar a la calculadora.
        and not re.search(r"\d", texto_normalizado)
    )


def _sin_letras_repetidas(texto: str) -> str:
    # "holaaaa" -> "hola", "graciass" -> "gracias", "byee" -> "bye".
    return re.sub(r"([a-zñ])\1+", r"\1", texto)


def _esta_en(limpio: str, frases: set) -> bool:
    # Compara también sin letras repetidas, para aceptar "holaaaa".
    corto = _sin_letras_repetidas(limpio)
    return limpio in frases or corto in {_sin_letras_repetidas(f) for f in frases}


def respuesta_social(pregunta: str) -> str | None:
    texto = normalizar(pregunta)
    limpio = " ".join(re.sub(r"[^a-z0-9ñ ]", " ", texto).split())

    if not limpio:
        return (
            "No entendí tu mensaje. Escríbeme tu consulta sobre "
            "refacciones, inventario, precios o mecánica automotriz."
        )

    if _esta_en(limpio, _SALUDOS):
        return "¡Hola! Bienvenido a El Pistón. ¿En qué puedo ayudarte?"

    if _esta_en(limpio, _GRACIAS):
        return "Con gusto. ¿Necesitas consultar algo más?"

    if _esta_en(limpio, _DESPEDIDAS):
        return "Hasta luego. Gracias por utilizar El Pistón."

    if _esta_en(limpio, _CONFIRMACIONES):
        return "De acuerdo. ¿Necesitas consultar algo más?"

    # Risas: "jaja", "jejeje", "xd", "lol"
    if re.fullmatch(r"(?:(?:ja|je|ji|jo|ha|he|xd|lol|lmao)\s*)+", limpio):
        return "¿En qué puedo ayudarte con una consulta automotriz?"

    if re.search(_IDENTIDAD, limpio):
        return (
            "Soy el asistente virtual de El Pistón. Te ayudo con "
            "refacciones, inventario, precios, cálculos de ventas "
            "y mecánica automotriz. ¿Qué necesitas?"
        )

    if re.search(_AYUDA, limpio) and len(limpio.split()) <= 6:
        return MENSAJE_AYUDA

    # Temas que no son de la refaccionaria: respuesta fija, sin modelo.
    if es_fuera_de_tema(limpio):
        return MENSAJE_FUERA_DE_TEMA

    # Solo números ("123") sin ninguna operación.
    if re.fullmatch(r"[\d\s.,]+", limpio):
        return (
            "Recibí solo un número. ¿Qué quieres hacer con él? "
            "Por ejemplo: \"si vendo 3 del ACE-001\" o \"cuánto es 150 por 4\"."
        )

    # Teclazos al azar: palabras sin vocales o casi sin vocales
    # ("sdfghj", "asdfghjkl", "qwrtp").
    palabras = limpio.split()

    def es_teclazo(p: str) -> bool:
        if p.isdigit():
            return False
        # "mot001", "bal_002": es un código, no un teclazo.
        if re.fullmatch(r"[a-z]{2,5}[_-]?\d{2,5}", p):
            return False
        vocales = len(re.findall(r"[aeiouy]", p))
        if vocales == 0:
            return True
        return len(p) >= 6 and vocales / len(p) < 0.2

    if all(es_teclazo(p) for p in palabras):
        return (
            "No entendí tu mensaje. ¿Podrías escribir tu consulta "
            "de otra forma?"
        )

    return None

