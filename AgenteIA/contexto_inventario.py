import re
import unicodedata


def normalizar_contexto(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )
    return " ".join(texto.casefold().split())


def obtener_productos_mencionados(
    texto: str,
    productos: list[dict]
) -> list[dict]:
    
    #Obtiene productos cuyos códigos aparecen explícitamente
    #en el texto, conservando el orden de aparición.
    
    encontrados = []

    for producto in productos:
        codigo = str(producto.get("codigo", "")).strip()

        if not codigo:
            continue

        coincidencia = re.search(
            rf"(?<![\w-]){re.escape(codigo)}(?![\w-])",
            texto,
            re.IGNORECASE,
        )

        if coincidencia:
            encontrados.append(
                (coincidencia.start(), producto)
            )

    encontrados.sort(key=lambda item: item[0])

    return [producto for _, producto in encontrados]


def resolver_producto_contextual(
    pregunta: str,
    historial: list,
    productos: list[dict],
):

    texto = normalizar_contexto(pregunta)

    referencias_ordinales = {
        "primero": 0,
        "primera": 0,
        "segundo": 1,
        "segunda": 1,
        "tercero": 2,
        "tercera": 2,
        "cuarto": 3,
        "cuarta": 3,
        "quinto": 4,
        "quinta": 4,
    }

    ordinal = None

    for palabra, indice in referencias_ordinales.items():
        if re.search(rf"\b{palabra}\b", texto):
            ordinal = indice
            break

    
    referencia_simple = any(
        expresion in texto
        for expresion in (
            "ese producto",
            "este producto",
            "el anterior",
            "del mismo",
            "y ahora",
            "cuantos quedan",
            "cuantas quedan",
            "cuantos tengo",
            "cuantas tengo",
            "cuanto cuesta ese",
            "cuanto cuesta este",
            "cuanto vale ese",
            "cuanto vale este",
            "su precio",
            "y su precio",
        )
    )

    if ordinal is None and not referencia_simple:
        return None

    # Analizar únicamente los mensajes recientes.
    mensajes_recientes = historial[-12:]

    if ordinal is not None:
        # Para "el primero", "el segundo", etc.,
        # buscar una lista anterior de varios productos.
        for mensaje in reversed(mensajes_recientes):
            if mensaje.rol != "model":
                continue

            mencionados = obtener_productos_mencionados(
                mensaje.texto,
                productos,
            )

            if len(mencionados) < 2:
                continue

            if ordinal < len(mencionados):
                return mencionados[ordinal]

        return None

    # Para "ese", "este" o "¿y ahora cuántos?",
    # buscar la última respuesta sobre un solo producto.
    for mensaje in reversed(mensajes_recientes):
        if mensaje.rol != "model":
            continue

        mencionados = obtener_productos_mencionados(
            mensaje.texto,
            productos,
        )

        if len(mencionados) == 1:
            return mencionados[0]

        # Si el último mensaje contiene varios productos,
        # no elegir uno arbitrariamente.
        if len(mencionados) > 1:
            return None

    return None

