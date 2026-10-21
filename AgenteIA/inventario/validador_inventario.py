import json
import re
from datetime import date

from AgenteIA.inventario.utilidades_inventario import (
    IVA,
    es_activo,
    LIMITE_STOCK_BAJO,
    MARCAS_NORMALIZADAS,
    con_iva,
    describir_producto,
    mismo_codigo,
    normalizar,
    obtener_existencia,
    obtener_precio,
)


# =====================================================================
# INVENTARIO
# =====================================================================

def cargar_inventario(inventario_json: str) -> list[dict]:
    # Convierte el JSON del programa en una lista de productos.
    # Si algún producto viene mal (no es objeto), se ignora en lugar
    # de tirar toda la consulta.
    if inventario_json is None or not str(inventario_json).strip():
        return []

    productos = json.loads(inventario_json)

    if not isinstance(productos, list):
        raise ValueError("El inventario debe ser una lista.")

    validos = []
    objetos = 0
    for producto in productos:
        if not isinstance(producto, dict):
            continue
        objetos += 1

        # Productos dados de baja: el asistente no los ofrece.
        if not es_activo(producto):
            continue

        # Nombres alternos de campos -> nombres que usa todo el asistente.
        if "precioMXN" not in producto and "precio" in producto:
            producto["precioMXN"] = producto["precio"]
        if "existencia" not in producto and "stock" in producto:
            producto["existencia"] = producto["stock"]

        validos.append(producto)

    # Error solo si nada venía como producto. Si todos están dados de
    # baja, se devuelve una lista vacía (no es un inventario inválido).
    if productos and objetos == 0:
        raise ValueError("Ningún producto del inventario es válido.")

    return validos


def buscar_por_codigo(productos: list[dict], codigo: str):
    # Devuelve el producto solo si el código es único en el inventario.
    coincidencias = [p for p in productos if mismo_codigo(p, codigo)]
    return coincidencias[0] if len(coincidencias) == 1 else None


# Se conservan estos nombres por si otro archivo los importa.
_existencia = obtener_existencia
_precio = obtener_precio
_etiqueta = describir_producto


# =====================================================================
# EXISTENCIA Y PRECIO
# =====================================================================

def responder_existencia(producto: dict) -> str:
    cantidad = obtener_existencia(producto)
    etiqueta = describir_producto(producto)

    if cantidad is None:
        return f"No hay una existencia válida registrada para {etiqueta}."

    if cantidad == 0:
        return f"El producto {etiqueta} está agotado: 0 piezas disponibles."

    texto = (
        f"El producto {etiqueta} tiene {cantidad} "
        f"{'pieza disponible' if cantidad == 1 else 'piezas disponibles'}."
    )

    if cantidad <= LIMITE_STOCK_BAJO:
        texto += " Existencia baja: conviene resurtir."

    return texto


def responder_precio(producto: dict) -> str:
    precio = obtener_precio(producto)
    etiqueta = describir_producto(producto)

    if precio is None:
        return f"No hay un precio válido registrado para {etiqueta}."

    return (
        f"El precio de {etiqueta} es ${precio:,.2f} MXN "
        f"(sin IVA). Con IVA ({int(IVA * 100)}%): ${con_iva(precio):,.2f} MXN."
    )


# =====================================================================
# VEHÍCULOS
# =====================================================================

# Nombres cortos o comunes -> nombre registrado.
# "chevy" se trata aparte (ver _expandir_chevy) porque también es modelo.
_ALIAS_MARCAS = {
    "vw": "volkswagen",
    "mercedes benz": "mercedes",
}

# Palabras que no forman parte del modelo del vehículo.
_PALABRAS_NO_VEHICULO = {
    "un", "una", "el", "la", "los", "las", "mi", "su", "tu", "ese",
    "esa", "este", "esta", "para", "con", "a", "al", "de", "del", "y",
    "o", "modelo", "ano", "anio", "carro", "coche", "auto", "automovil",
    "camioneta", "vehiculo", "le", "queda", "sirve", "es", "si",
    "compatible", "tambien", "version", "en", "que",
}

# Versiones o paquetes que no cambian el modelo para fines de
# compatibilidad ("Versa Sense" = "Versa").
_VERSIONES = {
    "sense", "advance", "exclusive", "platinum", "sport", "drive",
    "lt", "ls", "ltz", "xle", "le", "se", "comfortline", "trendline",
    "highline", "base", "plus", "premium", "limited",
}


