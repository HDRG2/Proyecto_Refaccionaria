import ast
import operator
import re

from AgenteIA.asistente.productos import (
    IVA,
    buscar_por_palabra,
    dinero,
    etiqueta_producto,
    identificar_producto,
    obtener_existencia,
    obtener_precio,
    productos_en_texto,
    productos_recientes,
    ultimo_mensaje_asistente,
)
from AgenteIA.asistente.texto import normalizar
from AgenteIA.inventario.contexto_inventario import (
    obtener_producto_seleccionado,
    resolver_posicion_lista,
)


_UNIDADES = {
    "cero": 0, "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3,
    "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
    "diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14,
    "quince": 15, "dieciseis": 16, "diecisiete": 17, "dieciocho": 18,
    "diecinueve": 19, "veinte": 20, "veintiun": 21, "veintiuno": 21,
    "veintiuna": 21, "veintidos": 22, "veintitres": 23,
    "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26,
    "veintisiete": 27, "veintiocho": 28, "veintinueve": 29,
}
_DECENAS = {
    "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60,
    "setenta": 70, "ochenta": 80, "noventa": 90,
}
_CENTENAS = {
    "cien": 100, "ciento": 100, "doscientos": 200, "doscientas": 200,
    "trescientos": 300, "trescientas": 300, "cuatrocientos": 400,
    "cuatrocientas": 400, "quinientos": 500, "quinientas": 500,
    "seiscientos": 600, "seiscientas": 600, "setecientos": 700,
    "setecientas": 700, "ochocientos": 800, "ochocientas": 800,
    "novecientos": 900, "novecientas": 900,
}
_VALOR_PALABRA = {**_UNIDADES, **_DECENAS, **_CENTENAS, "mil": 1000}

# "un", "uno" y "una" solos no son números ("dame uno", "una pregunta");
# solo cuentan dentro de un número compuesto ("treinta y uno", "un mil").
_SOLO_EN_COMPUESTO = {"un", "uno", "una"}


def _convertir_numeros_compuestos(texto: str) -> str:
    # "dos mil quinientos" -> "2500", "ciento veinte" -> "120",
    # "treinta y cinco" -> "35". Antes se convertían palabra por palabra
    # ("2 1000 500") y el cálculo salía mal.
    # Palabras y separadores por separado: "quinientos?" -> "quinientos", "?".
    tokens = re.findall(r"\w+|\W+", texto)
    salida: list[str] = []
    i = 0

    def siguiente_palabra(k: int) -> int | None:
        # Índice de la siguiente palabra si entre medio solo hay espacios.
        if k < len(tokens) and tokens[k].isspace():
            k += 1
        if k < len(tokens) and not tokens[k].isspace() and re.match(r"\w", tokens[k]):
            return k
        return None

    while i < len(tokens):
        if tokens[i] not in _VALOR_PALABRA:
            salida.append(tokens[i])
            i += 1
            continue

        # Juntar la secuencia de palabras numéricas.
        palabras = [tokens[i]]
        fin = i + 1
        while True:
            k = siguiente_palabra(fin)
            if k is None:
                break
            if tokens[k] in _VALOR_PALABRA:
                palabras.append(tokens[k])
                fin = k + 1
                continue
            # "treinta y cinco": la "y" solo une decenas con unidades.
            k2 = siguiente_palabra(k + 1) if tokens[k] == "y" else None
            if (
                k2 is not None
                and palabras[-1] in _DECENAS
                and tokens[k2] in _UNIDADES
                and 1 <= _UNIDADES[tokens[k2]] <= 9
            ):
                palabras.append(tokens[k2])
                fin = k2 + 1
                continue
            break

        if len(palabras) == 1 and palabras[0] in _SOLO_EN_COMPUESTO:
            salida.append(tokens[i])
            i += 1
            continue

        total = 0
        actual = 0
        for palabra in palabras:
            if palabra == "mil":
                total += (actual or 1) * 1000
                actual = 0
            else:
                actual += _VALOR_PALABRA[palabra]
        salida.append(str(total + actual))
        i = fin

    return "".join(salida)


def _palabras_a_numeros(texto: str) -> str:
    texto = re.sub(r"\bmedia docena\b", "6", texto)
    texto = re.sub(r"\buna docena\b|\bdocena\b", "12", texto)
    texto = re.sub(r"\bun par\b", "2", texto)
    texto = re.sub(r"\b(?:una|un) (pieza|unidad|caja)\b", r"1 \1", texto)
    return _convertir_numeros_compuestos(texto)


def _numero(texto: str) -> float:
    # "1,500" -> 1500 (miles), "1,5" -> 1.5 (decimal), igual que en
    # la expresión general de _resultado_aritmetico.
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", texto):
        return float(texto.replace(",", ""))
    return float(texto.replace(",", "."))


_OPERADORES_AST = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def _evaluar_nodo(nodo):
    if isinstance(nodo, ast.Expression):
        return _evaluar_nodo(nodo.body)
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, (int, float)):
        return float(nodo.value)
    if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, (ast.USub, ast.UAdd)):
        valor = _evaluar_nodo(nodo.operand)
        return -valor if isinstance(nodo.op, ast.USub) else valor
    if isinstance(nodo, ast.BinOp) and type(nodo.op) in _OPERADORES_AST:
        izquierda = _evaluar_nodo(nodo.left)
        derecha = _evaluar_nodo(nodo.right)
        if isinstance(nodo.op, ast.Div) and derecha == 0:
            raise ZeroDivisionError
        resultado = _OPERADORES_AST[type(nodo.op)](izquierda, derecha)
        if abs(resultado) > 1e12:
            raise OverflowError
        return resultado
    raise ValueError("Expresión no permitida")


def evaluar_expresion(expresion: str) -> float | None:
    # Evalúa solo números y + - * / ( ). Nunca usa eval().
    if len(expresion) > 120:
        return None
    try:
        arbol = ast.parse(expresion, mode="eval")
        return _evaluar_nodo(arbol)
    except ZeroDivisionError:
        raise
    except Exception:
        return None


