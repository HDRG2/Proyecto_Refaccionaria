import re
import unicodedata

from AgenteIA.mecanica.documentacion_automotriz import DOCUMENTACION_AUTOMOTRIZ


EXPRESIONES_EQUIVALENTES = {
    "sistema_refrigeracion": [
        "se calienta",
        "se sobrecalienta",
        "sobrecalentamiento",
        "sube la temperatura",
        "temperatura del motor",
        "hierve el anticongelante",
        "pierde refrigerante",
    ],
    "sistema_frenos": [
        "al frenar",
        "cuando freno",
        "cuando frena",
        "frenando",
        "rechina",
        "rechinan",
        "no frena",
        "frena poco",
        "chillan los frenos",
        "ruido al frenar",
        "pedal de freno",
        "tarda en frenar",
    ],
    "sistema_suspension": [
        "rebota mucho",
        "rebota demasiado",
        "golpes al pasar baches",
        "ruido en los baches",
        "se siente inestable",
    ],
    "sistema_electrico": [
        "no carga la bateria",
        "se descarga la bateria",
        "falla el alternador",
        "luces parpadean",
        "no da marcha",
    ],
    "sistema_combustible": [
        "bomba de gasolina",
        "bomba de combustible",
        "falta de gasolina",
        "presion de gasolina",
        "presion de combustible",
        "falla de inyectores",
    ],
    "sistema_lubricacion": [
        "baja presion de aceite",
        "sin aceite",
        "falta de lubricacion",
        "bomba de aceite",
        "testigo de aceite",
    ],
    "sistema_transmision": [
        "no entran los cambios",
        "patina la transmision",
        "patina el clutch",
        "caja de velocidades",
        "problemas al cambiar de marcha",
    ],
}


def normalizar_texto(texto: str) -> str:
    texto = texto.casefold()

    texto = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )

    return re.sub(r"\s+", " ", texto).strip()


def contiene_expresion(texto: str, expresion: str) -> bool:
    expresion = normalizar_texto(expresion)

    patron = (
        r"(?<!\w)"
        + re.escape(expresion)
        + r"(?!\w)"
    )

    return re.search(patron, texto) is not None


def detectar_enfoque(pregunta: str) -> str:
    texto = normalizar_texto(pregunta)

    if any(frase in texto for frase in [
        "como saber", "como revisar", "como diagnosticar",
        "como comprobar", "como verificar", "que revisar"
    ]):
        return "diagnostico"

    if any(frase in texto for frase in [
        "que pasa si", "que consecuencias", "que riesgos",
        "puede danar", "es peligroso"
    ]):
        return "consecuencias"

    if any(frase in texto for frase in [
        "que sintomas", "cuales son los sintomas",
        "que senales"
    ]):
        return "sintomas"

    if any(frase in texto for frase in [
        "por que", "que causa", "que provoca",
        "a que se debe"
    ]):
        return "causas"

    return "general"


