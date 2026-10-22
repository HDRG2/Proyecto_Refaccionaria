import re

from AgenteIA.asistente.productos import (
    IVA,
    buscar_por_palabra,
    dinero,
    etiqueta_producto,
    identificar_producto,
    obtener_existencia,
    obtener_precio,
    productos_en_texto,
)
from AgenteIA.asistente.texto import normalizar
from AgenteIA.inventario.contexto_inventario import rol_mensaje, texto_mensaje


def _piezas(cantidad: int) -> str:
    return f"{cantidad} {'pieza' if cantidad == 1 else 'piezas'}"


def _codigos_en(texto: str, productos: list[dict]) -> list[dict]:
    return [p for _, p in productos_en_texto(texto, productos)]


def _ultimo_asistente(historial) -> str:
    for mensaje in reversed(list(historial or [])):
        if rol_mensaje(mensaje) != "user":
            return texto_mensaje(mensaje)
    return ""


def _productos_de_lista(contexto, historial, productos, minimo: int = 2) -> list[dict]:
    # La lista que se acaba de mostrar: primero la última respuesta, luego
    # la lista que recuerda WinUI.
    en_ultimo = _codigos_en(_ultimo_asistente(historial), productos)
    if len(en_ultimo) >= minimo:
        return en_ultimo
    codigos = [str(c).casefold() for c in (getattr(contexto, "codigos_lista", None) or [])]
    lista = [p for c in codigos for p in productos if str(p.get("codigo", "")).casefold() == c]
    return lista if len(lista) >= minimo else []


def _recientes_uno_por_mensaje(historial, productos, cuantos: int = 2) -> list[dict]:
    # Los últimos productos vistos de UNO en UNO (fichas): "batería" y
    # luego "¿y el alternador?" -> [alternador, batería].
    vistos = []
    for mensaje in reversed(list(historial or [])[-8:]):
        if rol_mensaje(mensaje) == "user":
            continue
        en_mensaje = _codigos_en(texto_mensaje(mensaje), productos)
        if len(en_mensaje) != 1:
            continue
        if all(en_mensaje[0] is not p for p in vistos):
            vistos.append(en_mensaje[0])
        if len(vistos) == cuantos:
            break
    return list(reversed(vistos))


# =====================================================================
# 1. COMPARAR
# =====================================================================

# Solo comparaciones de PRECIO. "Diferencia entre batería y alternador"
# (sin hablar de precio) es de mecánica y la atiende otra etapa.
_PIDE_COMPARAR = (
    r"\bcompar\w*|\bdiferencia de precio\b|\b(?:mas|menos) (?:barat|car|economic|costos)\w*|"
    r"\bcual conviene\b|\bcual me conviene\b|\bcual sale mejor\b"
)


def _productos_a_comparar(pregunta, texto, productos, contexto, historial) -> list[dict]:
    # a) Nombrados: "el termostato o el radiador", "BAL-002 y FRE-001".
    nombrados = _codigos_en(texto, productos)
    if len(nombrados) >= 2:
        return nombrados[:4]

    partes = re.split(r"\s(?:o|y|vs|versus|contra|con)\s|,", texto)
    encontrados = []
    for parte in partes:
        candidatos = _codigos_en(parte, productos) or buscar_por_palabra(parte, productos)
        if len(candidatos) == 1 and all(candidatos[0] is not p for p in encontrados):
            encontrados.append(candidatos[0])
    if len(encontrados) >= 2:
        return encontrados[:4]

    # b) "las dos balatas", "ambos filtros": una palabra con 2+ productos.
    if re.search(r"\b(?:los dos|las dos|ambos|ambas|los tres|las tres|todas las|todos los)\b", texto):
        varios = buscar_por_palabra(pregunta, productos)
        if 2 <= len(varios) <= 6:
            return varios

    # c) Sin nombres: "¿cuál es más barato?" después de ver dos productos.
    if not buscar_por_palabra(pregunta, productos):
        recientes = _recientes_uno_por_mensaje(historial, productos)
        if len(recientes) == 2:
            return recientes
    return []


