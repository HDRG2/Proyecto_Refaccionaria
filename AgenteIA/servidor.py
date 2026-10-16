import json
import re
import time
import asyncio
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient
from AgenteIA.herramientas_inventario import (
    crear_herramientas_inventario,
)
from AgenteIA.validador_inventario import (
    cargar_inventario,
    responder_existencia,
    responder_precio,
    responder_compatibilidad,
)
from AgenteIA.contexto_inventario import (
    ContextoInventario,
    resolver_producto_contextual,
    obtener_producto_seleccionado,
    seleccionar_producto_contextual,
    resolver_seleccion_por_nombre,
    obtener_productos_mencionados,
    resolver_posicion_lista,
)

from AgenteIA.consultas_inteligentes import consultar_inventario_inteligente

@asynccontextmanager
async def ciclo_vida(app: FastAPI):
    async def preparar_qwen():
        try:
            async with httpx.AsyncClient(timeout=120.0) as cliente:
                respuesta = await cliente.post(
                    "http://127.0.0.1:11434/api/generate",
                    json={
                        "model": "qwen2.5:3b",
                        "keep_alive": "30m",
                    },
                )
                respuesta.raise_for_status()

            print(
                "[OLLAMA] Qwen cargado con permanencia de 30 minutos.",
                flush=True,
            )

        except Exception as error:
            print(
                f"[OLLAMA] No se pudo preparar Qwen: {error}",
                flush=True,
            )

    tarea_preparacion = asyncio.create_task(preparar_qwen())

    try:
        yield
    finally:
        if not tarea_preparacion.done():
            tarea_preparacion.cancel()
            try:
                await tarea_preparacion
            except asyncio.CancelledError:
                pass


app = FastAPI(
    title="El Pistón - IA Local",
    lifespan=ciclo_vida,
)


class MensajeHistorial(BaseModel):
    rol: str
    texto: str


class EstadoContexto(BaseModel):
    codigo_seleccionado: str | None = None
    codigos_lista: list[str] = Field(default_factory=list)



class Consulta(BaseModel):
    pregunta: str = Field(min_length=1, max_length=2000)
    inventario: str = Field(default="[]", max_length=150000)
    historial: list[MensajeHistorial] = Field(default_factory=list)
    
    contexto: EstadoContexto = Field(
        default_factory=EstadoContexto
    )


@app.get("/salud")
async def salud():
    return {
        "estado": "activo",
        "modelo": "qwen2.5:3b",
        "validador": "habilitado",
    }


def normalizar(texto: str) -> str:
    return " ".join(texto.casefold().split())


def identificar_producto(pregunta: str, productos: list[dict]):
    
    #Identifica un producto mediante su código completo
    #o su nombre completo.

    pregunta_normalizada = normalizar(pregunta)

    # Prioridad 1: código exacto
    encontrados_codigo = []

    for producto in productos:
        codigo = str(producto.get("codigo", "")).strip()

        if not codigo:
            continue

        patron = (
            r"(?<!\w)"
            + re.escape(codigo)
            + r"(?!\w)"
        )

        if re.search(patron, pregunta, re.IGNORECASE):
            encontrados_codigo.append(producto)

    if len(encontrados_codigo) == 1:
        return encontrados_codigo[0]

    if len(encontrados_codigo) > 1:
        return None

    # Prioridad 2: nombre completo
    encontrados_nombre = [
        producto
        for producto in productos
        if normalizar(str(producto.get("nombre", "")))
        and normalizar(str(producto.get("nombre", "")))
        in pregunta_normalizada
    ]

    if len(encontrados_nombre) == 1:
        return encontrados_nombre[0]

    return None


def detectar_intencion(pregunta: str):
    texto = normalizar(pregunta)

    palabras_existencia = (
        "existencia",
        "existencias",
        "stock",
        "unidades",
        "piezas",
        "disponibles",
        "cuántos",
        "cuántas",
        "cuantos",
        "cuantas",
        "cuántas quedan",
        "cuantos quedan",
    )

    palabras_precio = (
        "precio",
        "cuesta",
        "cuestan",
        "vale",
        "valen",
        "costo",
    )

    palabras_compatibilidad = (
        "compatible",
        "compatibilidad",
        "le queda",
        "le sirve",
        "funciona para",
    )

    if any(palabra in texto for palabra in palabras_compatibilidad):
        return "compatibilidad"

    if any(palabra in texto for palabra in palabras_precio):
        return "precio"

    if any(palabra in texto for palabra in palabras_existencia):
        return "existencia"

    return None