def seleccionar_documentacion(contenido: str, pregunta: str) -> str:
    # Selecciona los apartados relacionados con la pregunta.

    patron = re.compile(
        r"(?<!\w)(?<![a-záéíóúñ]\s)("
        r"FUNCI[ÓO]N|FUNCIONAMIENTO|"
        r"S[ÍI]NTOMAS(?: DE FALLAS DE SUMINISTRO)?|"
        r"CAUSAS(?: POSIBLES| DE RUIDOS| DE VIBRACI[ÓO]N|"
        r" DE PEDAL ESPONJOSO| DE DESCARGA|"
        r" DE FALLAS DE ARRANQUE)?|"
        r"DIFERENCIA ENTRE BATER[ÍI]A Y ALTERNADOR|"
        r"CONSECUENCIAS(?: DEL PATINAMIENTO)?|"
        r"DIAGN[ÓO]STICO|SEGURIDAD|"
        r"FALLAS DEL SENSOR|DIFERENCIA IMPORTANTE|"
        r"PATINAMIENTO DEL CLUTCH|"
        r"ACLARACIONES|ACLARACI[ÓO]N T[ÉE]CNICA|"
        r"ACLARACI[ÓO]N SOBRE LA BOMBA DE COMBUSTIBLE"
        r"):\s*",
        re.IGNORECASE
    )


    partes = patron.split(contenido)
    apartados = {}

    for indice in range(1, len(partes), 2):
        titulo = partes[indice].strip()
        texto = partes[indice + 1].strip()
        apartados[titulo] = texto

    if not apartados:
        return contenido

    enfoque = detectar_enfoque(pregunta)

    prioridades = {
        "diagnostico": ["diagnostico", "sintomas"],
        "consecuencias": ["consecuencias", "seguridad"],
        "sintomas": ["sintomas", "diagnostico"],
        "causas": ["causas", "diagnostico"],
        "general": ["sintomas", "causas", "diagnostico"]
    }

    consulta = normalizar_texto(pregunta)
    seleccionados = []

    # Priorizar apartados específicos del síntoma.
    equivalencias = {
        "ruidos": ["chillan", "chilla", "chirrido", "rechinan", "rechina",
                   "rechinido", "ruido", "suena", "suenan", "truena"],
        "vibracion": ["vibracion", "vibra"],
        "rebotes": ["rebota", "rebotes"],
        "golpeteos": ["golpes", "golpeteos", "baches"],
        "pedal esponjoso": ["pedal esponjoso"],
        "descarga": ["descarga", "descarga la bateria"],
        "sensor": ["sensor"],
        "patinamiento": ["patina", "patinamiento", "clutch"],
    }

    for titulo, texto in apartados.items():
        titulo_normalizado = normalizar_texto(titulo)

        for categoria, expresiones in equivalencias.items():
            if categoria in titulo_normalizado and any(
                expresion in consulta for expresion in expresiones
            ):
                seleccionados.append((titulo, texto))
                break

    
    # Si ya encontramos una causa específica del síntoma,
    # evitamos añadir diagnósticos generales innecesarios.
    hay_causa_especifica = any(
        normalizar_texto(titulo).startswith("causas")
        for titulo, _ in seleccionados
    )

    
    
    for prioridad in prioridades[enfoque]:
        for titulo, texto in apartados.items():
            titulo_normalizado = normalizar_texto(titulo)
            
            if (
                enfoque == "causas"
                and hay_causa_especifica
                and prioridad == "diagnostico"
            ):
                continue

            if not titulo_normalizado.startswith(prioridad):
                continue

            # Si encontramos una causa específica del síntoma,
            # evitamos agregar causas de otros síntomas.
            if prioridad == "causas":
                causas_especificas = [
                    item for item in seleccionados
                    if normalizar_texto(item[0]).startswith("causas")
                ]

                if causas_especificas:
                    if (titulo, texto) not in seleccionados:
                        continue

            if (titulo, texto) not in seleccionados:
                seleccionados.append((titulo, texto))


     # Incluir seguridad cuando la pregunta describe un riesgo.
    expresiones_riesgo = [
        "sobrecalienta",
        "sobrecalentando",
        "sobrecalentamiento",
        "se calienta mucho",
        "se esta calentando",
        "motor muy caliente",
        "temperatura del motor alta",
        "baja presion de aceite",
        "testigo de aceite",
        "no frena",
        "perdida de frenado",
        "olor a combustible"
    ]

    if any(frase in consulta for frase in expresiones_riesgo):
        for titulo, texto in apartados.items():
            if normalizar_texto(titulo) == "seguridad":
                if (titulo, texto) not in seleccionados:
                    seleccionados.append((titulo, texto))

    # Incluir aclaraciones específicas cuando la pregunta
    # esté relacionada con la bomba de combustible.
    consulta_bomba = any(
        expresion in consulta
        for expresion in [
            "bomba de gasolina",
            "bomba de combustible",
            "bomba de nafta"
        ]
    )

    if consulta_bomba:
        for titulo, texto in apartados.items():
            titulo_normalizado = normalizar_texto(titulo)

            if (
                "aclaracion sobre la bomba" in titulo_normalizado
                and (titulo, texto) not in seleccionados
            ):
                seleccionados.append((titulo, texto))

    
    if not seleccionados:
        seleccionados = list(apartados.items())[:3]

    return "\n".join(
        f"{titulo}: {texto}"
        for titulo, texto in seleccionados
    )



