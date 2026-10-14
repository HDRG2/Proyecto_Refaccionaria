import json
import re
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
from AgenteIA.contexto_inventario import resolver_producto_contextual
from AgenteIA.consultas_inteligentes import consultar_inventario_inteligente

app = FastAPI(title="El Pistón - IA Local")


class MensajeHistorial(BaseModel):
    rol: str
    texto: str


class Consulta(BaseModel):
    pregunta: str = Field(min_length=1, max_length=2000)
    inventario: str = Field(default="[]", max_length=150000)
    historial: list[MensajeHistorial] = Field(default_factory=list)


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



@app.post("/consultar")
async def consultar(datos: Consulta):

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
        print(
            "[CONSULTA INTELIGENTE] Respuesta verificada",
            flush=True
        )
        return {"respuesta": respuesta_inteligente}
        
    pregunta_normalizada = normalizar(datos.pregunta)

    consultas_lista = (
        "productos activos",
        "refacciones activas",
        "listar productos",
        "lista de productos",
        "productos disponibles",
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
            "respuesta": "\n".join(lineas)
        }

    # 2. Identificar producto e intención
    producto = identificar_producto(
        datos.pregunta,
        productos_actuales,
    )

    intencion = detectar_intencion(datos.pregunta)

    # Intentar recuperar el producto mencionado
    # anteriormente cuando no aparece explícitamente.
    if producto is None:
        producto = resolver_producto_contextual(
            datos.pregunta,
            datos.historial,
            productos_actuales,
        )

        if producto is not None:
            print(
                "[CONTEXTO] Producto identificado: "
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

        return {"respuesta": respuesta}

    # Consulta los precios.
    if producto is not None and intencion == "precio":
        respuesta = responder_precio(producto)

        print(
            "[VALIDADOR] Precio verificado: "
            f"{producto.get('codigo')}",
            flush=True,
        )

        return {"respuesta": respuesta}

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

        return {"respuesta": respuesta}


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
                "de la compatibilidad confirmada."
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

            "INVENTARIO ACTUAL (JSON):\n"
            f"{datos.inventario}\n\n"

            "PREGUNTA DEL VENDEDOR:\n"
            f"{datos.pregunta}\n\n"

            "Si necesitas datos del inventario, "
            "consulta las herramientas antes de responder."
        )

        resultado = await agente.run(task=tarea)

        respuesta = str(
            resultado.messages[-1].content
        ).strip()

        if not respuesta:
            raise ValueError(
                "AutoGen no devolvió una respuesta."
            )

        return {"respuesta": respuesta}

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