def _formato_numero(valor: float) -> str:
    if abs(valor - round(valor)) < 1e-9:
        return f"{int(round(valor)):,}"
    return f"{valor:,.2f}"


_DISPARADORES_CALCULO = (
    r"\b(?:suma|sumale|sumalo|sumala|sumalos|sumalas|sumame|sumar|"
    r"sumando|multiplica|multiplicalo|multiplicala|multiplicar|"
    r"resta|restale|restalo|restar|divide|dividelo|dividir|calcula|"
    r"calculame|calcular|cuanto seria|cuanto serian|cuanto saldria|"
    r"cuanto daria|cuanto da|cuanto me da|cuanto saco|cuanto sacaria|"
    r"cuanto gano|cuanto ganaria|cuanto junto|cuanto juntaria|"
    r"cuanto es|cuanto son|cuanta lana|cuanto dinero|cuanto varo|"
    r"cuanta feria|lana|varo|feria|vendo|vendiera|vendemos|vendieramos|"
    r"vender|venderlo|venderla|venderlos|venderlas|vendiendo|vendidos|vendidas|"
    r"gano|ganaria|ganancia|"
    r"iva|descuento|porciento|por ciento|mitad|"
    r"llevo|me llevo|lleve|llevara|se lleva|se llevan|un par|rebaja|"
    r"doble|triple|en total|total)\b"
)


_PRONOMBRES_PRODUCTO = (
    r"\b(?:lo|la|los|las|ese|esa|esos|esas|eso|este|esta|esto|"
    r"producto|productos|pieza|piezas|unidades|todo|todos|todas|"
    r"ambos|ambas|juntos|anterior|ultimo)\b"
)


def _resultado_aritmetico(texto: str) -> str | None:
    # Operaciones con números escritos por el usuario,
    # por ejemplo "cuánto es 150 por 4" o "suma 100 y 250".
    t = _palabras_a_numeros(texto)

    # Porcentajes: "16% de 500", "16 por ciento de 500"
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:%|por ciento|porciento)\s*de\s*(\d+(?:[.,]\d+)?)", t)
    if m:
        porcentaje = _numero(m.group(1))
        base = _numero(m.group(2))
        resultado = base * porcentaje / 100
        return (
            f"El {_formato_numero(porcentaje)}% de {_formato_numero(base)} "
            f"es {_formato_numero(resultado)}."
        )

    numeros = [_numero(n) for n in re.findall(r"\d+(?:[.,]\d+)?", t)]

    if len(numeros) < 2:
        return None

    # "suma 100, 200 y 300" -> suma de todos
    if re.search(r"\b(?:suma|sumale|sumame|sumar|total)\b", t) and not re.search(r"[*/x×÷]|\bpor\b|\bentre\b|\bmenos\b", t):
        resultado = sum(numeros)
        return (
            f"{' + '.join(_formato_numero(n) for n in numeros)} = "
            f"{_formato_numero(resultado)}"
        )

    # "multiplica 3 por 4 por 5" -> producto de todos
    if re.search(r"\b(?:multiplica|multiplicar)\b", t) and not re.search(r"\bmas\b|\bmenos\b|[+\-]", t):
        resultado = 1.0
        for n in numeros:
            resultado *= n
        return (
            f"{' × '.join(_formato_numero(n) for n in numeros)} = "
            f"{_formato_numero(resultado)}"
        )

    # "resta 50 a 200" / "resta 50 de 200" -> 200 - 50
    m = re.search(r"\b(?:resta|restale|restar)\s+(\d+(?:[.,]\d+)?)\s+(?:a|de)\s+(\d+(?:[.,]\d+)?)", t)
    if m:
        a, b = _numero(m.group(2)), _numero(m.group(1))
        return f"{_formato_numero(a)} − {_formato_numero(b)} = {_formato_numero(a - b)}"

    # "divide 100 entre 4"
    m = re.search(r"\b(?:divide|dividir)\s+(\d+(?:[.,]\d+)?)\s+(?:entre|por|/)\s+(\d+(?:[.,]\d+)?)", t)
    if m:
        a, b = _numero(m.group(1)), _numero(m.group(2))
        if b == 0:
            return "No se puede dividir entre cero."
        return f"{_formato_numero(a)} ÷ {_formato_numero(b)} = {_formato_numero(a / b)}"

    # Expresión general: "150 por 4 mas 20", "(100+50)*2"
    expresion = t
    expresion = re.sub(r"\bdividido entre\b|\bentre\b|÷", "/", expresion)
    expresion = re.sub(r"\bmultiplicado por\b|\bpor\b|×|(?<=\d)\s*x\s*(?=\d)", "*", expresion)
    expresion = re.sub(r"\bmas\b", "+", expresion)
    expresion = re.sub(r"\bmenos\b", "-", expresion)
    expresion = re.sub(r"(?<=\d),(?=\d{3}\b)", "", expresion)
    expresion = re.sub(r"(?<=\d),(?=\d)", ".", expresion)
    expresion = "".join(re.findall(r"[\d.+\-*/() ]", expresion))
    expresion = " ".join(expresion.split())

    if not re.search(r"\d\s*[+\-*/]\s*[\d(]", expresion):
        return None

    try:
        resultado = evaluar_expresion(expresion)
    except ZeroDivisionError:
        return "No se puede dividir entre cero."

    if resultado is None:
        return None

    return f"{expresion.replace('*', '×').replace('/', '÷')} = {_formato_numero(resultado)}"


