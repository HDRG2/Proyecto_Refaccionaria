import json
import re
from typing import Annotated

from AgenteIA.inventario.utilidades_inventario import (
    IVA,
    PALABRAS_VACIAS,
    con_iva,
    entero_estricto,
    es_activo,
    mismo_codigo,
    normalizar as _normalizar,
    obtener_existencia as _existencia,
    obtener_precio,
    raiz as _raiz,
    redondear,
)


MAX_RESULTADOS = 10
MAX_LISTADO = 60
IVA_TEXTO = f"{int(IVA * 100)} %"


# =====================================================================
# UTILIDADES
# =====================================================================

def _dinero(valor):
    # Decimal -> número con 2 decimales para el JSON (o None).
    return float(redondear(valor)) if valor is not None else None


def _resumen(producto: dict, incluir_vehiculos: bool = False) -> dict:
    # Solo los datos útiles, para no saturar al modelo.
    precio = obtener_precio(producto)
    datos = {
        "codigo": producto.get("codigo"),
        "nombre": producto.get("nombre"),
        "marca": producto.get("marca"),
        "categoria": producto.get("categoria"),
        "precio_sin_iva_mxn": _dinero(precio),
        "precio_con_iva_mxn": float(con_iva(precio)) if precio is not None else None,
        "existencia_piezas": _existencia(producto),
        "universal": producto.get("universal"),
    }
    if incluir_vehiculos:
        datos["vehiculos_compatibles"] = producto.get("vehiculosCompatibles", [])
    return datos


def _json(datos: dict) -> str:
    return json.dumps(datos, ensure_ascii=False)


# =====================================================================
# CREACIÓN DE LAS HERRAMIENTAS
# =====================================================================

