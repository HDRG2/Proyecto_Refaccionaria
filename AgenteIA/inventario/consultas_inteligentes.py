import re
from decimal import Decimal
from difflib import SequenceMatcher

from AgenteIA.inventario.utilidades_inventario import (
    LIMITE_STOCK_BAJO,
    MARCAS_NORMALIZADAS,
    a_decimal,
    codigos_mencionados,
    describir_producto,
    normalizar,
    obtener_existencia,
    obtener_precio,
)
from AgenteIA.inventario.validador_inventario import (
    normalizar_vehiculo,
    analizar_compatibilidad_registrada,
    mismo_modelo,
)
from AgenteIA.inventario.contexto_inventario import (
    obtener_producto_seleccionado,
    describir_vehiculo_contexto,
    detectar_cambio_tema,
    rol_mensaje,
    texto_mensaje,
)


# =====================================================================
# UTILIDADES
# =====================================================================

def normalizar_texto(texto: str) -> str:
    return normalizar(texto)


def dinero(valor) -> str:
    return f"${valor:,.2f} MXN"


def piezas(cantidad: int) -> str:
    return f"{cantidad} {'pieza' if cantidad == 1 else 'piezas'}"


def total_productos(cantidad: int) -> str:
    return f"Total: {cantidad} {'producto' if cantidad == 1 else 'productos'}."


def _menciona_producto_concreto(texto_normal: str, productos: list[dict]) -> bool:
    # True si la pregunta nombra UN producto por código ("BAL-001") o por
    # su nombre completo de 2 o más palabras ("Aceite Mobil 5W30").
    # Esas preguntas las contesta el servidor con ese producto, no con
    # una lista general.
    if codigos_mencionados(texto_normal, productos):
        return True
    for producto in productos:
        nombre = normalizar_texto(producto.get("nombre", ""))
        if len(nombre.split()) >= 2 and re.search(
            r"(?<!\w)" + re.escape(nombre) + r"(?!\w)", texto_normal
        ):
            return True
    return False


def _guardar(contexto, **valores) -> None:
    # Guarda datos en el contexto solo si se recibió uno.
    if contexto is None:
        return
    for nombre, valor in valores.items():
        if hasattr(contexto, nombre) and valor is not None:
            setattr(contexto, nombre, valor)


_PALABRAS_DINERO = (
    r"\b(?:pesos|peso|mxn|precio|precios|cuesten|cuestan|cueste|"
    r"valgan|valen|barato|baratos|baratas|caro|caros|caras|"
    r"presupuesto|dinero)\b|\$"
)


# =====================================================================
# TIPOS DE PRODUCTO (para "el filtro más barato", "balatas para...")
# =====================================================================

TIPOS_PRODUCTO = {
    "amortiguador": ("amortiguador", "amortiguadores"),
    "balata": ("balata", "balatas", "pastilla", "pastillas"),
    "filtro": ("filtro", "filtros"),
    "bujia": ("bujia", "bujias"),
    "aceite": ("aceite", "aceites"),
    "bateria": ("bateria", "baterias", "acumulador"),
    "foco": ("foco", "focos", "faro", "faros"),
    "banda": ("banda", "bandas", "correa", "correas"),
    "disco": ("disco", "discos", "rotor", "rotores"),
    "anticongelante": ("anticongelante", "refrigerante"),
    "radiador": ("radiador", "radiadores"),
    "llanta": ("llanta", "llantas", "neumatico", "neumaticos"),
}


def detectar_tipo(texto: str) -> str | None:
    # Devuelve el tipo que aparece PRIMERO en el texto.
    # "filtro de aceite" -> "filtro" (no "aceite").
    mejor_tipo: str | None = None
    mejor_posicion = len(texto) + 1
    for tipo, variantes in TIPOS_PRODUCTO.items():
        for variante in variantes:
            m = re.search(r"\b" + re.escape(variante) + r"\b", texto)
            if m and m.start() < mejor_posicion:
                mejor_posicion = m.start()
                mejor_tipo = tipo
    return mejor_tipo


def tipo_de_producto(producto: dict) -> str | None:
    # Cada producto tiene UN solo tipo: el primero que aparece en su nombre.
    return detectar_tipo(normalizar_texto(producto.get("nombre", "")))


def producto_es_del_tipo(producto: dict, tipo: str | None) -> bool:
    if tipo is None:
        return True

    propio = tipo_de_producto(producto)
    if propio is not None:
        return propio == tipo

    # El nombre no dice el tipo: se usa la categoría.
    categoria = normalizar_texto(producto.get("categoria", ""))
    return any(
        re.search(r"\b" + re.escape(v) + r"\b", categoria)
        for v in TIPOS_PRODUCTO[tipo]
    )


def detectar_categoria(texto: str, productos: list[dict]) -> str | None:
    # Devuelve la categoría registrada que se menciona ("frenos").
    categorias = sorted({
        str(p.get("categoria", "")).strip()
        for p in productos
        if str(p.get("categoria", "")).strip()
    }, key=len, reverse=True)

    for categoria in categorias:
        normal = normalizar_texto(categoria)
        singular = normal[:-1] if normal.endswith("s") else normal
        for forma in (normal, singular):
            if len(forma) >= 3 and re.search(
                r"(?<!\w)" + re.escape(forma) + r"(?:es|s)?(?!\w)", texto
            ):
                return categoria
    return None


def detectar_marca_producto(texto: str, productos: list[dict]) -> str | None:
    marcas = sorted({
        str(p.get("marca", "")).strip()
        for p in productos
        if str(p.get("marca", "")).strip()
        and normalizar_texto(p.get("marca", "")) not in ("sin marca", "")
    }, key=len, reverse=True)

    for marca in marcas:
        normal = normalizar_texto(marca)
        if len(normal) >= 2 and re.search(
            r"(?<!\w)" + re.escape(normal) + r"(?!\w)", texto
        ):
            return marca
    return None


