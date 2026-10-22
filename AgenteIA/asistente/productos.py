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


# "¿Para qué autos sirve?", "¿a qué carros le queda?", "autos compatibles"
PIDE_LISTA_VEHICULOS = (
    r"\b(?:para|a|con|en)\s+(?:que|cuales|cual)\s+(?:autos?|carros?|coches?|"
    r"vehiculos?|modelos?|camionetas?|marcas?)\b|"
    r"\b(?:autos?|carros?|coches?|vehiculos?|modelos?)\s+(?:compatibles|que le quedan|"
    r"que sirven|registrados)\b"
)


def pide_lista_vehiculos(pregunta: str) -> bool:
    return re.search(PIDE_LISTA_VEHICULOS, normalizar(pregunta)) is not None


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
        r"\b(?:compatibles?|compatibilidad|le queda|le sirve|funciona para)\b|"
        # "¿para qué auto funciona el alternador?", "¿a qué carros le queda?"
        + PIDE_LISTA_VEHICULOS
    )

    if re.search(palabras_compatibilidad, texto):
        return "compatibilidad"

    if re.search(palabras_precio, texto):
        return "precio"

    # "¿cuánto el sensor?", "termostato cuánto", "en cuánto la bobina":
    # "cuánto" sin "cuántos/cuántas" ni palabras de existencia es precio.
    # "Cada cuánto", "cuánto dura", "cuánto tiempo" no preguntan precio.
    if re.search(r"\bcuanto\b", texto) and not re.search(palabras_existencia, texto) \
            and not re.search(r"\b(?:quedan|queda|hay|tengo|tenemos)\b", texto) \
            and not re.search(
                r"\bcada cuant[oa]s?\b|\bcuanto (?:dura|duran|tiempo|tarda|tardan|aguanta|"
                r"aguantan|rinde|rinden|kilometraje|km|kilometros|mide|pesa|cabe|lleva de)\b",
                texto,
            ):
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
    mejores = [producto for puntaje, producto in puntajes if puntaje == mejor]

    # En español la pieza es la primera palabra del nombre: "aceite"
    # prefiere "Aceite de Motor" sobre "Filtro de Aceite".
    if len(mejores) > 1:
        def empieza_con_palabra(producto: dict) -> bool:
            primera = re.findall(r"[a-z]+", normalizar(str(producto.get("nombre", ""))))[:1]
            return bool(primera) and any(raiz(p) == raiz(primera[0]) for p in palabras)
        al_inicio = [p for p in mejores if empieza_con_palabra(p)]
        if len(al_inicio) == 1:
            return al_inicio
    return mejores


# ---------------------------------------------------------------------
# Solo el nombre de una pieza: "termostato", "sensor", "bujias del
# inventario", "oxigeno productos", "llantas".
# ---------------------------------------------------------------------

# Palabras que acompañan al nombre sin cambiar lo que se pide.
_RELLENO_PIEZA = {
    "inventario", "productos", "producto", "refaccion", "refacciones",
    "pieza", "piezas", "articulo", "articulos", "del", "de", "en", "el",
    "la", "los", "las", "un", "una", "unos", "unas", "mi", "tu", "y", "o",
    "tienes", "tienen", "tenemos", "tengo", "hay", "manejas", "manejan",
    "manejamos", "busca", "buscame", "buscar", "dame", "dime", "muestrame",
    "ensename", "mostrar", "ver", "quiero", "info", "informacion", "ficha",
    "datos", "detalles", "sobre", "disponible", "disponibles", "existe",
    "existen", "stock", "existencia", "lista", "registrado", "registrados",
    "registrada", "registradas", "que", "si", "alguna", "algun", "alguno",
    "favor", "porfa", "hola", "oye", "busco", "necesito", "ocupo",
    "requiero", "quisiera", "me", "das", "da", "pasas", "pasame",
    "consigues", "vendes", "venden", "vendemos", "tendras", "tienes",
    "mas", "otra", "otro", "otros", "otras", "ese", "esa", "este", "esta",
    "cosas", "cosa", "articulo",
}

