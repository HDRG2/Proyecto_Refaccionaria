import re
import unicodedata
from decimal import Decimal, InvalidOperation
from AgenteIA.validador_inventario import (
    normalizar_vehiculo,
    analizar_compatibilidad_registrada,
)

def normalizar_texto(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(
        caracter for caracter in texto
        if not unicodedata.combining(caracter)
    )
    return texto.casefold().strip()


def obtener_precio(producto: dict):
    try:
        precio = Decimal(str(producto.get("precioMXN", "")))
        if not precio.is_finite() or precio < 0:
            return None
        return precio
    except (InvalidOperation, ValueError, TypeError):
        return None


def describir_producto(producto: dict) -> str:
    nombre = producto.get("nombre", "Sin nombre")
    codigo = producto.get("codigo", "Sin código")
    return f"{nombre} ({codigo})"


def es_busqueda_inventario_vehiculo(pregunta: str) -> bool:
    
    #Reconoce preguntas que buscan refacciones del inventario para un vehículo.
    
    texto = normalizar_texto(pregunta)

    expresiones = (
        "que refacciones",
        "que productos",
        "que piezas",
        "que tienes para",
        "que manejas para",
        "tienes refacciones",
        "tienes productos",
        "tienes amortiguadores",
        "tienes balatas",
        "tienes filtros",
        "tienes bujias",
        "busco refacciones",
        "busco piezas",
        "muestrame refacciones",
        "muestrame productos",
    )

    return any(expresion in texto for expresion in expresiones)


def buscar_refacciones_por_vehiculo(
    pregunta: str,
    productos: list[dict]
) -> str | None:
    
    #Busca refacciones compatibles con un vehículo utilizando los registros reales del inventario.
    
    texto = normalizar_vehiculo(pregunta)
    
    if not es_busqueda_inventario_vehiculo(pregunta):
        return None

    # Identificar el año solicitado.
    coincidencia_anio = re.search(
        r"\b((?:19|20)\d{2})\b",
        texto
    )

    if coincidencia_anio is None:
        return None

    anio = int(coincidencia_anio.group(1))

    # Detectar marcas y modelos registrados.
    modelos_registrados = set()

    for producto in productos:
        compatibles = producto.get(
            "vehiculosCompatibles", []
        )

        if not isinstance(compatibles, list):
            continue

        for descripcion in compatibles:
            datos = analizar_compatibilidad_registrada(
                str(descripcion)
            )

            if datos is not None:
                modelos_registrados.add(datos[0])

    # Buscar el modelo más específico mencionado.
    modelos_detectados = [
        modelo
        for modelo in modelos_registrados
        if re.search(
            r"(?<!\w)" + re.escape(modelo) + r"(?!\w)",
            texto
        )
    ]

    if not modelos_detectados:
        return (
            "No pude identificar una marca y modelo "
            "registrados en el inventario de El Pistón. "
            "No puedo confirmar refacciones compatibles "
            "para ese vehículo. Verifica el nombre del "
            "vehículo o consulta al personal."
        )

    modelo_solicitado = max(
        modelos_detectados,
        key=len
    )

    vehiculo = f"{modelo_solicitado.title()} {anio}"
    
        # Detectar si el usuario solicita un tipo específico.
    tipos_producto = {
        "amortiguador": ("amortiguador", "amortiguadores"),
        "balata": ("balata", "balatas"),
        "filtro": ("filtro", "filtros"),
        "bujia": ("bujia", "bujias"),
        "aceite": ("aceite", "aceites"),
    }

    tipo_solicitado = None

    for tipo, variantes in tipos_producto.items():
        if any(
            re.search(r"\b" + re.escape(variante) + r"\b", texto)
            for variante in variantes
        ):
            tipo_solicitado = tipo
            break

    def coincide_tipo(producto):
        if tipo_solicitado is None:
            return True

        nombre = normalizar_vehiculo(
            str(producto.get("nombre", ""))
        )

        return re.search(
            r"\b" + re.escape(tipo_solicitado) + r"\b",
            nombre
        ) is not None or any(
            re.search(r"\b" + re.escape(variante) + r"\b", nombre)
            for variante in tipos_producto[tipo_solicitado]
        )

    encontrados = []
    universales = []

    for producto in productos:
        if not coincide_tipo(producto):
            continue

        if  producto.get("universal") is True:
            universales.append(producto)
            continue

        compatibles = producto.get(
            "vehiculosCompatibles", []
        )

        if not isinstance(compatibles, list):
            continue

        for descripcion in compatibles:
            datos = analizar_compatibilidad_registrada(
                str(descripcion)
            )

            if datos is None:
                continue

            modelo, inicio, fin = datos

            if (
                modelo == modelo_solicitado
                and inicio <= anio <= fin
            ):
                encontrados.append(producto)
                break

    lineas = [
        f"Refacciones con compatibilidad registrada "
        f"para {vehiculo}:"
    ]

    if encontrados:
        for producto in encontrados:
            lineas.append(
                f"- {describir_producto(producto)}"
            )
    else:
        lineas.append(
            "No se encontraron refacciones con "
            "compatibilidad registrada."
        )

    lineas.append(
        f"\nTotal de coincidencias: {len(encontrados)}."
    )

    if universales:
        lineas.append(
            "\nTambién hay productos registrados como "
            "universales que requieren verificar "
            "sus especificaciones antes de instalarlos:"
        )

        for producto in universales:
            lineas.append(
                f"- {describir_producto(producto)}"
            )

    return "\n".join(lineas)


def consultar_inventario_inteligente(
    pregunta: str,
    productos: list[dict]
) -> str | None:

    texto = normalizar_texto(pregunta)
    
    
    # Consultar todas las refacciones con vehículos compatibles registrados.
    consultas_compatibilidad_general = (
        "que refacciones tienen vehiculos compatibles registrados",
        "que productos tienen vehiculos compatibles registrados",
        "que refacciones tienen autos compatibles",
        "que productos tienen autos compatibles",
        "que refacciones tienen compatibilidad registrada",
        "que productos tienen compatibilidad registrada",
        "tienes alguna refaccion registrada en el inventario con un automovil compatible especifico",
    )

    pregunta_limpia = texto.strip(" ¿?¡!.,")

    if pregunta_limpia in consultas_compatibilidad_general:

        refacciones_compatibles = []

        for producto in productos:
            compatibles = producto.get("vehiculosCompatibles", [])

            if not isinstance(compatibles, list):
                continue

            vehiculos_validos = []

            for descripcion in compatibles:
                datos = analizar_compatibilidad_registrada(
                    str(descripcion)
                )

                if datos is not None:
                    vehiculos_validos.append(str(descripcion))

            if vehiculos_validos:
                refacciones_compatibles.append(
                    (producto, vehiculos_validos)
                )

        if not refacciones_compatibles:
            return (
                "Actualmente no hay refacciones con vehículos "
                "compatibles registrados en el inventario de El Pistón."
            )

        lineas = [
            "Refacciones con vehículos compatibles registrados:",
            "",
        ]

        for producto, vehiculos in refacciones_compatibles:
            lineas.append(
                f"• {describir_producto(producto)}"
            )

            for vehiculo in vehiculos:
                lineas.append(f"  - {vehiculo}")

            lineas.append("")

        total = len(refacciones_compatibles)

        lineas.append(
            f"Total: {total} "
            f"{'refacción' if total == 1 else 'refacciones'}."
        )

        return "\n".join(lineas)

    
    # Evitar recomendaciones de aceite sin verificar las especificaciones del vehículo.
    pregunta_aceite = re.search(
        r"\baceites?\b",
        texto
    ) is not None

    solicita_recomendacion = any(
        expresion in texto
        for expresion in (
            "recomiendas",
            "recomendar",
            "recomiendame",
            "que aceite necesita",
            "que aceite lleva",
            "que aceite usa",
            "cual aceite",
            "me sirve",
            "es adecuado",
        )
    )

    if pregunta_aceite and solicita_recomendacion:
        return (
            "Para recomendar un aceite necesito verificar "
            "las especificaciones del fabricante para "
            "la versión y motorización del vehículo. "
            "No puedo confirmar que un aceite sea adecuado "
            "solo porque esté registrado como universal. "
            "Indícame la marca, modelo, año y motor "
            "del automóvil para orientar la consulta."
        )
    
    respuesta_vehiculo = buscar_refacciones_por_vehiculo(
        pregunta,
        productos
    )

    if respuesta_vehiculo is not None:
        return respuesta_vehiculo

    # Las alternativas requieren el contexto de la recomendación.
    # No comparar todo el inventario cuando se pide "otra opción".
    solicita_alternativa = any(
        expresion in texto
        for expresion in (
            "otra opcion mas barata",
            "otra opcion mas economica",
            "otra alternativa mas barata",
            "algo mas barato",
            "una opcion mas barata",
        )
    )

    if solicita_alternativa:
        return (
            "Para buscar una alternativa más económica necesito "
            "conservar el tipo de refacción y el vehículo consultados. "
            "No sería correcto comparar productos de categorías "
            "diferentes. Indícame la refacción, marca, modelo y año "
            "del vehículo para verificar las opciones disponibles."
        )
    
    # 1. Buscar el producto más barato.
    if any(expresion in texto for expresion in (
        "mas barato",
        "mas economico",
        "menor precio",
        "producto mas barato",
        "refaccion mas barata",
    )):
        productos_con_precio = [
            (producto, obtener_precio(producto))
            for producto in productos
        ]

        productos_con_precio = [
            (producto, precio)
            for producto, precio in productos_con_precio
            if precio is not None
        ]

        if not productos_con_precio:
            return "No hay productos con precios válidos registrados."

        producto, precio = min(
            productos_con_precio,
            key=lambda elemento: elemento[1]
        )

        return (
            f"El producto más barato registrado es "
            f"{describir_producto(producto)}, "
            f"con un precio de ${precio:,.2f} MXN."
        )
    
        # Buscar el producto más caro del inventario.
    if any(expresion in texto for expresion in (
        "mas caro",
        "mas cara",
        "mayor precio",
        "precio mas alto",
        "mas costoso",
        "mas costosa",
        "producto mas caro",
        "refaccion mas cara",
    )):
        productos_con_precio = [
            (producto, obtener_precio(producto))
            for producto in productos
        ]

        productos_con_precio = [
            (producto, precio)
            for producto, precio in productos_con_precio
            if precio is not None
        ]

        if not productos_con_precio:
            return "No hay productos con precios válidos registrados."

        producto, precio = max(
            productos_con_precio,
            key=lambda elemento: elemento[1]
        )

        return (
            f"El producto más caro registrado es "
            f"{describir_producto(producto)}, "
            f"con un precio de ${precio:,.2f} MXN."
        )
        
    # Buscar productos con menos de cierta cantidad en existencia.
    coincidencia_stock = re.search(
        r"\b(?:menos de|menor(?:es)? a)\s+(\d+)\s*"
        r"(?:piezas?|unidades?|productos?)?\s*"
        r"(?:en existencia|de existencia|en stock|de stock)?\b",
        texto,
    )

    if coincidencia_stock and any(
        palabra in texto
        for palabra in (
            "producto", "productos", "refaccion", "refacciones",
            "pieza", "piezas", "unidad", "unidades",
            "existencia", "stock",
        )
    ):
        limite = int(coincidencia_stock.group(1))
        encontrados = []

        for producto in productos:
            try:
                existencia = int(producto.get("existencia"))
            except (ValueError, TypeError):
                continue

            if 0 <= existencia < limite:
                encontrados.append((producto, existencia))

        if not encontrados:
            return (
                f"No hay productos registrados con menos de "
                f"{limite} piezas en existencia."
            )

        encontrados.sort(key=lambda elemento: elemento[1])

        lineas = [
            f"Productos con menos de {limite} piezas en existencia:"
        ]

        for producto, existencia in encontrados:
            lineas.append(
                f"- {describir_producto(producto)}: "
                f"{existencia} unidades."
            )

        lineas.append(
            f"Total: {len(encontrados)} productos."
        )

        return "\n".join(lineas)
    
    
    # Buscar productos con más de cierta cantidad en existencia.
    coincidencia_stock_mayor = re.search(
        r"\b(?:mas de|más de|mayor(?:es)? a)\s+(\d+)\s*"
        r"(?:piezas?|unidades?|productos?)?\s*"
        r"(?:en existencia|de existencia|en stock|de stock)?\b",
        texto,
    )

    if coincidencia_stock_mayor and any(
        palabra in texto
        for palabra in (
            "producto", "productos", "refaccion", "refacciones",
            "pieza", "piezas", "unidad", "unidades",
            "existencia", "stock",
        )
    ):
        limite = int(coincidencia_stock_mayor.group(1))
        encontrados = []

        for producto in productos:
            try:
                existencia = int(producto.get("existencia"))
            except (ValueError, TypeError):
                continue

            if existencia > limite:
                encontrados.append((producto, existencia))

        if not encontrados:
            return (
                f"No hay productos registrados con más de "
                f"{limite} piezas en existencia."
            )

        encontrados.sort(
            key=lambda elemento: elemento[1],
            reverse=True,
        )

        lineas = [
            f"Productos con más de {limite} piezas en existencia:"
        ]

        for producto, existencia in encontrados:
            lineas.append(
                f"- {describir_producto(producto)}: "
                f"{existencia} unidades."
            )

        lineas.append(
            f"Total: {len(encontrados)} productos."
        )

        return "\n".join(lineas)


    
    # 2. Buscar productos agotados.
    expresiones_agotados = (
        "agotado",
        "agotados",
        "agotada",
        "agotadas",
        "sin existencia",
        "sin existencias",
        "sin stock",
        "existencia cero",
        "stock cero",
        "stock 0",
    )

    if any(
        expresion in texto
        for expresion in expresiones_agotados
    ):
        agotados = []

        for producto in productos:
            try:
                existencia = int(producto.get("existencia"))
            except (ValueError, TypeError):
                continue

            if existencia == 0:
                agotados.append(producto)

        if not agotados:
            return (
                "Actualmente no hay productos agotados "
                "en el inventario de El Pistón."
            )

        lineas = ["Productos agotados:"]

        for producto in agotados:
            lineas.append(
                f"- {describir_producto(producto)}: "
                "0 unidades."
            )

        lineas.append(
            f"Total: {len(agotados)} productos."
        )

        return "\n".join(lineas)
    
    
    # 3. Buscar productos con stock bajo (1 a 4 unidades).
    expresiones_stock_bajo = (
        "stock bajo",
        "bajo stock",
        "existencia baja",
        "existencias bajas",
        "pocas existencias",
        "pocas piezas",
        "productos con poco stock",
        "refacciones con poco stock",
        "inventario bajo",
    )

    if any(
        expresion in texto
        for expresion in expresiones_stock_bajo
    ):
        productos_bajos = []

        for producto in productos:
            try:
                existencia = int(producto.get("existencia"))
            except (ValueError, TypeError):
                continue

            if 1 <= existencia < 5:
                productos_bajos.append(producto)

        if not productos_bajos:
            return (
                "Actualmente no hay productos con stock bajo "
                "en el inventario de El Pistón."
            )

        lineas = ["Productos con stock bajo:"]

        for producto in productos_bajos:
            existencia = int(producto["existencia"])

            lineas.append(
                f"- {describir_producto(producto)}: "
                f"{existencia} unidades."
            )

        total = len(productos_bajos)
        lineas.append(
            f"Total: {total} {'producto' if total == 1 else 'productos'}."
        )

        return "\n".join(lineas)


    # 4. Buscar productos por categoría.
    categorias = sorted({
        str(producto.get("categoria", "")).strip()
        for producto in productos
        if str(producto.get("categoria", "")).strip()
    }, key=len, reverse=True)
    
    # Categorías conocidas de la refaccionaria.
    categorias_conocidas = (
        "Aceites",
        "Filtros",
        "Frenos",
        "Suspensión",
        "Sistema eléctrico",
        "Enfriamiento",
        "Encendido",
        "Escape",
        "Iluminación",
    )

    # Combinar categorías registradas y conocidas.
    categorias = sorted(
        set(categorias) | set(categorias_conocidas),
        key=len,
        reverse=True,
    )

    consulta_categoria = any(
        expresion in texto for expresion in (
            "productos de ",
            "refacciones de ",
            "categoria ",
            "productos en ",
            "refacciones en ",
            "muestrame ",
            "mostrar ",
            "que manejas de ",
            "que tienes de ",
            "que refacciones tenemos de ",
            "que productos tenemos de ",
            "que refacciones tenemos en ",
            "que productos tenemos en ",
        )
    )

    if consulta_categoria:
        for categoria in categorias:
            categoria_normalizada = normalizar_texto(categoria)

            if re.search(
                r"(?<!\w)" + re.escape(categoria_normalizada) + r"(?!\w)",
                texto
            ):
                encontrados = [
                    producto for producto in productos
                    if normalizar_texto(
                        producto.get("categoria", "")
                    ) == categoria_normalizada
                ]

                lineas = [
                    f"Productos de la categoría {categoria}:"
                ]

                for producto in encontrados:
                    lineas.append(
                        f"- {describir_producto(producto)}"
                    )

                lineas.append(
                    f"Total: {len(encontrados)} productos."
                )

                return "\n".join(lineas)

    # No es una consulta reconocida por este módulo.
    return None
