import re

from AgenteIA.asistente.texto import normalizar
from AgenteIA.inventario.utilidades_inventario import (
    obtener_existencia as _existencia_compartida,
    obtener_precio as _precio_compartido,
)


IVA = 0.16


def identificar_producto(pregunta: str, productos: list[dict]):
    
    #Identifica un producto mediante su código completo
    #o su nombre completo.

    pregunta_normalizada = normalizar(pregunta)

    # Prioridad 1: código exacto
    encontrados_codigo = []

    for producto in productos:
        codigo = str(producto.get("codigo", "")).strip()

        if not codigo:
            continue

        patron = (
            r"(?<!\w)"
            + re.escape(codigo)
            + r"(?!\w)"
        )

        if re.search(patron, pregunta, re.IGNORECASE):
            encontrados_codigo.append(producto)

    if len(encontrados_codigo) == 1:
        return encontrados_codigo[0]

    if len(encontrados_codigo) > 1:
        return None

    # Prioridad 2: nombre completo
    encontrados_nombre = [
        producto
        for producto in productos
        if normalizar(str(producto.get("nombre", "")))
        and normalizar(str(producto.get("nombre", "")))
        in pregunta_normalizada
    ]

    if len(encontrados_nombre) == 1:
        return encontrados_nombre[0]
    
    if len(encontrados_nombre) > 1:
        return None
    
    # Prioridad 3: Coincidencia parcial por palabras completas
    # Excluir palabras genericas para evitar falsos positivos
    
    palabras_ignoradas = {
       "de", "del", "la", "el", "los", "las",
        "para", "con", "sin", "un", "una",
        "producto", "productos", "refaccion", "refacciones", 
    }
    
    candidatos = []
    
    for producto in productos:
        nombre = normalizar(str(producto.get("nombre","")))
        
        palabras_nombre = [
            palabra
            for palabra in nombre.split()
            if len(palabra) >= 4
            and palabra not in palabras_ignoradas
        ]
        
        if not palabras_nombre:
            continue
        
        if all(
            re.search(
                r"(?<!\w)" + re.escape(palabra) + r"(?!\w)",
                pregunta_normalizada,   
            )
            for palabra in palabras_nombre
        ):
            candidatos.append(producto)
            
    if len(candidatos) == 1:
        return candidatos[0]
    
    # Si se encuentran varios candidatos, priorizar coincidencia
    # con la categoria del producto
    
    if len(candidatos) > 1:
        candidatos_categoria = []
        
        for producto in candidatos:
            categoria = normalizar(
                str(producto.get("categoria", ""))
            )
            
            if not categoria:
                continue
            
            # Comparacion de la forma singular
            # "Aceites" -> "aceites".
            categoria_singular = (
                categoria[:-1]
                if categoria.endswith("s")
                else categoria
            )
            
            patron_categoria = (
                r"(?<!\w)" + re.escape(categoria_singular) + r"(?!\w)"
            )
            
            if re.search(patron_categoria, pregunta_normalizada):
                candidatos_categoria.append(producto)
                
        if len(candidatos_categoria) == 1:
            return candidatos_categoria[0]
        
    return None # Sin condicion o con varios productos posibles


def detectar_intencion(pregunta: str):
    texto = normalizar(pregunta)
        # Detectar preguntas sobre universalidad.
    if re.search(r"\buniversal(?:es)?\b", texto):
        return "universalidad"

    # Con límites de palabra: "vale" no debe coincidir con "equivale",
    # ni "cuesta" con "encuesta", ni "costo" con "costoso".
    # (El texto ya viene sin acentos: "cuántos" llega como "cuantos".)
    palabras_existencia = (
        r"\b(?:existencias?|stock|unidades|piezas|disponibles?|"
        r"cuantos|cuantas)\b"
    )

    palabras_precio = r"\b(?:precios?|cuesta|cuestan|vale|valen|costos?)\b"

    palabras_compatibilidad = (
        r"\b(?:compatibles?|compatibilidad|le queda|le sirve|funciona para)\b"
    )

    if re.search(palabras_compatibilidad, texto):
        return "compatibilidad"

    if re.search(palabras_precio, texto):
        return "precio"

    if re.search(palabras_existencia, texto):
        return "existencia"

    return None


def extraer_vehiculo(pregunta: str):

    #Extrae un vehículo después de expresiones comunes.
    #No supone que cualquier texto sea un vehículo válido.
   
    texto = normalizar(pregunta)
   
    patron = (
        r"\b(?:con|para|a)\s+"
        r"(?:un|una|el|la)?\s*"
        r"([a-z0-9]+(?:[\s-]+[a-z0-9]+){1,5}"
        r"\s+(?:19|20)\d{2})\b"
    )

    coincidencia = re.search(
        patron,
        texto,
        re.IGNORECASE,
    )

    if coincidencia:
        return coincidencia.group(1).strip()

    return None