def _expandir_chevy(texto: str) -> str:
    # "chevy aveo"  -> "chevrolet aveo"  (chevy usado como marca)
    # "chevy 2008"  -> "chevy 2008"      (Chevy es el modelo)
    # "mi chevy del 2008" -> sin cambio
    palabras = texto.split()
    for i, palabra in enumerate(palabras):
        if palabra != "chevy" or i + 1 >= len(palabras):
            continue
        siguiente = palabras[i + 1]
        if siguiente in _PALABRAS_NO_VEHICULO or siguiente.isdigit():
            continue
        if i > 0 and palabras[i - 1] == "chevrolet":
            # "chevrolet chevy c2": la marca ya está escrita.
            continue
        palabras[i] = "chevrolet"
    return " ".join(palabras)


def normalizar_vehiculo(texto: str) -> str:
    """
    Normaliza acentos, mayúsculas, signos y espacios.
    También unifica nombres comunes de marcas (vw -> volkswagen).
    """
    texto = normalizar(texto)
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    texto = " ".join(texto.split())

    for alias, marca in _ALIAS_MARCAS.items():
        texto = re.sub(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", marca, texto)

    return _expandir_chevy(texto)


def _anio_valido(anio: int) -> bool:
    return 1950 <= anio <= date.today().year + 2


def analizar_compatibilidad_registrada(descripcion: str):
    """
    Convierte:
        Toyota Corolla (2014–2019)     -> ("toyota corolla", 2014, 2019)
        Toyota Corolla 2014-2019       -> ("toyota corolla", 2014, 2019)
        Toyota Corolla (2020-presente) -> ("toyota corolla", 2020, año actual)
        Toyota Corolla 2020+           -> ("toyota corolla", 2020, año actual)
        Toyota Corolla (2016)          -> ("toyota corolla", 2016, 2016)
        Toyota Corolla 2016            -> ("toyota corolla", 2016, 2016)
    Devuelve None si no tiene un formato reconocible.
    """
    texto = str(descripcion or "").strip()
    actual = date.today().year
    abierto = r"(?:presente|actual|hoy|a la fecha|en adelante)"

    patrones = (
        # (2012-2019) / (2012 a 2019)
        (r"^\s*(.*?)\s*\(\s*(\d{4})\s*(?:[-–—]|a)\s*(\d{4})\s*\)\s*$", "rango"),
        # 2012-2019
        (r"^\s*(.*?)\s+(\d{4})\s*(?:[-–—]|a)\s*(\d{4})\s*$", "rango"),
        # (2020-presente) / 2020 en adelante / 2020+
        (r"^\s*(.*?)\s*\(?\s*(\d{4})\s*(?:(?:[-–—]|a)?\s*" + abierto + r"|\+)\s*\)?\s*$", "abierto"),
        # (2015)
        (r"^\s*(.*?)\s*\(\s*(\d{4})\s*\)\s*$", "uno"),
        # 2015
        (r"^\s*(.*?)\s+(\d{4})\s*$", "uno"),
    )

    for patron, forma in patrones:
        coincidencia = re.match(patron, texto, re.IGNORECASE)
        if not coincidencia:
            continue

        modelo = normalizar_vehiculo(coincidencia.group(1))
        anio_inicio = int(coincidencia.group(2))

        if forma == "rango":
            anio_fin = int(coincidencia.group(3))
        elif forma == "abierto":
            anio_fin = actual
        else:
            anio_fin = anio_inicio

        if (
            not modelo
            or anio_inicio > anio_fin
            or not _anio_valido(anio_inicio)
            or not _anio_valido(anio_fin)
        ):
            return None

        return modelo, anio_inicio, anio_fin

    return None


def _limpiar_modelo(texto_normalizado: str) -> str:
    # "un versa" -> "versa"; "mi nissan versa" -> "nissan versa"
    palabras = [
        p for p in texto_normalizado.split()
        if p not in _PALABRAS_NO_VEHICULO
    ]
    return " ".join(palabras)


def _separar_marca(modelo: str) -> tuple[str | None, str]:
    # "nissan versa sense" -> ("nissan", "versa")
    # "versa"              -> (None, "versa")
    palabras = [p for p in modelo.split() if p not in _VERSIONES]
    if len(palabras) > 1 and palabras[0] in MARCAS_NORMALIZADAS:
        return palabras[0], " ".join(palabras[1:])
    return None, " ".join(palabras)


def mismo_modelo(solicitado: str, registrado: str) -> bool:
    # Compara modelos aceptando que falte la marca o la versión:
    #   "versa"          ~ "nissan versa"         -> True
    #   "versa sense"    ~ "nissan versa"         -> True (versión)
    #   "nissan versa"   ~ "versa"                -> True
    #   "corolla"        ~ "toyota corolla cross" -> False (otro modelo)
    #   "corolla cross"  ~ "toyota corolla"       -> False (otro modelo)
    #   "toyota versa"   ~ "nissan versa"         -> False (otra marca)
    #   "nissan"         ~ "nissan versa"         -> False (falta el modelo)
    if not solicitado or not registrado:
        return False

    marca_sol, modelo_sol = _separar_marca(normalizar_vehiculo(solicitado))
    marca_reg, modelo_reg = _separar_marca(normalizar_vehiculo(registrado))

    if not modelo_sol or not modelo_reg:
        return False

    # Solo dijeron la marca: no alcanza para confirmar.
    if modelo_sol in MARCAS_NORMALIZADAS and marca_sol is None:
        return False

    if marca_sol and marca_reg and marca_sol != marca_reg:
        return False

    return modelo_sol == modelo_reg


# Nombre anterior, por compatibilidad.
_mismo_modelo = mismo_modelo


def responder_compatibilidad(producto: dict, vehiculo: str) -> str:
    """
    Comprueba compatibilidad utilizando únicamente
    los vehículos registrados en el inventario.
    """
    etiqueta = describir_producto(producto)

    if producto.get("universal") is True:
        return (
            f"{etiqueta} está registrado como universal. "
            "Confirma las especificaciones antes de instalarlo."
        )

    compatibles = producto.get("vehiculosCompatibles", [])

    if not isinstance(compatibles, list):
        return f"No hay información válida de compatibilidad para {etiqueta}."

    vehiculo_normalizado = normalizar_vehiculo(vehiculo)

    coincidencia_anio = re.search(r"\b((?:19|20)\d{2})\b", vehiculo_normalizado)
    anio_solicitado = int(coincidencia_anio.group(1)) if coincidencia_anio else None

    modelo_solicitado = _limpiar_modelo(
        re.sub(r"\b(?:19|20)\d{2}\b", " ", vehiculo_normalizado)
    )

    if not modelo_solicitado or modelo_solicitado in MARCAS_NORMALIZADAS:
        return (
            "Necesito la marca y el modelo del vehículo para comprobar "
            "la compatibilidad. Por ejemplo: Nissan Versa 2015."
        )

    # Vehículo limpio para mostrar: "para un versa 2018" -> "Versa 2018".
    vehiculo_texto = modelo_solicitado.title() + (f" {anio_solicitado}" if anio_solicitado else "")
    rangos_del_modelo = []

    def rango(inicio: int, fin: int) -> str:
        return str(inicio) if inicio == fin else f"{inicio}-{fin}"

    for descripcion in compatibles:
        datos = analizar_compatibilidad_registrada(str(descripcion))

        if datos is None:
            continue

        modelo_registrado, inicio, fin = datos

        if not mismo_modelo(modelo_solicitado, modelo_registrado):
            continue

        rangos_del_modelo.append((modelo_registrado, inicio, fin))

        if anio_solicitado is not None and inicio <= anio_solicitado <= fin:
            return (
                f"Sí. {etiqueta} está registrado como compatible con "
                f"{vehiculo_texto}. Rango registrado: "
                f"{modelo_registrado.title()} {rango(inicio, fin)}."
            )

    # Modelo registrado pero sin año: mostrar los rangos.
    if rangos_del_modelo and anio_solicitado is None:
        rangos = ", ".join(f"{m.title()} {rango(i, f)}" for m, i, f in rangos_del_modelo)
        return (
            f"{etiqueta} tiene compatibilidad registrada con: {rangos}. "
            "Dime el año del vehículo para confirmarlo."
        )

    if rangos_del_modelo:
        rangos = ", ".join(rango(i, f) for _, i, f in rangos_del_modelo)
        return (
            f"No se encontró compatibilidad registrada de {etiqueta} con "
            f"{vehiculo_texto}. Los rangos registrados para ese modelo son: "
            f"{rangos}."
        )

    return (
        f"No se encontró compatibilidad registrada de {etiqueta} con "
        f"{vehiculo_texto}. Esto no confirma que sea físicamente incompatible; "
        "verifica las especificaciones o consulta al personal."
    )


