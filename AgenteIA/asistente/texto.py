import re
import unicodedata


def normalizar(texto: str) -> str:
    # Minúsculas, sin espacios repetidos y sin acentos,
    # para que "qué", "que" y "QUÉ" se traten igual.
    return quitar_acentos(" ".join(texto.casefold().split()))


def normalizar_terminos_automotrices(pregunta: str) -> str:
    
    # Aclara términos automotrices mexicanos para Qwen.
    # No modifica los datos originales del inventario.
    
    equivalencias = {
        "balatas": "pastillas de freno",
        "balata": "pastilla de freno",
    }

    pregunta_normalizada = pregunta

    for termino, equivalente in equivalencias.items():
        patron = r"\b" + re.escape(termino) + r"\b"

        pregunta_normalizada = re.sub(
            patron,
            equivalente,
            pregunta_normalizada,
            flags=re.IGNORECASE,
        )

    return pregunta_normalizada


def quitar_acentos(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(
        c for c in descompuesto
        if unicodedata.category(c) != "Mn"
    )


def _patron_flexible(frase: str) -> str:
    # Convierte "a como esta" en un patrón que también acepta
    # "a cómo está", "A COMO ESTA", etc.
    equivalentes = {
        "a": "[aáà]", "e": "[eéè]", "i": "[iíì]",
        "o": "[oóò]", "u": "[uúüù]", "n": "[nñ]",
    }
    partes = []
    for caracter in frase:
        if caracter == " ":
            partes.append(r"\s+")
        else:
            partes.append(equivalentes.get(caracter, re.escape(caracter)))
    return r"(?<!\w)" + "".join(partes) + r"(?!\w)"


# Expresiones coloquiales o en inglés que se traducen a una forma
# estándar para que las reglas las reconozcan.
EQUIVALENCIAS_REGISTRO = [
    # Precio (formal, informal y coloquial)
    ("en cuanto me lo dejas", "cuál es el precio de"),
    ("en cuanto lo dejas", "cuál es el precio de"),
    ("en cuanto lo das", "cuál es el precio de"),
    ("a como lo das", "cuál es el precio de"),
    ("a como lo dejas", "cuál es el precio de"),
    ("en cuanto sale", "cuál es el precio de"),
    ("cuanto me sale", "cuál es el precio de"),
    ("cuanto sale", "cuál es el precio de"),
    ("en cuanto esta", "cuál es el precio de"),
    ("a como esta", "cuál es el precio de"),
    ("a como sale", "cuál es el precio de"),
    ("a como anda", "cuál es el precio de"),
    ("en cuanto anda", "cuál es el precio de"),
    ("cuanto me cobras por", "cuál es el precio de"),
    ("cuanto me cobras", "cuál es el precio de"),
    ("cuanto cobras por", "cuál es el precio de"),
    ("cuanto cobras", "cuál es el precio de"),
    ("cuanto cobran por", "cuál es el precio de"),
    ("cuanto cobran", "cuál es el precio de"),
    ("que tan caro es", "cuál es el precio de"),
    ("que tan caro esta", "cuál es el precio de"),
    # Inglés básico (se entiende, pero se responde en español)
    ("how much is the", "cuál es el precio de"),
    ("how much is", "cuál es el precio de"),
    ("how much does", "cuál es el precio de"),
    ("how much", "cuánto"),
    ("price of the", "precio de"),
    ("price of", "precio de"),
    ("how many", "cuántas piezas"),
    ("in stock", "en existencia"),
    ("do you have", "hay"),
    # Coloquial automotriz
    ("ranfla", "carro"),
    ("nave", "carro"),
]


# Muletillas que no aportan significado y estorban a las reglas.
MULETILLAS = (
    "por favor", "porfavor", "porfa", "porfis", "plis", "pls",
    "please", "oye", "oiga", "oigan", "disculpa", "disculpe",
    "una pregunta", "una duda", "fijate", "fijese",
    "me podrias decir", "me podria decir", "me puedes decir",
    "me puede decir", "podrias decirme", "puedes decirme",
    "quisiera saber", "quiero saber", "me gustaria saber",
    "bro", "brother", "carnal", "compa", "compadre", "jefe",
    "jefa", "joven", "amigo", "amiga",
    "wey", "guey", "guey", "we", "chavo",
)


def preparar_pregunta(texto: str) -> str:
    # 1. Quitar caracteres invisibles y espacios repetidos.
    texto = "".join(
        c for c in texto
        if unicodedata.category(c)[0] != "C" or c in "\n\t"
    )
    texto = " ".join(texto.split())

    # 2. Reducir letras repetidas exageradas ("holaaaaa" -> "holaa").
    texto = re.sub(r"([a-zA-ZáéíóúüñÁÉÍÓÚÑ])\1{2,}", r"\1\1", texto)

    # 3. Traducir expresiones coloquiales o en inglés.
    for frase, reemplazo in EQUIVALENCIAS_REGISTRO:
        texto = re.sub(
            _patron_flexible(frase), reemplazo, texto,
            flags=re.IGNORECASE,
        )

    # 4. Quitar muletillas.
    for muletilla in MULETILLAS:
        texto = re.sub(
            _patron_flexible(muletilla) + r"[,]?", " ", texto,
            flags=re.IGNORECASE,
        )

    return " ".join(texto.split()).strip(" ,")
