import re
from dataclasses import dataclass, field

from AgenteIA.inventario.utilidades_inventario import (
    MARCAS_CONOCIDAS,
    codigos_mencionados,
    mismo_codigo,
    normalizar,
    raiz as _raiz,
)


PRODUCTOS_POR_PAGINA = 10


# =====================================================================
# MODELO DEL CONTEXTO
# =====================================================================

@dataclass
class ContextoInventario:
    # Guarda referencias a productos mediante sus códigos.
    # No almacena precios ni existencias para evitar
    # utilizar información desactualizada.

    codigo_seleccionado: str | None = None
    codigos_lista: list[str] = field(default_factory=list)

    # Página que está viendo el vendedor.
    pagina_actual: int = 1

    # Contexto para recomendaciones de refaccionaria.
    categoria_consultada: str | None = None
    marca_vehiculo: str | None = None
    modelo_vehiculo: str | None = None
    anio_vehiculo: int | None = None


CAMPOS_CONTEXTO = (
    "codigo_seleccionado",
    "codigos_lista",
    "pagina_actual",
    "categoria_consultada",
    "marca_vehiculo",
    "modelo_vehiculo",
    "anio_vehiculo",
)


def contexto_desde_estado(estado) -> ContextoInventario:
    # Crea un ContextoInventario a partir de lo que mandó WinUI
    # (objeto de Pydantic, diccionario o None). Si faltan campos,
    # se usan los valores por defecto.
    if estado is None:
        return ContextoInventario()

    def leer(nombre, defecto=None):
        if isinstance(estado, dict):
            return estado.get(nombre, defecto)
        return getattr(estado, nombre, defecto)

    pagina = leer("pagina_actual", 1)
    try:
        pagina = max(1, int(pagina or 1))
    except (TypeError, ValueError):
        pagina = 1

    anio = leer("anio_vehiculo")
    try:
        anio = int(anio) if anio is not None else None
    except (TypeError, ValueError):
        anio = None

    codigos = leer("codigos_lista") or []
    if isinstance(codigos, str):
        # Evita convertir "BAL-001" en ["B", "A", "L", ...].
        codigos = [codigos]

    return ContextoInventario(
        codigo_seleccionado=leer("codigo_seleccionado"),
        codigos_lista=[str(c) for c in codigos if str(c).strip()],
        pagina_actual=pagina,
        categoria_consultada=leer("categoria_consultada"),
        marca_vehiculo=leer("marca_vehiculo"),
        modelo_vehiculo=leer("modelo_vehiculo"),
        anio_vehiculo=anio,
    )


def contexto_a_diccionario(contexto) -> dict:
    # Convierte el contexto en el diccionario que se devuelve a WinUI.
    # Acepta ContextoInventario o el EstadoContexto de Pydantic.
    return {
        "codigo_seleccionado": getattr(contexto, "codigo_seleccionado", None),
        "codigos_lista": list(getattr(contexto, "codigos_lista", []) or []),
        "pagina_actual": getattr(contexto, "pagina_actual", 1) or 1,
        "categoria_consultada": getattr(contexto, "categoria_consultada", None),
        "marca_vehiculo": getattr(contexto, "marca_vehiculo", None),
        "modelo_vehiculo": getattr(contexto, "modelo_vehiculo", None),
        "anio_vehiculo": getattr(contexto, "anio_vehiculo", None),
    }


def crear_contexto_desde_productos(
    productos: list[dict]
) -> ContextoInventario:
    # Construye una lista ordenada de códigos de producto.
    codigos = []

    for producto in productos:
        codigo = str(producto.get("codigo", "")).strip()

        if codigo and codigo not in codigos:
            codigos.append(codigo)

    return ContextoInventario(
        codigo_seleccionado=None,
        codigos_lista=codigos,
    )


# =====================================================================
# TEXTO
# =====================================================================

def normalizar_contexto(texto: str) -> str:
    return normalizar(texto)