def _cantidad_solicitada(texto: str, producto: dict, posicion: int | None) -> tuple[int | None, str]:
    # Devuelve (cantidad, descripción) según lo que pidió el usuario.
    existencia = obtener_existencia(producto)
    t = _palabras_a_numeros(texto)

    # "5 mejor": corrige la cantidad del cálculo anterior.
    m = re.fullmatch(r"\W*(\d{1,3})\s+mejor\W*", t)
    if m:
        return int(m.group(1)), ""

    # Número justo antes del producto: "3 ACE-001", "2 piezas del ACE-001"
    if posicion is not None:
        antes = _palabras_a_numeros(texto[max(0, posicion - 25):posicion])
        m = re.search(r"(?<![\w-])(\d+)\s*(?:piezas?|unidades?|cajas?)?\s*(?:de|del|el|la|los|las)?\s*$", antes)
        if m:
            return int(m.group(1)), ""
        # "dos termostatos y UN radiador": el artículo justo antes es 1.
        if re.search(r"\b(?:un|una|uno)\s*(?:pieza\s+(?:de|del)\s*)?$", antes):
            return 1, ""

    if re.search(r"\b(?:todo|todos|todas|toda|completo|completa|"
                 r"todo el stock|toda la existencia|todas las piezas|"
                 r"todo el inventario)\b", t):
        if existencia is None:
            return None, "sin_existencia"
        return existencia, "todo el inventario disponible"

    if re.search(r"\bmitad\b", t):
        if existencia is None:
            return None, "sin_existencia"
        return existencia // 2, "la mitad del inventario disponible"

    m = re.search(
        r"\b(?:vendo|vendiera|vendemos|vender|venda|son|serian|"
        r"llevo|llevara|lleva|compran|compra|piden|pide|por|x|dame|ponme|"
        r"apartame|pasame|vendeme|quiero|das|mandame|agregame|agrega|anota|anotame|"
        r"mejor|ahora|sean|fueran|cambialo a|cambiala a|ponle|multiplica"
        r"(?:lo|la)?(?:\s+por)?)\s*(\d+)\b", t
    )
    if m:
        return int(m.group(1)), ""

    m = re.search(r"\b(\d+)\s*(?:piezas?|unidades?|cajas?)\b", t)
    if m:
        return int(m.group(1)), ""

    # Número justo antes del nombre de la pieza: "total de 5 bujias",
    # "2 balatas con 10% de descuento", "6 filtros de aire".
    raices_nombre = {
        w[:5] for w in re.findall(r"[a-z]+", normalizar(str(producto.get("nombre", ""))))
        if len(w) >= 4
    }
    for m in re.finditer(r"(?<![\w.,%-])(\d{1,4})\s+(?:piezas?\s+(?:de|del)\s+)?([a-z]{4,})", t):
        if m.group(2)[:5] in raices_nombre:
            return int(m.group(1)), ""

    if re.search(r"\bdoble\b", t):
        return 2, ""
    if re.search(r"\btriple\b", t):
        return 3, ""

    return None, ""


def _descuento(texto: str) -> float | None:
    # "descuento de 10%", "10% de descuento", "con 15 de descuento",
    # "rebaja del 15", "10 por ciento de rebaja".
    palabra = r"(?:descuento|rebaja|rebajita)"
    numero = r"(\d+(?:[.,]\d+)?)"
    porciento = r"\s*(?:%|por ciento|porciento)?"
    m = (
        re.search(palabra + r"\s*(?:de|del)?\s*" + numero + porciento, texto)
        or re.search(numero + porciento + r"\s*(?:de)?\s*" + palabra, texto)
    )
    if m:
        valor = _numero(m.group(1))
        if 0 < valor <= 100:
            return valor
    return None


_PIDE_TOTAL_ANTERIOR = (
    r"\b(?:la suma|suma de (?:los|las|todo|todos)|los productos|las refacciones|"
    r"todo junto|todos juntos|ambos|ambas|los dos|las dos|la cuenta|"
    r"a todo|en todo|al total)\b"
)


def _cantidad_previa(historial, producto: dict) -> int | None:
    # Para seguimientos como "¿y con IVA?" o "súmame esto"
    # reutiliza la cantidad del último cálculo del mismo producto.
    ultimo = ultimo_mensaje_asistente(historial)
    codigo = str(producto.get("codigo", ""))
    for linea in ultimo.splitlines():
        if codigo and codigo in linea:
            m = re.search(r":\s*(\d+)\s*×", linea)
            if m:
                return int(m.group(1))
    if codigo and codigo in ultimo:
        m = re.search(r"Cantidad:\s*(\d+)", ultimo)
        if m:
            return int(m.group(1))
    return None


def _productos_con_descuento(texto: str, lineas_productos: list[tuple[dict, int]]) -> set[str] | None:
    # "la suma, si las balatas tienen 20% de descuento" -> solo las balatas.
    # Devuelve los códigos que llevan descuento, o None si el descuento
    # es para toda la cuenta.
    if len(lineas_productos) < 2:
        return None
    nombrados = {
        str(p.get("codigo"))
        for p, _ in lineas_productos
        if productos_en_texto(texto, [p]) or buscar_por_palabra(texto, [p])
    }
    if nombrados and len(nombrados) < len(lineas_productos):
        return nombrados
    return None


def _armar_calculo(lineas_productos: list[tuple[dict, int]], texto: str, avisos: list[str]) -> str:
    descuento = _descuento(texto)
    con_descuento = _productos_con_descuento(texto, lineas_productos) if descuento else None

    subtotal = 0.0
    lineas = []

    if len(lineas_productos) == 1:
        producto, cantidad = lineas_productos[0]
        precio = obtener_precio(producto) or 0.0
        subtotal = precio * cantidad
        lineas.append(f"Cálculo para {etiqueta_producto(producto)}:")
        lineas.append(f"• Precio unitario: {dinero(precio)}")
        lineas.append(
            f"• Cantidad: {cantidad} {'pieza' if cantidad == 1 else 'piezas'}"
        )
    else:
        lineas.append("Suma de productos:")
        for producto, cantidad in lineas_productos:
            precio = obtener_precio(producto) or 0.0
            importe = precio * cantidad
            linea = (
                f"• {etiqueta_producto(producto)}: {cantidad} × "
                f"{dinero(precio)} = {dinero(importe)}"
            )
            if con_descuento is not None and str(producto.get("codigo")) in con_descuento:
                importe -= importe * descuento / 100
                linea += f" − {_formato_numero(descuento)}% = {dinero(importe)}"
            subtotal += importe
            lineas.append(linea)

    lineas.append(f"• Subtotal: {dinero(subtotal)}")

    if descuento is not None and con_descuento is None:
        monto = subtotal * descuento / 100
        subtotal -= monto
        lineas.append(
            f"• Descuento ({_formato_numero(descuento)}%): -{dinero(monto)}"
        )
        lineas.append(f"• Subtotal con descuento: {dinero(subtotal)}")

    iva = subtotal * IVA
    lineas.append(f"• IVA (16%): {dinero(iva)}")
    lineas.append(f"• Total con IVA: {dinero(subtotal + iva)}")

    if avisos:
        lineas.append("")
        lineas.extend(avisos)

    return "\n".join(lineas)


