import re
import unicodedata

from AgenteIA.mecanica.documentacion_automotriz import DOCUMENTACION_AUTOMOTRIZ


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or "").casefold())
    return "".join(c for c in texto if not unicodedata.combining(c))


def _raiz(palabra: str) -> str:
    # "cables"/"cableado" -> "cable"; "balatas"/"balata" -> "balat"
    return palabra[:5] if len(palabra) >= 5 else palabra


# Síntomas: la raíz de cada palabra ("rechin" cubre rechina, rechinido,
# rechinar...). Si la respuesta usa uno que no viene de la pregunta ni de
# la documentación, es un síntoma inventado.
_SINTOMAS = (
    "rechin", "chilla", "chillan", "chirri", "vibra", "tiembl", "humo",
    "vapor", "golpet", "truena", "truen", "zumba", "zumbid", "fuga",
    "gotea", "goteo", "calien", "sobrec", "patina", "jalone", "tiron",
    "rebota", "rebote", "olor", "huele", "quemad", "cascab", "ahoga",
    "parpad", "chispa", "silbid", "pitido", "crujid", "cruje", "tronid",
    "derram", "escurr",
)


def _piezas_documentadas() -> set[str]:
    piezas = set()
    for datos in DOCUMENTACION_AUTOMOTRIZ.values():
        for frase in datos.get("palabras_clave", []):
            for palabra in re.findall(r"[a-z]+", _normalizar(frase)):
                if len(palabra) >= 5:
                    piezas.add(_raiz(palabra))
    return piezas


_PIEZAS = _piezas_documentadas()

# Piezas que se mencionan como consejo general en casi cualquier respuesta
# ("revisar con un mecánico", "consultar el manual") y no son inventos.
_PIEZAS_GENERALES = {_raiz(p) for p in (
    "manual", "fabricante", "mecanico", "taller", "escaner", "vehiculo",
    "motor", "sistema", "servicio", "revision", "mantenimiento",
    "indicar", "indica", "indicador", "componente", "componentes",
    "parte", "partes", "pieza", "piezas", "falla", "fallas", "problema",
    "danado", "estado", "funcionamiento", "presion", "nivel",
)}


def _texto_de_sistemas(conocimiento: str) -> str:
    # Toda la documentación de los sistemas que se le dieron al modelo
    # (no solo los apartados elegidos), para no castigar menciones válidas.
    titulos = re.findall(r"SISTEMA: ([A-ZÁÉÍÓÚÑ ]+)", conocimiento or "")
    partes = [conocimiento or ""]
    for clave, datos in DOCUMENTACION_AUTOMOTRIZ.items():
        if clave.replace("_", " ").upper() in titulos:
            partes.append(datos.get("contenido", ""))
            partes.extend(datos.get("palabras_clave", []))
            partes.extend(datos.get("expresiones", []))
    return " ".join(partes)


def terminos_inventados(respuesta: str, pregunta: str, conocimiento: str) -> list[str]:
    """Síntomas o piezas de la respuesta que no vienen de la pregunta
    ni de la documentación. Lista vacía = respuesta aceptable."""
    respaldo = _normalizar(pregunta + " " + _texto_de_sistemas(conocimiento))
    raices_respaldo = {_raiz(p) for p in re.findall(r"[a-z]+", respaldo)}

    inventados = []
    for palabra in re.findall(r"[a-z]+", _normalizar(respuesta)):
        raiz = _raiz(palabra)
        if raiz in raices_respaldo or raiz in _PIEZAS_GENERALES:
            continue
        es_sintoma = any(palabra.startswith(s) for s in _SINTOMAS)
        es_pieza = len(palabra) >= 5 and raiz in _PIEZAS
        if (es_sintoma or es_pieza) and palabra not in inventados:
            # El síntoma puede venir con otra forma ("vibracion" en la
            # documentación y "vibra" en la respuesta).
            if es_sintoma and any(respaldo.find(s) >= 0 for s in _SINTOMAS if palabra.startswith(s)):
                continue
            inventados.append(palabra)
    return inventados


_TITULOS_LEGIBLES = {
    "FUNCIÓN": "Función", "FUNCIONAMIENTO": "Función",
    "DIAGNÓSTICO": "Qué revisar", "SEGURIDAD": "Por seguridad",
    "CONSECUENCIAS": "Si no se atiende", "MANTENIMIENTO": "Mantenimiento",
}


def respuesta_desde_documentacion(conocimiento: str, maximo_apartados: int = 3) -> str | None:
    """Arma una respuesta con la documentación revisada (sin modelo)."""
    if not conocimiento:
        return None

    # Solo el primer sistema (el que mejor coincide con la pregunta).
    primero = re.split(r"\n\s*\nSISTEMA: ", conocimiento.strip())[0]
    cuerpo = primero.split("DOCUMENTACIÓN RELEVANTE:", 1)[-1].strip()

    lineas = []
    for linea in cuerpo.splitlines():
        m = re.match(r"\s*([A-ZÁÉÍÓÚÑ ]+):\s*(.+)", linea)
        if not m:
            continue
        titulo, texto = m.group(1).strip(), m.group(2).strip()
        if titulo.startswith("SÍNTOMAS"):
            nombre = "Síntomas comunes"
        elif titulo.startswith("CAUSAS"):
            nombre = "Causas posibles"
        else:
            nombre = _TITULOS_LEGIBLES.get(titulo, titulo.capitalize())
        lineas.append(f"{nombre}: {texto}")
        if len(lineas) >= maximo_apartados:
            break

    # La seguridad siempre va si la documentación la trae.
    m = re.search(r"SEGURIDAD:\s*(.+)", cuerpo)
    if m and not any(l.startswith("Por seguridad") for l in lineas):
        lineas.append(f"Por seguridad: {m.group(1).strip()}")

    return "\n\n".join(lineas) if lineas else None