# =====================================================================
# CAMBIO DE TEMA
# =====================================================================

# Siempre indican cambio de tema, estén donde estén.
_FRASES_CAMBIO_TEMA_FUERTES = (
    "cambiemos de tema",
    "cambio de tema",
    "otro tema",
    "otra consulta",
    "nueva consulta",
    "olvida lo anterior",
    "olvida todo",
    "olvidalo",
    "olvida eso",
    "empecemos de nuevo",
    "empezar de nuevo",
    "desde cero",
)

# Solo cuentan al inicio del mensaje. "Otra cosa, ¿cuánto cuesta el
# filtro?" sí cambia de tema; "¿tienes otra cosa más barata?" no.
_FRASES_CAMBIO_TEMA_DEBILES = (
    "otra pregunta",
    "otra cosa",
    "nada de eso",
)

_FRASES_CAMBIO_TEMA = _FRASES_CAMBIO_TEMA_FUERTES + _FRASES_CAMBIO_TEMA_DEBILES

_MULETILLAS_INICIO = r"(?:(?:y|oye|bueno|pues|ok|mejor|no|ya)\W+)*"


def detectar_cambio_tema(pregunta: str) -> bool:
    texto = normalizar_contexto(pregunta)

    if any(
        re.search(r"(?<!\w)" + re.escape(frase) + r"(?!\w)", texto)
        for frase in _FRASES_CAMBIO_TEMA_FUERTES
    ):
        return True

    return any(
        re.search(r"^\W*" + _MULETILLAS_INICIO + re.escape(frase) + r"(?!\w)", texto)
        for frase in _FRASES_CAMBIO_TEMA_DEBILES
    )


def limpiar_contexto(contexto) -> None:
    # Borra lo que se recuerda de la conversación.
    # Funciona con ContextoInventario o con el EstadoContexto de Pydantic.
    contexto.codigo_seleccionado = None
    contexto.codigos_lista = []
    contexto.pagina_actual = 1
    for nombre in ("categoria_consultada", "marca_vehiculo",
                   "modelo_vehiculo", "anio_vehiculo"):
        if hasattr(contexto, nombre):
            setattr(contexto, nombre, None)


def es_solo_cambio_tema(pregunta: str) -> bool:
    # True si el mensaje SOLO pide cambiar de tema
    # ("olvida lo anterior"), sin otra consulta.
    texto = normalizar_contexto(pregunta).strip(" ¿?¡!.,")
    for frase in _FRASES_CAMBIO_TEMA:
        texto = re.sub(r"(?<!\w)" + re.escape(frase) + r"(?!\w)", " ", texto)
    texto = re.sub(r"\b(?:por favor|porfa|y|pues|bueno|ok|va|sale|oye)\b", " ", texto)
    return not texto.strip(" ¿?¡!.,")


# =====================================================================
# MEMORIA DEL VEHÍCULO
# =====================================================================

_MARCAS_CONOCIDAS = MARCAS_CONOCIDAS

# Apodos de marca -> marca registrada.
_ALIAS_MARCA = {"vw": "volkswagen", "chevy": "chevrolet"}


_PALABRAS_NO_MODELO = {
    # Preposiciones, artículos y verbos
    "para", "con", "a", "un", "una", "el", "la", "los", "las", "mi",
    "su", "tu", "de", "del", "y", "o", "es", "le", "queda", "quedan",
    "sirve", "sirven", "compatible", "compatibles", "tienes", "tienen",
    "hay", "que", "cual", "cuales", "busco", "necesito", "ocupo",
    "quiero", "manejas", "manejan", "tengo", "tiene", "en", "por",
    # Vehículo genérico
    "carro", "coche", "auto", "automovil", "camioneta", "vehiculo",
    "nave", "troca", "modelo", "ano",
    # Palabras de negocio que no son vehículos ("ventas del 2025")
    "ventas", "venta", "vendi", "vendimos", "compras", "compra",
    "inventario", "reporte", "corte", "mes", "meses", "semana", "dia",
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
    "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    # Tipos de producto
    "productos", "producto", "refacciones", "refaccion", "piezas",
    "pieza", "cosas", "algo", "balatas", "balata", "filtro", "filtros",
    "aceite", "aceites", "bujia", "bujias", "amortiguador",
    "amortiguadores", "frenos", "freno", "bateria", "baterias",
    "focos", "foco", "banda", "bandas", "radiador", "llantas",
    "llanta", "anticongelante", "liquido",
}


