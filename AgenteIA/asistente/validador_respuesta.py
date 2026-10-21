from dataclasses import dataclass, field
import re

from AgenteIA.asistente.productos import (
    IVA,
    ficha_producto,
    obtener_existencia,
    obtener_precio,
    productos_en_texto,
)


# "$1,234.50", "$ 350", "$350.00"
_MONTO_SIGNO = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)")
# "350 pesos", "1,234.50 MXN"
_MONTO_PESOS = re.compile(
    r"(?<![\w.,$])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*(?:pesos|mxn)\b",
    re.IGNORECASE,
)
# "12 piezas", "1 unidad", "3 pzas"
_CANTIDAD_PIEZAS = re.compile(
    r"(?<![\w.,$])(\d+)\s*(?:piezas?|pzas?|unidades?|unidad)\b", re.IGNORECASE
)
_CODIGO = re.compile(r"(?<![\w-])([A-Za-z]{2,5})-(\d{2,5})(?![\w-])")
# Números sueltos dentro de los textos confiables.
_NUMERO = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")

_TOLERANCIA = 0.011  # un centavo, por redondeos


@dataclass
class ResultadoValidacion:
    valida: bool
    motivos: list[str] = field(default_factory=list)


def _a_numero(texto: str) -> float:
    return float(texto.replace(",", ""))


def _montos_en(texto: str) -> list[float]:
    montos = [_a_numero(m) for m in _MONTO_SIGNO.findall(texto)]
    montos += [_a_numero(m) for m in _MONTO_PESOS.findall(texto)]
    return montos


def textos_de_herramientas(mensajes) -> list[str]:
    # Resultados de las herramientas dentro de resultado.messages de
    # AutoGen (ToolCallExecutionEvent -> lista de FunctionExecutionResult).
    # No se toman los mensajes del propio modelo: no son confiables.
    textos = []
    for mensaje in mensajes or []:
        if "ToolCallExecution" not in type(mensaje).__name__:
            continue
        contenido = getattr(mensaje, "content", None)
        if isinstance(contenido, list):
            for item in contenido:
                textos.append(str(getattr(item, "content", item)))
        elif contenido is not None:
            textos.append(str(contenido))
    return textos


def _valores_permitidos(productos: list[dict], textos_confiables: list[str], pregunta: str):
    montos: set[float] = set()
    cantidades: set[int] = set()

    for producto in productos:
        precio = obtener_precio(producto)
        if precio is not None:
            montos.add(round(precio, 2))
            montos.add(round(precio * (1 + IVA), 2))
            montos.add(round(precio * IVA, 2))
        existencia = obtener_existencia(producto)
        if existencia is not None:
            cantidades.add(existencia)

    for texto in textos_confiables:
        for numero in _NUMERO.findall(texto or ""):
            valor = _a_numero(numero)
            montos.add(round(valor, 2))
            if valor == int(valor):
                cantidades.add(int(valor))

    # De la pregunta solo se aceptan CANTIDADES ("si vendo 3"), no
    # montos: si el vendedor pregunta "¿cuesta $500?", el modelo no
    # debe poder confirmarlo sin que salga del inventario.
    for numero in _NUMERO.findall(pregunta or ""):
        valor = _a_numero(numero)
        if valor == int(valor):
            cantidades.add(int(valor))

    return montos, cantidades


def _monto_permitido(monto: float, permitidos: set[float]) -> bool:
    return any(abs(monto - p) <= _TOLERANCIA for p in permitidos)


def validar_respuesta_inventario(
    respuesta: str,
    productos: list[dict],
    textos_confiables: list[str] | tuple[str, ...] = (),
    pregunta: str = "",
) -> ResultadoValidacion:
    # textos_confiables: resultados de herramientas (ver textos_de_herramientas).
    motivos: list[str] = []
    textos_confiables = list(textos_confiables)
    montos_ok, cantidades_ok = _valores_permitidos(productos, textos_confiables, pregunta)

    # 1. Códigos: solo se revisan los que se parecen a los del inventario
    #    (mismo prefijo, p. ej. "ACE-"), para no confundir "SAE-30" u otros.
    codigos_inventario = {
        str(p.get("codigo", "")).strip().upper() for p in productos if p.get("codigo")
    }
    prefijos = {c.split("-")[0] for c in codigos_inventario if "-" in c}
    for prefijo, numero in _CODIGO.findall(respuesta):
        codigo = f"{prefijo}-{numero}".upper()
        if prefijo.upper() in prefijos and codigo not in codigos_inventario:
            motivos.append(f"código inexistente: {codigo}")

    # 2. Precios y montos.
    for monto in _montos_en(respuesta):
        if not _monto_permitido(round(monto, 2), montos_ok):
            motivos.append(f"monto no verificado: ${monto:,.2f}")

    # 3. Existencias ("quedan 12 piezas").
    for cantidad in _CANTIDAD_PIEZAS.findall(respuesta):
        if int(cantidad) not in cantidades_ok:
            motivos.append(f"cantidad no verificada: {cantidad} piezas")

    return ResultadoValidacion(valida=not motivos, motivos=motivos)


MENSAJE_SIN_VERIFICAR = (
    "No pude verificar los datos de esa consulta en el inventario. "
    "Indícame el nombre o código del producto (por ejemplo ACE-001) "
    "y te doy su información exacta."
)


def respuesta_de_respaldo(pregunta: str, productos: list[dict]) -> str:
    # Lo que se contesta cuando la respuesta del modelo no pasó la
    # validación: la ficha real de los productos mencionados, o pedir
    # el código.
    mencionados = [p for _, p in productos_en_texto(pregunta, productos)]
    if 1 <= len(mencionados) <= 5:
        return "\n\n".join(ficha_producto(p) for p in mencionados)
    return MENSAJE_SIN_VERIFICAR
