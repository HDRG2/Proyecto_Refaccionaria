import re

from AgenteIA.asistente.productos import (
    dinero,
    etiqueta_producto,
    obtener_existencia,
    obtener_precio,
)
from AgenteIA.asistente.texto import normalizar


def leer_catalogo(catalogo) -> dict:
    """Acepta un dict, un modelo de Pydantic o None. Devuelve listas limpias."""
    if catalogo is None:
        return {"marcas": [], "categorias": [], "autos": []}
    if hasattr(catalogo, "model_dump"):
        catalogo = catalogo.model_dump()
    if not isinstance(catalogo, dict):
        return {"marcas": [], "categorias": [], "autos": []}

    def nombres(clave):
        valores = catalogo.get(clave) or []
        return [str(v).strip() for v in valores if isinstance(v, (str, int)) and str(v).strip()]

    autos = []
    for auto in catalogo.get("autos") or []:
        if not isinstance(auto, dict):
            continue
        marca = str(auto.get("marca") or "").strip()
        modelo = str(auto.get("modelo") or "").strip()
        try:
            inicio = int(auto.get("anio_inicio") or auto.get("anioInicio") or 0)
            fin = int(auto.get("anio_fin") or auto.get("anioFin") or 0)
        except (TypeError, ValueError):
            inicio = fin = 0
        if modelo:
            autos.append({"marca": marca, "modelo": modelo, "inicio": inicio, "fin": fin})

    return {"marcas": nombres("marcas"), "categorias": nombres("categorias"), "autos": autos}


def entradas_para_vocabulario(catalogo: dict) -> list[dict]:
    """Nombres del catálogo con la forma de un producto, para que la
    corrección de errores de dedo también los conozca ("ultra8", "fokus")."""
    entradas = [{"marca": m} for m in catalogo["marcas"]]
    entradas += [{"categoria": c} for c in catalogo["categorias"]]
    entradas += [{"vehiculosCompatibles": [f"{a['marca']} {a['modelo']}"]} for a in catalogo["autos"]]
    return entradas


# Palabras que acompañan al nombre sin cambiar lo que se pide.
_RELLENO = {
    "marca", "marcas", "de", "del", "la", "el", "los", "las", "un", "una",
    "categoria", "categorias", "productos", "producto", "refacciones",
    "piezas", "tienes", "tienen", "hay", "manejas", "manejan", "que",
    "auto", "carro", "coche", "camioneta", "modelo", "para", "mi",
    "inventario", "en", "info", "dame", "dime", "muestrame", "busco",
    "algo", "lo", "todo", "y",
}


def _resto(texto: str) -> tuple[str, int | None]:
    palabras = re.findall(r"[a-z0-9]+", texto)
    anio = next((int(p) for p in palabras if re.fullmatch(r"(?:19|20)\d{2}", p)), None)
    resto = [p for p in palabras if p not in _RELLENO and not re.fullmatch(r"(?:19|20)\d{2}", p)]
    return " ".join(resto), anio


def _lista_productos(titulo: str, grupo: list[dict]) -> str:
    lineas = [titulo]
    for p in grupo:
        precio = obtener_precio(p)
        existencia = obtener_existencia(p)
        detalle = []
        if precio is not None:
            detalle.append(dinero(precio))
        if existencia is not None:
            detalle.append(f"{existencia} {'pieza' if existencia == 1 else 'piezas'}")
        lineas.append(f"• {etiqueta_producto(p)}" + (f": {' — '.join(detalle)}" if detalle else ""))
    lineas.append(f"Total: {len(grupo)} {'producto' if len(grupo) == 1 else 'productos'}.")
    return "\n".join(lineas)