_SEPARADOR_PIEZAS = (
    r",|;|\s(?:y|e|mas|más|con|tambien)\s(?=\s*(?:\d+|un|una|uno|dos|tres|cuatro|"
    r"cinco|seis|siete|ocho|nueve|diez|par|media docena|docena)\b)"
)


def _piezas_por_partes(texto: str, productos: list[dict]) -> list[tuple[int, dict]]:
    # Parte el mensaje en "2 baterías" / "1 alternador" y busca una
    # pieza en cada parte. Devuelve (posición del nombre, producto).
    encontrados: list[tuple[int, dict]] = []
    inicio = 0
    cortes = [m.start() for m in re.finditer(_SEPARADOR_PIEZAS, texto)] + [len(texto)]
    for fin in cortes:
        parte = texto[inicio:fin]
        candidatos = [p for _, p in productos_en_texto(parte, productos)] \
            or buscar_por_palabra(parte, productos)
        if len(candidatos) == 1:
            producto = candidatos[0]
            raices = {
                w[:5] for w in re.findall(r"[a-z]+", normalizar(str(producto.get("nombre", ""))))
                if len(w) >= 4
            }
            posicion = next(
                (inicio + m.start() for m in re.finditer(r"[a-z]+", parte) if m.group()[:5] in raices),
                inicio,
            )
            if all(p is not producto for _, p in encontrados):
                encontrados.append((posicion, producto))
        inicio = fin + 1
    return encontrados


# ---------------------------------------------------------------------
# Vender TODO un grupo: una categoría completa o la lista que se mostró
# ("si vendo todo de escape", "vendo todo el encendido", "vendo todo"
# después de una lista, "si los vendo todos cuánto gano").
# ---------------------------------------------------------------------

_PIDE_TODO = r"\b(?:todo|toda|todos|todas|completo|completa|completos|completas)\b"
_PIDE_TOTAL = r"\b(?:total|suma|sumale|sumalo|sumalos|sumalas|sumame|valor|vale|valen)\b"
_PIDE_VENTA = (
    r"\b(?:vend\w*|suma\w*|total|valor|vale|valen|cuanto (?:gano|ganaria|saco|"
    r"sacaria|junto|seria|serian|da|dan|es|son)|ganancia|cobro|cobraria)\b"
)
_RESPUESTAS_LISTA = (
    "Productos de la categoría", "Productos activos", "Encontré estos productos",
    "Productos con", "Opciones", "Productos de la marca", "Refacciones con",
    "Balatas con", "Filtros con",
)


_NO_ES_GRUPO = {
    "inventario", "lista", "anterior", "esto", "eso", "esos", "esas", "estos",
    "estas", "total", "existencia", "stock", "productos", "producto", "piezas",
}


# "cuánto cuesta todo", "si compro todos los productos de la lista",
# "cuánto me sale todo": una pieza de cada producto (lo que pagaría un
# cliente), no toda la existencia.
_PIDE_COMPRA = (
    r"\b(?:cuanto (?:me )?(?:cuesta|cuestan|sale|salen|costaria|costarian|"
    r"saldria|saldrian)|compr\w*|me llevo|llevo|llevaria|precio de todo)\b"
)
_PIDE_UNA_DE_CADA = r"\b(?:un[oa]? de cada|1 de cada|una pieza de cada|cada uno|cada una)\b"
_HABLA_DE_EXISTENCIA = (
    r"\b(?:vend\w*|existencia|existencias|stock|inventario|gano|ganaria|"
    r"ganancia|ganancias|utilidad|todas las piezas|todas sus piezas)\b"
)
_MENCIONA_LISTA = (
    r"\b(?:(?:de|en) (?:la|esta|esa|tu|mi) lista|lo de (?:arriba|la lista)|"
    r"(?:los|las) de (?:arriba|la lista)|de arriba|lista anterior|esos productos|"
    r"esas piezas|esas refacciones|esos)\b"
)


def _categoria_pedida(texto: str, productos: list[dict]) -> str | None:
    """Categoría pedida como grupo: "todo lo de motor", "los productos
    del apartado de motor", "todos los de la categoría escape",
    "todo de frenos". Aunque haya un producto que se llame igual
    ("Motor de Arranque"), aquí se habla de la categoría."""
    from AgenteIA.inventario.consultas_inteligentes import detectar_categoria

    categoria = detectar_categoria(texto, productos)
    if categoria is None:
        return None
    forma = re.escape(normalizar(categoria))
    singular = forma[:-1] if forma.endswith("s") else forma
    patron = (
        r"\b(?:lo|los|las|productos|piezas|refacciones|articulos|todo|toda|todos|todas|"
        r"apartado|categoria|seccion|area|departamento)\b"
        # Entre medio solo relleno ("que están en el apartado"), nunca el
        # nombre de una pieza ("todo el filtro de aceite").
        r"(?:\s+(?:que|estan|esta|hay|tenemos|tienes|tengo|manejas|los|las|el|la|lo|"
        r"productos|piezas|refacciones|articulos|apartado|categoria|seccion|area|"
        r"departamento|todo|todos|toda|todas)){0,6}\s+"
        r"(?:de|del|en)\s+(?:(?:la|el|los|las)\s+)?"
        r"(?:(?:apartado|categoria|seccion|area|departamento)\s+(?:de\s+)?)?"
        rf"(?:{forma}|{singular})(?:es|s)?\b"
    )
    m = re.search(patron, texto)
    if not m:
        return None
    # Si el nombre completo de una pieza aparece ("filtro de aceite",
    # "motor de arranque"), se habla de esa pieza.
    if productos_en_texto(texto, productos):
        return None
    # "todo el motor de arranque": después de la categoría sigue el
    # nombre de un producto, no es la categoría.
    resto = texto[m.end():].strip()
    if resto and any(
        normalizar(str(p.get("nombre", ""))).startswith(
            normalizar(categoria).rstrip("s") + " " + resto.split()[0]
        ) or normalizar(str(p.get("nombre", ""))).startswith(
            normalizar(categoria) + " " + resto.split()[0]
        )
        for p in productos
    ):
        return None
    return categoria


