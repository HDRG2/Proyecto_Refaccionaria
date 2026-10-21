import re

from AgenteIA.asistente.productos import (
    dinero,
    etiqueta_producto,
    obtener_existencia,
    obtener_precio,
    productos_en_texto,
)
from AgenteIA.asistente.texto import normalizar


# Categorías que maneja el programa de El Pistón (los botones de WinUI).
# Sirven para reconocer una categoría aunque hoy no tenga productos.
CATEGORIAS_CONOCIDAS = (
    "Aceites", "Filtros", "Frenos", "Suspensión", "Dirección", "Motor",
    "Transmisión", "Sistema eléctrico", "Enfriamiento", "Encendido",
    "Escape", "Iluminación", "Carrocería", "Accesorios", "Lubricantes",
)


def categoria_sin_productos(pregunta: str, productos: list[dict]) -> str | None:
    # "¿qué tenemos de escape?" cuando no hay productos de Escape:
    # devuelve "Escape" para avisar, en lugar de mostrar todo el inventario.
    texto = normalizar(pregunta)
    existentes = {normalizar(str(p.get("categoria", ""))) for p in productos}
    for categoria in CATEGORIAS_CONOCIDAS:
        nombre = normalizar(categoria)
        if nombre in existentes:
            continue
        singular = nombre[:-1] if nombre.endswith("s") else nombre
        if re.search(
            r"(?<!\w)(?:" + re.escape(nombre) + "|" + re.escape(singular) + r")(?:es|s)?(?!\w)",
            texto,
        ):
            return categoria
    return None


def mensaje_categoria_vacia(categoria: str) -> str:
    return (
        f"No hay productos registrados en la categoría {categoria} en este "
        "momento. Escribe \"¿qué categorías tenemos?\" para ver las que sí "
        "tienen productos."
    )


_PALABRAS_FILTRO_COMPLEJO = (
    "poco", "bajo", "agotad", "mas caro", "mas barato", "menor",
    "mayor", "sin stock", "menos de", "mas de", "entre", "universal",
    "compatible", "barato", "caro", "ordena", "ordenados",
)


def es_solicitud_listado(pregunta: str, productos: list[dict]) -> bool:
    texto = normalizar(pregunta).strip(" ¿?¡!.,")

    # "dame los otros 10 productos" es cambiar de página, no una lista nueva.
    if detectar_cambio_pagina(pregunta, productos) is not None:
        return False

    if any(p in texto for p in _PALABRAS_FILTRO_COMPLEJO):
        return False

    # Si mencionan un producto concreto, no es un listado general.
    if productos_en_texto(texto, productos):
        return False

    # Cálculos sobre el inventario ("valor del inventario").
    if re.search(r"\b(?:valor|vale|valen|suma|sumale|total|cuanto dinero|"
                 r"cuanto seria|vendo|vendiera)\b", texto):
        return False

    if re.search(r"\b(?:inventario|inventory|catalogo|listado|stock completo)\b", texto):
        return True

    if re.search(
        r"\b(?:que|cuales|q)\s+(?:productos|refacciones|piezas|cosas|"
        r"articulos)?\s*(?:tenemos|tienes|tienen|tiene|hay|manejas|"
        r"manejan|manejamos|vendes|venden|vendemos|quedan|ofreces|"
        r"ofrecen|ofrecemos)\b(?!\s+que)",
        texto,
    ):
        return True

    if re.search(
        r"\b(?:muestrame|ensename|pasame|dame|ver|mostrar|lista|"
        r"listame|quiero ver)\b.{0,15}\b(?:todo|todos|todas|productos|"
        r"refacciones|piezas|existencias)\b",
        texto,
    ):
        return True

    if re.search(r"\btodo lo que (?:hay|tienes|tenemos|tienen|manejan)\b", texto):
        return True

    if re.search(r"\bwhat do you have\b", texto):
        return True

    return False