def filtrar_por_tema(texto: str, productos: list[dict], contexto=None):
    # Filtra por tipo, categoría o marca mencionados.
    # Devuelve (productos_filtrados, descripción_del_filtro).
    # Si se pidió un tipo y no hay productos de ese tipo, devuelve una
    # lista VACÍA (antes devolvía todo el inventario y se contestaba
    # con un producto de otro tipo).
    tipo = detectar_tipo(texto)
    if tipo is not None:
        filtrados = [p for p in productos if producto_es_del_tipo(p, tipo)]
        return filtrados, f"tipo {tipo}"

    categoria = detectar_categoria(texto, productos)
    if categoria is not None:
        filtrados = [
            p for p in productos
            if normalizar_texto(p.get("categoria", "")) == normalizar_texto(categoria)
        ]
        if filtrados:
            _guardar(contexto, categoria_consultada=categoria)
            return filtrados, f"categoría {categoria}"

    marca = detectar_marca_producto(texto, productos)
    if marca is not None:
        filtrados = [
            p for p in productos
            if normalizar_texto(p.get("marca", "")) == normalizar_texto(marca)
        ]
        if filtrados:
            return filtrados, f"marca {marca}"

    return productos, None


# =====================================================================
# BÚSQUEDA POR VEHÍCULO
# =====================================================================

def es_busqueda_inventario_vehiculo(pregunta: str) -> bool:
    # Reconoce preguntas que buscan refacciones del inventario
    # para un vehículo.
    texto = normalizar_texto(pregunta)

    expresiones = (
        "que refacciones", "que productos", "que piezas",
        "que tienes para", "que manejas para", "que tienen para",
        "que hay para", "que tenemos para", "que le queda",
        "que le sirve", "que le quedan", "que le sirven",
        "tienes refacciones", "tienes productos", "tienes piezas",
        "busco refacciones", "busco piezas", "busco algo para",
        "algo para", "que tengas para", "lo que tengas para",
        "muestrame refacciones", "muestrame productos",
        "refacciones para", "productos para", "piezas para",
        "compatibles con", "compatible con", "le queda a",
        "sirve para", "sirven para", "quedan para",
        "para ese carro", "para el mismo carro", "para ese vehiculo",
        "para mi carro", "para el carro",
        # "toyota corolla piezas compatibles de mi inventario"
        "piezas compatibles", "refacciones compatibles",
        "productos compatibles", "partes compatibles",
        "compatibles de mi inventario", "compatibles del inventario",
        "compatibles en el inventario", "que tengo para", "que tengo compatible",
        "que le quede", "que le queden", "que le sirva", "que le sirvan",
    )

    if any(expresion in texto for expresion in expresiones):
        return True

    # "hay algo para un corolla 2016", "pa un versa 2015 que tienes":
    # un vehículo con año + una pregunta de qué hay.
    if re.search(r"\b(?:para|pa|a)\s+(?:un|una|el|la|mi|su|ese|esa)?\s*[a-z][a-z0-9 ]*?(?:19|20)\d{2}\b", texto) \
            and re.search(r"\b(?:tienes|tienen|hay|tengo|tenemos|manejas|manejan|algo|que|cuales)\b", texto):
        return True

    # "¿tienes balatas para un versa 2015?", "¿hay filtros para mi tsuru?"
    if detectar_tipo(texto) is not None and re.search(
        r"\b(?:para|a)\s+(?:un|una|el|la|mi|su|ese|esa)?\s*[a-z]", texto
    ) and re.search(r"\b(?:tienes|tienen|hay|manejas|manejan|tenemos|busco|"
                    r"necesito|ocupo|quiero|que|cuales|venden|vendes)\b", texto):
        return True

    # Forma corta, sin verbo: "balatas para versa 2015",
    # "amortiguadores para mi tsuru del 2010".
    if detectar_tipo(texto) is not None and re.search(
        r"\b(?:para|a)\s+(?:un|una|el|la|mi|su|ese|esa)?\s*[a-z][a-z0-9 ]*?"
        r"(?:del\s+|modelo\s+)?(?:19|20)\d{2}\b",
        texto,
    ):
        return True

    return False


def _modelos_registrados(productos: list[dict]) -> set:
    modelos = set()
    for producto in productos:
        compatibles = producto.get("vehiculosCompatibles", [])
        if not isinstance(compatibles, list):
            continue
        for descripcion in compatibles:
            datos = analizar_compatibilidad_registrada(str(descripcion))
            if datos is not None:
                modelos.add(datos[0])
    return modelos


def _marca_mencionada(texto_vehiculo: str) -> str | None:
    # Marca de vehículo escrita en el texto ya normalizado ("toyota").
    for marca in sorted(MARCAS_NORMALIZADAS, key=len, reverse=True):
        if re.search(r"(?<!\w)" + re.escape(marca) + r"(?!\w)", texto_vehiculo):
            return marca
    return None


def _nombre_tipo(tipo: str | None, plural: bool = True) -> str:
    # "balata" -> "balatas"; None -> "refacciones"
    if tipo is None:
        return "refacciones" if plural else "refacción"
    if not plural:
        return _TIPOS_SINGULAR.get(tipo, tipo)
    return _TIPOS_PLURAL.get(tipo, tipo)


_TIPOS_PLURAL = {
    "amortiguador": "amortiguadores", "balata": "balatas", "filtro": "filtros",
    "bujia": "bujías", "aceite": "aceites", "bateria": "baterías",
    "foco": "focos", "banda": "bandas", "disco": "discos",
    "anticongelante": "anticongelantes", "radiador": "radiadores",
    "llanta": "llantas",
}
_TIPOS_SINGULAR = {"bujia": "bujía", "bateria": "batería"}