def _lista_reciente(historial, contexto, productos) -> list[dict]:
    """Productos de la lista más reciente de la conversación, completa.
    Primero el último mensaje; si no trae productos (por ejemplo fue
    "No pude identificar..."), la lista que guarda el contexto; si no,
    el mensaje anterior más reciente con dos o más productos."""
    ultimo = ultimo_mensaje_asistente(historial)
    en_ultimo = _codigos_en(ultimo, productos)
    if len(en_ultimo) >= 2:
        return en_ultimo
    if len(en_ultimo) == 1:
        return []

    codigos = list(getattr(contexto, "codigos_lista", []) or [])
    if len(codigos) >= 2:
        por_codigo = {str(p.get("codigo", "")).casefold(): p for p in productos}
        grupo = [por_codigo[c.casefold()] for c in codigos if c.casefold() in por_codigo]
        if len(grupo) >= 2:
            return grupo

    for mensaje in reversed(list(historial or [])):
        if getattr(mensaje, "rol", None) == "user":
            continue
        grupo = _codigos_en(getattr(mensaje, "texto", "") or "", productos)
        if len(grupo) >= 2:
            return grupo
    return []


def _codigos_en(texto: str, productos: list[dict]) -> list[dict]:
    return [p for _, p in productos_en_texto(texto, productos)]


def _grupo_a_vender(texto, pregunta, productos, contexto, historial):
    """Devuelve (descripción, productos) si se pide vender todo un grupo."""
    pide_todo = re.search(_PIDE_TODO, texto) is not None
    pide_total = re.search(_PIDE_TOTAL, texto) is not None
    pide_operacion = re.search(_PIDE_VENTA, texto) or re.search(_PIDE_COMPRA, texto)
    if not pide_operacion or not (pide_todo or pide_total):
        return None

    # "todos los productos de la lista": directo a la lista anterior.
    if re.search(_MENCIONA_LISTA, texto) and not productos_en_texto(texto, productos):
        grupo = _lista_reciente(historial, contexto, productos)
        if len(grupo) >= 2:
            return "los productos de la lista anterior", grupo

    # "todo lo de motor", "los productos del apartado de motor": la
    # categoría, aunque exista un producto llamado "Motor de Arranque".
    pedida = _categoria_pedida(texto, productos)
    if pedida is not None:
        grupo = [p for p in productos
                 if normalizar(str(p.get("categoria", ""))) == normalizar(pedida)]
        return f"la categoría {pedida}", grupo

    # Un producto concreto ("vendo todo el filtro de aceite") no es grupo:
    # lo calcula el flujo normal con toda su existencia.
    if productos_en_texto(texto, productos) or identificar_producto(pregunta, productos):
        return None
    por_palabra = buscar_por_palabra(pregunta, productos)

    # 1. Categoría nombrada: "todo de escape", "escape total".
    from AgenteIA.inventario.consultas_inteligentes import detectar_categoria
    from AgenteIA.asistente.listados import categoria_sin_productos

    categoria = detectar_categoria(texto, productos)
    if categoria is not None and len(por_palabra) != 1:
        grupo = [p for p in productos
                 if normalizar(str(p.get("categoria", ""))) == normalizar(categoria)]
        return f"la categoría {categoria}", grupo

    vacia = categoria_sin_productos(pregunta, productos)
    if vacia is not None:
        return f"la categoría {vacia}", []

    if len(por_palabra) == 1:
        return None

    # "vendo todo de llantas": nombra algo que no es categoría ni producto.
    m = re.search(
        r"\btod[oa]s?\s+(?:(?:de|del|el|la|los|las|categoria)\s+)+([a-z]{4,})", texto
    )
    if m and m.group(1) not in _NO_ES_GRUPO and not por_palabra:
        return f"«{m.group(1)}»", []

    # 2. La lista que se acaba de mostrar ("vendo todo", "súmalos").
    # Lo anterior fue UN producto ("venderlo todo" tras su ficha):
    # lo calcula el flujo normal con ese producto.
    grupo = _lista_reciente(historial, contexto, productos)
    if len(grupo) >= 2:
        return "los productos de la lista anterior", grupo

    return None


def _respuesta_una_de_cada(descripcion: str, grupo: list[dict], texto: str) -> str:
    """"Cuánto cuesta todo": una pieza de cada producto."""
    lineas = [f"Una pieza de cada uno de {descripcion}:"]
    subtotal = 0.0
    valor_existencia = 0.0
    sin_existencia = []
    contados = 0
    for producto in grupo:
        precio = obtener_precio(producto)
        existencia = obtener_existencia(producto) or 0
        if precio is None or existencia <= 0:
            sin_existencia.append(etiqueta_producto(producto))
            continue
        subtotal += precio
        valor_existencia += precio * existencia
        contados += 1
        lineas.append(f"• {etiqueta_producto(producto)}: {dinero(precio)}")

    if contados == 0:
        return f"Los productos de {descripcion} no tienen existencia disponible."

    descuento = _descuento(texto)
    lineas.append(f"• Productos: {contados}")
    lineas.append(f"• Subtotal: {dinero(subtotal)}")
    if descuento:
        rebaja = subtotal * descuento / 100
        subtotal -= rebaja
        lineas.append(f"• Descuento ({descuento:g}%): -{dinero(rebaja)}")
        lineas.append(f"• Subtotal con descuento: {dinero(subtotal)}")
    lineas.append(f"• IVA (16%): {dinero(subtotal * IVA)}")
    lineas.append(f"• Total con IVA: {dinero(subtotal * (1 + IVA))}")

    if sin_existencia:
        lineas.append("\nSin existencia (no se cuentan): " + ", ".join(sin_existencia))
    lineas.append(
        f"\nSi fuera toda la existencia de esos productos: {dinero(valor_existencia)} "
        f"+ IVA = {dinero(valor_existencia * (1 + IVA))}."
    )
    return "\n".join(lineas)