def extraer_vehiculo(pregunta: str):

    #Extrae un vehículo después de expresiones comunes.
    #No supone que cualquier texto sea un vehículo válido.
   
    patron = (
        r"\b(?:con|para)\s+"
        r"(?:un|una|el|la)?\s*"
        r"([A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 -]+?"
        r"\s+(?:19|20)\d{2})\b"
    )

    coincidencia = re.search(
        patron,
        pregunta,
        re.IGNORECASE,
    )

    if coincidencia:
        return coincidencia.group(1).strip()

    return None

def crear_respuesta_con_contexto(
    respuesta: str,
    contexto: ContextoInventario,
    producto: dict | None = None,
) -> dict:

    if producto is not None:
        contexto.codigo_seleccionado = str(
            producto.get("codigo", "")
        ).strip() or None

    return {
        "respuesta": respuesta,
        "contexto": {
            "codigo_seleccionado": contexto.codigo_seleccionado,
            "codigos_lista": contexto.codigos_lista,
        },
    }

@app.post("/consultar")
async def consultar(datos: Consulta):
    
    inicio_consulta = time.perf_counter()

    # 1. Validar el inventario recibido desde WinUI 3
    try:
        productos_actuales = cargar_inventario(
            datos.inventario
        )
    except (ValueError, TypeError) as error:
        raise HTTPException(
            status_code=400,
            detail="El inventario recibido no es válido.",
        ) from error
    
        # Consultas inteligentes del inventario.
    respuesta_inteligente = consultar_inventario_inteligente(
        datos.pregunta,
        productos_actuales
    )

    if respuesta_inteligente is not None:
        productos_en_respuesta = obtener_productos_mencionados(
            respuesta_inteligente,
            productos_actuales,
        )
        
        print(
            "[CONSULTA INTELIGENTE] Respuesta verificada",
            flush=True,
        )

        return {
        "respuesta": respuesta_inteligente,
            "contexto": {
                "codigo_seleccionado": None,
                "codigos_lista": [
                    str(p["codigo"])
                    for p in productos_en_respuesta
                ],
            },
        }
        
    pregunta_normalizada = normalizar(datos.pregunta)

    consultas_lista = (
        "productos activos",
        "refacciones activas",
        "listar productos",
        "lista de productos",
        "productos disponibles",
        "productos tenemos disponibles",
        "qué productos tenemos",
        "que productos tenemos",
        "qué refacciones tenemos",
        "que refacciones tenemos",
        "mostrar productos",
        "muéstrame los productos",
        "muestrame los productos",
    )

    if any(
        expresion in pregunta_normalizada
        for expresion in consultas_lista
    ):
        if not productos_actuales:
            return {
                "respuesta": (
                    "Actualmente no hay productos activos "
                    "registrados en El Pistón."
                )
            }

        lineas = [
            "Estos son los productos activos de El Pistón:"
        ]

        for indice, producto_lista in enumerate(
            productos_actuales,
            start=1,
        ):
            nombre = producto_lista.get("nombre", "Sin nombre")
            codigo = producto_lista.get("codigo", "Sin código")

            lineas.append(
                f"{indice}. {nombre} ({codigo})"
            )

        lineas.append(
            f"\nTotal: {len(productos_actuales)} productos activos."
        )

        print(
            "[VALIDADOR] Lista de productos activos generada",
            flush=True,
        )

        return {
            "respuesta": "\n".join(lineas),
            "contexto":{
                "codigo_seleccionado": None,
                "codigos_lista": [
                    str(p["codigo"])
                    for p in productos_actuales
                ]
            }
        }

    # 2. Identificar producto e intención
    producto = identificar_producto(
        datos.pregunta,
        productos_actuales,
    )

    intencion = detectar_intencion(datos.pregunta)
    
    # Reconstruir el contexto recibido desde WinUI
    
    contexto = ContextoInventario(
        codigo_seleccionado=datos.contexto.codigo_seleccionado,
        codigos_lista=list(datos.contexto.codigos_lista),
    )
    
    if not contexto.codigos_lista:
        solicitudes_lista = (
            "productos activos",
            "refacciones activas",
            "listar productos",
            "lista de productos",
            "productos disponibles",
        )

        historial_solicito_lista = any(
            mensaje.rol == "user"
            and any(
                expresion in normalizar(mensaje.texto)
                for expresion in solicitudes_lista
            )
            for mensaje in datos.historial
        )

        if historial_solicito_lista:
            contexto.codigos_lista = [
                str(p["codigo"])
                for p in productos_actuales
            ]

            print(
                "[CONTEXTO] Lista recuperada del inventario",
                contexto.codigos_lista,
                flush=True,
            )
    
    print(
        "[DEBUG CONTEXTO RECIBIDO]",
        contexto.codigos_lista,
        flush=True,
    )
    
     # Resolver referencias ordinales de forma segura.
        # Resolver posiciones utilizando la función probada.
    estado_posicion, producto_posicion = resolver_posicion_lista(
        datos.pregunta,
        contexto,
        productos_actuales,
    )

    # Se mencionó una posición, pero todavía no hay lista.
    if estado_posicion == "sin_lista":
        return crear_respuesta_con_contexto(
            "Todavía no hemos consultado una lista de productos. "
            "Solicita la lista de productos activos para poder "
            "identificarlos por su posición.",
            contexto,
        )

    # La posición solicitada no existe.
    if estado_posicion == "fuera_de_rango":
        return crear_respuesta_con_contexto(
            "No existe un producto en esa posición. "
            f"La lista consultada contiene "
            f"{len(contexto.codigos_lista)} productos.",
            contexto,
        )

    # El producto ya no existe en el inventario actualizado.
    if estado_posicion == "producto_eliminado":
        return crear_respuesta_con_contexto(
            "El producto de esa posición ya no está "
            "disponible en el inventario actual.",
            contexto,
        )

    # Se encontró correctamente el producto solicitado.
    if estado_posicion == "encontrado":
        producto = producto_posicion
        
    # Identificar una refacción mencionada por nombre
    # dentro de la lista contextual.
    if producto is None:
        producto_por_nombre = resolver_seleccion_por_nombre(
            datos.pregunta,
            contexto,
            productos_actuales,
        )

        if producto_por_nombre is not None:
            producto = producto_por_nombre

            seleccionar_producto_contextual(
                contexto,
                str(producto["codigo"]),
                productos_actuales,
            )

            print(
                "[CONTEXTO] Refacción seleccionada por nombre: "
                f"{producto.get('codigo')}",
                flush=True,
            )

    # Intentar recuperar el producto mencionado
    # anteriormente cuando no aparece explícitamente.
    if producto is None and intencion in(
        "precio",
        "existencia",
        "compatibilidad",  
    ):
        producto = obtener_producto_seleccionado(
            contexto,
            productos_actuales,
        )
        
        if producto is not None:
            print(
                "[CONTEXTO ESTRUCTURADO] Producto: "
                f"{producto.get('codigo')}",
                flush=True,
            )
            
    # 3. Respuestas exactas, sin intervención de Qwen

    # Evitar consultas ambiguas de inventario.
    if producto is None and intencion in (
        "existencia",
        "precio",
        "compatibilidad",
    ):
        print(
            f"[SEGURIDAD] Consulta ambigua: {datos.pregunta}",
            flush=True,
        )

        return {
            "respuesta": (
                "No pude identificar con seguridad la refacción. "
                "Indícame su nombre o código, por ejemplo ACE-001."
            )
        }

    # Consulta las existencias.
    if producto is not None and intencion == "existencia":
        respuesta = responder_existencia(producto)

        print(
            "[VALIDADOR] Existencia verificada: "
            f"{producto.get('codigo')}",
            flush=True,
        )

        return crear_respuesta_con_contexto(
            respuesta,
            contexto,
            producto,
        )

    # Consulta los precios.
    
    if producto is not None and intencion == "precio":

        # Detectar si también se solicitan existencias.
        pregunta_normalizada = normalizar(datos.pregunta)

        solicita_existencias = any(
            expresion in pregunta_normalizada
            for expresion in (
                "cuantas piezas",
                "cuantos productos",
                "cuantas unidades",
                "cuantos quedan",
                "cuantas quedan",
                "cuantos hay",
                "existencias",
                "existencia",
                "stock",
                "disponibles",
                "disponibilidad",
            )
        )

        # Consultar siempre el precio real.
        respuesta = responder_precio(producto)

        if solicita_existencias:
            existencia = producto.get("existencia")

            try:
                cantidad = int(existencia)

                respuesta += (
                    f"\nExistencias disponibles: "
                    f"{cantidad} piezas."
                )

            except (ValueError, TypeError):
                respuesta += (
                    "\nNo se pudo verificar la cantidad "
                    "disponible de este producto."
                )

            print(
                "[VALIDADOR] Precio y existencias verificados: "
                f"{producto.get('codigo')}",
                flush=True,
            )

        else:
            print(
                "[VALIDADOR] Precio verificado: "
                f"{producto.get('codigo')}",
                flush=True,
            )

        return crear_respuesta_con_contexto(
            respuesta,
            contexto,
            producto,
        )

    # Consulta la compatibilidad.
    if producto is not None and intencion == "compatibilidad":
        vehiculo = extraer_vehiculo(datos.pregunta)

        if vehiculo is None:
            return {
                "respuesta": (
                    "Indícame la marca, modelo y año del vehículo. "
                    "Por ejemplo: Toyota Corolla 2016."
                )
            }

        respuesta = responder_compatibilidad(
            producto,
            vehiculo,
        )

        print(
            "[VALIDADOR] Compatibilidad consultada: "
            f"{producto.get('codigo')} con {vehiculo}",
            flush=True,
        )

        return crear_respuesta_con_contexto(
            respuesta,
            contexto,
            producto,
        )

    # 4. Consultas que requieren comprensión de lenguaje
    modelo = OllamaChatCompletionClient(
        model="qwen2.5:3b",
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": False,
            "family": "unknown",
            "structured_output": False,
        },
    )

    try:
        consultar_producto, listar_productos_activos = (
            crear_herramientas_inventario(
                datos.inventario
            )
        )

        agente = AssistantAgent(
            name="AsistenteElPiston",
            model_client=modelo,
            tools=[
                consultar_producto,
                listar_productos_activos,
            ],
            reflect_on_tool_use=True,
            system_message=(
                "Eres el asistente virtual de El Pistón, "
                "una refaccionaria automotriz. "
                "Responde siempre en español de México. "
                "Responde únicamente a la pregunta actual del vendedor. "
                "No agregues información sobre temas que no preguntó. "
                "Para preguntas generales de mecánica, responde de forma "
                "clara y precisa, utilizando normalmente de 1 a 3 oraciones. "
                "Evita explicaciones extensas cuando una respuesta breve "
                "sea suficiente. "
                "No menciones aceites, compatibilidades, inventario ni "
                "vehículos específicos a menos que sean relevantes "
                "para la pregunta actual. "
                "No inventes ejemplos de vehículos ni recomendaciones "
                "que el vendedor no haya solicitado. "
                "Para preguntas sobre inventario, utiliza "
                "las herramientas disponibles. "
                "Nunca inventes precios, existencias "
                "ni compatibilidades. "
                "Los datos actuales del inventario tienen "
                "prioridad sobre el historial. "
                "Si no puedes identificar un producto "
                "con seguridad, solicita su código. "
                "Si no puedes confirmar una compatibilidad, "
                "indica que no está registrada. "

                "IMPORTANTE SOBRE RECOMENDACIONES AUTOMOTRICES: "
                "No recomiendes aceites, filtros, bujías, frenos "
                "ni otras refacciones para un vehículo específico "
                "sin comprobar las especificaciones necesarias. "

                "Que un producto esté marcado como universal "
                "NO demuestra que sea adecuado para cualquier vehículo. "

                "Si el usuario pregunta qué aceite necesita "
                "o cuál le recomiendas para un automóvil, "
                "solicita la motorización o versión cuando sea necesaria "
                "y aclara que debe verificarse la especificación "
                "del fabricante antes de recomendar un producto. "

                "No inventes viscosidades, especificaciones técnicas "
                "ni compatibilidades. "

                "Para preguntas generales de mecánica "
                "puedes utilizar tus conocimientos, "
                "pero distingue la orientación general "
                "de la compatibilidad confirmada. "

                "PRECISIÓN TÉCNICA AUTOMOTRIZ: "
                "Identifica correctamente cada componente automotriz "
                "y explica únicamente su función comprobable. "
                "No confundas componentes distintos aunque tengan "
                "nombres parecidos o trabajen en sistemas relacionados. "
                "Distingue entre el sistema de lubricación, refrigeración, "
                "combustible, encendido, frenos y sistema eléctrico. "
                "No inventes características, procedimientos, especificaciones "
                "ni relaciones técnicas entre componentes. "
                "Si una respuesta depende del modelo, año, motorización "
                "o versión del vehículo, solicita los datos necesarios. "
                "Si no tienes suficiente certeza técnica, indícalo "
                "claramente en lugar de inventar una explicación. "
                "Para preguntas sencillas, explica primero la función "
                "principal del componente en 1 a 3 oraciones. "
                "Evita información adicional que no sea necesaria. "
            ),
        )

        conversacion = "\n".join(
            (
                f"{'Vendedor' if m.rol == 'user' else 'Asistente'}: "
                f"{m.texto}"
            )
            for m in datos.historial[-20:]
            if m.rol in ("user", "model")
        )

        tarea = (
            "REGLAS:\n"
            "El inventario actual es la fuente válida "
            "para existencias, precios y compatibilidades.\n"
            "El historial sirve para comprender referencias, "
            "no para obtener cantidades anteriores.\n\n"

            "HISTORIAL:\n"
            f"{conversacion or 'Sin historial.'}\n\n"

            
            "INVENTARIO ACTUAL:\n"
            "El inventario está disponible mediante las herramientas "
            "del asistente. Consulta esas herramientas cuando necesites "
            "verificar productos, precios, existencias o compatibilidades.\n\n"

            "PREGUNTA DEL VENDEDOR:\n"
            f"{datos.pregunta}\n\n"

            "Si necesitas datos del inventario, "
            "consulta las herramientas antes de responder."
        )

        inicio_qwen = time.perf_counter()
        
        resultado = await agente.run(task=tarea)

        tiempo_qwen = time.perf_counter() - inicio_qwen
        
        print(
            f"[RENDIMIENTO] Qwen respondió en "
            f"{tiempo_qwen:.2f} segundos",
            flush=True,
        )
        
        tiempo_total = time.perf_counter() - inicio_consulta
        
        print(
            f"[RENDIMIENTO] Preparación previa a Qwen: "
            f"{tiempo_total - tiempo_qwen:.2f} segundos",
            flush=True,
        )
        
        respuesta = str(
            resultado.messages[-1].content
        ).strip()

        if not respuesta:
            raise ValueError(
                "AutoGen no devolvió una respuesta."
            )
        

         # Conservar el contexto cuando Ollama genera una lista.
        pregunta_lista = normalizar(datos.pregunta)

        expresiones_lista = (
            "lista de",
            "listame",
            "listar",
            "muestrame los productos",
            "muéstrame los productos",
            "que productos tenemos",
            "qué productos tenemos",
            "productos que tenemos",
            "refacciones que tenemos",
        )

        if any(
            expresion in pregunta_lista
            for expresion in expresiones_lista
        ):
            contexto.codigos_lista = [
                str(p["codigo"])
                for p in productos_actuales
            ]
            contexto.codigo_seleccionado = None

        return crear_respuesta_con_contexto(
            respuesta,
            contexto,
        )

    except Exception as error:
        print(
            f"[ERROR AUTOGEN] {type(error).__name__}: {error}",
            flush=True,
        )

        raise HTTPException(
            status_code=503,
            detail="No se pudo consultar el modelo local.",
        ) from error

    finally:
        await modelo.close()