def tipo_de_pregunta_anterior(historial, pregunta_actual: str = "") -> str | None:
    # Busca el tipo de refacción de las preguntas anteriores del vendedor.
    # "¿tienes balatas para Versa 2015?" -> "balata"
    # Se detiene si hubo un cambio de tema.
    actual = normalizar_texto(pregunta_actual)
    saltar_actual = True
    revisadas = 0

    for mensaje in reversed(list(historial or [])):
        if rol_mensaje(mensaje) != "user":
            continue
        texto = normalizar_texto(texto_mensaje(mensaje))

        # El historial puede incluir la pregunta actual al final.
        if saltar_actual and texto == actual:
            saltar_actual = False
            continue
        saltar_actual = False

        if detectar_cambio_tema(texto):
            return None

        tipo = detectar_tipo(texto)
        if tipo is not None:
            return tipo

        revisadas += 1
        if revisadas >= 4:
            return None

    return None


def respuesta_anterior_fue_por_vehiculo(historial) -> bool:
    # True si la última respuesta del asistente fue una búsqueda de
    # refacciones por vehículo (las que genera este módulo).
    for mensaje in reversed(list(historial or [])):
        if rol_mensaje(mensaje) == "user":
            continue
        texto = normalizar_texto(texto_mensaje(mensaje))
        return (
            "con compatibilidad registrada para" in texto
            or "compatibilidad registrada en estos modelos" in texto
        )
    return False