def _respuesta_grupo(descripcion: str, grupo: list[dict], texto: str) -> str:
    if not grupo:
        donde = f"de {descripcion}" if descripcion.startswith("«") else f"en {descripcion}"
        return f"No hay productos registrados {donde} en el inventario, así que no hay nada que calcular."

    una_de_cada = re.search(_PIDE_UNA_DE_CADA, texto) or (
        re.search(_PIDE_COMPRA, texto) and not re.search(_HABLA_DE_EXISTENCIA, texto)
    )
    if una_de_cada:
        return _respuesta_una_de_cada(descripcion, grupo, texto)

    lineas = [f"Venta de toda la existencia de {descripcion}:"]
    subtotal = 0.0
    piezas = 0
    sin_existencia = []
    for producto in grupo:
        precio = obtener_precio(producto)
        existencia = obtener_existencia(producto) or 0
        if precio is None or existencia <= 0:
            sin_existencia.append(etiqueta_producto(producto))
            continue
        importe = precio * existencia
        subtotal += importe
        piezas += existencia
        lineas.append(
            f"• {etiqueta_producto(producto)}: {existencia} × {dinero(precio)} = {dinero(importe)}"
        )

    if piezas == 0:
        return f"Los productos de {descripcion} no tienen existencia disponible."

    descuento = _descuento(texto)
    lineas.append(f"• Piezas: {piezas}")
    lineas.append(f"• Subtotal: {dinero(subtotal)}")
    if descuento:
        rebaja = subtotal * descuento / 100
        subtotal -= rebaja
        lineas.append(f"• Descuento ({descuento:g}%): -{dinero(rebaja)}")
        lineas.append(f"• Subtotal con descuento: {dinero(subtotal)}")
    lineas.append(f"• IVA (16%): {dinero(subtotal * IVA)}")
    lineas.append(f"• Total con IVA: {dinero(subtotal * (1 + IVA))}")

    if sin_existencia:
        lineas.append("\nSin existencia (no se cuentan): " + ", ".join(sin_existencia))
    if re.search(r"\b(?:gano|ganaria|ganancia|ganancias|utilidad)\b", texto):
        lineas.append(
            "\nEsto es lo que se cobraría. Para saber la ganancia hace falta el "
            "costo de compra de cada pieza, y el inventario no lo trae."
        )
    return "\n".join(lineas)