def extraer_vehiculo_contexto(pregunta: str) -> dict | None:
    # Busca "marca modelo año" en el texto.
    # Ejemplos: "Nissan Versa 2015", "versa 2015", "mi tsuru del 2010".
    texto = normalizar_contexto(pregunta)

    anio = None
    m_anio = re.search(r"\b((?:19[5-9]|20[0-4])\d)\b", texto)
    if m_anio:
        anio = int(m_anio.group(1))

    marca = None
    for posible in _MARCAS_CONOCIDAS:
        if re.search(r"(?<!\w)" + re.escape(posible) + r"(?!\w)", texto):
            marca = posible
            break

    modelo = None
    if anio is not None:
        # Se toman hasta 3 palabras justo antes del año, deteniéndose
        # en preposiciones o palabras que no son parte del modelo.
        # "balatas para versa 2015" -> "versa"
        antes = texto[:m_anio.start()].split()
        conectores = {"del", "de", "modelo", "ano", "anio", "año"}
        while antes and antes[-1] in conectores:
            antes.pop()

        palabras_modelo = []
        for palabra in reversed(antes):
            if palabra in _PALABRAS_NO_MODELO or len(palabras_modelo) == 3:
                break
            palabras_modelo.insert(0, palabra)

        palabras_modelo = [p for p in palabras_modelo if p != marca]
        if palabras_modelo:
            modelo = " ".join(palabras_modelo[-2:])

    # "Chevy" también es un modelo en México: "mi chevy 2008".
    if marca == "chevy" and modelo is None and anio is not None:
        modelo = "chevy"

    if marca in _ALIAS_MARCA:
        marca = _ALIAS_MARCA[marca]

    if marca is None and modelo is None and anio is None:
        return None

    return {"marca": marca, "modelo": modelo, "anio": anio}


def recordar_vehiculo(contexto, pregunta: str) -> bool:
    # Si la pregunta menciona un vehículo, se guarda en el contexto.
    #   - Si dicen marca o modelo, se reemplaza el vehículo completo
    #     ("Versa 2015" y luego "Toyota 2018" -> Toyota 2018, sin Versa).
    #   - Si solo dicen el año ("¿y del 2018?"), solo cambia el año.
    vehiculo = extraer_vehiculo_contexto(pregunta)

    if vehiculo is None or not hasattr(contexto, "modelo_vehiculo"):
        return False

    marca, modelo, anio = vehiculo["marca"], vehiculo["modelo"], vehiculo["anio"]
    marca_guardada = getattr(contexto, "marca_vehiculo", None)
    modelo_guardado = getattr(contexto, "modelo_vehiculo", None)

    # Solo la marca, sin modelo ni año ("¿y para un Toyota?"):
    # se guarda únicamente si es una marca distinta a la recordada.
    if modelo is None and anio is None:
        if marca and marca_guardada and normalizar(marca) != normalizar(marca_guardada):
            contexto.marca_vehiculo = marca
            contexto.modelo_vehiculo = None
            contexto.anio_vehiculo = None
            return True
        return False

    if marca or modelo:
        # Mismo modelo sin marca ("¿y versa 2018?"): se conserva la marca.
        if (
            marca is None
            and modelo
            and modelo_guardado
            and normalizar(modelo) == normalizar(modelo_guardado)
        ):
            marca = marca_guardada

        contexto.marca_vehiculo = marca
        contexto.modelo_vehiculo = modelo
        contexto.anio_vehiculo = anio
        return True

    # Solo el año: tiene sentido únicamente si ya hay un vehículo
    # recordado (evita que "ventas del 2025" se tome como vehículo).
    if modelo_guardado or marca_guardada:
        contexto.anio_vehiculo = anio
        return True

    return False