def buscar_refacciones_por_vehiculo(
    pregunta: str,
    productos: list[dict],
    contexto=None,
    tipo_anterior: str | None = None,
    viene_de_busqueda_vehiculo: bool = False,
) -> str | None:
    # Busca refacciones compatibles con un vehículo utilizando
    # los registros reales del inventario.
    #
    # "tipo_anterior" es el tipo de la pregunta previa ("balata"), para
    # entender seguimientos como "¿y para Toyota 2018?".
    texto_normal = normalizar_texto(pregunta)

    # Si preguntan por UN producto concreto ("¿el BAL-001 le queda a
    # un Versa?"), lo resuelve la compatibilidad del servidor.
    if _menciona_producto_concreto(texto_normal, productos):
        return None

    # Si la respuesta anterior fue una lista por vehículo y ahora solo
    # cambian el vehículo ("¿y para Toyota 2018?"), se repite la búsqueda
    # aunque haya un producto seleccionado de esa lista.
    sigue_lista_vehiculo = bool(
        viene_de_busqueda_vehiculo
        and tipo_anterior
        and re.search(
            r"^\W*(?:y\s+)?(?:tambien\s+)?(?:que tal\s+)?(?:para|a)\b", texto_normal
        )
    )

    # Si se está viendo UN producto y la pregunta es de compatibilidad
    # sin pedir una lista ("¿es compatible con un Sentra 2016?"),
    # la contesta el servidor con ese producto.
    if (
        not sigue_lista_vehiculo
        and contexto is not None
        and getattr(contexto, "codigo_seleccionado", None)
        and detectar_tipo(texto_normal) is None
        and not re.search(
            r"\b(?:que|cuales|tienes|tienen|hay|busco|refacciones|productos|"
            r"piezas|muestrame|algo|opciones|manejas|manejan)\b",
            texto_normal,
        )
    ):
        return None

    # Seguimiento corto con el vehículo recordado:
    # "¿y amortiguadores?", "¿también balatas?", "¿y filtros para ese carro?"
    seguimiento = (
        contexto is not None
        and getattr(contexto, "modelo_vehiculo", None)
        and detectar_tipo(texto_normal) is not None
        and len(texto_normal.strip(" ¿?¡!.,").split()) <= 6
        and re.search(r"^\W*(?:y|tambien|y tambien|ahora|que tal)\b|\bese (?:carro|vehiculo|coche)\b|"
                      r"\bmismo (?:carro|vehiculo|coche)\b", texto_normal)
    )

    texto = normalizar_vehiculo(pregunta)

    # Seguimiento corto cambiando de vehículo, sin repetir el tipo:
    # "¿y para Toyota 2018?", "¿y para un Sentra?", "también para mi Aveo"
    # Solo si la respuesta anterior fue una búsqueda por vehículo; así
    # "¿y para un Versa?" después de una pregunta de MECÁNICA sobre
    # balatas sigue siendo de mecánica y no se vuelve búsqueda.
    seguimiento_vehiculo = (
        viene_de_busqueda_vehiculo
        and tipo_anterior is not None
        and detectar_tipo(texto_normal) is None
        and len(texto_normal.strip(" ¿?¡!.,").split()) <= 7
        and re.search(
            r"^\W*(?:y\s+)?(?:tambien\s+)?(?:que tal\s+)?(?:para|a)\b", texto_normal
        )
        and (
            re.search(r"\b(?:19|20)\d{2}\b", texto) is not None
            or _marca_mencionada(texto) is not None
            or re.search(r"\b(?:para|a)\s+(?:un|una|el|la|mi|su)\s+[a-z]{3,}", texto_normal)
            is not None
        )
    )

    if (
        not es_busqueda_inventario_vehiculo(pregunta)
        and not seguimiento
        and not seguimiento_vehiculo
    ):
        return None

    # 1. Año (opcional).
    coincidencia_anio = re.search(r"\b((?:19|20)\d{2})\b", texto)
    anio = int(coincidencia_anio.group(1)) if coincidencia_anio else None

    # 2. Modelo registrado mencionado en la pregunta.
    modelos_registrados = _modelos_registrados(productos)

    palabras_texto = re.findall(r"[a-z0-9]+", texto)

    def parecido(a: str, b: str) -> bool:
        # "corrolla" ~ "corolla", "tzuru" ~ "tsuru" (errores de dedo).
        return len(a) >= 4 and len(b) >= 4 and SequenceMatcher(None, a, b).ratio() >= 0.85

    def menciona_modelo(modelo: str) -> bool:
        # Acepta "nissan versa" y también solo "versa".
        formas = [modelo]
        partes = modelo.split()
        if len(partes) > 1:
            formas.append(" ".join(partes[1:]))
        if any(
            len(forma) >= 2
            and re.search(r"(?<!\w)" + re.escape(forma) + r"(?!\w)", texto)
            for forma in formas
        ):
            return True
        # Modelo de una palabra escrito con un error ("corrolla").
        nombre = partes[-1] if partes else ""
        return any(parecido(p, nombre) for p in palabras_texto)

    modelos_detectados = [
        modelo for modelo in modelos_registrados
        if menciona_modelo(modelo)
    ]

    modelo_solicitado = max(modelos_detectados, key=len) if modelos_detectados else None

    # 3. Si no mencionó vehículo, usar el que se recuerda del contexto
    #    ("¿y balatas para ese carro?", "¿y amortiguadores?").
    usa_contexto = False
    marca_en_texto = _marca_mencionada(texto)
    if modelo_solicitado is None and contexto is not None:
        modelo_recordado = getattr(contexto, "modelo_vehiculo", None)
        marca_recordada_normal = normalizar_vehiculo(
            str(getattr(contexto, "marca_vehiculo", None) or "")
        )
        # Si nombró otra marca ("¿y para Toyota?"), no usar el modelo
        # recordado de la marca anterior.
        if marca_en_texto and marca_recordada_normal and marca_en_texto != marca_recordada_normal:
            modelo_recordado = None
        if modelo_recordado:
            marca_recordada = getattr(contexto, "marca_vehiculo", None)
            recordado = normalizar_vehiculo(str(modelo_recordado))
            if marca_recordada:
                marca_normal = normalizar_vehiculo(str(marca_recordada))
                if marca_normal not in recordado.split():
                    recordado = f"{marca_normal} {recordado}"
            # Mismo modelo exacto: "corolla" no toma "corolla cross".
            candidatos = [
                m for m in modelos_registrados
                if mismo_modelo(recordado, m)
            ]
            if candidatos:
                modelo_solicitado = max(candidatos, key=len)
                usa_contexto = True
            if anio is None:
                anio = getattr(contexto, "anio_vehiculo", None)

    tipo_solicitado = detectar_tipo(texto_normal)
    if tipo_solicitado is None and seguimiento_vehiculo:
        tipo_solicitado = tipo_anterior

    # Necesitamos al menos un vehículo (dicho o recordado).
    vehiculo_mencionado = (
        modelo_solicitado is not None
        or anio is not None
        or marca_en_texto is not None
        or re.search(r"\b(?:para|a)\s+(?:un|una|el|la|mi)\s+[a-z]{3,}", texto_normal)
    )
    if not vehiculo_mencionado:
        return None

    universales = [
        p for p in productos
        if p.get("universal") is True and producto_es_del_tipo(p, tipo_solicitado)
    ]

    # 4. Vehículo no registrado: avisar sin decir "no entendí".
    if modelo_solicitado is None:
        vehiculo_texto = describir_vehiculo_contexto(contexto) if contexto else None
        if not vehiculo_texto and marca_en_texto:
            vehiculo_texto = marca_en_texto.title() + (f" {anio}" if anio else "")

        # Solo dijeron la marca ("Toyota 2018"): mostrar qué modelos de
        # esa marca tienen refacciones registradas, para que elijan.
        if marca_en_texto:
            de_la_marca = []
            for producto in productos:
                if producto.get("universal") is True or not producto_es_del_tipo(producto, tipo_solicitado):
                    continue
                compatibles = producto.get("vehiculosCompatibles", [])
                if not isinstance(compatibles, list):
                    continue
                for descripcion in compatibles:
                    datos = analizar_compatibilidad_registrada(str(descripcion))
                    if datos is None:
                        continue
                    modelo, inicio, fin = datos
                    if modelo.split()[0] == marca_en_texto and (anio is None or inicio <= anio <= fin):
                        de_la_marca.append((producto, modelo, inicio, fin))

            if de_la_marca:
                lineas = [
                    f"Para {vehiculo_texto} tengo {_nombre_tipo(tipo_solicitado)} con "
                    "compatibilidad registrada en estos modelos. Dime cuál es el tuyo "
                    "para confirmar:"
                ]
                for producto, modelo, inicio, fin in de_la_marca:
                    lineas.append(
                        f"- {modelo.title()} {inicio}-{fin}: {describir_producto(producto)}"
                    )
                return "\n".join(lineas)

        lineas = [
            f"No tengo {_nombre_tipo(tipo_solicitado)} con compatibilidad registrada para "
            f"{vehiculo_texto or 'ese vehículo'} en el inventario de El Pistón."
        ]
        if universales:
            lineas.append(
                "\nEstos productos están registrados como universales "
                "(verifica las especificaciones antes de instalarlos):"
            )
            for producto in universales:
                lineas.append(f"- {describir_producto(producto)}")
        else:
            lineas.append(
                "Verifica la marca, modelo y año, o consulta al personal "
                "para confirmar opciones."
            )
        return "\n".join(lineas)

    primera = modelo_solicitado.split()[0]
    _guardar(
        contexto,
        marca_vehiculo=primera if primera in MARCAS_NORMALIZADAS else None,
        modelo_vehiculo=modelo_solicitado,
        anio_vehiculo=anio,
    )

    vehiculo = f"{modelo_solicitado.title()}{f' {anio}' if anio else ''}"

    # 5. Buscar productos compatibles.
    encontrados = []

    for producto in productos:
        if not producto_es_del_tipo(producto, tipo_solicitado):
            continue
        if producto.get("universal") is True:
            continue

        compatibles = producto.get("vehiculosCompatibles", [])
        if not isinstance(compatibles, list):
            continue

        for descripcion in compatibles:
            datos = analizar_compatibilidad_registrada(str(descripcion))
            if datos is None:
                continue
            modelo, inicio, fin = datos
            if mismo_modelo(modelo_solicitado, modelo) and (anio is None or inicio <= anio <= fin):
                encontrados.append((producto, inicio, fin))
                break

    # "Balatas con compatibilidad..." / "Refacciones con compatibilidad..."
    encabezado = (
        f"{_nombre_tipo(tipo_solicitado).capitalize()} con compatibilidad "
        f"registrada para {vehiculo}:"
    )
    if usa_contexto:
        encabezado += " (vehículo de la consulta anterior)"

    def renglon(producto: dict, inicio: int, fin: int) -> str:
        existencia = obtener_existencia(producto)
        detalle = f" — {piezas(existencia)}" if existencia is not None else ""
        anios = f" [{inicio}-{fin}]" if anio is None else ""
        return f"- {describir_producto(producto)}{anios}{detalle}"

    if encontrados:
        lineas = [encabezado]
        for producto, inicio, fin in encontrados:
            lineas.append(renglon(producto, inicio, fin))
        lineas.append(f"\nTotal de coincidencias: {len(encontrados)}.")
    else:
        lineas = [
            f"No tengo {_nombre_tipo(tipo_solicitado)} con compatibilidad "
            f"registrada para {vehiculo}."
            + (" (vehículo de la consulta anterior)" if usa_contexto else "")
        ]

        # Si pidieron un tipo y no hay, mostrar qué otras refacciones sí
        # están registradas para ese vehículo (útil para el vendedor).
        if tipo_solicitado is not None:
            otras = []
            for producto in productos:
                if producto.get("universal") is True:
                    continue
                compatibles = producto.get("vehiculosCompatibles", [])
                if not isinstance(compatibles, list):
                    continue
                for descripcion in compatibles:
                    datos = analizar_compatibilidad_registrada(str(descripcion))
                    if datos is None:
                        continue
                    modelo, inicio, fin = datos
                    if mismo_modelo(modelo_solicitado, modelo) and (anio is None or inicio <= anio <= fin):
                        otras.append((producto, inicio, fin))
                        break
            if otras:
                lineas.append(f"\nPara {vehiculo} sí hay registradas estas refacciones:")
                for producto, inicio, fin in otras[:10]:
                    lineas.append(renglon(producto, inicio, fin))

    if universales:
        lineas.append(
            "\nTambién hay productos registrados como universales que "
            "requieren verificar sus especificaciones antes de instalarlos:"
        )
        for producto in universales:
            lineas.append(f"- {describir_producto(producto)}")

    return "\n".join(lineas)