def obtener_precio(producto: dict) -> float | None:
    # Mismas reglas que el resto del asistente (utilidades_inventario):
    # rechaza precios negativos, NaN, infinito y texto inválido.
    precio = _precio_compartido(producto)
    return float(precio) if precio is not None else None


def obtener_existencia(producto: dict) -> int | None:
    # Acepta 10, 10.0 o "10"; rechaza 10.7, negativos y texto inválido.
    return _existencia_compartida(producto)


def dinero(valor: float) -> str:
    return f"${valor:,.2f}"


def etiqueta_producto(producto: dict) -> str:
    return f"{producto.get('nombre', 'Sin nombre')} ({producto.get('codigo', 'Sin código')})"


def ficha_producto(producto: dict) -> str:
    precio = obtener_precio(producto)
    existencia = obtener_existencia(producto)

    lineas = [etiqueta_producto(producto)]

    if producto.get("marca"):
        lineas.append(f"• Marca: {producto.get('marca')}")
    if producto.get("categoria"):
        lineas.append(f"• Categoría: {producto.get('categoria')}")

    if precio is not None:
        lineas.append(f"• Precio: {dinero(precio)} (sin IVA)")
        lineas.append(f"• Precio con IVA (16%): {dinero(precio * (1 + IVA))}")
    else:
        lineas.append("• Precio: no registrado")

    if existencia is not None:
        lineas.append(
            f"• Existencia: {existencia} "
            f"{'pieza' if existencia == 1 else 'piezas'}"
        )
    else:
        lineas.append("• Existencia: no registrada")

    universal = producto.get("universal")
    if isinstance(universal, bool):
        lineas.append(f"• Universal: {'Sí' if universal else 'No'}")

    return "\n".join(lineas)


def productos_en_texto(texto: str, productos: list[dict]) -> list[tuple[int, dict]]:
    # Encuentra productos mencionados por código o nombre completo.
    # Devuelve (posición, producto) en el orden en que aparecen.
    texto_normal = normalizar(texto)
    encontrados: dict[str, tuple[int, dict]] = {}

    for producto in productos:
        codigo = normalizar(str(producto.get("codigo", "")))
        nombre = normalizar(str(producto.get("nombre", "")))

        for termino in (codigo, nombre):
            if not termino:
                continue
            m = re.search(
                r"(?<!\w)" + re.escape(termino) + r"(?!\w)",
                texto_normal,
            )
            if m:
                clave = codigo or nombre
                if clave not in encontrados or m.start() < encontrados[clave][0]:
                    encontrados[clave] = (m.start(), producto)

    return sorted(encontrados.values(), key=lambda x: x[0])


def ultimo_mensaje_asistente(historial) -> str:
    for mensaje in reversed(historial or []):
        if mensaje.rol != "user":
            return mensaje.texto or ""
    return ""


PREGUNTA_MECANICA = (
    r"\b(?:para que sirve|para que es|que es|que son|como funciona|"
    r"como se|cada cuanto|por que|porque|cuando|como cambio|como "
    r"instalo|como pongo|falla|fallas|ruido|sintoma|sintomas|riesgo|"
    r"peligro|que pasa|diferencia|recomiendas|recomienda|sirve para|"
    r"le queda|compatible|hay que|se debe|debo)\b"
)


PEDIR_PRODUCTO = (
    r"\b(?:dame|dime|pasame|muestrame|ensename|busca|buscame|quiero|"
    r"necesito|ocupo|info|informacion|datos|detalles|ficha|hay|"
    r"tienes|tienen|tenemos|manejan|manejas|venden|vendes|queda|"
    r"quedan|existe|checa|revisa|consulta|ver)\b"
)


def es_pedido_de_producto(pregunta: str, producto: dict) -> bool:
    texto = normalizar(pregunta).strip(" ¿?¡!.,")

    if re.search(PREGUNTA_MECANICA, texto):
        return False

    if re.search(PEDIR_PRODUCTO, texto):
        return True

    # Solo escribieron el nombre o el código del producto.
    resto = texto
    for termino in (
        normalizar(str(producto.get("codigo", ""))),
        normalizar(str(producto.get("nombre", ""))),
    ):
        if termino:
            resto = resto.replace(termino, " ")
    resto = re.sub(
        r"\b(?:el|la|los|las|un|una|de|del|producto|refaccion|pieza|y|"
        r"codigo|que|sobre)\b", " ", resto
    )
    return not resto.strip(" ¿?¡!.,")


