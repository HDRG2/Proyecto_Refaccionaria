import re
import unicodedata
from dataclasses import dataclass, field

@dataclass
class ContextoInventario:
    
    #Guarda referencias a productos mediante sus códigos.
    #No almacena precios ni existencias para evitar
    #utilizar información desactualizada.
    
    codigo_seleccionado: str | None = None
    codigos_lista: list[str] = field(default_factory=list)
    
    # Con este atributo podremos recordar la página que está viendo el vendedor
    pagina_actual: int = 1
    
    #Contexto para recomendaciones de refaccionaria.
    categoria_consultada: str | None = None
    marca_vehiculo: str | None = None
    modelo_vehiculo: str | None = None
    anio_vehiculo: int | None = None

def crear_contexto_desde_productos(
    productos: list[dict]
) -> ContextoInventario:
    
    #Construye una lista ordenada de códigos de producto.
    

    codigos = []

    for producto in productos:
        codigo = str(producto.get("codigo", "")).strip()

        if codigo and codigo not in codigos:
            codigos.append(codigo)

    return ContextoInventario(
        codigo_seleccionado=None,
        codigos_lista=codigos
    )


def seleccionar_producto_contextual(
    contexto: ContextoInventario,
    codigo: str,
    productos: list[dict]
) -> bool:
    
    #Selecciona un producto únicamente si su código
    #existe de forma única en el inventario actual.
    

    coincidencias = [
        producto
        for producto in productos
        if str(producto.get("codigo", "")).strip().casefold()
        == codigo.strip().casefold()
    ]

    if len(coincidencias) != 1:
        return False

    contexto.codigo_seleccionado = str(
        coincidencias[0]["codigo"]
    )

    return True


def obtener_producto_seleccionado(
    contexto: ContextoInventario,
    productos: list[dict]
) -> dict | None:
    
    #Recupera el producto seleccionado utilizando
    #el inventario actual.
    

    if contexto.codigo_seleccionado is None:
        return None

    coincidencias = [
        producto
        for producto in productos
        if str(producto.get("codigo", "")).strip().casefold()
        == contexto.codigo_seleccionado.casefold()
    ]

    if len(coincidencias) != 1:
        return None

    return coincidencias[0]



def normalizar_contexto(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )
    return " ".join(texto.casefold().split())


def obtener_productos_mencionados(
    texto: str,
    productos: list[dict]
) -> list[dict]:
    
    #Obtiene productos cuyos códigos aparecen explícitamente
    #en el texto, conservando el orden de aparición.
    
    encontrados = []

    for producto in productos:
        codigo = str(producto.get("codigo", "")).strip()

        if not codigo:
            continue

        coincidencia = re.search(
            rf"(?<![\w-]){re.escape(codigo)}(?![\w-])",
            texto,
            re.IGNORECASE,
        )

        if coincidencia:
            encontrados.append(
                (coincidencia.start(), producto)
            )

    encontrados.sort(key=lambda item: item[0])

    return [producto for _, producto in encontrados]


def resolver_producto_contextual(
    pregunta: str,
    historial: list,
    productos: list[dict],
):

    texto = normalizar_contexto(pregunta)

    referencias_ordinales = {
        "primer": 0,
        "primero": 0,
        "primera": 0,
        "segundo": 1,
        "segunda": 1,
        "tercer": 2,
        "tercero": 2,
        "tercera": 2,
        "cuarto": 3,
        "cuarta": 3,
        "quinto": 4,
        "quinta": 4,
    }

    ordinal = None

    for palabra, indice in referencias_ordinales.items():
        if re.search(rf"\b{palabra}\b", texto):
            ordinal = indice
            break

    
    referencia_simple = any(
        expresion in texto
        for expresion in (
            "ese producto",
            "este producto",
            "el anterior",
            "del mismo",
            "y ahora",
            "cuantos quedan",
            "cuantas quedan",
            "cuantos tengo",
            "cuantas tengo",
            "cuanto cuesta ese",
            "cuanto cuesta este",
            "cuanto vale ese",
            "cuanto vale este",
            "su precio",
            "y su precio",
            "cuanto cuesta",
            "cuanto vale",
            "que precio tiene",
            "cual es su precio",
            "cuantas unidades quedan",
            "cuantas piezas quedan",
        )
    )

    if ordinal is None and not referencia_simple:
        return None

    # Analizar únicamente los mensajes recientes.
    mensajes_recientes = historial[-12:]
    
    for mensaje in reversed(mensajes_recientes):
        if mensaje.rol != "user":
            continue
        texto_anterior = normalizar_contexto(mensaje.texto)
        
        if any(
            expresion in texto_anterior
            for expresion in (
                "cambiemos de tema",
                "otra pregunta",
                "olvida lo anterior"
                
            )
        ):
            return None   
        
        break
        
    if ordinal is not None:
        # Para "el primero", "el segundo", etc.,
        # buscar una lista anterior de varios productos.
        for mensaje in reversed(mensajes_recientes):
            if mensaje.rol != "model":
                continue

            mencionados = obtener_productos_mencionados(
                mensaje.texto,
                productos,
            )

            if len(mencionados) < 2:
                continue

            if ordinal < len(mencionados):
                return mencionados[ordinal]

        return None

    # Buscar únicamente la última respuesta del asistente.
    # No saltar a respuestas más antiguas, porque podrían
    # referirse a otro producto.

    ultima_respuesta = next(
        (
            mensaje
            for mensaje in reversed(mensajes_recientes)
            if mensaje.rol == "model"
        ),
        None,
    )

    if ultima_respuesta is None:
        return None

    mencionados = obtener_productos_mencionados(
        ultima_respuesta.texto,
        productos,
    )

    # Solo recuperar el producto si hay exactamente uno.
    if len(mencionados) == 1:
        return mencionados[0]

    # Si no hay productos o hay varios, pedir aclaración.
    return None