def comparar_productos(pregunta, productos, contexto=None, historial=None) -> str | None:
    texto = normalizar(pregunta)
    if not re.search(_PIDE_COMPARAR, texto):
        return None
    # "compara la batería y el alternador" sin hablar de precio, y sin
    # que sean del inventario, puede ser de mecánica: solo se compara si
    # los productos se encuentran en el inventario (ver abajo).
    # "el más barato de esos" lo atiende consulta_sobre_lista.
    if re.search(r"\b(?:de esos|de esas|de la lista|de ahi|de estos|de estas)\b", texto):
        return None

    elegidos = [p for p in _productos_a_comparar(pregunta, texto, productos, contexto, historial)
                if obtener_precio(p) is not None]
    if len(elegidos) < 2:
        return None

    elegidos.sort(key=obtener_precio)
    pide_caro = re.search(r"\bmas (?:car|costos)\w*|\bmenos (?:barat|economic)\w*", texto)
    destacado = elegidos[-1] if pide_caro else elegidos[0]
    adjetivo = "más caro" if pide_caro else "más barato"

    lineas = [f"El {adjetivo} es {etiqueta_producto(destacado)}: {dinero(obtener_precio(destacado))} sin IVA."]
    lineas.append("")
    for p in elegidos:
        existencia = obtener_existencia(p)
        lineas.append(
            f"• {etiqueta_producto(p)}: {dinero(obtener_precio(p))} sin IVA "
            f"({dinero(obtener_precio(p) * (1 + IVA))} con IVA)"
            + (f" — {_piezas(existencia)}" if existencia is not None else "")
        )
    diferencia = obtener_precio(elegidos[-1]) - obtener_precio(elegidos[0])
    lineas.append("")
    lineas.append(f"Diferencia entre el más caro y el más barato: {dinero(diferencia)} sin IVA.")
    return "\n".join(lineas)


# =====================================================================
# 2. CONTAR POR CATEGORÍA O MARCA
# =====================================================================

def conteo_por_grupo(pregunta, productos) -> str | None:
    from AgenteIA.inventario.consultas_inteligentes import (
        detectar_categoria,
        detectar_marca_producto,
    )

    texto = normalizar(pregunta)
    if not re.search(r"\bcuant[oa]s\b", texto):
        return None

    # "¿cuántas marcas / categorías manejamos?"
    for campo, palabra, nombre in (("marca", "marcas", "marcas"), ("categoria", "categorias", "categorías")):
        if re.search(rf"\bcuant[oa]s\s+{palabra}\b", texto):
            valores = sorted({
                str(p.get(campo, "")).strip() for p in productos
                if str(p.get(campo, "")).strip()
                and normalizar(str(p.get(campo))) not in ("sin marca", "sin categoria")
            })
            return f"Se manejan {len(valores)} {nombre}: " + ", ".join(valores) + "."

    if not re.search(r"\b(?:productos|refacciones|articulos|piezas|unidades|hay|tenemos|quedan)\b", texto):
        return None
    if productos_en_texto(texto, productos):
        return None
    # "¿cuántas piezas de aceite quedan?": la palabra señala UN producto
    # (Aceite de Motor), no la categoría.
    if len(buscar_por_palabra(pregunta, productos)) == 1 and not re.search(
        r"\b(?:categoria|marca|de la categoria|de la marca)\b", texto
    ):
        return None

    categoria = detectar_categoria(texto, productos)
    marca = None if categoria else detectar_marca_producto(texto, productos)
    if categoria is None and marca is None:
        return None

    campo, valor = ("categoria", categoria) if categoria else ("marca", marca)
    grupo = [p for p in productos if normalizar(str(p.get(campo, ""))) == normalizar(valor)]
    piezas = sum((obtener_existencia(p) or 0) for p in grupo)
    etiqueta = f"la categoría {valor}" if categoria else f"la marca {valor}"
    return (
        f"En {etiqueta} hay {len(grupo)} {'producto' if len(grupo) == 1 else 'productos'} "
        f"con {_piezas(piezas)} en existencia en total."
    )


# =====================================================================
# 3. SOBRE LA LISTA QUE SE ACABA DE MOSTRAR
# =====================================================================

_SOBRE_LISTA = r"\b(?:de esos|de esas|de estos|de estas|de la lista|de ahi|de los que me diste|esos|esas)\b"