# Palabras que describen la pieza ("discos DE FRENO", "balatas
# TRASERAS"): si no hay producto, junto con un tipo conocido se contesta
# "no hay" en lugar de adivinar.
_DESCRIPTORES_PIEZA = {
    "freno", "frenos", "motor", "aire", "aceite", "agua", "gasolina",
    "combustible", "delantero", "delantera", "delanteros", "delanteras",
    "trasero", "trasera", "traseros", "traseras", "izquierdo", "derecho",
    "izquierda", "derecha", "electrico", "electrica", "nuevo", "nueva",
    "original", "originales", "generico", "generica", "direccion",
    "suspension", "transmision", "escape", "clutch", "encendido",
    "distribucion", "tiempo", "accesorios", "oxigeno", "radiador",
}

# Tipos de refacción que se reconocen aunque no haya ninguno en el
# inventario ("llantas" -> "No hay llantas registradas...").
_TIPOS_CONOCIDOS = {
    "llanta", "neumatico", "rin", "mofle", "silenciador", "catalizador",
    "escape", "sensor", "bomba", "manguera", "radiador", "termostato",
    "ventilador", "alternador", "marcha", "bateria", "bujia", "bobina",
    "cable", "fusible", "relevador", "foco", "faro", "calavera", "balata",
    "disco", "tambor", "zapata", "caliper", "amortiguador", "resorte",
    "rotula", "terminal", "buje", "horquilla", "banda", "correa", "cadena",
    "filtro", "aceite", "anticongelante", "refrigerante", "liquido",
    "clutch", "embrague", "inyector", "empaque", "junta", "valvula",
    "piston", "compresor", "condensador", "espejo", "limpiaparabrisas",
    "pluma", "tapete", "polea", "tensor", "soporte", "flecha", "baleros",
    "balero", "cremallera", "carburador", "turbo",
}


def _raiz_pieza(palabra: str) -> str:
    return palabra[:5] if len(palabra) >= 5 else palabra


def busqueda_solo_pieza(pregunta: str, productos: list[dict]):
    # Si el mensaje es SOLO el nombre de una pieza (con palabras de
    # relleno como "del inventario"), devuelve:
    #   ("encontrados", [productos])  si hay productos con ese nombre,
    #   ("sin_productos", "llantas")  si es un tipo de pieza que no hay,
    #   None                          si el mensaje pide otra cosa.
    # Así "termostato" muestra la ficha del inventario y no una
    # explicación de mecánica (el vendedor busca la pieza).
    texto = normalizar(pregunta).strip(" ¿?¡!.,")

    # "busco ACE-001", "pru-009 en inventario": un código con relleno.
    codigos = [
        p for p in productos
        if str(p.get("codigo", "")).strip()
        and re.search(r"(?<![\w-])" + re.escape(normalizar(p["codigo"])) + r"(?![\w-])", texto)
    ]
    if len(codigos) == 1:
        sin_codigo = texto.replace(normalizar(codigos[0]["codigo"]), " ")
        if all(p in _RELLENO_PIEZA for p in re.findall(r"[a-z0-9]+", sin_codigo)):
            return "encontrados", codigos

    palabras = re.findall(r"[a-z0-9]+", texto)
    resto = [p for p in palabras if p not in _RELLENO_PIEZA]

    def palabras_de(producto: dict) -> list[str]:
        return re.findall(r"[a-z0-9]+", normalizar(
            f"{producto.get('nombre', '')} {producto.get('marca', '')}"
        ))

    # Los números solo valen si son parte de un nombre ("5w 30", "12v");
    # un año o una cantidad ("balatas 2015", "3 filtros") es otra consulta.
    numeros_en_nombres = {w for p in productos for w in palabras_de(p) if re.search(r"\d", w)}
    if not resto or len(resto) > 5 or any(
        re.search(r"\d", p) and p not in numeros_en_nombres for p in resto
    ):
        return None

    raices = {_raiz_pieza(p) for p in resto}

    def raices_de(producto: dict) -> set:
        return {
            _raiz_pieza(w) for w in palabras_de(producto)
            if len(w) >= 3 or re.search(r"\d", w)
        }

    # Todas las palabras deben estar en el nombre o la marca del producto.
    encontrados = [p for p in productos if raices <= raices_de(p)]
    if encontrados:
        return "encontrados", encontrados

    # Ninguno: solo se contesta si TODO lo escrito es un tipo de pieza
    # conocido ("llantas", "mofle"); si hay otras palabras, no se adivina.
    tipos = {_raiz_pieza(t) for t in _TIPOS_CONOCIDOS}
    descriptores = {_raiz_pieza(d) for d in _DESCRIPTORES_PIEZA}
    if raices & tipos and raices <= tipos | descriptores:
        return "sin_productos", " ".join(resto)
    return None