# =====================================================================
# SECCIONES DE CONSULTA
# =====================================================================

def _compatibilidad_general(texto: str, productos: list[dict]) -> str | None:
    pide = re.search(
        r"\b(?:que|cuales)\s+(?:refacciones|productos|piezas)\s+(?:tienen|tiene|"
        r"cuentan con)\s+(?:vehiculos|autos|carros|coches)?\s*"
        r"(?:compatibles|compatibilidad)(?:\s+registrad[ao]s?)?\b",
        texto,
    ) or "con un automovil compatible especifico" in texto

    if not pide:
        return None

    refacciones = []
    for producto in productos:
        compatibles = producto.get("vehiculosCompatibles", [])
        if not isinstance(compatibles, list):
            continue
        validos = [
            str(d) for d in compatibles
            if analizar_compatibilidad_registrada(str(d)) is not None
        ]
        if validos:
            refacciones.append((producto, validos))

    if not refacciones:
        return (
            "Actualmente no hay refacciones con vehículos compatibles "
            "registrados en el inventario de El Pistón."
        )

    lineas = ["Refacciones con vehículos compatibles registrados:", ""]
    for producto, vehiculos in refacciones:
        lineas.append(f"• {describir_producto(producto)}")
        for vehiculo in vehiculos:
            lineas.append(f"  - {vehiculo}")
        lineas.append("")

    total = len(refacciones)
    lineas.append(f"Total: {total} {'refacción' if total == 1 else 'refacciones'}.")
    return "\n".join(lineas)


def _recomendacion_aceite(texto: str) -> str | None:
    if re.search(r"\baceites?\b", texto) is None:
        return None

    pide_recomendacion = any(
        expresion in texto
        for expresion in (
            "recomiendas", "recomendar", "recomiendame", "recomienda",
            "que aceite necesita", "que aceite lleva", "que aceite usa",
            "que aceite le pongo", "que aceite le echo", "cual aceite",
            "que aceite es mejor", "es adecuado", "le sirve el aceite",
            "me sirve el aceite",
        )
    )

    if not pide_recomendacion:
        return None

    return (
        "Para recomendar un aceite necesito verificar las especificaciones "
        "del fabricante para la versión y motorización del vehículo. "
        "No puedo confirmar que un aceite sea adecuado solo porque esté "
        "registrado como universal. Indícame la marca, modelo, año y motor "
        "del automóvil para orientar la consulta."
    )


