import asyncio
import json
import re

from AgenteIA.asistente.configuracion import MODELO, OLLAMA_HOST, modelo_piensa
from AgenteIA.asistente.listados import CATEGORIAS_CONOCIDAS, menciona_categoria
from AgenteIA.asistente.productos import buscar_por_palabra, productos_en_texto
from AgenteIA.asistente.texto import normalizar


# ---------------------------------------------------------------------
# Tipos de consulta que el modelo puede elegir
# ---------------------------------------------------------------------

TIPOS = {
    "pagina_siguiente": "ver la siguiente página de la lista que ya se mostró",
    "pagina_anterior": "regresar a la página anterior de la lista",
    "pagina_numero": "ir a una página concreta (numero)",
    "posicion": "elegir un producto por su número en la lista mostrada (numero)",
    "listar_inventario": "ver todos los productos del inventario",
    "listar_categoria": "ver los productos de una categoría (categoria)",
    "precio": "precio de un producto (codigo, o vacío si es el que se está viendo)",
    "existencia": "cuántas piezas hay de un producto (codigo o vacío)",
    "ficha": "ver la información completa de un producto (codigo)",
    "calcular_venta": "cuánto sale vender cierta cantidad (codigo o vacío, cantidad, descuento opcional)",
    "vender_todo": "cuánto sale vender toda la existencia (codigo o vacío)",
    "compatibilidad": "si un producto le queda a un vehículo (codigo o vacío, vehiculo)",
    "recomendar_venta": "qué ofrecerle a un cliente para cierto servicio (categoria)",
    "mas_caro": "el producto más caro",
    "mas_barato": "el producto más barato",
    "agotados": "productos que YA NO tienen ninguna pieza (cero, se acabaron)",
    "stock_bajo": "productos a los que les QUEDAN POCAS piezas (se están acabando, hay que resurtir)",
    "conteo": "cuántos productos hay en total",
    "valor_inventario": "cuánto vale todo el inventario",
    "sintoma": "describe una falla o síntoma del vehículo (texto: el síntoma en pocas palabras)",
    "otro": "cualquier otra cosa, o no estás seguro",
}

# Solo "tipo" es obligatorio y cada campo tiene un largo máximo: si todos
# fueran obligatorios, el modelo los llenaría aunque no apliquen y a veces
# se queda escribiendo un texto largo que corta el JSON.
_ESQUEMA = {
    "type": "object",
    "properties": {
        "tipo": {"type": "string", "enum": list(TIPOS)},
        "codigo": {"type": "string", "maxLength": 12},
        "cantidad": {"type": "string", "maxLength": 6},
        "descuento": {"type": "string", "maxLength": 4},
        "categoria": {"type": "string", "maxLength": 40},
        "numero": {"type": "string", "maxLength": 4},
        "vehiculo": {"type": "string", "maxLength": 40},
        "texto": {"type": "string", "maxLength": 80},
    },
    "required": ["tipo"],
}

_EJEMPLOS = [
    ("pásame los que faltan", '{"tipo":"pagina_siguiente"}'),
    ("regrésate", '{"tipo":"pagina_anterior"}'),
    ("enséñame el 4", '{"tipo":"posicion","numero":"4"}'),
    ("¿a cuánto anda el aceite mobil?", '{"tipo":"precio","codigo":"ACE-001"}'),
    ("¿y ese a cuánto?", '{"tipo":"precio","codigo":""}'),
    ("¿todavía quedan del alternador?", '{"tipo":"existencia","codigo":"PRU-009"}'),
    ("si se lleva tres balatas con 10 de descuento",
     '{"tipo":"calcular_venta","codigo":"BAL-002","cantidad":"3","descuento":"10"}'),
    ("¿y si me compra todas?", '{"tipo":"vender_todo","codigo":""}'),
    ("¿las balatas le entran a un versa 2015?",
     '{"tipo":"compatibilidad","codigo":"BAL-002","vehiculo":"Nissan Versa 2015"}'),
    ("viene un señor que quiere afinar su carro, ¿qué le vendo?",
     '{"tipo":"recomendar_venta","categoria":"Encendido"}'),
    ("¿qué es lo que ya no tenemos?", '{"tipo":"agotados"}'),
    ("¿qué se nos está terminando?", '{"tipo":"stock_bajo"}'),
    ("el cliente dice que su carro chilla cuando frena",
     '{"tipo":"sintoma","texto":"rechina al frenar"}'),
    ("¿qué opinas del clima de hoy?", '{"tipo":"otro"}'),
]