def describir_vehiculo_contexto(contexto) -> str | None:
    # Devuelve "Nissan Versa 2015" con lo que se recuerda, o None.
    partes = []
    marca = getattr(contexto, "marca_vehiculo", None)
    modelo = getattr(contexto, "modelo_vehiculo", None)
    anio = getattr(contexto, "anio_vehiculo", None)

    if marca and (not modelo or marca not in modelo):
        partes.append(str(marca))
    if modelo:
        partes.append(str(modelo))
    if anio:
        partes.append(str(anio))

    if not modelo and not anio:
        return None

    return " ".join(partes).title()


def actualizar_contexto_conversacion(contexto, pregunta: str) -> dict:
    # Se llama al inicio de cada pregunta.
    # Devuelve lo que pasó para que el servidor decida qué responder.
    resultado = {"cambio_tema": False, "solo_cambio_tema": False, "vehiculo": False}

    if detectar_cambio_tema(pregunta):
        limpiar_contexto(contexto)
        resultado["cambio_tema"] = True
        resultado["solo_cambio_tema"] = es_solo_cambio_tema(pregunta)

    if recordar_vehiculo(contexto, pregunta):
        resultado["vehiculo"] = True

    return resultado


# =====================================================================
# PRODUCTO SELECCIONADO
# =====================================================================

def seleccionar_producto_contextual(
    contexto: ContextoInventario,
    codigo: str,
    productos: list[dict]
) -> bool:
    # Selecciona un producto únicamente si su código
    # existe de forma única en el inventario actual.
    coincidencias = [
        producto
        for producto in productos
        if mismo_codigo(producto, codigo)
    ]

    if len(coincidencias) != 1:
        return False

    contexto.codigo_seleccionado = str(coincidencias[0]["codigo"])

    categoria = coincidencias[0].get("categoria")
    if categoria and hasattr(contexto, "categoria_consultada"):
        contexto.categoria_consultada = str(categoria)

    return True


def obtener_producto_seleccionado(
    contexto: ContextoInventario,
    productos: list[dict]
) -> dict | None:
    # Recupera el producto seleccionado utilizando el inventario actual.
    if not contexto.codigo_seleccionado:
        return None

    coincidencias = [
        producto
        for producto in productos
        if mismo_codigo(producto, contexto.codigo_seleccionado)
    ]

    if len(coincidencias) != 1:
        return None

    return coincidencias[0]


# =====================================================================
# PRODUCTOS MENCIONADOS EN UN TEXTO
# =====================================================================

def obtener_productos_mencionados(
    texto: str,
    productos: list[dict]
) -> list[dict]:
    # Obtiene productos cuyos códigos aparecen explícitamente
    # en el texto, conservando el orden de aparición.
    return codigos_mencionados(texto, productos)


# =====================================================================
# REFERENCIAS AL HISTORIAL ("ese producto", "el primero")
# =====================================================================

_ORDINALES = {
    "primer": 0, "primero": 0, "primera": 0,
    "segundo": 1, "segunda": 1,
    "tercer": 2, "tercero": 2, "tercera": 2,
    "cuarto": 3, "cuarta": 3,
    "quinto": 4, "quinta": 4,
    "sexto": 5, "sexta": 5,
    "septimo": 6, "septima": 6,
    "octavo": 7, "octava": 7,
    "noveno": 8, "novena": 8,
    "decimo": 9, "decima": 9,
}

# Frases donde un ordinal NO se refiere a una lista
# ("primer cambio de aceite", "primera vez", "segunda velocidad").
_ORDINAL_NO_LISTA = (
    r"\b(?:primer|primera|segunda|segundo|tercera|tercer|cuarta|quinta)\s+"
    r"(?:vez|veces|cambio|servicio|afinacion|mantenimiento|velocidad|"
    r"marcha|mano|dueno|lugar|paso|revision|ano|mes|semana|km|kilometro|"
    r"opcion de pago|generacion)\b"
)