def _alternativa_mas_barata(texto: str, productos: list[dict], contexto) -> str | None:
    pide = re.search(
        r"\b(?:otra|otro|una|alguna|algun)\s+(?:opcion|alternativa|marca|"
        r"producto|similar)?\s*(?:mas\s+)?(?:barat[oa]|economic[oa])\b"
        r"|\balgo mas (?:barato|economico)\b"
        r"|\b(?:hay|tienes|tienen)\s+(?:algo\s+|otr[oa]\s+)?(?:mas\s+)?barat[oa]\b"
        r"|\bmas barat[oa] que (?:ese|esa|este|esta|el anterior)\b",
        texto,
    )
    if not pide:
        return None

    seleccionado = obtener_producto_seleccionado(contexto, productos) if contexto else None

    if seleccionado is not None:
        precio_actual = obtener_precio(seleccionado)
        if precio_actual is None:
            return (
                f"{describir_producto(seleccionado)} no tiene un precio válido "
                "registrado, así que no puedo compararlo."
            )

        categoria = normalizar_texto(seleccionado.get("categoria", ""))
        tipo = tipo_de_producto(seleccionado)

        # Mismo TIPO (balata con balata). Solo si el producto no tiene
        # tipo reconocible se compara por categoría; así una balata no
        # ofrece un disco como alternativa aunque ambos sean "Frenos".
        def es_alternativa(p: dict) -> bool:
            if tipo is not None:
                return tipo_de_producto(p) == tipo
            return bool(categoria) and normalizar_texto(p.get("categoria", "")) == categoria

        opciones = [
            p for p in productos
            if p is not seleccionado
            and str(p.get("codigo", "")) != str(seleccionado.get("codigo", ""))
            and obtener_precio(p) is not None
            and obtener_precio(p) < precio_actual
            and es_alternativa(p)
        ]
        opciones.sort(key=obtener_precio)

        grupo = f"del mismo tipo ({tipo})" if tipo else "de la misma categoría"

        if not opciones:
            return (
                f"No hay una opción más barata que {describir_producto(seleccionado)} "
                f"({dinero(precio_actual)}) {grupo}."
            )

        lineas = [
            f"Opciones más baratas que {describir_producto(seleccionado)} "
            f"({dinero(precio_actual)}) {grupo}:"
        ]
        for p in opciones[:5]:
            lineas.append(f"- {describir_producto(p)}: {dinero(obtener_precio(p))}")
        lineas.append(
            "Verifica la compatibilidad con el vehículo antes de cambiar de producto."
        )
        return "\n".join(lineas)

    categoria = getattr(contexto, "categoria_consultada", None) if contexto else None
    if categoria:
        opciones = sorted(
            [
                p for p in productos
                if normalizar_texto(p.get("categoria", "")) == normalizar_texto(categoria)
                and obtener_precio(p) is not None
            ],
            key=obtener_precio,
        )
        if opciones:
            lineas = [f"Opciones de la categoría {categoria}, de la más barata a la más cara:"]
            for p in opciones[:5]:
                lineas.append(f"- {describir_producto(p)}: {dinero(obtener_precio(p))}")
            return "\n".join(lineas)

    return (
        "¿Más barata que cuál refacción? Dime su nombre o código "
        "(por ejemplo, BAL-001) y te muestro las opciones más económicas "
        "de la misma categoría."
    )


def _mas_barato_o_caro(texto: str, productos: list[dict], contexto) -> str | None:
    barato = re.search(
        r"\bmas\s+(?:barat[oa]s?|economic[oa]s?)\b|\bmenos\s+(?:car[oa]s?|costos[oa]s?)\b|"
        r"\bmenor precio\b|\bprecio mas bajo\b", texto)
    caro = re.search(
        r"\bmas\s+(?:car[oa]s?|costos[oa]s?)\b|\bmenos\s+(?:barat[oa]s?|economic[oa]s?)\b|"
        r"\bmayor precio\b|\bprecio mas alto\b", texto)

    if not barato and not caro:
        return None

    candidatos, filtro = filtrar_por_tema(texto, productos, contexto)
    del_filtro = f" ({filtro})" if filtro else ""

    if not candidatos:
        return f"No hay productos{del_filtro} en el inventario de El Pistón."

    con_precio = [(p, obtener_precio(p)) for p in candidatos if obtener_precio(p) is not None]

    if not con_precio:
        return f"No hay productos{del_filtro} con precio válido registrado."

    elegir = min if barato else max
    producto, precio = elegir(con_precio, key=lambda e: e[1])

    adjetivo = "más barato" if barato else "más caro"

    return (
        f"El producto {adjetivo}{del_filtro} es "
        f"{describir_producto(producto)}, con un precio de {dinero(precio)}."
    )


def _rango_precio(texto: str, productos: list[dict], contexto) -> str | None:
    if not re.search(_PALABRAS_DINERO, texto):
        return None

    # Acepta 500, 500.50, 1,500 y 1,500.50 (coma = miles, punto = decimales).
    numero = r"\$?\s*(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    minimo = maximo = None

    def leer(valor: str) -> Decimal | None:
        return a_decimal(valor.replace(",", ""))

    m = re.search(r"\bentre\s+" + numero + r"\s*(?:pesos)?\s+y\s+" + numero, texto)
    if m:
        a, b = leer(m.group(1)), leer(m.group(2))
        if a is not None and b is not None:
            minimo, maximo = min(a, b), max(a, b)
    else:
        m = re.search(r"\b(?:menos de|menor(?:es)? a|debajo de|abajo de|hasta|maximo|no mas de)\s+" + numero, texto)
        if m:
            maximo = leer(m.group(1))
        m = re.search(r"\b(?:mas de|mayor(?:es)? a|arriba de|encima de|minimo|desde)\s+" + numero, texto)
        if m:
            minimo = leer(m.group(1))

    if minimo is None and maximo is None:
        return None

    candidatos, filtro = filtrar_por_tema(texto, productos, contexto)

    encontrados = []
    for p in candidatos:
        precio = obtener_precio(p)
        if precio is None:
            continue
        if minimo is not None and precio < minimo:
            continue
        if maximo is not None and precio > maximo:
            continue
        encontrados.append((p, precio))

    if minimo is not None and maximo is not None:
        rango = f"entre ${minimo:,.2f} y ${maximo:,.2f}"
    elif maximo is not None:
        rango = f"de hasta ${maximo:,.2f}"
    else:
        rango = f"de más de ${minimo:,.2f}"

    del_filtro = f" ({filtro})" if filtro else ""

    if not encontrados:
        return f"No hay productos{del_filtro} con precio {rango}."

    encontrados.sort(key=lambda e: e[1])
    lineas = [f"Productos{del_filtro} con precio {rango}:"]
    for p, precio in encontrados:
        lineas.append(f"- {describir_producto(p)}: {dinero(precio)}")
    lineas.append(total_productos(len(encontrados)))
    return "\n".join(lineas)