def _catalogo(productos: list[dict], maximo: int = 60) -> str:
    return "\n".join(
        f"{p.get('codigo')} — {p.get('nombre')} ({p.get('categoria', '')})"
        for p in productos[:maximo]
    )


def _categorias(productos: list[dict]) -> list[str]:
    # Las del inventario más las del programa (aunque no tengan productos).
    del_inventario = {str(p.get("categoria", "")).strip() for p in productos if p.get("categoria")}
    normales = {normalizar(c) for c in del_inventario}
    extra = {c for c in CATEGORIAS_CONOCIDAS if normalizar(c) not in normales}
    return sorted(del_inventario | extra)


def armar_mensajes(pregunta: str, productos: list[dict], contexto, historial) -> list[dict]:
    tipos = "\n".join(f"- {t}: {d}" for t, d in TIPOS.items())
    ejemplos = "\n".join(f'Mensaje: {m}\nJSON: {j}' for m, j in _EJEMPLOS)

    seleccionado = getattr(contexto, "codigo_seleccionado", None) or "ninguno"
    hay_lista = "sí" if getattr(contexto, "codigos_lista", None) else "no"

    recientes = [
        f"{'Vendedor' if m.rol == 'user' else 'Asistente'}: {(m.texto or '')[:200]}"
        for m in (historial or [])[-4:]
    ]

    sistema = (
        "Clasificas mensajes de un vendedor de una refaccionaria mexicana. "
        "NO respondes la pregunta: solo eliges el tipo de consulta y "
        "extraes los datos. Responde únicamente con JSON.\n\n"
        f"TIPOS:\n{tipos}\n\n"
        "REGLAS:\n"
        "- codigo: SOLO un código del CATÁLOGO, o vacío si el vendedor se "
        "refiere al producto que se está viendo. Nunca inventes códigos.\n"
        "- categoria: SOLO una de las CATEGORÍAS, escrita igual.\n"
        "- cantidad, descuento y numero: solo dígitos, o vacío.\n"
        "- Incluye SOLO los campos que apliquen; los demás no los escribas.\n"
        "- Si no estás seguro, usa el tipo \"otro\".\n\n"
        f"CATÁLOGO:\n{_catalogo(productos)}\n\n"
        f"CATEGORÍAS: {', '.join(_categorias(productos))}\n\n"
        f"EJEMPLOS (con otro inventario):\n{ejemplos}"
    )

    usuario = (
        f"Producto que se está viendo: {seleccionado}\n"
        f"Hay una lista en pantalla: {hay_lista}\n"
        + (f"Conversación reciente:\n" + "\n".join(recientes) + "\n" if recientes else "")
        + f"\nMensaje: {pregunta}\nJSON:"
    )

    return [
        {"role": "system", "content": sistema},
        {"role": "user", "content": usuario},
    ]


# ---------------------------------------------------------------------
# Validación: de la clasificación a una frase que las reglas entienden
# ---------------------------------------------------------------------

def _entero(valor, minimo: int, maximo: int) -> int | None:
    m = re.search(r"\d+", str(valor or ""))
    if not m:
        return None
    numero = int(m.group())
    return numero if minimo <= numero <= maximo else None


def _codigo_valido(valor, productos: list[dict]) -> str | None:
    codigo = str(valor or "").strip().upper()
    if not codigo:
        return None
    for producto in productos:
        if str(producto.get("codigo", "")).strip().upper() == codigo:
            return str(producto.get("codigo")).strip()
    return None


def _categoria_valida(valor, productos: list[dict]) -> str | None:
    buscada = normalizar(str(valor or "")).strip()
    if not buscada:
        return None
    for categoria in _categorias(productos):
        if normalizar(categoria) == buscada:
            return categoria
    return None


def _codigos_mencionados(texto: str, productos: list[dict]) -> set[str]:
    # Productos nombrados en un texto, por código, nombre o palabra
    # ("el alternador", "las balatas", "PRU-009").
    encontrados = {str(p.get("codigo")) for _, p in productos_en_texto(texto or "", productos)}
    if not encontrados and texto:
        encontrados = {str(p.get("codigo")) for p in buscar_por_palabra(texto, productos)}
    return encontrados