def buscar_conocimiento(
    pregunta: str,
    max_resultados: int = 2
) -> str | None:
    
    pregunta_normalizada = normalizar_texto(pregunta)
    
    
    # Reconocer distintas formas de describir síntomas mecánicos.
    equivalencias_sintomas = {
        "sobrecalentamiento": [
            "sobrecalentando",
            "se calienta mucho",
            "motor muy caliente",
            "temperatura del motor alta",
            "se esta calentando",
        ],
        "falta de potencia": [
            "pierde potencia",
            "perdida de potencia",
            "no tiene fuerza",
            "le falta fuerza",
        ],
        "arranque lento": [
            "tarda en arrancar",
            "le cuesta arrancar",
            "demora en arrancar",
            "arranca lentamente",
            "arranque dificil",
        ],
        "luces tenues": [
            "luces debiles",
            "luces se ven debiles",
            "luces con poca intensidad",
            "luces alumbran poco",
            "faros debiles",
            "faros tenues",
        ],
    }

    terminos_adicionales = []

    for termino, expresiones in equivalencias_sintomas.items():
        if any(
            expresion in pregunta_normalizada
            for expresion in expresiones
        ):
            terminos_adicionales.append(termino)

    if terminos_adicionales:
        pregunta_normalizada += " " + " ".join(terminos_adicionales)


    if not pregunta_normalizada:
        return None

    coincidencias = []

    for nombre_sistema, datos in DOCUMENTACION_AUTOMOTRIZ.items():
        puntuacion = 0

        for expresion in EXPRESIONES_EQUIVALENTES.get(
            nombre_sistema, []
        ):
            if contiene_expresion(
                pregunta_normalizada, expresion
            ):
                puntuacion += 3

        # Frases típicas de cada sistema escritas en documentacion_automotriz
        # ("ruido al frenar", "vibra a cierta velocidad"). Antes no se usaban.
        for expresion in datos.get("expresiones", []):
            if contiene_expresion(
                pregunta_normalizada, expresion
            ):
                puntuacion += 3

        for palabra_clave in datos.get("palabras_clave", []):
            if contiene_expresion(
                pregunta_normalizada, palabra_clave
            ):
                puntuacion += 2

        if puntuacion > 0:
            coincidencias.append(
                (
                    puntuacion,
                    nombre_sistema,
                    datos["contenido"],
                )
            )

    if not coincidencias:
        return None

    coincidencias.sort(
        key=lambda resultado: resultado[0],
        reverse=True
    )

    mejor_puntuacion = coincidencias[0][0]

    # Seleccionar hasta dos sistemas con coincidencias reales.
    # Mantener primero el sistema con mayor puntuación.
    # El segundo sistema solo se agrega si tiene al menos la mitad de la
    # puntuación del mejor: "el volante vibra a alta velocidad" es de
    # llantas; la palabra "volante" sola no debe traer la documentación
    # de dirección (volante duro o chueco) y confundir al modelo.
    mejores_resultados = [
        resultado for resultado in coincidencias[:max(1, max_resultados)]
        if resultado[0] * 2 >= mejor_puntuacion
    ]

    
    documentacion = []

    for _, nombre_sistema, contenido in mejores_resultados:
        titulo = nombre_sistema.replace("_", " ").upper()

        contenido_relevante = seleccionar_documentacion(
            contenido,
            pregunta
        )

        documentacion.append(
            f"SISTEMA: {titulo}\n"
            f"DOCUMENTACIÓN RELEVANTE:\n"
            f"{contenido_relevante}"
        )

    return "\n\n".join(documentacion)