def respuesta_catalogo(pregunta: str, productos: list[dict], catalogo: dict):
    """Si el mensaje es solo una marca, categoría o auto del catálogo,
    devuelve (respuesta, productos mostrados). Si no, (None, [])."""
    texto = normalizar(pregunta).strip(" ¿?¡!.,")
    resto, anio = _resto(texto)
    if not resto or len(resto.split()) > 4:
        return None, []

    # 1. Marca de piezas: "mobil", "ultra 8", "marca bosch".
    # Se compara también sin espacios: "ultra8" = "Ultra 8".
    def clave(t: str) -> str:
        return re.sub(r"[^a-z0-9]", "", normalizar(t))

    marcas = {clave(m): m for m in catalogo["marcas"]}
    marcas.update({clave(p.get("marca", "")): p.get("marca") for p in productos if p.get("marca")})
    if clave(resto) in marcas and anio is None:
        nombre = marcas[clave(resto)]
        grupo = [p for p in productos if clave(p.get("marca", "")) == clave(resto)]
        if grupo:
            return _lista_productos(f"Productos de la marca {nombre}:", grupo), grupo
        return (
            f"La marca {nombre} está registrada, pero todavía no tiene productos "
            "en el inventario activo. Cuando se agregue un producto de esa marca "
            "aparecerá aquí.", []
        )

    # 2. Categoría del catálogo sin productos ("clutch").
    categorias = {clave(c): c for c in catalogo["categorias"]}
    if clave(resto) in categorias and anio is None:
        nombre = categorias[clave(resto)]
        grupo = [p for p in productos if clave(p.get("categoria", "")) == clave(resto)]
        if grupo:
            return _lista_productos(f"Productos de la categoría {nombre}:", grupo), grupo
        return (
            f"La categoría {nombre} está registrada, pero todavía no tiene "
            "productos en el inventario activo.", []
        )

    # 3. Auto: "focus", "ford focus", "focus 2018", "yamaha".
    autos = catalogo["autos"]
    coinciden = [
        a for a in autos
        if clave(resto) in (clave(a["modelo"]), clave(f"{a['marca']} {a['modelo']}"))
    ]
    solo_marca = [] if coinciden else [a for a in autos if clave(resto) == clave(a["marca"])]
    if not coinciden and not solo_marca:
        return None, []

    from AgenteIA.inventario.validador_inventario import (
        analizar_compatibilidad_registrada,
        mismo_modelo,
    )

    def compatibles_con(auto) -> list[dict]:
        buscado = f"{auto['marca']} {auto['modelo']}"
        encontrados = []
        for p in productos:
            for descripcion in p.get("vehiculosCompatibles") or []:
                datos = analizar_compatibilidad_registrada(str(descripcion))
                if datos and mismo_modelo(buscado, datos[0]) and (
                    anio is None or datos[1] <= anio <= datos[2]
                ):
                    encontrados.append(p)
                    break
        return encontrados

    def rango(auto) -> str:
        if auto["inicio"] and auto["fin"]:
            return f" ({auto['inicio']}-{auto['fin']})"
        return ""

    if coinciden:
        auto = coinciden[0]
        nombre = f"{auto['marca']} {auto['modelo']}".strip()
        fuera = anio is not None and auto["inicio"] and not (auto["inicio"] <= anio <= auto["fin"])
        grupo = compatibles_con(auto)
        if grupo:
            titulo = f"Refacciones con compatibilidad registrada para {nombre}{f' {anio}' if anio else ''}:"
            return _lista_productos(titulo, grupo), grupo
        texto_respuesta = (
            f"El {nombre}{rango(auto)} está registrado, pero todavía no hay "
            f"refacciones con compatibilidad registrada para él"
            + (f" en {anio}" if anio else "") + "."
        )
        if fuera:
            texto_respuesta += f" Además, {anio} queda fuera del rango registrado{rango(auto)}."
        return texto_respuesta, []

    # Solo la marca del auto ("yamaha", "ford").
    marca = solo_marca[0]["marca"]
    lineas = [f"Modelos de {marca} registrados:"]
    con_piezas = []
    for auto in solo_marca:
        grupo = compatibles_con(auto)
        con_piezas += [p for p in grupo if p not in con_piezas]
        lineas.append(
            f"• {auto['modelo']}{rango(auto)}: "
            + (f"{len(grupo)} {'refacción compatible' if len(grupo) == 1 else 'refacciones compatibles'}"
               if grupo else "sin refacciones registradas todavía")
        )
    lineas.append("")
    lineas.append("Dime el modelo y el año para ver las refacciones compatibles.")
    return "\n".join(lineas), con_piezas