def resolver_seleccion_por_nombre(
    pregunta: str,
    contexto: ContextoInventario,
    productos: list[dict],
) -> dict | None:
  
    #Identifica una refacción por su nombre dentro
    #de los productos mencionados en la conversación.

    #Solo selecciona si existe una coincidencia única.
    
    texto = normalizar_contexto(pregunta)

    palabras_ignoradas = {
        "el", "la", "los", "las",
        "un", "una", "de", "del",
        "para", "por", "favor",
        "producto", "refaccion",
        "quiero", "ese", "esa",
        "cuanto", "cuantos", "cuantas",
        "cuesta", "vale", "precio",
        "tiene", "tenemos", "quedan",
        "disponibles", "hay",
    }

    palabras_pregunta = {
        palabra
        for palabra in re.findall(r"\b\w+\b", texto)
        if palabra not in palabras_ignoradas
        and len(palabra) >= 4
    }

    if not palabras_pregunta:
        return None

    codigos_permitidos = {
        codigo.casefold()
        for codigo in contexto.codigos_lista
    }

    coincidencias = []

    for producto in productos:
        codigo = str(producto.get("codigo", "")).strip()

        if codigo.casefold() not in codigos_permitidos:
            continue

        nombre = normalizar_contexto(
            str(producto.get("nombre", ""))
        )

        palabras_nombre = set(
            re.findall(r"\b\w+\b", nombre)
        )

        if palabras_pregunta & palabras_nombre:
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
    import re
    import unicodedata

    def limpiar(texto: str) -> str:
        texto = texto.casefold()
        texto = "".join(
            caracter
            for caracter in unicodedata.normalize("NFD", texto)
            if unicodedata.category(caracter) != "Mn"
        )
        return texto

    ordinales = {
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

    texto = limpiar(pregunta)

    # 1. Buscar referencias escritas con palabras.
    coincidencia = re.search(
        r"\b(" + "|".join(
            re.escape(palabra) for palabra in ordinales
        ) + r")\b",
        texto,
    )

    posicion = None

    if coincidencia is not None:
        posicion = ordinales[coincidencia.group(1)]

    # 2. Buscar referencias numéricas.
    if posicion is None:
        coincidencia_numero = re.search(
            r"\b(?:producto|refaccion|articulo|numero|num|nro|n)"
            r"\s*(?:numero|num|nro|n)?\s*[#°º.]?\s*(\d+)\b",
            texto,
        )

        if coincidencia_numero is None:
            coincidencia_numero = re.search(
                r"\b(?:el|la|del|al)\s+(\d+)"
                r"(?:\s*(?:er|ro|do|to|vo|mo))?\b",
                texto,
            )

        if coincidencia_numero is not None:
            numero = int(coincidencia_numero.group(1))

            if numero < 1:
                return "fuera_de_rango", None

            posicion = numero - 1

    # 3. Si no se mencionó ninguna posición.
    if posicion is None:
        return "sin_referencia", None

    # 4. Verificar que exista una lista anterior.
    if not contexto.codigos_lista:
        return "sin_lista", None

    # 5. Verificar que la posición esté dentro de la lista.
    if posicion >= len(contexto.codigos_lista):
        return "fuera_de_rango", None

    # 6. Obtener el código del producto solicitado.
    codigo = contexto.codigos_lista[posicion]

    producto = next(
        (
            p for p in productos
            if str(p.get("codigo", "")).strip().casefold()
            == str(codigo).strip().casefold()
        ),
        None,
    )

    if producto is None:
        return "producto_eliminado", None

    return "encontrado", producto