_PALABRAS_NO_PRODUCTO = {
    "tienes", "tienen", "tenemos", "tiene", "quedan", "queda", "cuanto",
    "cuanta", "cuantos", "cuantas", "cuesta", "cuestan", "precio",
    "precios", "piezas", "pieza", "dame", "quiero", "necesito", "ocupo",
    "manejan", "manejas", "venden", "vendes", "vendo", "vende", "para",
    "sobre", "existencia", "existencias", "stock", "producto",
    "productos", "refaccion", "refacciones", "busca", "buscame",
    "muestrame", "ensename", "pasame", "informacion", "detalles",
    "datos", "cual", "cuales", "como", "esta", "estan", "algun",
    "alguna", "algunos", "algunas", "todo", "todos", "todas", "favor",
    "sumalo", "sumala", "suma", "total", "seria", "serian", "unidades",
    "vehiculo", "carro", "coche", "auto", "nuevo", "nueva", "hola",
}


def buscar_por_palabra(pregunta: str, productos: list[dict]) -> list[dict]:
    # "¿hay balatas?", "¿tienes aceite?" -> productos cuyo nombre
    # contiene esa palabra (acepta plurales: balatas/balata).
    texto = normalizar(pregunta)
    palabras = [
        p for p in re.findall(r"[a-z]+", texto)
        if len(p) >= 4 and p not in _PALABRAS_NO_PRODUCTO
    ]

    if not palabras:
        return []

    def raiz(palabra: str) -> str:
        return palabra[:5] if len(palabra) >= 5 else palabra

    puntajes = []
    for producto in productos:
        palabras_nombre = re.findall(
            r"[a-z]+", normalizar(str(producto.get("nombre", "")))
        )
        coincidencias = {
            p for p in palabras
            for n in palabras_nombre
            if len(n) >= 4 and raiz(p) == raiz(n)
        }
        if coincidencias:
            puntajes.append((len(coincidencias), producto))

    if not puntajes:
        return []

    # Se quedan los que coinciden con MÁS palabras:
    # "aceite de motor" prefiere "Aceite de Motor 5W-30"
    # sobre "Filtro de Aceite".
    mejor = max(puntaje for puntaje, _ in puntajes)
    return [producto for puntaje, producto in puntajes if puntaje == mejor]


def lista_coincidencias(productos: list[dict]) -> str:
    lineas = ["Encontré estos productos:"]
    for p in productos[:10]:
        precio = obtener_precio(p)
        existencia = obtener_existencia(p)
        lineas.append(
            f"• {etiqueta_producto(p)}: "
            f"{dinero(precio) if precio is not None else 'sin precio'} — "
            f"{existencia if existencia is not None else '?'} piezas"
        )
    lineas.append("")
    lineas.append("Dime el código del que te interesa para darte más detalles.")
    return "\n".join(lineas)


_PALABRAS_INVENTARIO = (
    r"\b(?:inventario|producto|productos|refaccion|refacciones|"
    r"existencia|existencias|stock|precio|precios|pieza|piezas|"
    r"codigo|venta|ventas|vender|marca|categoria)\b"
)


def menciona_inventario(pregunta: str) -> bool:
    return re.search(_PALABRAS_INVENTARIO, normalizar(pregunta)) is not None


def productos_recientes(historial, productos: list[dict], mensajes: int = 6) -> list[dict]:
    # Productos mencionados en los últimos mensajes de la conversación,
    # en el orden en que aparecieron y sin repetir.
    vistos: dict[str, dict] = {}
    for mensaje in (historial or [])[-mensajes:]:
        for _, producto in productos_en_texto(mensaje.texto or "", productos):
            vistos.setdefault(str(producto.get("codigo")), producto)
    return list(vistos.values())


# Palabras que no son nombres de refacciones aunque vengan después de
# "¿tienes...?" o "¿hay...?" ("¿tienes tiempo?", "¿hay alguna duda?").
_NO_ES_REFACCION = {
    "algo", "alguna", "alguno", "algun", "tiempo", "idea", "duda", "dudas",
    "pregunta", "problema", "problemas", "otro", "otra", "otros", "otras",
    "mas", "nada", "cosa", "cosas", "opcion", "opciones",
    "llevo", "lleva", "llevar", "llevan", "sale", "par",
}


def respuesta_producto_no_encontrado(pregunta: str) -> str | None:
    # "¿Tienes llantas para tractor?" cuando ningún producto coincide.
    # Responde con reglas en lugar de dejar que el modelo improvise.
    texto = normalizar(pregunta)
    terminos = [
        p for p in re.findall(r"[a-z]+", texto)
        if len(p) >= 4
        and p not in _PALABRAS_NO_PRODUCTO
        and p not in _NO_ES_REFACCION
    ]
    if not terminos or len(terminos) > 4:
        return None
    buscado = " ".join(terminos)
    return (
        f"No encontré «{buscado}» en el inventario de El Pistón. "
        "Si lo conoces con otro nombre o tienes el código, dímelo y lo "
        "reviso. También puedes escribir \"¿qué tenemos en inventario?\" "
        "para ver la lista completa."
    )