def filtrar_listado(pregunta: str, productos: list[dict]) -> tuple[list[dict], str | None]:
    # "¿Qué tenemos de frenos?" -> solo productos de esa categoría,
    # marca o con esa palabra en el nombre.
    texto = normalizar(pregunta)

    for campo in ("categoria", "marca"):
        valores = {
            normalizar(str(p.get(campo, ""))) for p in productos
            if p.get(campo)
        }
        for valor in valores:
            singular = valor[:-1] if valor.endswith("s") else valor
            for forma in (valor, singular):
                if len(forma) >= 3 and re.search(
                    r"(?<!\w)" + re.escape(forma) + r"(?:es|s)?(?!\w)", texto
                ):
                    filtrados = [
                        p for p in productos
                        if normalizar(str(p.get(campo, ""))) == valor
                    ]
                    if filtrados:
                        etiqueta = "Categoría" if campo == "categoria" else "Marca"
                        return filtrados, f"{etiqueta}: {filtrados[0].get(campo)}"

    m = re.search(r"\b(?:de|del|en)\s+([a-z]{4,})\b", texto)
    if m and m.group(1) not in ("inventario", "existencia", "productos", "refacciones", "todo"):
        palabra = m.group(1)
        raiz = palabra[:-2] if palabra.endswith("es") else palabra[:-1] if palabra.endswith("s") else palabra
        filtrados = [
            p for p in productos
            if raiz in normalizar(str(p.get("nombre", "")))
        ]
        if filtrados:
            return filtrados, f"Búsqueda: {palabra}"

    return productos, None


def respuesta_conteo(pregunta: str, productos: list[dict]) -> str | None:
    texto = normalizar(pregunta)

    if productos_en_texto(texto, productos):
        return None

    if re.search(
        r"\bcuant[oa]s\s+(?:productos|refacciones|articulos|tipos de "
        r"productos|productos distintos)\b.{0,25}\b(?:hay|tenemos|tienes|"
        r"tienen|manejan|manejamos|son|existen|activos)\b",
        texto,
    ) or re.search(r"\bcuant[oa]s\s+(?:productos|refacciones)\s*$", texto.strip(" ?¿!.")):
        total_piezas = sum((obtener_existencia(p) or 0) for p in productos)
        return (
            f"Actualmente hay {len(productos)} productos activos en el "
            f"inventario de El Pistón, con {total_piezas} piezas en total."
        )

    if re.search(
        r"\bcuant[oa]s\s+(?:piezas|unidades)\b.{0,20}\b(?:en total|"
        r"en el inventario|en inventario|tenemos en total|hay en total)\b",
        texto,
    ):
        total_piezas = sum((obtener_existencia(p) or 0) for p in productos)
        return (
            f"En total hay {total_piezas} piezas en existencia, "
            f"repartidas en {len(productos)} productos activos."
        )

    return None


def respuesta_ranking(pregunta: str, productos: list[dict]) -> str | None:
    # "¿cuál es el más caro?", "el más barato", "¿qué está agotado?",
    # "¿qué tiene poco stock?", "¿de qué hay más piezas?"
    texto = normalizar(pregunta)

    if not productos:
        return None

    con_precio = [p for p in productos if obtener_precio(p) is not None]
    con_existencia = [p for p in productos if obtener_existencia(p) is not None]

    if re.search(r"\bmas (?:caro|costoso)s?\b|\bmayor precio\b", texto) and con_precio:
        p = max(con_precio, key=obtener_precio)
        return f"El producto más caro es {etiqueta_producto(p)}: {dinero(obtener_precio(p))} (sin IVA)."

    if re.search(r"\bmas (?:barato|economico)s?\b|\bmenor precio\b", texto) and con_precio:
        p = min(con_precio, key=obtener_precio)
        return f"El producto más barato es {etiqueta_producto(p)}: {dinero(obtener_precio(p))} (sin IVA)."

    if re.search(r"\bagotad[oa]s?\b|\bsin (?:stock|existencia|piezas)\b|\bno hay piezas\b", texto):
        agotados = [p for p in con_existencia if obtener_existencia(p) == 0]
        if not agotados:
            return "No hay productos agotados en este momento."
        return "Productos agotados:\n" + "\n".join(f"• {etiqueta_producto(p)}" for p in agotados)

    if re.search(r"\b(?:poco|bajo|baja|poca)s? (?:stock|existencia|inventario)\b|\bstock bajo\b|\bpor agotarse\b|\bse estan acabando\b", texto):
        bajos = sorted(
            [p for p in con_existencia if 0 < obtener_existencia(p) <= 5],
            key=obtener_existencia,
        )
        if not bajos:
            return "No hay productos con existencia baja (5 piezas o menos)."
        return "Productos con existencia baja (5 piezas o menos):\n" + "\n".join(
            f"• {etiqueta_producto(p)}: {obtener_existencia(p)} piezas" for p in bajos
        )

    if re.search(r"\bmas (?:piezas|existencia|stock|unidades)\b|\bmayor (?:existencia|stock)\b", texto) and con_existencia:
        p = max(con_existencia, key=obtener_existencia)
        return f"El producto con más existencia es {etiqueta_producto(p)}: {obtener_existencia(p)} piezas."

    return None


