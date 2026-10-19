import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation


def cargar_inventario(inventario_json: str) -> list[dict]:
    productos = json.loads(inventario_json)

    if not isinstance(productos, list):
        raise ValueError("El inventario debe ser una lista.")

    if not all(isinstance(p, dict) for p in productos):
        raise ValueError("Cada producto debe ser un objeto JSON.")

    return productos


def buscar_por_codigo(productos: list[dict], codigo: str):
    codigo = codigo.strip().casefold()

    coincidencias = [
        p for p in productos
        if str(p.get("codigo", "")).strip().casefold() == codigo
    ]

    if len(coincidencias) == 1:
        return coincidencias[0]

    return None


def responder_existencia(producto: dict) -> str:
    nombre = producto["nombre"]
    codigo = producto["codigo"]
    cantidad = producto.get("existencia")

    if type(cantidad) is not int or cantidad < 0:
        return "No hay una existencia válida registrada."

    if cantidad == 0:
        return (
            f"El producto {nombre} ({codigo}) "
            "está agotado: 0 unidades disponibles."
        )

    return (
        f"El producto {nombre} ({codigo}) "
        f"tiene {cantidad} unidades disponibles."
    )


def responder_precio(producto: dict) -> str:
    nombre = producto["nombre"]
    codigo = producto["codigo"]

    try:
        precio = Decimal(str(producto["precioMXN"]))
    except (KeyError, InvalidOperation, TypeError):
        return "No hay un precio válido registrado."

    if not precio.is_finite() or precio < 0:
        return "No hay un precio válido registrado."

    return (
        f"El precio de {nombre} ({codigo}) "
        f"es ${precio:,.2f} MXN."
    )


def normalizar_vehiculo(texto: str) -> str:
    """
    Normaliza acentos, mayúsculas y espacios.
    """
    texto = unicodedata.normalize("NFKD", texto)

    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )

    texto = texto.casefold()
    texto = re.sub(r"[^a-z0-9]+", " ", texto)

    return " ".join(texto.split())


def analizar_compatibilidad_registrada(descripcion: str):
    """
    Convierte:
        Toyota Corolla (2014–2019)

    En:
        ("toyota corolla", 2014, 2019)
    """
    patron = (
        r"^\s*(.*?)\s*\(\s*"
        r"(\d{4})\s*[-–—]\s*(\d{4})"
        r"\s*\)\s*$"
    )

    coincidencia = re.match(patron, descripcion)

    if not coincidencia:
        return None

    modelo = normalizar_vehiculo(coincidencia.group(1))
    anio_inicio = int(coincidencia.group(2))
    anio_fin = int(coincidencia.group(3))

    if not modelo or anio_inicio > anio_fin:
        return None

    return modelo, anio_inicio, anio_fin


def responder_compatibilidad(producto: dict, vehiculo: str) -> str:
    """
    Comprueba compatibilidad utilizando únicamente
    los vehículos registrados en el inventario.
    """
    nombre = producto["nombre"]
    codigo = producto["codigo"]

    if producto.get("universal") is True:
        return (
            f"{nombre} ({codigo}) está registrado como universal. "
            "Confirma las especificaciones antes de instalarlo."
        )

    compatibles = producto.get("vehiculosCompatibles", [])

    if not isinstance(compatibles, list):
        return "No hay información válida de compatibilidad."

    vehiculo_normalizado = normalizar_vehiculo(vehiculo)

    coincidencia_anio = re.search(
        r"\b((?:19|20)\d{2})\b",
        vehiculo_normalizado
    )

    if not coincidencia_anio:
        return (
            "Necesito el año del vehículo para comprobar "
            "la compatibilidad. Por ejemplo: Toyota Corolla 2016."
        )

    anio_solicitado = int(coincidencia_anio.group(1))

    modelo_solicitado = normalizar_vehiculo(
        re.sub(
            r"\b(?:19|20)\d{2}\b",
            "",
            vehiculo_normalizado
        )
    )

    if not modelo_solicitado:
        return (
            "Necesito la marca y el modelo del vehículo "
            "para comprobar la compatibilidad."
        )

    rangos_del_modelo = []

    for descripcion in compatibles:
        datos = analizar_compatibilidad_registrada(
            str(descripcion)
        )

        if datos is None:
            continue

        modelo_registrado, inicio, fin = datos

        if modelo_solicitado != modelo_registrado:
            continue

        rangos_del_modelo.append((inicio, fin))

        if inicio <= anio_solicitado <= fin:
            return (
                f"Sí. {nombre} ({codigo}) está registrado "
                f"como compatible con {vehiculo}. "
                f"Rango registrado: {inicio}-{fin}."
            )

    if rangos_del_modelo:
        rangos = ", ".join(
            f"{inicio}-{fin}"
            for inicio, fin in rangos_del_modelo
        )

        return (
            f"No se encontró compatibilidad registrada "
            f"de {nombre} ({codigo}) con {vehiculo}. "
            f"Los rangos registrados para ese modelo son: {rangos}."
        )

    return (
        f"No se encontró compatibilidad registrada "
        f"de {nombre} ({codigo}) con {vehiculo}. "
        "Esto no confirma que sea físicamente incompatible."
    )

