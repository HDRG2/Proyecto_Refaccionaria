import re
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


IVA = Decimal("0.16")

# Igual que en el programa (VentaService): stock bajo = 5 piezas o menos.
LIMITE_STOCK_BAJO = 5

CLAVES_PRECIO = ("precioMXN", "precio", "precio_mxn", "Precio", "precioUnitario")
CLAVES_EXISTENCIA = ("existencia", "stock", "Stock", "existencias")

CENTAVOS = Decimal("0.01")


# =====================================================================
# TEXTO
# =====================================================================

def normalizar(valor) -> str:
    # Quita acentos, pasa a minúsculas y une espacios.
    # "  Balatas  Delanteras " -> "balatas delanteras"
    texto = unicodedata.normalize("NFKD", str(valor if valor is not None else ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.casefold().split())


def raiz(palabra: str) -> str:
    # "balatas"/"balata" -> "balat"; "filtros"/"filtro" -> "filtr"
    return palabra[:5] if len(palabra) >= 5 else palabra


def contiene_frase(texto: str, frase: str) -> bool:
    # True si "frase" aparece como palabra(s) completa(s) dentro de "texto".
    return bool(frase) and re.search(
        r"(?<!\w)" + re.escape(frase) + r"(?!\w)", texto
    ) is not None


# Palabras que no aportan a una búsqueda de producto.
PALABRAS_VACIAS = {
    "para", "con", "del", "los", "las", "una", "uno", "unos", "unas",
    "que", "por", "mas", "sin", "como", "este", "esta", "ese", "esa",
    "hay", "tienes", "tienen", "tengo", "quiero", "busco", "necesito",
    "ocupo", "precio", "cuanto", "cuesta", "vale", "dame", "dime",
    "favor", "porfa", "carro", "coche", "auto", "modelo",
}


# =====================================================================
# NÚMEROS
# =====================================================================

def a_decimal(valor) -> Decimal | None:
    # Convierte a Decimal finito. Rechaza bool, texto inválido, NaN e infinito.
    if valor is None or isinstance(valor, bool):
        return None
    try:
        numero = Decimal(str(valor).strip())
    except (InvalidOperation, TypeError, ValueError):
        return None
    return numero if numero.is_finite() else None


def entero_estricto(valor) -> int | None:
    # Acepta 10, 10.0 o "10". Rechaza 10.7, True, "diez", NaN.
    numero = a_decimal(valor)
    if numero is None or numero != numero.to_integral_value():
        return None
    return int(numero)


def redondear(valor: Decimal) -> Decimal:
    # Redondeo comercial a centavos (0.005 -> 0.01).
    return Decimal(valor).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def con_iva(precio: Decimal) -> Decimal:
    return redondear(precio * (1 + IVA))


# =====================================================================
# PRODUCTO
# =====================================================================

def obtener_precio(producto: dict) -> Decimal | None:
    # Precio sin IVA como Decimal, o None si no hay uno válido.
    for clave in CLAVES_PRECIO:
        if clave not in producto:
            continue
        precio = a_decimal(producto.get(clave))
        if precio is not None and precio >= 0:
            return precio
    return None


def obtener_existencia(producto: dict) -> int | None:
    # Existencia en piezas, o None si no hay una válida (negativa,
    # con decimales o texto inválido).
    for clave in CLAVES_EXISTENCIA:
        if clave not in producto:
            continue
        cantidad = entero_estricto(producto.get(clave))
        if cantidad is not None and cantidad >= 0:
            return cantidad
    return None


# Campos con los que un sistema suele marcar un producto dado de baja.
CLAVES_ACTIVO = (
    "activo", "Activo", "habilitado", "Habilitado", "isActive", "IsActive",
    "estado", "Estado", "estatus", "Estatus",
)

# Valores que significan "dado de baja".
_VALORES_INACTIVO = {
    "false", "0", "no", "inactivo", "inactiva", "baja", "de baja",
    "dado de baja", "descontinuado", "descontinuada", "deshabilitado",
    "deshabilitada", "eliminado", "eliminada", "suspendido", "suspendida",
}


def es_activo(producto: dict) -> bool:
    # Si el inventario marca el producto como dado de baja
    # ("activo": false, "estado": "Baja", "habilitado": 0...),
    # el asistente no lo ofrece. Si no trae ningún campo de ese tipo,
    # se considera activo (así funciona igual con inventarios que no lo usan).
    for clave in CLAVES_ACTIVO:
        if clave not in producto:
            continue
        valor = producto.get(clave)
        if valor is None:
            continue
        if isinstance(valor, bool):
            return valor
        if isinstance(valor, (int, float)):
            return valor != 0
        return normalizar(valor) not in _VALORES_INACTIVO
    return True


def describir_producto(producto: dict) -> str:
    nombre = producto.get("nombre") or "Sin nombre"
    codigo = producto.get("codigo") or "Sin código"
    return f"{nombre} ({codigo})"


def mismo_codigo(producto: dict, codigo) -> bool:
    return (
        str(producto.get("codigo", "")).strip().casefold()
        == str(codigo or "").strip().casefold()
        and bool(str(codigo or "").strip())
    )


def codigos_mencionados(texto: str, productos: list[dict]) -> list[dict]:
    # Productos cuyo código aparece en el texto, en orden de aparición.
    encontrados = []
    for producto in productos:
        codigo = str(producto.get("codigo", "")).strip()
        if not codigo:
            continue
        m = re.search(
            rf"(?<![\w-]){re.escape(codigo)}(?![\w-])",
            str(texto or ""),
            re.IGNORECASE,
        )
        if m:
            encontrados.append((m.start(), producto))
    encontrados.sort(key=lambda item: item[0])
    return [producto for _, producto in encontrados]


# =====================================================================
# MARCAS DE VEHÍCULOS
# =====================================================================

# Como las escribe la gente (incluye apodos).
MARCAS_CONOCIDAS = (
    "nissan", "chevrolet", "chevy", "volkswagen", "vw", "toyota",
    "honda", "ford", "mazda", "kia", "hyundai", "dodge", "ram",
    "jeep", "chrysler", "renault", "peugeot", "seat", "suzuki",
    "mitsubishi", "audi", "bmw", "mercedes", "fiat", "gmc", "buick",
    "cadillac", "subaru", "volvo", "mg", "jac", "baic", "chirey",
)

# Ya normalizadas (vw -> volkswagen). "chevy" no está porque en México
# también es un modelo (Chevrolet Chevy).
MARCAS_NORMALIZADAS = frozenset(
    m for m in MARCAS_CONOCIDAS if m not in ("chevy", "vw")
)