def construir_frase(
    clasificacion: dict,
    productos: list[dict],
    contexto,
    pregunta: str = "",
    ultima_respuesta: str = "",
) -> str | None:
    # Convierte {"tipo": "calcular_venta", "codigo": "ACE-001", ...} en
    # "si vendo 3 del ACE-001". Devuelve None si algo no es válido.
    if not isinstance(clasificacion, dict):
        return None

    tipo = clasificacion.get("tipo")
    escrito = str(clasificacion.get("codigo") or "").strip()
    codigo = _codigo_valido(escrito, productos)

    # Escribió un código que no existe: lo inventó.
    if escrito and codigo is None:
        return None

    seleccionado = _codigo_valido(getattr(contexto, "codigo_seleccionado", None), productos)

    # El modelo no puede ELEGIR un producto que nadie mencionó: el código
    # debe venir del mensaje, del producto que se está viendo o de la
    # última respuesta. ("¿y si es un Versa 2015?" hablando de bandas no
    # puede convertirse en "¿las balatas le quedan al Versa?").
    if codigo and codigo != seleccionado and codigo not in (
        _codigos_mencionados(pregunta, productos)
        | _codigos_mencionados(ultima_respuesta, productos)
    ):
        return None
    hay_lista = bool(getattr(contexto, "codigos_lista", None))

    # Para los tipos que hablan de UN producto: el nombrado o el que se ve.
    producto = codigo or seleccionado
    del_producto = f" del {codigo}" if codigo else ""

    # "Motor", "iluminación": el modelo a veces lo toma como cambio de
    # página. Si el mensaje nombra una categoría o un producto, no lo es.
    if tipo in ("pagina_siguiente", "pagina_anterior", "pagina_numero", "posicion") and (
        menciona_categoria(pregunta, productos)
        or _codigos_mencionados(pregunta, productos)
        # "MOT 001": parece un código, no una página.
        or re.search(r"\b[a-z]{2,5}[\s_-]*0\d{1,4}\b|\b[a-z]{2,5}[_-]\d{2,5}\b", normalizar(pregunta))
    ):
        return None

    # "dímelo sin precios": no puede convertirse en una consulta de precio.
    if tipo == "precio" and re.search(r"\bsin (?:el |los |sus )?precios?\b", normalizar(pregunta)):
        return None

    if tipo == "pagina_siguiente":
        return "siguientes productos" if hay_lista else None
    if tipo == "pagina_anterior":
        return "página anterior" if hay_lista else None
    if tipo == "pagina_numero":
        numero = _entero(clasificacion.get("numero"), 1, 100)
        return f"página {numero}" if numero and hay_lista else None
    if tipo == "posicion":
        numero = _entero(clasificacion.get("numero"), 1, 500)
        return f"el producto {numero}" if numero and hay_lista else None

    if tipo == "listar_inventario":
        return "¿qué tenemos en inventario?"
    if tipo == "listar_categoria":
        categoria = _categoria_valida(clasificacion.get("categoria"), productos)
        return f"¿qué tenemos de {normalizar(categoria)}?" if categoria else None
    if tipo == "recomendar_venta":
        categoria = _categoria_valida(clasificacion.get("categoria"), productos)
        if not categoria:
            return None
        return f"un cliente quiere {normalizar(categoria)}, ¿qué le ofrezco?"

    if tipo == "precio" and producto:
        return f"¿cuánto cuesta el {producto}?"
    if tipo == "existencia" and producto:
        return f"¿cuántas piezas quedan del {producto}?"
    if tipo == "ficha" and codigo:
        return f"dame el {codigo}"

    if tipo == "calcular_venta" and producto:
        cantidad = _entero(clasificacion.get("cantidad"), 1, 100000)
        if not cantidad:
            return None
        frase = f"si vendo {cantidad} del {producto}"
        descuento = _entero(clasificacion.get("descuento"), 1, 100)
        if descuento:
            frase += f" con {descuento}% de descuento"
        return frase
    if tipo == "vender_todo" and producto:
        return f"súmalo si vendo todo el {producto}"

    if tipo == "compatibilidad" and producto:
        vehiculo = str(clasificacion.get("vehiculo") or "").strip()
        # Necesita marca/modelo y un año de 4 dígitos.
        if not re.search(r"[a-zA-Z]{3,}", vehiculo) or not re.search(r"\b(?:19|20)\d{2}\b", vehiculo):
            return None
        return f"¿el {producto} es compatible con un {vehiculo}?"

    frases_fijas = {
        "mas_caro": "¿cuál es el producto más caro?",
        "mas_barato": "¿cuál es el producto más barato?",
        "agotados": "¿qué está agotado?",
        "stock_bajo": "¿qué tiene poco stock?",
        "conteo": "¿cuántos productos tenemos?",
        "valor_inventario": "¿cuánto vale todo el inventario?",
    }
    if tipo in frases_fijas:
        return frases_fijas[tipo]

    if tipo == "sintoma":
        texto = str(clasificacion.get("texto") or "").strip()
        palabras = texto.split()
        # Una descripción corta del síntoma, sin números ni códigos.
        if not (2 <= len(palabras) <= 10) or re.search(r"\d|[A-Z]{2,5}-\d", texto):
            return None
        # El modelo pequeño a veces copia el ejemplo ("falla mi mofle" ->
        # "rechina al frenar"). Si el mensaje ya apuntaba a un sistema del
        # vehículo (escape), la frase nueva no puede llevarlo a otro (frenos).
        if not _mismo_sistema(pregunta, texto):
            return None
        return texto

    return None