# "Un cliente quiere hacer servicio de frenos, ¿qué le ofrezco?"
# "¿Qué le puedo vender para el cambio de aceite?"
_PIDE_RECOMENDACION_VENTA = (
    r"\b(?:ofrezco|ofrecer|ofrecerle|ofrezca|ofrecemos|le vendo|venderle|"
    r"le doy|que le recomiendo|que le sugiero|que le puedo vender)\b"
)


def respuesta_recomendacion_venta(pregunta: str, productos: list[dict]) -> tuple[str | None, list[dict]]:
    # Responde con los productos reales de la categoría (o marca, o
    # palabra) que mencionó el vendedor, sin pasar por el modelo.
    # Devuelve (respuesta, productos mostrados) o (None, []) si no aplica.
    texto = normalizar(pregunta)

    if not re.search(_PIDE_RECOMENDACION_VENTA, texto):
        return None, []

    # Si nombró un producto concreto, lo atienden las otras etapas.
    if productos_en_texto(texto, productos):
        return None, []

    filtrados, descripcion = filtrar_listado(pregunta, productos)
    if descripcion is None or not filtrados:
        vacia = categoria_sin_productos(pregunta, productos)
        if vacia:
            return mensaje_categoria_vacia(vacia), []
        return None, []

    disponibles = [p for p in filtrados if (obtener_existencia(p) or 0) > 0]
    agotados = [p for p in filtrados if obtener_existencia(p) == 0]

    # Primero los que hay en existencia, del más barato al más caro.
    disponibles.sort(key=lambda p: obtener_precio(p) if obtener_precio(p) is not None else float("inf"))
    mostrados = disponibles[:8]

    if not mostrados:
        lineas = [f"No hay piezas en existencia de {descripcion.split(': ', 1)[-1]}."]
        if agotados:
            lineas.append("Agotados: " + ", ".join(etiqueta_producto(p) for p in agotados[:5]) + ".")
        return "\n".join(lineas), agotados[:5]

    lineas = [f"Puedes ofrecerle ({descripcion}):"]
    for p in mostrados:
        precio = obtener_precio(p)
        existencia = obtener_existencia(p)
        lineas.append(
            f"• {etiqueta_producto(p)}: "
            f"{dinero(precio) + ' sin IVA' if precio is not None else 'sin precio registrado'}"
            f" — {existencia} {'pieza' if existencia == 1 else 'piezas'}"
        )

    if len(disponibles) > len(mostrados):
        lineas.append(f"…y {len(disponibles) - len(mostrados)} más en esta categoría.")
    if agotados:
        lineas.append("Agotados: " + ", ".join(etiqueta_producto(p) for p in agotados[:5]) + ".")

    lineas.append("")
    lineas.append(
        "Confirma con el cliente marca, modelo y año del vehículo antes de "
        "venderle la pieza."
    )
    return "\n".join(lineas), mostrados


# ---------------------------------------------------------------------
# Cambio de página: "siguientes 10", "dame los otros", "más productos",
# "página anterior", "regrésame", "página 2", "los primeros"...
# Se detecta por familias de palabras, no por frases exactas. Solo cuenta
# si el mensaje está hecho ÚNICAMENTE de palabras de paginación y de
# relleno: "¿tienes otras balatas?" es una búsqueda, no una página.
# ---------------------------------------------------------------------

_SIGUIENTE = {
    "siguiente", "siguientes", "sig", "siguen", "sigue", "otros", "otras",
    "resto", "demas", "faltan", "continua", "continuar", "despues", "next",
    "mas", "adelante",
}
_ANTERIOR = {
    "anterior", "anteriores", "atras", "regresa", "regresame", "regresar",
    "vuelve", "volver", "previa", "previos", "previas",
}
_INICIO = {"primeros", "primeras", "inicio", "principio"}