# Señalan claramente al producto anterior ("ese producto", "su precio").
_REFERENCIAS_CLARAS = (
    "ese producto", "este producto", "esa pieza", "esta pieza",
    "esa refaccion", "esta refaccion", "el anterior", "del mismo",
    "cuanto cuesta ese", "cuanto cuesta este", "cuanto cuesta esa",
    "cuanto cuesta esta", "cuanto vale ese", "cuanto vale este",
    "su precio", "y su precio", "cual es su precio", "sumalo",
    "multiplicalo", "si lo vendo", "si la vendo", "de que marca es",
    "que marca es",
)

# Pueden referirse al producto anterior, pero también a uno nuevo
# ("¿cuánto cuesta el aceite Mobil?"). Solo se usan si la pregunta
# no nombra otra refacción.
_REFERENCIAS_GENERICAS = (
    "y ahora", "cuantos quedan", "cuantas quedan", "cuantos tengo",
    "cuantas tengo", "cuanto cuesta", "cuanto vale", "que precio tiene",
    "cuantas unidades quedan", "cuantas piezas quedan", "con iva",
    "y si vendo", "es universal", "es compatible", "le queda",
    "de que marca",
)

_PALABRAS_DE_PREGUNTA = {
    "cuanto", "cuantos", "cuantas", "cuesta", "vale", "precio", "tiene",
    "quedan", "tengo", "ahora", "vendo", "universal", "compatible",
    "queda", "marca", "unidades", "piezas", "pieza", "producto",
    "refaccion", "para", "con", "que", "cual", "esta", "este", "ese",
    "esa", "tambien", "todavia", "aun", "hay",
}


def _rol(mensaje) -> str:
    # El historial puede llegar como objetos (Pydantic) o diccionarios.
    if isinstance(mensaje, dict):
        return str(mensaje.get("rol") or mensaje.get("role") or "")
    return str(getattr(mensaje, "rol", None) or getattr(mensaje, "role", "") or "")


def _texto(mensaje) -> str:
    if isinstance(mensaje, dict):
        return str(mensaje.get("texto") or mensaje.get("content") or "")
    return str(getattr(mensaje, "texto", None) or getattr(mensaje, "content", "") or "")


# Nombres públicos para otros módulos.
rol_mensaje = _rol
texto_mensaje = _texto


def _nombra_otra_refaccion(texto: str, productos: list[dict]) -> bool:
    # True si la pregunta menciona palabras de algún producto del
    # inventario ("aceite", "mobil", "frenos"), o sea, habla de otra cosa.
    palabras = {
        p for p in re.findall(r"[a-z0-9]+", texto)
        if len(p) >= 4 and p not in _PALABRAS_DE_PREGUNTA
    }
    if not palabras:
        return False

    raices_pregunta = {_raiz(p) for p in palabras}
    for producto in productos:
        texto_producto = normalizar_contexto(
            f"{producto.get('nombre', '')} {producto.get('marca', '')} "
            f"{producto.get('categoria', '')}"
        )
        raices = {
            _raiz(p) for p in re.findall(r"[a-z0-9]+", texto_producto)
            if len(p) >= 4
        }
        if raices_pregunta & raices:
            return True
    return False