def mensaje_pieza_sin_productos(nombre: str) -> str:
    return (
        f"No hay productos de «{nombre}» en el inventario activo de El Pistón. "
        "Si lo conoces con otro nombre o tienes el código, dímelo y lo "
        "reviso. Si es una duda de mecánica, cuéntame el síntoma "
        "(por ejemplo: \"la llanta vibra a alta velocidad\")."
    )


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
    r"codigo|venta|ventas|vender|marca|categoria|"
    # Preguntas de venta: "¿qué le ofrezco a un cliente?"
    r"ofrezco|ofrecer|ofrecerle|ofrezca|ofrecemos|venderle|vendo|"
    r"le doy|le vendo)\b"
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


def normalizar_codigos(pregunta: str, productos: list[dict]) -> str:
    # "MOT 001", "mot001", "MOT_001", "mot - 001" -> "MOT-001".
    for producto in productos:
        codigo = str(producto.get("codigo", "")).strip()
        m = re.fullmatch(r"([A-Za-z]{2,5})-(\d{2,5})", codigo)
        if not m:
            continue
        prefijo, numero = m.groups()
        pregunta = re.sub(
            r"(?<![\w-])" + re.escape(prefijo) + r"[\s_-]*" + re.escape(numero) + r"(?![\w-])",
            codigo,
            pregunta,
            flags=re.IGNORECASE,
        )
    return pregunta


# ---------------------------------------------------------------------
# Códigos que no existen ("MOT 001" cuando no hay un MOT-001 activo)
# ---------------------------------------------------------------------

# Palabras que pueden ir junto al código: "el código MOT-001", "dame el ABC 12".
_RELLENO_CODIGO = (
    r"(?:el|la|del|de|codigo|clave|producto|refaccion|articulo|pieza|info|"
    r"ficha|dame|dime|busca|buscame|muestrame|ensename|que es|cual es|y|"
    r"precio|precio de|existencia de|cuanto cuesta|cuanto vale)"
)

# Palabras cortas que no son prefijo de código ("el 10", "pagina 20").
_NO_PREFIJO = {
    "el", "la", "los", "las", "del", "de", "al", "pag", "num", "no", "nro",
    "item", "top", "mas", "menos", "hay", "son", "unos", "unas", "como",
    "solo", "cada", "por", "con", "sin", "para", "total", "vendi", "vendo",
}


def _prefijos_y_modelos(productos: list[dict]) -> tuple[set, set]:
    prefijos, nombres_vehiculo = set(), set()
    for producto in productos:
        m = re.fullmatch(r"([A-Za-z]{2,5})-\d{2,5}", str(producto.get("codigo", "")).strip())
        if m:
            prefijos.add(m.group(1).casefold())
        compatibles = producto.get("vehiculosCompatibles") or []
        if isinstance(compatibles, list):
            for vehiculo in compatibles:
                nombres_vehiculo.update(re.findall(r"[a-z]+", normalizar(str(vehiculo))))
    return prefijos, nombres_vehiculo


def codigo_no_registrado(pregunta: str, productos: list[dict]) -> str | None:
    # Si el mensaje es SOLO un código ("MOT 001", "mot001", "el código
    # XYZ-12") y ningún producto activo lo tiene, devuelve el código
    # escrito en formato "MOT-001". Si no, None.
    #
    # Se cuida no confundir vehículos ni páginas: "versa 2015",
    # "ram 1500", "página 2" o "el 10" no son códigos.
    from AgenteIA.inventario.utilidades_inventario import MARCAS_CONOCIDAS

    texto = normalizar(pregunta).strip(" ¿?¡!.,")
    m = re.fullmatch(
        rf"(?:{_RELLENO_CODIGO}\s+)*([a-z]{{2,5}})([\s_-]*)(\d{{1,5}})", texto
    )
    if not m:
        return None

    prefijo, separador, numero = m.groups()
    codigo = f"{prefijo.upper()}-{numero}"

    if any(
        str(p.get("codigo", "")).strip().casefold() == codigo.casefold()
        for p in productos
    ):
        return None

    prefijos, nombres_vehiculo = _prefijos_y_modelos(productos)

    if prefijo in _NO_PREFIJO or prefijo in MARCAS_CONOCIDAS or prefijo in nombres_vehiculo:
        return None

    con_guion = "-" in separador or "_" in separador
    pegado = separador == ""
    # "versa 2015": un año separado por espacio no es un código.
    if not con_guion and not pegado and re.fullmatch(r"(?:19|20)\d{2}", numero):
        return None

    # Solo se toma como código si TIENE forma de código: guion o guion
    # bajo, letras y números pegados, un cero al inicio ("001") o un
    # prefijo que ya usan otros productos ("BAL 9").
    if not (con_guion or pegado or numero.startswith("0") or prefijo in prefijos):
        return None
    # Un solo dígito ("BAL 9") solo si el prefijo ya existe o lleva guion.
    if len(numero) == 1 and not (con_guion or prefijo in prefijos):
        return None

    return codigo