def crear_herramientas_inventario(inventario_json: str):
    # Devuelve las herramientas listas para AutoGen.
    # El inventario se recibe una vez por consulta (siempre actualizado).
    productos = json.loads(inventario_json or "[]")

    if not isinstance(productos, list):
        raise ValueError("El inventario debe ser una lista JSON.")

    # Los productos dados de baja no se consultan, listan ni venden.
    productos = [p for p in productos if isinstance(p, dict) and es_activo(p)]

    # -----------------------------------------------------------------
    def consultar_producto(
        busqueda: Annotated[str, "Código (ej. BAL-001), nombre, marca o categoría de la refacción"],
    ) -> str:
        """Busca refacciones en el inventario REAL de El Pistón por código,
        nombre, marca o categoría. Devuelve precio sin IVA, precio con IVA,
        existencia en piezas y vehículos compatibles registrados.
        Úsala SIEMPRE antes de decir un precio, una existencia o una
        compatibilidad. Si no encuentra nada, no inventes el producto."""
        print(f"[AUTOGEN] consultar_producto({busqueda!r})", flush=True)

        termino = _normalizar(busqueda)

        if not termino:
            return _json({"error": "Indica el código, nombre, marca o categoría a buscar."})

        # 1. Código o nombre exacto.
        encontrados = [
            p for p in productos
            if termino in (_normalizar(p.get("codigo")), _normalizar(p.get("nombre")))
        ]

        # 2. Código mencionado dentro del texto ("precio del BAL-001").
        if not encontrados:
            encontrados = [
                p for p in productos
                if _normalizar(p.get("codigo"))
                and re.search(r"(?<![\w-])" + re.escape(_normalizar(p.get("codigo"))) + r"(?![\w-])", termino)
            ]

        # 3. Frase completa dentro del nombre.
        if not encontrados:
            encontrados = [
                p for p in productos
                if re.search(r"(?<!\w)" + re.escape(termino) + r"(?!\w)", _normalizar(p.get("nombre")))
            ]

        # 4. Palabras sueltas (acepta plurales): gana el que coincide
        #    con más palabras del nombre, marca o categoría.
        #    Se ignoran palabras como "para", "con", "del", "precio".
        if not encontrados:
            palabras = [
                p for p in re.findall(r"[a-z0-9]+", termino)
                if len(p) >= 3 and p not in PALABRAS_VACIAS
            ]
            puntajes = []
            for producto in productos:
                texto_producto = _normalizar(
                    f"{producto.get('nombre', '')} {producto.get('marca', '')} "
                    f"{producto.get('categoria', '')}"
                )
                raices = {
                    _raiz(w) for w in re.findall(r"[a-z0-9]+", texto_producto)
                    if w not in PALABRAS_VACIAS
                }
                puntos = sum(1 for w in palabras if _raiz(w) in raices)
                if puntos:
                    puntajes.append((puntos, producto))
            if puntajes:
                mejor = max(p for p, _ in puntajes)
                encontrados = [prod for p, prod in puntajes if p == mejor]

        if not encontrados:
            return _json({
                "encontrados": 0,
                "mensaje": (
                    "No se encontró una refacción que coincida con la búsqueda. "
                    "No utilices el precio de otro producto ni inventes datos. "
                    "Pide al vendedor el código o el nombre exacto."
                ),
            })

        resultado = {
            "encontrados": len(encontrados),
            "nota": f"Los precios del inventario no incluyen IVA; el IVA es {IVA_TEXTO}.",
            "productos": [_resumen(p, incluir_vehiculos=True) for p in encontrados[:MAX_RESULTADOS]],
        }
        if len(encontrados) > MAX_RESULTADOS:
            resultado["aviso"] = (
                f"Hay {len(encontrados)} coincidencias; se muestran {MAX_RESULTADOS}. "
                "Pide al vendedor más detalles para precisar."
            )
        return _json(resultado)

    # -----------------------------------------------------------------
    def listar_productos_activos(
        categoria: Annotated[str, "Categoría a filtrar (ej. Frenos). Vacío para todo el inventario"] = "",
    ) -> str:
        """Lista resumida de las refacciones activas del inventario REAL
        (código, nombre, marca, categoría, precio y existencia).
        Úsala cuando pregunten qué productos hay o qué se maneja de una
        categoría. No la uses para saludos ni preguntas de mecánica."""
        print(f"[AUTOGEN] listar_productos_activos({categoria!r})", flush=True)

        lista = productos
        filtro = _normalizar(categoria)

        if filtro:
            raiz_filtro = _raiz(filtro)
            lista = [
                p for p in lista
                if _raiz(_normalizar(p.get("categoria"))) == raiz_filtro
                or (len(filtro) >= 3 and filtro in _normalizar(p.get("categoria")))
            ]

        return _json({
            "total": len(lista),
            "mostrando": min(len(lista), MAX_LISTADO),
            "nota": "Los precios no incluyen IVA.",
            "productos": [_resumen(p) for p in lista[:MAX_LISTADO]],
        })

    # -----------------------------------------------------------------
    def calcular_venta(
        codigo: Annotated[str, "Código exacto del producto, por ejemplo ACE-001"],
        cantidad: Annotated[int, "Número de piezas a vender"],
    ) -> str:
        """Calcula con exactitud el subtotal, el IVA (16 %) y el total de
        vender cierta cantidad de un producto. Úsala SIEMPRE que pidan
        sumar, multiplicar o calcular una venta; no hagas la cuenta tú."""
        print(f"[AUTOGEN] calcular_venta({codigo!r}, {cantidad!r})", flush=True)

        coincidencias = [p for p in productos if mismo_codigo(p, codigo)]

        if not coincidencias:
            return _json({"error": f"No existe un producto con el código {codigo}."})

        if len(coincidencias) > 1:
            return _json({"error": f"El código {codigo} está repetido en el inventario; revisa el registro."})

        producto = coincidencias[0]

        # Rechaza 2.7, True o texto: no se vende "media pieza" en silencio.
        piezas = entero_estricto(cantidad)
        if piezas is None:
            return _json({"error": "La cantidad debe ser un número entero de piezas."})

        if piezas <= 0:
            return _json({"error": "La cantidad debe ser mayor que cero."})

        precio = obtener_precio(producto)
        if precio is None:
            return _json({"error": "El producto no tiene un precio válido registrado."})

        subtotal = redondear(precio * piezas)
        iva = redondear(subtotal * IVA)
        existencia = _existencia(producto)

        resultado = {
            "producto": f"{producto.get('nombre')} ({producto.get('codigo')})",
            "cantidad": piezas,
            "precio_unitario_mxn": _dinero(precio),
            "subtotal_mxn": float(subtotal),
            "iva_mxn": float(iva),
            "total_con_iva_mxn": float(subtotal + iva),
        }

        if existencia is not None and piezas > existencia:
            resultado["aviso"] = (
                f"Solo hay {existencia} piezas en existencia; "
                f"el cálculo es con las {piezas} solicitadas."
            )

        return _json(resultado)

    return consultar_producto, listar_productos_activos, calcular_venta