def _rango_existencia(texto: str, productos: list[dict]) -> str | None:
    # Si habla de dinero, no es un rango de piezas.
    if re.search(_PALABRAS_DINERO, texto):
        return None

    menor = re.search(
        r"\b(?:menos de|menor(?:es)? a|debajo de)\s+(\d+)\s*"
        r"(?:piezas?|unidades?|productos?)?\s*"
        r"(?:en existencia|de existencia|en stock|de stock)?\b",
        texto,
    )
    mayor = re.search(
        r"\b(?:mas de|mayor(?:es)? a|arriba de)\s+(\d+)\s*"
        r"(?:piezas?|unidades?|productos?)?\s*"
        r"(?:en existencia|de existencia|en stock|de stock)?\b",
        texto,
    )

    habla_de_inventario = any(
        palabra in texto
        for palabra in ("producto", "productos", "refaccion", "refacciones",
                        "pieza", "piezas", "unidad", "unidades",
                        "existencia", "stock")
    )

    if not habla_de_inventario or (not menor and not mayor):
        return None

    if menor:
        limite = int(menor.group(1))
        encontrados = [
            (p, obtener_existencia(p)) for p in productos
            if obtener_existencia(p) is not None and 0 <= obtener_existencia(p) < limite
        ]
        encontrados.sort(key=lambda e: e[1])
        descripcion = f"menos de {limite} piezas"
    else:
        limite = int(mayor.group(1))
        encontrados = [
            (p, obtener_existencia(p)) for p in productos
            if obtener_existencia(p) is not None and obtener_existencia(p) > limite
        ]
        encontrados.sort(key=lambda e: e[1], reverse=True)
        descripcion = f"más de {limite} piezas"

    if not encontrados:
        return f"No hay productos registrados con {descripcion} en existencia."

    lineas = [f"Productos con {descripcion} en existencia:"]
    for p, existencia in encontrados:
        lineas.append(f"- {describir_producto(p)}: {piezas(existencia)}.")
    lineas.append(total_productos(len(encontrados)))
    return "\n".join(lineas)


def _con_tema(funcion, texto: str, productos: list[dict]) -> str | None:
    # Aplica la consulta solo a la categoría o marca nombrada, si hay una.
    respuesta_total = funcion(texto, productos)
    if respuesta_total is None:
        return None
    categoria = detectar_categoria(texto, productos)
    marca = None if categoria else detectar_marca_producto(texto, productos)
    if categoria is None and marca is None:
        return respuesta_total
    campo, valor = ("categoria", categoria) if categoria else ("marca", marca)
    del_grupo = [p for p in productos if normalizar_texto(p.get(campo, "")) == normalizar_texto(valor)]
    respuesta = funcion(texto, del_grupo)
    etiqueta = f"de la categoría {valor}" if categoria else f"de la marca {valor}"
    if respuesta is None:
        return None
    if respuesta.startswith("Actualmente no hay"):
        return respuesta.replace("en el inventario de El Pistón", f"{etiqueta} en el inventario")
    primera, _, resto = respuesta.partition("\n")
    return f"{primera.rstrip(':')} {etiqueta}:\n{resto}" if resto else respuesta


def _agotados(texto: str, productos: list[dict]) -> str | None:
    if not re.search(
        r"\bagotad[oa]s?\b|\bsin (?:existencias?|stock|piezas)\b|"
        r"\b(?:existencia|stock) (?:cero|0)\b|\bse acabaron\b",
        texto,
    ):
        return None

    agotados = [p for p in productos if obtener_existencia(p) == 0]

    if not agotados:
        return "Actualmente no hay productos agotados en el inventario de El Pistón."

    lineas = ["Productos agotados:"]
    for p in agotados:
        lineas.append(f"- {describir_producto(p)}: 0 piezas.")
    lineas.append(total_productos(len(agotados)))
    return "\n".join(lineas)


def _stock_bajo(texto: str, productos: list[dict]) -> str | None:
    if not re.search(
        r"\bstock bajo\b|\bbajo stock\b|\bexistencias? bajas?\b|"
        r"\bpocas? (?:existencias?|piezas|unidades|stock)\b|\bpoco stock\b|"
        r"\binventario bajo\b|\bpor agotarse\b|\bse (?:nos )?(?:estan|esta) (?:acabando|terminando)\b|"
        r"\bquedan pocas?\b|\bhay que (?:pedir|surtir|resurtir)\b|\bresurtir\b|\bsurtir\b",
        texto,
    ):
        return None

    bajos = sorted(
        [p for p in productos
         if obtener_existencia(p) is not None
         and 1 <= obtener_existencia(p) <= LIMITE_STOCK_BAJO],
        key=obtener_existencia,
    )

    agotados = [p for p in productos if obtener_existencia(p) == 0]

    if not bajos and not agotados:
        return "Actualmente no hay productos con stock bajo en el inventario de El Pistón."

    lineas = []
    if bajos:
        lineas.append(f"Productos con stock bajo ({LIMITE_STOCK_BAJO} piezas o menos):")
        for p in bajos:
            lineas.append(f"- {describir_producto(p)}: {piezas(obtener_existencia(p))}.")
        lineas.append(total_productos(len(bajos)))
    if agotados:
        if lineas:
            lineas.append("")
        lineas.append("Además están agotados:")
        for p in agotados:
            lineas.append(f"- {describir_producto(p)}")
    return "\n".join(lineas)