def respuesta_codigo_no_registrado(codigo: str, productos: list[dict]) -> str:
    prefijo, numero = codigo.split("-")
    # Solo los del mismo prefijo ("MOT-002" para "MOT-001"); que solo
    # coincida el número ("ACE-001") no le sirve al vendedor.
    parecidos = [
        p for p in productos
        if str(p.get("codigo", "")).upper().startswith(prefijo + "-")
    ]
    texto = (
        f"No hay ningún producto activo con el código {codigo} en el "
        "inventario de El Pistón. Revisa que esté bien escrito; si el "
        "producto se dio de baja, ya no aparece aquí."
    )
    if parecidos:
        texto += "\n\nCódigos parecidos que sí existen:\n" + "\n".join(
            f"• {etiqueta_producto(p)}" for p in parecidos[:6]
        )
    else:
        texto += " También puedes buscarlo por su nombre."
    return texto


def vehiculos_registrados(producto: dict) -> str:
    # Respuesta a "¿para qué autos sirve el alternador?".
    etiqueta = etiqueta_producto(producto)
    compatibles = producto.get("vehiculosCompatibles") or []
    if not isinstance(compatibles, list):
        compatibles = []
    compatibles = [str(v).strip() for v in compatibles if str(v).strip()]

    if producto.get("universal") is True:
        texto = (
            f"{etiqueta} está registrado como universal. Confirma las "
            "especificaciones del vehículo antes de venderlo."
        )
        if compatibles:
            texto += "\nVehículos registrados:\n" + "\n".join(f"• {v}" for v in compatibles)
        return texto

    if not compatibles:
        return (
            f"{etiqueta} no tiene vehículos compatibles registrados en el "
            "inventario. Confirma marca, modelo, año y motor con el cliente y "
            "verifica la especificación antes de venderlo."
        )

    return (
        f"Vehículos compatibles registrados para {etiqueta}:\n"
        + "\n".join(f"• {v}" for v in compatibles)
        + "\n\nConfirma el motor y la versión del vehículo antes de venderlo."
    )


def es_solo_vehiculo(pregunta: str, productos: list[dict] | None = None) -> bool:
    # "nissan", "nissan versa", "versa 2015", "toyota corolla 2014":
    # el vendedor solo escribió un vehículo. Con el inventario también
    # reconoce un modelo registrado solo: "versa", "corolla".
    from AgenteIA.inventario.utilidades_inventario import MARCAS_CONOCIDAS

    texto = normalizar(pregunta).strip(" ¿?¡!.,")
    palabras = re.findall(r"[a-z0-9]+", texto)
    if not palabras or len(palabras) > 5:
        return False
    if productos and len(palabras) <= 3:
        _, modelos = _prefijos_y_modelos(productos)
        modelos -= set(MARCAS_CONOCIDAS)
        resto = [p for p in palabras if p not in modelos and p not in
                 {"un", "una", "el", "la", "mi", "del", "modelo", "para", "de"}
                 and not re.fullmatch(r"(?:19|20)\d{2}", p)]
        if any(p in modelos for p in palabras) and not resto:
            return True
    tiene_marca = any(p in MARCAS_CONOCIDAS for p in palabras)
    tiene_anio = any(re.fullmatch(r"(?:19|20)\d{2}", p) for p in palabras)
    relleno = {"un", "una", "el", "la", "mi", "del", "modelo", "y", "para", "de"}
    otras = [p for p in palabras if p not in MARCAS_CONOCIDAS and p not in relleno
             and not re.fullmatch(r"(?:19|20)\d{2}", p)]
    # Marca y/o año, y como mucho dos palabras más (el modelo).
    return (tiene_marca or (tiene_anio and otras)) and len(otras) <= 2