def resolver_producto_contextual(
    pregunta: str,
    historial: list,
    productos: list[dict],
):
    # Respaldo cuando WinUI no mandó contexto:
    # busca el producto en las últimas respuestas del asistente.
    texto = normalizar_contexto(pregunta)

    if re.search(_ORDINAL_NO_LISTA, texto):
        return None

    # Si la pregunta trae un código, ese manda.
    if obtener_productos_mencionados(pregunta, productos):
        return None

    ordinal = None

    for palabra, indice in _ORDINALES.items():
        if re.search(rf"\b{palabra}\b", texto):
            ordinal = indice
            break

    if re.search(r"\b(?:ultimo|ultima)\b", texto):
        ordinal = -1

    referencia_simple = any(e in texto for e in _REFERENCIAS_CLARAS) or (
        any(e in texto for e in _REFERENCIAS_GENERICAS)
        and not _nombra_otra_refaccion(texto, productos)
    )

    if ordinal is None and not referencia_simple:
        return None

    mensajes_recientes = list(historial or [])[-12:]

    # Si el vendedor cambió de tema, no recuperar productos viejos.
    for mensaje in reversed(mensajes_recientes):
        if _rol(mensaje) != "user":
            continue
        if detectar_cambio_tema(_texto(mensaje)):
            return None
        break

    if ordinal is not None:
        # "el primero", "el último": buscar una lista anterior.
        for mensaje in reversed(mensajes_recientes):
            if _rol(mensaje) == "user":
                continue

            mencionados = obtener_productos_mencionados(_texto(mensaje), productos)

            if len(mencionados) < 2:
                continue

            if ordinal == -1:
                return mencionados[-1]

            if ordinal < len(mencionados):
                return mencionados[ordinal]

        return None

    # Buscar únicamente la última respuesta del asistente.
    ultima_respuesta = next(
        (m for m in reversed(mensajes_recientes) if _rol(m) != "user"),
        None,
    )

    if ultima_respuesta is None:
        return None

    mencionados = obtener_productos_mencionados(_texto(ultima_respuesta), productos)

    # Solo recuperar el producto si hay exactamente uno.
    if len(mencionados) == 1:
        return mencionados[0]

    return None


# =====================================================================
# SEGUIMIENTO EN PREGUNTAS DE MECÁNICA
# =====================================================================

# Inicios típicos de una pregunta que continúa la anterior:
# "¿y si es un Versa 2015?", "¿y en carretera?", "¿pero es peligroso?"
_INICIO_SEGUIMIENTO = (
    r"^\W*(?:y|pero|entonces|tambien|o sea|osea|aunque|ademas|"
    r"que tal si|y que pasa si|y si|y en|y para|y con|y sin|"
    r"y cuando|y como|y cuanto|y por que|y porque|y que|y cual|y es|y se)\b"
)

# Palabras que señalan algo dicho antes: "eso", "esa falla", "lo mismo".
_REFERENCIA_ANTERIOR = (
    r"\b(?:eso|esa falla|ese ruido|ese problema|ese sintoma|esa pieza|"
    r"lo mismo|lo anterior|lo que dijiste|lo que me dijiste|esas|esos)\b"
)

MAX_PALABRAS_SEGUIMIENTO = 10


def _es_pregunta_de_seguimiento(texto_normalizado: str) -> bool:
    if len(texto_normalizado.strip(" ¿?¡!.,").split()) > MAX_PALABRAS_SEGUIMIENTO:
        return False
    return bool(
        re.search(_INICIO_SEGUIMIENTO, texto_normalizado)
        or re.search(_REFERENCIA_ANTERIOR, texto_normalizado)
    )