def _sistemas(texto: str) -> set[str]:
    from AgenteIA.mecanica.buscador_mecanico import buscar_conocimiento

    documentacion = buscar_conocimiento(texto) or ""
    return set(re.findall(r"SISTEMA: ([A-ZÁÉÍÓÚÑ ]+)", documentacion))


def _mismo_sistema(original: str, reescrita: str) -> bool:
    sistemas_original = _sistemas(original)
    if not sistemas_original:
        # El mensaje no se entendía ("no quiere jalar"): justo para eso
        # sirve la reescritura.
        return True
    return bool(sistemas_original & _sistemas(reescrita))

    return None


# ---------------------------------------------------------------------
# Llamada al modelo
# ---------------------------------------------------------------------

def leer_json_tolerante(contenido: str) -> dict | None:
    # Lee el JSON del modelo. Si llegó cortado ('{"tipo":"precio","texto":"bla'),
    # rescata el tipo y los campos que sí se cerraron.
    try:
        datos = json.loads(contenido)
        return datos if isinstance(datos, dict) else None
    except (json.JSONDecodeError, TypeError):
        pass

    campos = dict(re.findall(r'"(\w+)"\s*:\s*"([^"\\]{0,80})"', contenido or ""))
    if campos.get("tipo") not in TIPOS:
        return None
    return campos


async def _clasificar(mensajes: list[dict]) -> dict | None:
    from ollama import AsyncClient  # mismo paquete que usa autogen

    argumentos = {
        "model": MODELO,
        "messages": mensajes,
        "format": _ESQUEMA,
        # num_predict: la respuesta es un JSON corto. Sin límite, un modelo
        # chico a veces se queda generando espacios hasta el timeout.
        "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 150},
        "keep_alive": "30m",
    }
    if modelo_piensa():
        argumentos["think"] = False

    respuesta = await AsyncClient(host=OLLAMA_HOST).chat(**argumentos)
    return leer_json_tolerante(respuesta.message.content or "")


async def reescribir_pregunta(pregunta: str, productos: list[dict], contexto, historial) -> str | None:
    # Devuelve una frase estándar para volver a intentar con las reglas,
    # o None si no aplica o algo falló. Nunca lanza errores.
    if not pregunta or len(pregunta) > 400 or not productos:
        return None

    try:
        clasificacion = await asyncio.wait_for(
            _clasificar(armar_mensajes(pregunta, productos, contexto, historial)),
            timeout=8,
        )
    except Exception as error:  # noqa: BLE001 - nunca debe tumbar la consulta
        print(f"[REESCRITURA] No se pudo clasificar: {type(error).__name__}: {error}", flush=True)
        return None

    ultima_respuesta = next(
        (m.texto or "" for m in reversed(historial or []) if m.rol != "user"),
        "",
    )
    frase = construir_frase(clasificacion, productos, contexto, pregunta, ultima_respuesta)

    print(
        f"[REESCRITURA] {pregunta!r} -> {clasificacion.get('tipo') if isinstance(clasificacion, dict) else '?'}"
        f" -> {frase!r}",
        flush=True,
    )

    if frase and normalizar(frase) == normalizar(pregunta):
        return None
    return frase