_RELLENO_PAGINA = {
    "dame", "dime", "muestrame", "ensename", "pasame", "quiero", "ver",
    "mostrar", "muestra", "pon", "ponme", "manda", "mandame", "y", "a", "al",
    "la", "las", "el", "lo", "los", "de", "del", "que", "me", "en", "unos",
    "unas", "otro", "otra", "porfa", "por", "favor", "va", "ok", "sale",
    "ahora", "pagina", "paginas", "lista", "listado", "producto",
    "productos", "refacciones", "articulos", "resultados", "diez", "hay",
    "tienes", "tienen", "son", "cuales", "con", "ir", "vamos",
}


def detectar_cambio_pagina(pregunta: str, productos: list[dict] | None = None):
    # Devuelve "siguiente", "anterior", un número de página o None.
    texto = normalizar(pregunta).strip(" ¿?¡!.,")

    m = re.search(r"\bpagina\s*(?:numero\s*)?(\d{1,3})\b", texto)
    if m and len(texto.split()) <= 6:
        return int(m.group(1))

    palabras = re.findall(r"[a-z0-9]+", texto)
    if not palabras or len(palabras) > 8:
        return None

    vocabulario = _SIGUIENTE | _ANTERIOR | _INICIO | _RELLENO_PAGINA
    if any(p not in vocabulario and not p.isdigit() for p in palabras):
        return None

    # "dame los productos" sin ninguna palabra de paginación no es cambio
    # de página (lo atiende el listado general).
    if any(p in _ANTERIOR for p in palabras):
        return "anterior"
    if any(p in _INICIO for p in palabras):
        return 1
    if any(p in _SIGUIENTE for p in palabras):
        return "siguiente"
    return None



# ---------------------------------------------------------------------
# Mensaje que es solo una categoría: "Motor", "iluminación",
# "dime solo los de escape", "productos de suspensión".
# ---------------------------------------------------------------------

_RELLENO_CATEGORIA = {
    "dime", "dame", "muestrame", "ensename", "pasame", "quiero", "ver",
    "mostrar", "solo", "solamente", "nada", "mas", "nomas", "los", "las",
    "el", "la", "lo", "de", "del", "en", "y", "a", "que", "hay", "tenemos",
    "tienes", "tienen", "productos", "producto", "refacciones", "refaccion",
    "piezas", "categoria", "porfa", "por", "favor", "ahora", "y", "unos",
    "unas", "algo",
}


def es_solo_categoria(pregunta: str, productos: list[dict]) -> str | None:
    # Devuelve el nombre de la categoría si el mensaje solo la nombra.
    texto = normalizar(pregunta)
    palabras = [p for p in re.findall(r"[a-z]+", texto) if p not in _RELLENO_CATEGORIA]
    if not palabras or len(palabras) > 3:
        return None
    resto = " ".join(palabras)

    del_inventario = {
        normalizar(str(p.get("categoria", ""))): str(p.get("categoria", "")).strip()
        for p in productos if p.get("categoria")
    }
    conocidas = {normalizar(c): c for c in CATEGORIAS_CONOCIDAS}
    for normal, nombre in {**conocidas, **del_inventario}.items():
        singular = normal[:-1] if normal.endswith("s") else normal
        if resto in (normal, singular, singular + "es", normal + "s"):
            return nombre
    return None


def menciona_categoria(pregunta: str, productos: list[dict]) -> bool:
    # True si el texto nombra alguna categoría (del inventario o del programa).
    texto = normalizar(pregunta)
    nombres = {normalizar(c) for c in CATEGORIAS_CONOCIDAS} | {
        normalizar(str(p.get("categoria", ""))) for p in productos if p.get("categoria")
    }
    for nombre in nombres:
        singular = nombre[:-1] if nombre.endswith("s") else nombre
        if nombre and re.search(
            r"(?<!\w)(?:" + re.escape(nombre) + "|" + re.escape(singular) + r")(?:es|s)?(?!\w)", texto
        ):
            return True
    return False


# ---------------------------------------------------------------------
# "Solo dime el nombre", "sin precios", "¿cómo se llama?"
# ---------------------------------------------------------------------

_PIDE_SOLO_NOMBRE = (
    r"\b(?:solo|solamente|nada mas|nomas|unicamente)\b.{0,20}\bnombres?\b|"
    r"\bsin (?:el |los |sus )?precios?\b|"
    r"\bcomo se llaman?\b|\bcual es (?:su|el) nombre\b|\bque nombre tiene\b"
)


def pide_solo_nombre(pregunta: str) -> bool:
    return re.search(_PIDE_SOLO_NOMBRE, normalizar(pregunta)) is not None