def _lista_categorias_o_marcas(texto: str, productos: list[dict]) -> str | None:
    # "categorías", "categorías disponibles", "ver categorías",
    # "¿qué categorías hay?", "marcas que manejas"...
    solo = (
        r"^\W*(?:(?:ver|ensename|muestrame|dame|dime|lista de|las|todas las)\s+)*"
        r"{}(?:\s+(?:disponibles|que hay|que tienes|que tenemos|que manejas|"
        r"que manejamos|registradas|registrados|del inventario|de productos|"
        r"de refacciones))?\W*$"
    )
    pide_categorias = re.search(
        r"\b(?:que|cuales)\s+(?:categorias|tipos de (?:productos|refacciones))\b|"
        r"\bcategorias\s+(?:hay|tienes|tienen|manejan|manejas)\b|\blista de categorias\b",
        texto,
    ) or re.search(solo.format("categorias?"), texto)
    pide_marcas = re.search(
        r"\b(?:que|cuales)\s+marcas\b|\bmarcas\s+(?:hay|tienes|tienen|manejan|manejas)\b|"
        r"\blista de marcas\b",
        texto,
    ) or re.search(solo.format("marcas"), texto)

    if not pide_categorias and not pide_marcas:
        return None

    campo = "categoria" if pide_categorias else "marca"
    conteo: dict[str, int] = {}
    for p in productos:
        valor = str(p.get(campo, "")).strip()
        if valor and normalizar_texto(valor) not in ("sin marca", "sin categoria"):
            conteo[valor] = conteo.get(valor, 0) + 1

    if not conteo:
        return f"No hay {'categorías' if campo == 'categoria' else 'marcas'} registradas."

    titulo = "Categorías" if campo == "categoria" else "Marcas"
    lineas = [f"{titulo} que se manejan en El Pistón:"]
    for valor, cantidad in sorted(conteo.items()):
        lineas.append(f"- {valor}: {cantidad} {'producto' if cantidad == 1 else 'productos'}")
    return "\n".join(lineas)


def _por_categoria_o_marca(texto: str, productos: list[dict], contexto) -> str | None:
    pide = re.search(
        r"\b(?:productos|refacciones|piezas)\s+(?:de|del|en)\b|\bcategoria\b|"
        r"\bmuestrame\b|\bmostrar\b|\bque (?:manejas|manejan|tienes|tienen|tenemos|hay) "
        r"(?:de|del|en)\b|\bmarca\b|\bque (?:refacciones|productos) tenemos (?:de|en)\b",
        texto,
    )
    if not pide:
        return None

    categoria = detectar_categoria(texto, productos)
    if categoria is not None:
        encontrados = [
            p for p in productos
            if normalizar_texto(p.get("categoria", "")) == normalizar_texto(categoria)
        ]
        _guardar(contexto, categoria_consultada=categoria)
        lineas = [f"Productos de la categoría {categoria}:"]
        for p in encontrados:
            precio = obtener_precio(p)
            existencia = obtener_existencia(p)
            detalle = []
            if precio is not None:
                detalle.append(dinero(precio))
            if existencia is not None:
                detalle.append(piezas(existencia))
            lineas.append(
                f"- {describir_producto(p)}"
                + (f": {' — '.join(detalle)}" if detalle else "")
            )
        lineas.append(total_productos(len(encontrados)))
        return "\n".join(lineas)

    marca = detectar_marca_producto(texto, productos)
    if marca is not None:
        encontrados = [
            p for p in productos
            if normalizar_texto(p.get("marca", "")) == normalizar_texto(marca)
        ]
        lineas = [f"Productos de la marca {marca}:"]
        for p in encontrados:
            precio = obtener_precio(p)
            lineas.append(
                f"- {describir_producto(p)}"
                + (f": {dinero(precio)}" if precio is not None else "")
            )
        lineas.append(total_productos(len(encontrados)))
        return "\n".join(lineas)

    return None


# =====================================================================
# FUNCIÓN PRINCIPAL (la llama el servidor)
# =====================================================================

def consultar_inventario_inteligente(
    pregunta: str,
    productos: list[dict],
    contexto=None,
    historial=None,
) -> str | None:
    # Devuelve una respuesta exacta del inventario,
    # o None si la pregunta no es de este tipo.
    #
    texto = normalizar_texto(pregunta)

    # Tipo de la pregunta anterior ("balatas"), para entender
    # seguimientos como "¿y para Toyota 2018?".
    tipo_anterior = tipo_de_pregunta_anterior(historial, pregunta)

    # Si preguntan por UN producto concreto ("¿el BAL-001 está agotado?",
    # "¿el Aceite Mobil 5W30 tiene stock bajo?"), no contestar con una
    # lista general: lo resuelve el servidor con ese producto.
    if _menciona_producto_concreto(texto, productos):
        return None

    for seccion in (
        lambda: _compatibilidad_general(texto, productos),
        lambda: _recomendacion_aceite(texto),
        lambda: buscar_refacciones_por_vehiculo(
            pregunta, productos, contexto, tipo_anterior,
            respuesta_anterior_fue_por_vehiculo(historial),
        ),
        lambda: _alternativa_mas_barata(texto, productos, contexto),
        lambda: _rango_precio(texto, productos, contexto),
        lambda: _mas_barato_o_caro(texto, productos, contexto),
        lambda: _rango_existencia(texto, productos),
        # "¿qué está por agotarse de frenos?": solo esa categoría o marca.
        lambda: _con_tema(_agotados, texto, productos),
        lambda: _con_tema(_stock_bajo, texto, productos),
        lambda: _lista_categorias_o_marcas(texto, productos),
        lambda: _por_categoria_o_marca(texto, productos, contexto),
    ):
        respuesta = seccion()
        if respuesta is not None:
            return respuesta

    # No es una consulta reconocida por este módulo.
    return None