def consulta_sobre_lista(pregunta, productos, contexto=None, historial=None) -> str | None:
    texto = normalizar(pregunta)
    if not re.search(_SOBRE_LISTA, texto):
        return None
    # "¿y de esas cuántas hay?" vale aunque la lista tenga un solo producto.
    lista = _productos_de_lista(contexto, historial, productos, minimo=1)
    if not lista:
        return None

    con_precio = [p for p in lista if obtener_precio(p) is not None]
    if re.search(r"\bmas (?:barat|economic)\w*|\bmenor precio\b", texto) and con_precio:
        p = min(con_precio, key=obtener_precio)
        return f"El más barato de esa lista es {etiqueta_producto(p)}: {dinero(obtener_precio(p))} sin IVA."
    if re.search(r"\bmas (?:car|costos)\w*|\bmayor precio\b", texto) and con_precio:
        p = max(con_precio, key=obtener_precio)
        return f"El más caro de esa lista es {etiqueta_producto(p)}: {dinero(obtener_precio(p))} sin IVA."

    if re.search(r"\bcuant[oa]s\b|\bexistencia|\bstock\b|\bquedan\b|\bhay\b", texto):
        lineas = ["Existencia de los productos de esa lista:"]
        for p in lista:
            existencia = obtener_existencia(p)
            lineas.append(f"• {etiqueta_producto(p)}: {_piezas(existencia) if existencia is not None else 'sin dato'}")
        return "\n".join(lineas)

    if re.search(r"\bprecio|\bcuesta|\bcuestan|\bvale|\bvalen|\biva\b", texto) and con_precio:
        lineas = ["Precios de los productos de esa lista:"]
        for p in con_precio:
            lineas.append(
                f"• {etiqueta_producto(p)}: {dinero(obtener_precio(p))} sin IVA "
                f"({dinero(obtener_precio(p) * (1 + IVA))} con IVA)"
            )
        return "\n".join(lineas)
    return None


# =====================================================================
# 4. ¿ALCANZA LA EXISTENCIA?
# =====================================================================

_PIDE_SUFICIENCIA = (
    r"\b(?:alcanza|alcanzan|alcanzaria|suficiente|suficientes|ajusta|"
    r"completo|completamos|hay para|tengo para|tenemos para|da para)\b"
)


def suficiencia(pregunta, productos, contexto=None) -> str | None:
    from AgenteIA.asistente.calculadora import _palabras_a_numeros
    from AgenteIA.inventario.contexto_inventario import obtener_producto_seleccionado

    texto = normalizar(pregunta)
    if not re.search(_PIDE_SUFICIENCIA, texto):
        return None
    numeros = re.findall(r"\b(\d{1,5})\b", _palabras_a_numeros(texto))
    if not numeros:
        return None
    pedidas = int(numeros[-1])

    producto = identificar_producto(pregunta, productos)
    if producto is None:
        por_palabra = buscar_por_palabra(pregunta, productos)
        producto = por_palabra[0] if len(por_palabra) == 1 else None
    if producto is None and contexto is not None:
        producto = obtener_producto_seleccionado(contexto, productos)
    if producto is None:
        return None

    existencia = obtener_existencia(producto)
    if existencia is None:
        return f"No hay una existencia válida registrada para {etiqueta_producto(producto)}."
    if existencia >= pedidas:
        return (
            f"Sí alcanza: hay {_piezas(existencia)} de {etiqueta_producto(producto)} "
            f"y se necesitan {pedidas}. Quedarían {_piezas(existencia - pedidas)}."
        )
    return (
        f"No alcanza: solo hay {_piezas(existencia)} de {etiqueta_producto(producto)} "
        f"y se necesitan {pedidas}. Faltan {_piezas(pedidas - existencia)}."
    )


# =====================================================================
# 5. PRECIOS DE TODA UNA CATEGORÍA ("precio con iva de todo frenos")
# =====================================================================

def precios_de_grupo(pregunta, productos) -> str | None:
    from AgenteIA.inventario.consultas_inteligentes import detectar_categoria

    texto = normalizar(pregunta)
    if not re.search(r"\bprecios?\b|\bcuanto cuestan\b|\bcuesta\b", texto):
        return None
    if not re.search(r"\b(?:todo|toda|todos|todas|categoria|los de|las de)\b", texto):
        return None
    if productos_en_texto(texto, productos):
        return None
    categoria = detectar_categoria(texto, productos)
    if categoria is None:
        return None
    grupo = [p for p in productos
             if normalizar(str(p.get("categoria", ""))) == normalizar(categoria)
             and obtener_precio(p) is not None]
    if not grupo:
        return None
    lineas = [f"Precios de la categoría {categoria}:"]
    for p in sorted(grupo, key=obtener_precio):
        lineas.append(
            f"• {etiqueta_producto(p)}: {dinero(obtener_precio(p))} sin IVA "
            f"({dinero(obtener_precio(p) * (1 + IVA))} con IVA)"
        )
    return "\n".join(lineas)


# =====================================================================
# Todas, en orden
# =====================================================================

def consulta_extra(pregunta, productos, contexto=None, historial=None) -> str | None:
    for funcion in (
        lambda: suficiencia(pregunta, productos, contexto),
        lambda: comparar_productos(pregunta, productos, contexto, historial),
        lambda: consulta_sobre_lista(pregunta, productos, contexto, historial),
        lambda: conteo_por_grupo(pregunta, productos),
        lambda: precios_de_grupo(pregunta, productos),
    ):
        respuesta = funcion()
        if respuesta is not None:
            return respuesta
    return None