def detectar_seguimiento_mecanico(historial, pregunta: str, productos: list[dict]):
    # Si la pregunta actual continúa una pregunta de mecánica anterior,
    # devuelve (tema, respuesta_anterior). Si no, None.
    #
    # "tema" son las preguntas anteriores del vendedor que forman la
    # conversación, de la más vieja a la más reciente:
    #   "¿por qué rechinan las balatas?"  ->  "¿y si es un Versa 2015?"
    #   ->  "¿y es peligroso?"
    #   tema = "¿por qué rechinan las balatas? / ¿y si es un Versa 2015?"
    #
    # La respuesta anterior NO debe pasarse al modelo (un modelo pequeño
    # la copia); se devuelve solo para revisar que no fuera de inventario.
    texto = normalizar_contexto(pregunta)

    if not _es_pregunta_de_seguimiento(texto) or detectar_cambio_tema(texto):
        return None

    mensajes = list(historial or [])

    # El historial puede traer la pregunta actual al final.
    if mensajes and _rol(mensajes[-1]) == "user" and normalizar_contexto(
        _texto(mensajes[-1])
    ) == texto:
        mensajes = mensajes[:-1]

    preguntas: list[str] = []
    respuesta_anterior = None

    for mensaje in reversed(mensajes):
        if _rol(mensaje) != "user":
            if respuesta_anterior is None:
                respuesta_anterior = _texto(mensaje).strip()
            continue

        anterior = _texto(mensaje).strip()
        if not anterior or detectar_cambio_tema(anterior):
            break

        preguntas.insert(0, anterior)

        # Se sigue hacia atrás solo mientras también sean seguimientos,
        # hasta llegar a la pregunta que abrió el tema.
        if (
            not _es_pregunta_de_seguimiento(normalizar_contexto(anterior))
            or len(preguntas) >= 3
        ):
            break

    if not preguntas or not respuesta_anterior:
        return None

    # Si lo anterior fue de inventario (códigos, precios, listas),
    # no es un seguimiento de mecánica.
    if (
        obtener_productos_mencionados(respuesta_anterior, productos)
        or "$" in respuesta_anterior
        or "compatibilidad registrada" in normalizar_contexto(respuesta_anterior)
    ):
        return None

    return " / ".join(preguntas), respuesta_anterior


def resolver_seleccion_por_nombre(
    pregunta: str,
    contexto: ContextoInventario,
    productos: list[dict],
) -> dict | None:
    # Identifica una refacción por su nombre dentro de la lista
    # mostrada ("el de Mobil", "las balatas", "el filtro").
    # Solo selecciona si existe una coincidencia única.
    texto = normalizar_contexto(pregunta)

    palabras_ignoradas = {
        "el", "la", "los", "las", "un", "una", "de", "del", "para",
        "por", "favor", "producto", "refaccion", "quiero", "ese", "esa",
        "cuanto", "cuantos", "cuantas", "cuesta", "vale", "precio",
        "tiene", "tenemos", "quedan", "disponibles", "hay", "dame",
        "dime", "pasame", "cual", "este", "esta", "piezas", "pieza",
        "sumalo", "vendo", "todo", "todos", "como", "sobre", "info",
    }

    palabras_pregunta = {
        palabra
        for palabra in re.findall(r"\b\w+\b", texto)
        if palabra not in palabras_ignoradas and len(palabra) >= 4
    }

    if not palabras_pregunta:
        return None

    codigos_permitidos = {
        str(codigo).casefold()
        for codigo in contexto.codigos_lista
    }

    raices_pregunta = {_raiz(p) for p in palabras_pregunta}

    coincidencias = []

    for producto in productos:
        codigo = str(producto.get("codigo", "")).strip()

        if codigo.casefold() not in codigos_permitidos:
            continue

        # Se compara con el nombre y también con la marca.
        texto_producto = normalizar_contexto(
            f"{producto.get('nombre', '')} {producto.get('marca', '')}"
        )

        raices_producto = {
            _raiz(p) for p in re.findall(r"\b\w+\b", texto_producto)
            if len(p) >= 4
        }

        if raices_pregunta & raices_producto:
            coincidencias.append(producto)

    # Nunca seleccionar arbitrariamente entre varios.
    if len(coincidencias) != 1:
        return None

    return coincidencias[0]


