import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

from AgenteIA.asistente.configuracion import MODELO, OLLAMA_HOST, modelo_piensa
from AgenteIA.asistente.reescritura import reescribir_pregunta
from AgenteIA.inventario.contexto_inventario import contexto_a_diccionario
from AgenteIA.asistente.etapas import (
    EstadoConsulta,
    etapa_filtros_iniciales,
    etapa_cargar_inventario,
    etapa_conteo,
    etapa_calculadora,
    etapa_recomendacion_venta,
    etapa_consultas_inteligentes,
    etapa_ranking,
    etapa_listado_general,
    etapa_identificar_producto,
    etapa_paginacion,
    etapa_posicion_en_lista,
    etapa_referencias_contexto,
    etapa_productos_universales,
    etapa_consulta_ambigua,
    etapa_respuestas_validadas,
    etapa_respuestas_rapidas,
    etapa_modelo,
)


@asynccontextmanager
async def ciclo_vida(_app: FastAPI):
    async def preparar_qwen():
        try:
            async with httpx.AsyncClient(timeout=120.0) as cliente:
                respuesta = await cliente.post(
                    f"{OLLAMA_HOST}/api/generate",
                    json={
                        "model": MODELO,
                        "keep_alive": "30m",
                    },
                )
                respuesta.raise_for_status()

            print(
                f"[OLLAMA] {MODELO} cargado con permanencia de 30 minutos"
                f"{' (razonamiento apagado)' if modelo_piensa() else ''}.",
                flush=True,
            )

        except Exception as error:
            print(
                f"[OLLAMA] No se pudo preparar {MODELO}: {error}",
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
    pagina_actual: int = Field(default=1, ge=1)

    # Memoria extra de la conversación (ver contexto_inventario.py).
    # Son opcionales: si WinUI no los manda, se usan valores vacíos.
    categoria_consultada: str | None = None
    marca_vehiculo: str | None = None
    modelo_vehiculo: str | None = None
    anio_vehiculo: int | None = None


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
        "modelo": MODELO,
        "validador": "habilitado",
    }


@app.post("/consultar")
async def consultar(datos: Consulta):
    # Todas las respuestas salen con el contexto COMPLETO,
    # para que WinUI siempre devuelva la memoria de la conversación.
    resultado = await procesar_consulta(datos)

    if isinstance(resultado, dict):
        contexto_respuesta = resultado.get("contexto") or {}
        completo = contexto_a_diccionario(datos.contexto)
        completo.update(
            {k: v for k, v in contexto_respuesta.items() if k in completo}
        )
        resultado["contexto"] = completo

    return resultado


# Orden en que se atiende cada consulta. Cada etapa devuelve la
# respuesta para WinUI o None para pasar a la siguiente.
# Si cambias el orden, corre pruebas_inventario.py.
ETAPAS = (
    etapa_filtros_iniciales,
    etapa_cargar_inventario,
    etapa_conteo,
    etapa_calculadora,
    etapa_recomendacion_venta,
    etapa_consultas_inteligentes,
    etapa_ranking,
    etapa_listado_general,
    etapa_identificar_producto,
    etapa_paginacion,
    etapa_posicion_en_lista,
    etapa_referencias_contexto,
    etapa_productos_universales,
    etapa_consulta_ambigua,
    etapa_respuestas_validadas,
    etapa_respuestas_rapidas,
)


# Respuestas de las reglas que en realidad significan "no entendí".
# Con estas también se intenta la reescritura.
RESPUESTAS_DE_DUDA = (
    "No encontré «",
    "No pude identificar con seguridad",
    "Para hacer el cálculo necesito saber de qué producto",
)


def _es_duda(respuesta) -> bool:
    texto = respuesta.get("respuesta", "") if isinstance(respuesta, dict) else ""
    return texto.startswith(RESPUESTAS_DE_DUDA)


def _correr_etapas(datos: Consulta):
    estado = EstadoConsulta(datos=datos)
    for etapa in ETAPAS:
        respuesta = etapa(estado)
        if respuesta is not None:
            return respuesta, estado
    return None, estado


async def procesar_consulta(datos: Consulta):
    # Copia del mensaje tal como llegó (las etapas modifican "datos").
    original = datos.model_copy(deep=True)

    # 1. Primer intento: las reglas con el mensaje del vendedor.
    respuesta, estado = _correr_etapas(datos)

    if respuesta is not None and not _es_duda(respuesta):
        return respuesta

    # Un seguimiento de mecánica ("¿y si es un Versa 2015?") lo contesta
    # el modelo con el tema anterior; no se reescribe.
    if respuesta is None and estado.seguimiento_mecanico is not None:
        return await etapa_modelo(estado)

    # 2. Segundo intento: el modelo traduce el mensaje a una frase
    #    estándar ("pásame los que faltan" -> "siguientes productos")
    #    y las reglas lo vuelven a intentar (ver reescritura.py).
    frase = await reescribir_pregunta(
        datos.pregunta,
        estado.productos_actuales or [],
        estado.contexto or estado.contexto_calculo or original.contexto,
        original.historial,
    )

    if frase:
        segunda = original.model_copy(deep=True)
        segunda.pregunta = frase
        respuesta_2, estado_2 = _correr_etapas(segunda)

        if respuesta_2 is not None and not _es_duda(respuesta_2):
            return respuesta_2

        # Ninguna regla con la frase limpia ("no arranca el carro"): el
        # modelo responde con ella, porque así encuentra la documentación
        # ("no quiere arrancar" no la encontraba).
        if respuesta is None and respuesta_2 is None:
            return await etapa_modelo(estado_2)

    if respuesta is not None:
        return respuesta

    # 3. Ninguna regla aplicó: se consulta al modelo como antes.
    return await etapa_modelo(estado)