def resolver_calculo(
    pregunta: str,
    productos: list[dict],
    contexto: "ContextoInventario",
    historial,
) -> tuple[str | None, dict | None]:
    texto = normalizar(pregunta)

    tiene_disparador = (
        re.search(_DISPARADORES_CALCULO, texto) is not None
        or "%" in texto
    )
    tiene_operador = re.search(r"\d\s*[+\-*/x×÷]\s*\d", texto) is not None

    pide_valor_inventario = (
        re.search(r"\b(?:inventario|todo lo que (?:hay|tenemos|tienes))\b", texto)
        and re.search(
            r"\b(?:valor|vale|valen|suma|sumale|total|vendo|vendiera|"
            r"vendemos|cuanto seria|cuanto dinero|lana|varo|feria)\b", texto
        )
        # "todo lo que hay en llantas" es esa categoría, no el inventario.
        and _categoria_pedida(texto, productos) is None
    )

    # "3 termostatos", "y 2 baterías": cantidad + UNA pieza, sin verbo.
    cantidad_y_pieza = (
        re.match(r"^\W*(?:y\s+)?(?:si\s+)?(?:son\s+)?\d{1,3}\s+[a-z]", _palabras_a_numeros(texto))
        and len(texto.split()) <= 6
        and len(buscar_por_palabra(pregunta, productos)) == 1
    )
    # "dame 3", "ponme 2", "apártame 5" con un producto ya seleccionado.
    # También corrige la cantidad del cálculo anterior: "mejor 5",
    # "ahora 10", "que sean 4", "y si son 6", "cámbialo a 2", "5 mejor".
    cantidad_sola = (
        re.fullmatch(
            r"\W*(?:no,?\s+)?(?:y\s+)?(?:dame|ponme|apartame|pasame|vendeme|quiero|me das|"
            r"mandame|agregame|agrega|anota|anotame|mejor|ahora|mejor que sean|que sean|"
            r"y si son|si son|si fueran|y si fueran|cambialo a|cambiala a|ponle|son)\s+(\d{1,3})"
            r"(?:\s+(?:piezas?|unidades?|de esos?|de esas?|mas|mejor))?(?:\s+con iva)?\W*"
            r"|\W*(\d{1,3})\s+mejor\W*",
            _palabras_a_numeros(texto),
        )
        and getattr(contexto, "codigo_seleccionado", None)
    )

    # "cuánto cuesta todo?", "si compro todos los de la lista".
    compra_todo = (
        re.search(_PIDE_COMPRA, texto) is not None
        and re.search(_PIDE_TODO, texto) is not None
    )
    # "compro 2 balatas y 1 radiador": compra con cantidades.
    if re.search(r"\bcompr\w*\b", texto) and re.search(r"\d", _palabras_a_numeros(texto)):
        tiene_disparador = True

    if not tiene_disparador and not tiene_operador and not pide_valor_inventario \
            and not cantidad_y_pieza and not cantidad_sola and not compra_todo:
        return None, None

    # "Un cliente va a hacer afinación, ¿qué le vendo?" es una
    # recomendación, no un cálculo (lo atiende recomendacion_venta).
    from AgenteIA.asistente.listados import _PIDE_RECOMENDACION_VENTA
    if re.search(_PIDE_RECOMENDACION_VENTA, texto) and not re.search(r"\d", texto):
        return None, None

    # "Total de piezas" es una consulta de existencias, no de dinero.
    if (
        re.search(r"\btotal\b", texto)
        and re.search(r"\b(?:piezas|unidades|existencia|stock|productos|refacciones|articulos)\b", texto)
        and not re.search(r"\b(?:precio|dinero|lana|vale|vendo|venta|iva|\$)\b", texto)
    ):
        return None, None

    # 1a. "si vendo los 55 productos", "total si vendo las 488 piezas",
    # "si vendo todos los productos": todo el inventario cuando el número
    # coincide con los productos o con las piezas que hay.
    habla_de_todo = re.search(
        r"\b(?:productos|piezas|refacciones|articulos|unidades|mercancia)\b", texto
    ) and re.search(_PIDE_VENTA, texto) or re.search(_PIDE_COMPRA, texto) and re.search(
        r"\b(?:productos|piezas|refacciones|articulos|unidades|mercancia)\b", texto
    )
    if habla_de_todo and not productos_en_texto(texto, productos) \
            and len(buscar_por_palabra(pregunta, productos)) != 1 \
            and not re.search(_MENCIONA_LISTA, texto) \
            and _categoria_pedida(texto, productos) is None:
        total_productos = len(productos)
        total_piezas = sum((obtener_existencia(p) or 0) for p in productos)
        numeros_texto = [int(n) for n in re.findall(r"\b\d{1,6}\b", _palabras_a_numeros(texto))]
        numero = numeros_texto[0] if len(numeros_texto) == 1 else None
        todos = re.search(
            r"\btod[oa]s? (?:l[oa]s )?(?:productos|piezas|refacciones|articulos|unidades|"
            r"mercancia)\b(?! de (?:la|esta|esa) lista)", texto
        )
        ultimo_es_lista = len(_codigos_en(ultimo_mensaje_asistente(historial), productos)) >= 2
        if numero is not None and numero in (total_productos, total_piezas):
            pide_valor_inventario = True
        elif numero is None and todos and not ultimo_es_lista:
            pide_valor_inventario = True
        elif numero is not None and numero > 0 and re.search(
            r"\b(?:los|las)\s+" + str(numero) + r"\b", _palabras_a_numeros(texto)
        ):
            # "si vendo los 100 productos": no coincide con el inventario.
            return (
                f"En el inventario activo hay {total_productos} productos distintos y "
                f"{total_piezas} piezas en total, así que no sé cuáles serían esos "
                f"{numero}. Puedes preguntar «si vendo todo el inventario», "
                "«si vendo todo de frenos» o «si vendo 3 del ACE-001»."
            ), None

    # 1. Valor de todo el inventario.
    if pide_valor_inventario:
        subtotal = sum(
            (obtener_precio(p) or 0.0) * (obtener_existencia(p) or 0)
            for p in productos
        )
        piezas = sum((obtener_existencia(p) or 0) for p in productos)
        respuesta = (
            "Valor de todo el inventario activo:\n"
            f"• Productos: {len(productos)}\n"
            f"• Piezas: {piezas}\n"
            f"• Subtotal: {dinero(subtotal)}\n"
            f"• IVA (16%): {dinero(subtotal * IVA)}\n"
            f"• Total con IVA: {dinero(subtotal * (1 + IVA))}"
        )
        return respuesta, None

    # 1b. Vender todo un grupo (categoría o lista anterior).
    grupo = _grupo_a_vender(texto, pregunta, productos, contexto, historial)
    if grupo is not None:
        descripcion, productos_grupo = grupo
        return _respuesta_grupo(descripcion, productos_grupo, texto), None

    # "cuánto cuesta todo?" sin ninguna lista antes.
    if compra_todo and not productos_en_texto(texto, productos) \
            and not identificar_producto(pregunta, productos) \
            and len(buscar_por_palabra(pregunta, productos)) != 1 \
            and not getattr(contexto, "codigo_seleccionado", None) \
            and len(_codigos_en(ultimo_mensaje_asistente(historial), productos)) != 1:
        return (
            "¿Todo de qué? Primero pídeme una lista (por ejemplo «frenos» o "
            "«qué tienes para un versa 2015») y luego pregunta «cuánto cuesta "
            "todo». Te doy el total de una pieza de cada producto y el de "
            "toda su existencia."
        ), None

    # 2. Productos mencionados en la pregunta.
    mencionados = productos_en_texto(texto, productos)

    # "me llevo 2 baterías y 1 alternador": varias piezas por su nombre
    # corto, cada una con su cantidad.
    if len(mencionados) < 2:
        varios = _piezas_por_partes(texto, productos)
        if len(varios) >= 2:
            mencionados = varios

    if not mencionados:
        producto_parcial = identificar_producto(pregunta, productos)
        if producto_parcial is not None:
            mencionados = [(None, producto_parcial)]

    if not mencionados:
        por_palabra = buscar_por_palabra(pregunta, productos)
        if len(por_palabra) == 1:
            mencionados = [(None, por_palabra[0])]

    # 2b. "¿Cuánto quedaría la suma de los productos si las balatas tienen
    #     20% de descuento?": nombra uno, pero pide el total de los
    #     productos del cálculo anterior.
    ultimo = ultimo_mensaje_asistente(historial)
    if re.search(_PIDE_TOTAL_ANTERIOR, texto):
        en_ultimo = productos_en_texto(ultimo, productos)
        codigos_ultimo = {str(p.get("codigo")) for _, p in en_ultimo}
        if len(en_ultimo) >= 2 and all(
            str(p.get("codigo")) in codigos_ultimo for _, p in mencionados
        ):
            mencionados = [(None, p) for _, p in en_ultimo]

    # 3. Operación aritmética pura (sin productos ni referencias).
    numeros = re.findall(r"\d+(?:[.,]\d+)?", _palabras_a_numeros(texto))
    if (
        not mencionados
        and len(numeros) >= 2
        and not re.search(_PRONOMBRES_PRODUCTO, texto)
        and not re.search(r"\b(?:vendo|vendiera|vendemos)\b", texto)
    ):
        resultado = _resultado_aritmetico(texto)
        if resultado is not None:
            return resultado, None

    if not mencionados and len(numeros) >= 1 and "%" in texto and " de " in texto:
        resultado = _resultado_aritmetico(texto)
        if resultado is not None:
            return resultado, None

    # 4. Productos por referencia (posición, contexto o último mensaje).
    plural = re.search(
        r"\b(?:los|las|ambos|ambas|todos|juntos|juntas|sumalos|sumalas|"
        r"los dos|las dos|los tres|las tres|esto|eso|todo esto|"
        r"lo anterior)\b", texto
    ) is not None

    if not mencionados:
        estado, producto_posicion = resolver_posicion_lista(
            pregunta, contexto, productos
        )
        if estado == "encontrado" and producto_posicion is not None:
            mencionados = [(None, producto_posicion)]

    ultimo = ultimo_mensaje_asistente(historial)

    if not mencionados and plural:
        en_ultimo = productos_en_texto(ultimo, productos)
        if len(en_ultimo) >= 2:
            mencionados = [(None, p) for _, p in en_ultimo]
        else:
            recientes = productos_recientes(historial, productos)
            if len(recientes) >= 2:
                mencionados = [(None, p) for p in recientes]

    if not mencionados:
        seleccionado = obtener_producto_seleccionado(contexto, productos)
        if seleccionado is not None:
            mencionados = [(None, seleccionado)]

    if not mencionados:
        en_ultimo = productos_en_texto(ultimo, productos)
        if len(en_ultimo) == 1:
            mencionados = [(None, en_ultimo[0][1])]

    # 5. "Súmame esto": sumar las cantidades en $ del último mensaje.
    if not mencionados:
        # Solo cantidades sueltas de una respuesta que NO es una lista de
        # productos (sumar precios unitarios de una lista no significa
        # nada) y sin contar resultados ya calculados ("= $3,888.00",
        # "Total: ...").
        if re.search(r"\b(?:suma|sumale|sumalo|sumalos|sumame|total)\b", texto) \
                and not ultimo.lstrip().startswith(_RESPUESTAS_LISTA):
            montos = [
                _numero(m)
                for linea in ultimo.splitlines()
                if not re.search(r"(?i)total|subtotal|iva|descuento", linea)
                for m in re.findall(r"(?<!= )\$\s?([\d,]+(?:\.\d+)?)", linea)
            ]
            if len(montos) >= 2:
                return (
                    "Suma de las cantidades de mi respuesta anterior:\n"
                    f"{' + '.join(dinero(m) for m in montos)} = "
                    f"{dinero(sum(montos))}"
                ), None

        # Pedía un cálculo, pero no hay producto identificable.
        if re.search(r"\b(?:suma|sumale|sumame|sumalo|sumala|sumalos|"
                     r"multiplica|multiplicalo|vendo|vendiera|todo|iva|"
                     r"descuento|esto|eso|total|llevo|lleve|llevara|"
                     r"lleva|llevan|un par)\b", texto):
            return (
                "Para hacer el cálculo necesito saber de qué producto se trata. "
                "Dime su nombre o código, por ejemplo: "
                "\"si vendo 3 del ACE-001\" o \"súmalo si vendo todo el FIL-001\"."
            ), None

        return None, None

    # 6. Calcular con las cantidades solicitadas.
    lineas_productos: list[tuple[dict, int]] = []
    avisos: list[str] = []

    for posicion, producto in mencionados:
        if obtener_precio(producto) is None:
            avisos.append(
                f"No hay un precio registrado para {etiqueta_producto(producto)}."
            )
            continue

        # "descuento a todo" habla de la cuenta, no de vender toda la
        # existencia. Se tapa con espacios para no mover las posiciones.
        texto_cantidad = re.sub(
            r"\b(?:a|en|sobre) todo\b|\bal total\b",
            lambda m: " " * len(m.group()),
            texto,
        )
        cantidad, descripcion = _cantidad_solicitada(texto_cantidad, producto, posicion)

        if descripcion == "sin_existencia":
            avisos.append(
                f"No se pudo verificar la existencia de {etiqueta_producto(producto)}."
            )
            continue

        if cantidad is None:
            cantidad = _cantidad_previa(historial, producto)

        # "¿Y con IVA?" o "precio con 10% de descuento" sin cantidad:
        # precio de UNA pieza.
        if (
            cantidad is None
            and (re.search(r"\biva\b", texto) or _descuento(texto))
            and not re.search(r"\b(?:suma|sumalo|sumala|sumalos|vendo|vendiera|"
                              r"todo|total|multiplica|multiplicalo)\b", texto)
        ):
            cantidad = 1

        if cantidad is None:
            if len(mencionados) == 1:
                return (
                    f"{etiqueta_producto(producto)} cuesta "
                    f"{dinero(obtener_precio(producto))} por pieza. "
                    "¿Cuántas piezas quieres calcular? Por ejemplo: "
                    "\"si vendo 3\" o \"si lo vendo todo\"."
                ), producto
            cantidad = 1

        if cantidad <= 0:
            avisos.append(
                f"La cantidad para {etiqueta_producto(producto)} debe ser mayor que cero."
            )
            continue

        existencia = obtener_existencia(producto)
        if existencia == 0:
            avisos.append(
                f"Aviso: {etiqueta_producto(producto)} no tiene piezas "
                "en existencia en este momento."
            )
        elif existencia is not None and cantidad > existencia:
            avisos.append(
                f"Aviso: solo hay {existencia} "
                f"{'pieza' if existencia == 1 else 'piezas'} de "
                f"{etiqueta_producto(producto)} en existencia; "
                f"el cálculo es con las {cantidad} que pediste."
            )

        if descripcion:
            avisos.append(f"Se tomó {descripcion} de {etiqueta_producto(producto)}.")

        lineas_productos.append((producto, cantidad))

    if not lineas_productos:
        return "\n".join(avisos) or None, None

    respuesta = _armar_calculo(lineas_productos, texto, avisos)
    producto_unico = lineas_productos[0][0] if len(lineas_productos) == 1 else None
    return respuesta, producto_unico