def resolver_posicion_lista(
    pregunta: str,
    contexto: ContextoInventario,
    productos: list[dict],
) -> tuple[str, dict | None]:
    # Resuelve "el segundo", "el producto 3", "el número 4",
    # "el último" usando la lista que se mostró.
    #
    # Estados posibles:
    #   "sin_referencia"     -> la pregunta no habla de una posición.
    #   "sin_lista"          -> habla de una posición, pero no hay lista.
    #   "fuera_de_rango"     -> la posición no existe en la lista.
    #   "producto_eliminado" -> el producto ya no está en el inventario.
    #   "encontrado"         -> se encontró el producto.
    texto = normalizar_contexto(pregunta)

    # Frases como "el primer cambio de aceite" no son posiciones.
    if re.search(_ORDINAL_NO_LISTA, texto):
        return "sin_referencia", None

    posicion = None
    es_explicita = False     # "producto 3", "de la lista", "opción 2"
    relativa_a_pagina = False

    menciona_lista = re.search(
        r"\b(?:producto|productos|refaccion|refacciones|articulo|opcion|"
        r"lista|listado|resultado|de esos|de estos|de esas|de estas|"
        r"de ahi|de arriba)\b",
        texto,
    ) is not None

    # 1. Ordinales con palabra: "el segundo", "la tercera".
    coincidencia = re.search(
        r"\b(" + "|".join(re.escape(p) for p in _ORDINALES) + r")\b",
        texto,
    )

    if coincidencia is not None:
        posicion = _ORDINALES[coincidencia.group(1)]
        relativa_a_pagina = True
        es_explicita = menciona_lista

    # 2. "el último", "la última".
    elif re.search(r"\b(?:el|la)\s+(?:ultimo|ultima)\b", texto):
        if not contexto.codigos_lista:
            return ("sin_lista", None) if menciona_lista else ("sin_referencia", None)
        inicio_pagina = (max(1, contexto.pagina_actual) - 1) * PRODUCTOS_POR_PAGINA
        fin_pagina = min(len(contexto.codigos_lista), inicio_pagina + PRODUCTOS_POR_PAGINA)
        posicion = max(inicio_pagina, fin_pagina - 1)
        es_explicita = True

    # 3. Números: "producto 3", "el número 2", "opción 4", "el #5".
    if posicion is None:
        coincidencia_numero = re.search(
            r"\b(?:producto|refaccion|articulo|opcion|numero|num|nro)"
            r"\s*(?:numero|num|nro|n)?\s*[#°º.]?\s*(\d{1,3})\b(?!\s*%)",
            texto,
        )

        if coincidencia_numero is not None:
            es_explicita = True
        elif re.search(r"\b(?:descuento|rebaja|rebajita|porcentaje|por ciento)\b|%", texto):
            # "rebaja del 15", "descuento del 10": es un porcentaje.
            coincidencia_numero = None
        else:
            # "el 3", "la 2", "del 4": solo si hay lista y el número
            # es pequeño (no un año, porcentaje, kilometraje o cantidad).
            coincidencia_numero = re.search(
                r"\b(?:el|la|del|al)\s+#?(\d{1,2})"
                r"(?:\s*(?:er|ro|do|to|vo|mo|°|º))?\b"
                r"(?!\s*(?:%|por ?ciento|km|kilometros|mil|pesos|piezas|"
                r"unidades|litros|anos|w|de |x|\.\d|,\d))",
                texto,
            )

        if coincidencia_numero is not None:
            numero = int(coincidencia_numero.group(1))

            if numero < 1:
                return ("fuera_de_rango", None) if contexto.codigos_lista else ("sin_referencia", None)

            posicion = numero - 1

    # 4. No se mencionó ninguna posición.
    if posicion is None:
        return "sin_referencia", None

    # 5. No hay lista: solo se avisa si la referencia era clara.
    if not contexto.codigos_lista:
        return ("sin_lista", None) if es_explicita else ("sin_referencia", None)


    # 6. Verificar que la posición esté dentro de la lista.
    if posicion >= len(contexto.codigos_lista):
        return ("fuera_de_rango", None) if es_explicita or relativa_a_pagina else ("sin_referencia", None)

    # 7. Obtener el producto con el inventario actual.
    codigo = contexto.codigos_lista[posicion]

    producto = next(
        (
            p for p in productos
            if mismo_codigo(p, codigo)
        ),
        None,
    )

    if producto is None:
        return "producto_eliminado", None

    return "encontrado", producto

