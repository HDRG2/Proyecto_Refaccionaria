from dataclasses import dataclass
from typing import Any
import re
import time

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient
from fastapi import HTTPException

from AgenteIA.asistente.calculadora import resolver_calculo
from AgenteIA.asistente.configuracion import MODELO, argumentos_ollama
from AgenteIA.asistente.filtros_respuesta import (
    ajustar_respuesta_mecanica,
    quitar_razonamiento,
)
from AgenteIA.asistente.idioma import (
    MENSAJE_SOLO_ESPANOL,
    REGLA_IDIOMA,
    contiene_escritura_extranjera,
    detectar_cambio_idioma,
    es_texto_en_espanol,
    parece_otro_idioma,
)
from AgenteIA.asistente.listados import (
    detectar_cambio_pagina,
    categoria_sin_productos,
    es_solicitud_listado,
    es_solo_categoria,
    filtrar_listado,
    mensaje_categoria_vacia,
    pide_solo_nombre,
    respuesta_conteo,
    respuesta_ranking,
    respuesta_recomendacion_venta,
)
from AgenteIA.asistente.prompts import (
    INSTRUCCIONES_INVENTARIO,
    INSTRUCCIONES_MECANICA,
    tarea_inventario,
    tarea_mecanica,
)
from AgenteIA.asistente.productos import (
    PEDIR_PRODUCTO,
    PREGUNTA_MECANICA,
    buscar_por_palabra,
    detectar_intencion,
    es_pedido_de_producto,
    extraer_vehiculo,
    ficha_producto,
    identificar_producto,
    lista_coincidencias,
    menciona_inventario,
    es_solo_vehiculo,
    normalizar_codigos,
    busqueda_solo_pieza,
    mensaje_pieza_sin_productos,
    codigo_no_registrado,
    respuesta_codigo_no_registrado,
    obtener_existencia,
    pide_lista_vehiculos,
    respuesta_producto_no_encontrado,
    ultimo_mensaje_asistente,
    vehiculos_registrados,
)
from AgenteIA.asistente.respuestas import (
    crear_respuesta_con_contexto,
    respuesta_sin_cambios,
)
from AgenteIA.asistente.seguridad import (
    detectar_inyeccion_ampliada,
    detectar_inyeccion_instrucciones,
    detectar_modificacion_inventario,
)
from AgenteIA.asistente.social import respuesta_social
from AgenteIA.asistente.catalogo import (
    entradas_para_vocabulario,
    leer_catalogo,
    respuesta_catalogo,
)
from AgenteIA.asistente.coloquial import corregir_ortografia
from AgenteIA.asistente.consultas_extra import consulta_extra
from AgenteIA.asistente.texto import (
    normalizar,
    normalizar_terminos_automotrices,
    preparar_pregunta,
)
from AgenteIA.asistente.validador_respuesta import (
    respuesta_de_respaldo,
    textos_de_herramientas,
    validar_respuesta_inventario,
)
from AgenteIA.inventario.consultas_inteligentes import (
    consultar_inventario_inteligente,
)
from AgenteIA.inventario.contexto_inventario import (
    actualizar_contexto_conversacion,
    contexto_desde_estado,
    describir_vehiculo_contexto,
    detectar_seguimiento_mecanico,
    obtener_producto_seleccionado,
    obtener_productos_mencionados,
    resolver_posicion_lista,
    resolver_producto_contextual,
    resolver_seleccion_por_nombre,
    seleccionar_producto_contextual,
)
from AgenteIA.inventario.herramientas_inventario import (
    crear_herramientas_inventario,
)
from AgenteIA.inventario.validador_inventario import (
    cargar_inventario,
    responder_compatibilidad,
    responder_existencia,
    responder_precio,
)
from AgenteIA.mecanica.buscador_mecanico import buscar_conocimiento
from AgenteIA.mecanica.validador_mecanica import (
    respuesta_desde_documentacion,
    terminos_inventados,
)
from AgenteIA.mecanica.conocimientos_mecanicos import (
    buscar_respuesta_rapida,
    respuesta_falla_sin_sintoma,
)


MENSAJE_SIN_DOCUMENTACION = (
    "No tengo información técnica verificada para responder eso con "
    "seguridad. Revisa el manual o la ficha del fabricante, o consúltalo "
    "con un mecánico. Si es sobre un producto, dime su nombre o código y "
    "te doy sus datos del inventario."
)


MENSAJE_NO_ENTENDI = (
    "No entendí tu mensaje. Escríbeme tu consulta sobre refacciones, "
    "inventario, precios o mecánica automotriz. Por ejemplo: "
    "\"¿cuánto cuesta el ACE-001?\" o \"mi carro rechina al frenar\"."
)


@dataclass
class EstadoConsulta:
    """Lo que una etapa le pasa a las siguientes durante una consulta."""

    datos: Any
    contexto: Any = None
    contexto_calculo: Any = None
    inicio_consulta: Any = None
    intencion: Any = None
    producto: Any = None
    productos_actuales: Any = None
    seguimiento_mecanico: Any = None
    solicitud_listado: Any = None
    catalogo: Any = None


def etapa_filtros_iniciales(estado_consulta: EstadoConsulta):
    """Prepara la pregunta y aplica protecciones: manipulación, idioma, cambio de tema, mensajes sociales y órdenes de modificar el inventario."""
    datos = estado_consulta.datos

    inicio_consulta = time.perf_counter()

    # PREPARAR LA PREGUNTA: registros formal, informal y coloquial.
    pregunta_original = datos.pregunta
    datos.pregunta = preparar_pregunta(datos.pregunta)

    print(
        f"[ENTRADA] Original: {pregunta_original!r} | "
        f"Preparada: {datos.pregunta!r}",
        flush=True,
    )

    # PROTECCIÓN: intentos de manipular al asistente.
    if (
        detectar_inyeccion_instrucciones(datos.pregunta)
        or detectar_inyeccion_ampliada(datos.pregunta)
    ):
        print("[SEGURIDAD] Intento de manipulación detectado.", flush=True)

        return respuesta_sin_cambios(
            "Soy el asistente virtual de El Pistón. No puedo cambiar "
            "mis instrucciones, mi función ni mi idioma. Puedo ayudarte "
            "con refacciones, inventario, precios, cálculos de ventas "
            "y mecánica automotriz.",
            datos,
        )

    # PROTECCIÓN DE IDIOMA: siempre en español.
    if detectar_cambio_idioma(datos.pregunta) or contiene_escritura_extranjera(datos.pregunta):
        print("[IDIOMA] Solicitud de cambio de idioma bloqueada.", flush=True)

        return respuesta_sin_cambios(MENSAJE_SOLO_ESPANOL, datos)

    # MEMORIA DE LA CONVERSACIÓN: cambio de tema y vehículo mencionado.
    estado_conversacion = actualizar_contexto_conversacion(
        datos.contexto,
        datos.pregunta,
    )

    if estado_conversacion["solo_cambio_tema"]:
        print("[CONTEXTO] Cambio de tema: memoria reiniciada.", flush=True)

        return respuesta_sin_cambios(
            "Listo, empezamos de nuevo. ¿En qué te ayudo?",
            datos,
        )

    # MENSAJES SOCIALES: saludos, gracias, identidad, ayuda, sin sentido.
    respuesta_breve = respuesta_social(datos.pregunta)

    if respuesta_breve is not None:
        print("[SOCIAL] Respuesta breve.", flush=True)

        return respuesta_sin_cambios(respuesta_breve, datos)
    
    # PROTECCIÓN: impedir órdenes de modificación del inventario.
    if detectar_modificacion_inventario(datos.pregunta):
        print(
            "[SEGURIDAD] Solicitud de modificación del inventario.",
            flush=True,
        )

        return {
            "respuesta": (
                "No puedo modificar precios, existencias ni "
                "productos desde el asistente virtual. "
                "Estas operaciones deben realizarse desde "
                "las funciones administrativas autorizadas "
                "de El Pistón."
            ),
            "contexto": {
                "codigo_seleccionado": datos.contexto.codigo_seleccionado,
                "codigos_lista": list(datos.contexto.codigos_lista),
                "pagina_actual": datos.contexto.pagina_actual,
            },
        }

    estado_consulta.inicio_consulta = inicio_consulta
    return None


def etapa_cargar_inventario(estado_consulta: EstadoConsulta):
    """Valida el inventario que mandó WinUI."""
    datos = estado_consulta.datos

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

    estado_consulta.productos_actuales = productos_actuales

    # "MOT 001", "mot001" -> "MOT-001"
    datos.pregunta = normalizar_codigos(datos.pregunta, productos_actuales)

    # Catálogo completo (marcas, categorías y autos registrados aunque no
    # tengan productos). Si WinUI no lo manda, queda vacío.
    estado_consulta.catalogo = leer_catalogo(getattr(datos, "catalogo", None))

    # Errores de dedo: "valatas" -> "balatas", "corrolla" -> "corolla".
    # También conoce los nombres del catálogo ("fokus" -> "focus").
    corregida = corregir_ortografia(
        datos.pregunta,
        productos_actuales + entradas_para_vocabulario(estado_consulta.catalogo),
    )
    if corregida != datos.pregunta:
        print(f"[ORTOGRAFIA] {datos.pregunta!r} -> {corregida!r}", flush=True)
        datos.pregunta = corregida

    # Otro idioma con letras latinas ("Kwalok ñan ña bwebwenato…"): se
    # revisa aquí porque ya se conocen los nombres del inventario.
    vocabulario = {
        palabra
        for p in productos_actuales + entradas_para_vocabulario(estado_consulta.catalogo)
        for campo in ("nombre", "marca", "categoria")
        for palabra in re.findall(r"[a-zñ]+", normalizar(str(p.get(campo, ""))))
    }
    if parece_otro_idioma(datos.pregunta, vocabulario):
        print("[IDIOMA] Mensaje en otro idioma.", flush=True)
        return respuesta_sin_cambios(MENSAJE_SOLO_ESPANOL, datos)

    # "MOT 001" cuando no existe un MOT-001 activo: se avisa sin adivinar
    # (antes el modelo lo tomaba como "página 1").
    codigo = codigo_no_registrado(datos.pregunta, productos_actuales)
    if codigo:
        print(f"[CÓDIGO] {codigo} no está en el inventario activo.", flush=True)
        return respuesta_sin_cambios(
            respuesta_codigo_no_registrado(codigo, productos_actuales), datos
        )
    return None


def etapa_conteo(estado_consulta: EstadoConsulta):
    """¿Cuántos productos tenemos?"""
    datos = estado_consulta.datos
    productos_actuales = estado_consulta.productos_actuales

    # CONTEO DEL INVENTARIO ("¿cuántos productos tenemos?").
    respuesta_de_conteo = respuesta_conteo(
        datos.pregunta,
        productos_actuales,
    )

    if respuesta_de_conteo is not None:
        print("[CONTEO] Respuesta verificada.", flush=True)

        return respuesta_sin_cambios(respuesta_de_conteo, datos)

    return None


def etapa_consultas_extra(estado_consulta: EstadoConsulta):
    """Comparar productos, contar por grupo, preguntas sobre la lista mostrada y suficiencia."""
    datos = estado_consulta.datos
    contexto = contexto_desde_estado(datos.contexto)
    respuesta = consulta_extra(
        datos.pregunta, estado_consulta.productos_actuales, contexto, datos.historial
    )
    if respuesta is None:
        return None
    print("[CONSULTA EXTRA] Respuesta del inventario.", flush=True)
    # Si la respuesta habla de un solo producto, queda seleccionado.
    mencionados = obtener_productos_mencionados(respuesta, estado_consulta.productos_actuales)
    return crear_respuesta_con_contexto(
        respuesta, contexto, mencionados[0] if len(mencionados) == 1 else None
    )


def etapa_calculadora(estado_consulta: EstadoConsulta):
    """Sumas, multiplicaciones, IVA y descuentos."""
    datos = estado_consulta.datos
    productos_actuales = estado_consulta.productos_actuales

    # CALCULADORA: sumas, multiplicaciones, IVA y descuentos
    # usando el producto actual o el último mencionado.
    contexto_calculo = contexto_desde_estado(datos.contexto)

    respuesta_calculo, producto_calculo = resolver_calculo(
        datos.pregunta,
        productos_actuales,
        contexto_calculo,
        datos.historial,
    )

    if respuesta_calculo is not None:
        print("[CALCULADORA] Cálculo exacto generado.", flush=True)

        return crear_respuesta_con_contexto(
            respuesta_calculo,
            contexto_calculo,
            producto_calculo,
        )

    estado_consulta.contexto_calculo = contexto_calculo
    return None


def etapa_recomendacion_venta(estado_consulta: EstadoConsulta):
    """¿Qué le ofrezco para...? Productos reales de la categoría."""
    datos = estado_consulta.datos
    contexto_calculo = estado_consulta.contexto_calculo

    respuesta, mostrados = respuesta_recomendacion_venta(
        datos.pregunta,
        estado_consulta.productos_actuales,
        datos.historial,
    )

    if respuesta is None:
        return None

    print("[VENTA] Recomendación desde el inventario.", flush=True)

    contexto_calculo.codigos_lista = [str(p["codigo"]) for p in mostrados]
    contexto_calculo.pagina_actual = 1
    contexto_calculo.codigo_seleccionado = (
        str(mostrados[0]["codigo"]) if len(mostrados) == 1 else None
    )

    return crear_respuesta_con_contexto(respuesta, contexto_calculo)


def etapa_solo_categoria(estado_consulta: EstadoConsulta):
    """"Motor", "iluminación", "dime solo los de escape"."""
    datos = estado_consulta.datos
    productos_actuales = estado_consulta.productos_actuales

    categoria = es_solo_categoria(datos.pregunta, productos_actuales)
    if categoria is None:
        return None

    respuesta = consultar_inventario_inteligente(
        f"¿qué productos de la categoría {categoria} tenemos?",
        productos_actuales,
        estado_consulta.contexto_calculo,
        datos.historial,
    )

    # La categoría existe en el programa pero no tiene productos.
    if respuesta is None or not respuesta.startswith("Productos de la categoría"):
        respuesta = mensaje_categoria_vacia(categoria)

    # Recordar la lista para "el tercero", "solo dime el nombre"...
    contexto = estado_consulta.contexto_calculo
    mostrados = obtener_productos_mencionados(respuesta, productos_actuales)
    contexto.codigos_lista = [str(p["codigo"]) for p in mostrados]
    contexto.pagina_actual = 1
    contexto.codigo_seleccionado = (
        str(mostrados[0]["codigo"]) if len(mostrados) == 1 else None
    )

    print(f"[CATEGORÍA] {categoria}", flush=True)
    return crear_respuesta_con_contexto(respuesta, contexto)


def etapa_catalogo(estado_consulta: EstadoConsulta):
    """"ultra 8", "mobil", "focus 2018", "clutch": marca, categoría o auto del catálogo."""
    datos = estado_consulta.datos
    respuesta, mostrados = respuesta_catalogo(
        datos.pregunta,
        estado_consulta.productos_actuales,
        estado_consulta.catalogo or leer_catalogo(None),
    )
    if respuesta is None:
        return None
    print("[CATÁLOGO] Marca, categoría o auto registrado.", flush=True)
    contexto = estado_consulta.contexto_calculo
    contexto.codigos_lista = [str(p["codigo"]) for p in mostrados]
    contexto.pagina_actual = 1
    contexto.codigo_seleccionado = str(mostrados[0]["codigo"]) if len(mostrados) == 1 else None
    return crear_respuesta_con_contexto(respuesta, contexto)


def etapa_solo_pieza(estado_consulta: EstadoConsulta):
    """"termostato", "sensor", "bujias del inventario": busca la pieza."""
    datos = estado_consulta.datos
    productos_actuales = estado_consulta.productos_actuales

    resultado = busqueda_solo_pieza(datos.pregunta, productos_actuales)
    if resultado is None:
        return None

    contexto = estado_consulta.contexto_calculo
    estado, valor = resultado

    if estado == "sin_productos":
        print(f"[PIEZA] Sin productos: {valor}", flush=True)
        return crear_respuesta_con_contexto(mensaje_pieza_sin_productos(valor), contexto)

    encontrados = valor
    contexto.codigos_lista = [str(p["codigo"]) for p in encontrados]
    contexto.pagina_actual = 1

    if len(encontrados) == 1:
        contexto.codigo_seleccionado = str(encontrados[0]["codigo"])
        print(f"[PIEZA] {encontrados[0]['codigo']}", flush=True)
        return crear_respuesta_con_contexto(ficha_producto(encontrados[0]), contexto)

    contexto.codigo_seleccionado = None
    print(f"[PIEZA] {len(encontrados)} coincidencias", flush=True)
    return crear_respuesta_con_contexto(lista_coincidencias(encontrados), contexto)


def etapa_consultas_inteligentes(estado_consulta: EstadoConsulta):
    """Consultas exactas del inventario (por vehículo, precio, stock, categoría...)."""
    contexto_calculo = estado_consulta.contexto_calculo
    datos = estado_consulta.datos
    productos_actuales = estado_consulta.productos_actuales

    # ¿Es una solicitud de ver el inventario?
    solicitud_listado = es_solicitud_listado(
        datos.pregunta,
        productos_actuales,
    )

    # Consultas inteligentes del inventario.
    # Si piden la lista general ("¿qué tenemos?"), la arma el servidor.
    # Si piden un tema ("¿qué tienes de frenos?"), lo resuelve
    # consultas_inteligentes con precios y existencias.
    lista_general = (
        solicitud_listado
        and filtrar_listado(datos.pregunta, productos_actuales)[1] is None
    )

    respuesta_inteligente = (
        None
        if lista_general
        else consultar_inventario_inteligente(
            datos.pregunta,
            productos_actuales,
            contexto_calculo,
            datos.historial,
        )
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

        # Recordar los productos de la respuesta para poder decir
        # "el primero", "súmalos" o "¿y con IVA?" después.
        if productos_en_respuesta:
            contexto_calculo.codigos_lista = [
                str(p["codigo"]) for p in productos_en_respuesta
            ]
            contexto_calculo.pagina_actual = 1
            contexto_calculo.codigo_seleccionado = (
                str(productos_en_respuesta[0]["codigo"])
                if len(productos_en_respuesta) == 1
                else None
            )

        return crear_respuesta_con_contexto(
            respuesta_inteligente,
            contexto_calculo,
        )

    estado_consulta.solicitud_listado = solicitud_listado
    return None


def etapa_ranking(estado_consulta: EstadoConsulta):
    """Más caro, más barato, agotados, poco stock."""
    datos = estado_consulta.datos
    productos_actuales = estado_consulta.productos_actuales

    # MÁS CARO / MÁS BARATO / AGOTADOS / POCO STOCK
    respuesta_de_ranking = respuesta_ranking(
        datos.pregunta,
        productos_actuales,
    )

    if respuesta_de_ranking is not None:
        print("[RANKING] Respuesta verificada.", flush=True)

        return respuesta_sin_cambios(respuesta_de_ranking, datos)

    return None


def etapa_listado_general(estado_consulta: EstadoConsulta):
    """Lista general de productos (primera página)."""
    datos = estado_consulta.datos
    productos_actuales = estado_consulta.productos_actuales
    solicitud_listado = estado_consulta.solicitud_listado

    pregunta_normalizada = normalizar(datos.pregunta)

    consultas_lista = (
        "productos activos",
        "refacciones activas",
        "listar productos",
        "listar refacciones",
        "lista de productos",
        "lista de refacciones",
        "productos disponibles",
        "refacciones disponibles",
        "productos tenemos disponibles",
        "refacciones tenemos disponibles",
        "mostrar productos",
        "mostrar refacciones",
        "muestrame los productos",
        "muestrame las refacciones",
    )


    preguntas_lista_general = (
        "que productos tenemos",
        "qué productos tenemos",
        "que refacciones tenemos",
        "qué refacciones tenemos",
    )

    if(
        any(
            expresion in pregunta_normalizada
            for expresion in consultas_lista
        )
        or pregunta_normalizada.strip(" ¿?¡!.,") in preguntas_lista_general
        or solicitud_listado
    ): 
    
        # Filtrar si piden una categoría, marca o palabra
        # ("¿qué tenemos de frenos?").
        productos_listado, descripcion_filtro = filtrar_listado(
            datos.pregunta,
            productos_actuales,
        )

        # "¿qué tenemos de escape?" sin productos de Escape: avisarlo en
        # lugar de mostrar todo el inventario.
        if descripcion_filtro is None:
            vacia = categoria_sin_productos(datos.pregunta, productos_actuales)
            if vacia:
                print(f"[VALIDADOR] Categoría sin productos: {vacia}", flush=True)
                return respuesta_sin_cambios(mensaje_categoria_vacia(vacia), datos)

        titulo_listado = (
            f"Productos de El Pistón ({descripcion_filtro}):"
            if descripcion_filtro
            else "Productos activos de El Pistón:"
        )

        if not productos_listado:
            return respuesta_sin_cambios(
                "Actualmente no hay productos activos "
                "registrados en El Pistón.",
                datos,
            )

        
        # PAGINACIÓN DEL INVENTARIO
        productos_por_pagina = 10
        total_productos = len(productos_listado)

        total_paginas = (
            total_productos + productos_por_pagina - 1
        ) // productos_por_pagina

        # Por ahora mostramos la primera página.
        pagina_actual = 1
        
        
        
        inicio = (pagina_actual - 1) * productos_por_pagina
        fin = inicio + productos_por_pagina

        productos_pagina = productos_listado[inicio:fin]

        lineas = [
            titulo_listado,
            f"Página {pagina_actual} de {total_paginas}",
            "",
        ]

        for indice, producto_lista in enumerate(
            productos_pagina,
            start=inicio + 1,
        ):
            nombre = producto_lista.get("nombre", "Sin nombre")
            codigo = producto_lista.get("codigo", "Sin código")

            lineas.append(
                f"{indice}. {nombre} ({codigo})"
            )

        lineas.append("")

        lineas.append(
            f"Mostrando {len(productos_pagina)} "
            f"de {total_productos} productos activos."
        )

        if pagina_actual < total_paginas:
            lineas.append(
                "\nEscribe 'siguientes 10 productos' "
                "para ver más."
            )

        print(
            "[VALIDADOR] Lista de productos activos generada",
            flush=True,
        )

        return {
            "respuesta": "\n".join(lineas),
            "contexto": {
                "codigo_seleccionado": (
                    str(productos_listado[0]["codigo"])
                    if total_productos == 1
                    else None
                ),
                # Guardamos TODOS los códigos,
                # no solamente los de la página visible.
                "codigos_lista": [
                    str(p["codigo"])
                    for p in productos_listado
                ],
                "pagina_actual": pagina_actual,
            },
        }

    return None


def etapa_identificar_producto(estado_consulta: EstadoConsulta):
    """Identifica el producto y la intención de la pregunta y reconstruye el contexto."""
    datos = estado_consulta.datos
    productos_actuales = estado_consulta.productos_actuales

    # 2. Identificar producto e intención
    producto = identificar_producto(
        datos.pregunta,
        productos_actuales,
    )

    intencion = detectar_intencion(datos.pregunta)
    
    print(
        f"[DEBUG INTENCIÓN] Pregunta: {datos.pregunta!r} | "
        f"Intención: {intencion!r} | "
        f"Producto: {producto.get('codigo') if producto else None}",
        flush=True,
    )
    
    # Reconstruir el contexto recibido desde WinUI
    
    contexto = contexto_desde_estado(datos.contexto)
    
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

    estado_consulta.contexto = contexto
    estado_consulta.intencion = intencion
    estado_consulta.producto = producto
    return None


def etapa_paginacion(estado_consulta: EstadoConsulta):
    """Siguiente / anterior página de la lista, o una página concreta."""
    contexto = estado_consulta.contexto
    datos = estado_consulta.datos
    productos_actuales = estado_consulta.productos_actuales

    # "siguientes 10", "dame los otros", "regrésame", "página 2"...
    # (ver detectar_cambio_pagina en listados.py)
    cambio = detectar_cambio_pagina(datos.pregunta, productos_actuales)

    if cambio is None:
        return None

    productos_por_pagina = 10

    if not contexto.codigos_lista:
        return crear_respuesta_con_contexto(
            "Primero solicita la lista de productos activos "
            "para poder cambiar de página.",
            contexto,
        )

    # Recuperar los productos en el orden de la lista original.
    productos_por_codigo = {
        str(p["codigo"]): p
        for p in productos_actuales
    }

    productos_lista = [
        productos_por_codigo[codigo]
        for codigo in contexto.codigos_lista
        if codigo in productos_por_codigo
    ]

    total_productos = len(productos_lista)

    if total_productos == 0:
        contexto.codigos_lista = []
        contexto.pagina_actual = 1

        return crear_respuesta_con_contexto(
            "Los productos de la lista anterior ya no "
            "están disponibles en el inventario.",
            contexto,
        )

    total_paginas = (
        total_productos + productos_por_pagina - 1
    ) // productos_por_pagina

    pagina_actual = max(
        1,
        min(contexto.pagina_actual, total_paginas),
    )

    if isinstance(cambio, int):
        if not 1 <= cambio <= total_paginas:
            return crear_respuesta_con_contexto(
                f"Esa página no existe. La lista tiene "
                f"{total_paginas} {'página' if total_paginas == 1 else 'páginas'}.",
                contexto,
            )
        pagina_actual = cambio

    elif cambio == "siguiente":
        if pagina_actual >= total_paginas:
            contexto.pagina_actual = pagina_actual

            return crear_respuesta_con_contexto(
                f"Ya estás en la última página "
                f"({pagina_actual} de {total_paginas}).",
                contexto,
            )

        pagina_actual += 1

    elif cambio == "anterior":
        if pagina_actual <= 1:
            contexto.pagina_actual = 1

            return crear_respuesta_con_contexto(
                "Ya estás en la primera página.",
                contexto,
            )

        pagina_actual -= 1

    contexto.pagina_actual = pagina_actual

    inicio = (pagina_actual - 1) * productos_por_pagina
    fin = inicio + productos_por_pagina

    productos_pagina = productos_lista[inicio:fin]

    lineas = [
        "Productos activos de El Pistón:",
        f"Página {pagina_actual} de {total_paginas}",
        "",
    ]

    for indice, producto_lista in enumerate(
        productos_pagina,
        start=inicio + 1,
    ):
        nombre = producto_lista.get("nombre", "Sin nombre")
        codigo = producto_lista.get("codigo", "Sin código")

        lineas.append(
            f"{indice}. {nombre} ({codigo})"
        )

    lineas.append("")
    lineas.append(
        f"Mostrando {len(productos_pagina)} "
        f"de {total_productos} productos activos."
    )

    if pagina_actual < total_paginas:
        lineas.append(
            "\nEscribe 'siguientes 10 productos' para ver más."
        )

    if pagina_actual > 1:
        lineas.append(
            "Escribe 'página anterior' para regresar."
        )

    print(
        f"[PAGINACIÓN] Página {pagina_actual} "
        f"de {total_paginas}",
        flush=True,
    )

    return crear_respuesta_con_contexto(
        "\n".join(lineas),
        contexto,
    )


def etapa_solo_nombre(estado_consulta: EstadoConsulta):
    """"Solo dime el nombre", "sin precios": nombre y código, sin datos extra."""
    contexto = estado_consulta.contexto
    datos = estado_consulta.datos
    productos_actuales = estado_consulta.productos_actuales

    if not pide_solo_nombre(datos.pregunta):
        return None

    producto = estado_consulta.producto or obtener_producto_seleccionado(
        contexto, productos_actuales
    )

    if producto is not None:
        respuesta = f"{producto.get('nombre')} ({producto.get('codigo')})"
    elif contexto.codigos_lista:
        por_codigo = {str(p.get("codigo")): p for p in productos_actuales}
        nombres = [
            f"{i}. {por_codigo[c].get('nombre')} ({c})"
            for i, c in enumerate(contexto.codigos_lista, start=1)
            if c in por_codigo
        ]
        respuesta = "\n".join(nombres) if nombres else None
    else:
        respuesta = None

    if respuesta is None:
        respuesta = "¿De qué producto? Dime su nombre o código, por ejemplo ACE-001."

    print("[VALIDADOR] Solo nombres.", flush=True)
    return crear_respuesta_con_contexto(respuesta, contexto, producto)


def etapa_posicion_en_lista(estado_consulta: EstadoConsulta):
    """"El segundo", "el producto 3"."""
    contexto = estado_consulta.contexto
    datos = estado_consulta.datos
    intencion = estado_consulta.intencion
    producto = estado_consulta.producto
    productos_actuales = estado_consulta.productos_actuales

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

        # "El segundo", "el producto 3": si no preguntó nada más,
        # mostrar su ficha y dejarlo seleccionado.
        if intencion is None:
            print(
                "[CONTEXTO] Producto por posición: "
                f"{producto.get('codigo')}",
                flush=True,
            )

            return crear_respuesta_con_contexto(
                ficha_producto(producto),
                contexto,
                producto,
            )

    estado_consulta.producto = producto
    return None


def etapa_referencias_contexto(estado_consulta: EstadoConsulta):
    """Producto por nombre, por referencia ("ese producto") o por palabra."""
    contexto = estado_consulta.contexto
    datos = estado_consulta.datos
    intencion = estado_consulta.intencion
    producto = estado_consulta.producto
    productos_actuales = estado_consulta.productos_actuales

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

    # Detectar preguntas que hacen referencia al producto anterior.
    pregunta_contextual = normalizar(datos.pregunta).strip(" ¿?¡!.,")

        # Detectar referencias claras al producto anterior.
    referencias_producto_anterior = (
        "cuanto cuesta",
        "que precio tiene",
        "cuanto vale",
        "cual es el precio de",
        "cual es el precio",
        "cuantas piezas tiene",
        "cuantas piezas quedan",
        "cuantas quedan",
        "cuantos quedan",
        "cuantas hay",
        "tiene existencias",
        "hay existencias",
        "es universal",
    )

    # Frases que indican explícitamente una referencia anterior.
    referencias_explicitas = (
        "ese producto",
        "esa refaccion",
        "esa pieza",
        "del mismo producto",
        "de ese producto",
    )

    # Preguntas de compatibilidad que pueden referirse
    # al producto seleccionado anteriormente.
    preguntas_compatibilidad = (
        "es compatible con",
        "le queda a",
        "sirve para",
    )

    # Preguntas cortas que solo traen palabras de precio/existencia:
    # "y su precio", "y cuánto", "¿cuántos tienes?", "precio con iva".
    _solo_funcion = {
        "y", "el", "la", "los", "las", "su", "sus", "de", "del", "cuanto",
        "cuanta", "cuantos", "cuantas", "cuesta", "cuestan", "vale", "valen",
        "precio", "precios", "pieza", "piezas", "quedan", "queda", "hay",
        "tiene", "tienes", "tenemos", "existencia", "existencias", "stock",
        "es", "universal", "que", "cual", "con", "sin", "iva", "unidades",
        "disponibles", "entonces", "oye", "pero", "ahora", "mismo", "ese",
        "esa", "este", "esta", "dime", "dame", "me", "lo", "sale", "cobro",
        "a", "como", "en", "le", "y?", "todavia", "aun", "quedaron",
    }
    palabras_contextuales = re.findall(r"[a-z0-9]+", pregunta_contextual)
    solo_palabras_de_consulta = (
        0 < len(palabras_contextuales) <= 6
        and all(p in _solo_funcion for p in palabras_contextuales)
    )

    es_continuacion_contextual = (
        solo_palabras_de_consulta
        or pregunta_contextual in referencias_producto_anterior
        or any(
            referencia in pregunta_contextual
            for referencia in referencias_explicitas
        )
        or (
            intencion == "compatibilidad"
            and any(
                expresion in pregunta_contextual
                for expresion in preguntas_compatibilidad
            )
        )
    )

    # Intentar recuperar el producto mencionado anteriormente
    # solamente cuando la pregunta sea una continuación clara.
    
    if producto is None and es_continuacion_contextual and intencion in (
        "precio",
        "existencia",
        "compatibilidad",
        "universalidad",
    ):
        producto = obtener_producto_seleccionado(
            contexto,
            productos_actuales,
        )

        # Respaldo: si WinUI no mandó el contexto, buscar el
        # producto en las últimas respuestas del historial.
        if producto is None:
            producto = resolver_producto_contextual(
                datos.pregunta,
                datos.historial,
                productos_actuales,
            )

        if producto is not None:
            print(
                "[CONTEXTO ESTRUCTURADO] Producto: "
                f"{producto.get('codigo')}",
                flush=True,
            )
     
    
       
    # SEGUIMIENTO DE COMPATIBILIDAD: "¿y para un Versa 2018?",
    # "¿le queda a un Tsuru 2010?" con el producto que se está viendo.
    if (
        intencion is None
        and extraer_vehiculo(datos.pregunta) is not None
        and re.search(
            r"^\W*(?:y\s+)?(?:para|con|a|le queda|le sirve|sirve|y si es)\b",
            normalizar(datos.pregunta),
        )
    ):
        producto_seguimiento = producto or obtener_producto_seleccionado(
            contexto,
            productos_actuales,
        )

        if producto_seguimiento is not None:
            producto = producto_seguimiento
            intencion = "compatibilidad"

            print(
                "[CONTEXTO] Seguimiento de compatibilidad: "
                f"{producto.get('codigo')}",
                flush=True,
            )

    # BÚSQUEDA POR PALABRA: "¿hay balatas?", "¿cuánto cuesta el aceite?"
    if producto is None:
        texto_busqueda = normalizar(datos.pregunta)

        pide_producto = (
            intencion in ("precio", "existencia")
            # "¿para qué autos sirve el amortiguador?"
            or (intencion == "compatibilidad" and pide_lista_vehiculos(datos.pregunta))
            or (
                re.search(PEDIR_PRODUCTO, texto_busqueda) is not None
                and re.search(PREGUNTA_MECANICA, texto_busqueda) is None
            )
        )

        if pide_producto:
            coincidencias = buscar_por_palabra(
                datos.pregunta,
                productos_actuales,
            )

            if len(coincidencias) == 1:
                producto = coincidencias[0]

                print(
                    "[BÚSQUEDA] Producto por palabra: "
                    f"{producto.get('codigo')}",
                    flush=True,
                )

                if intencion is None:
                    return crear_respuesta_con_contexto(
                        ficha_producto(producto),
                        contexto,
                        producto,
                    )

            elif len(coincidencias) > 1:
                contexto.codigos_lista = [
                    str(p.get("codigo")) for p in coincidencias
                ]
                contexto.codigo_seleccionado = None

                return crear_respuesta_con_contexto(
                    lista_coincidencias(coincidencias),
                    contexto,
                )

            else:
                no_encontrado = respuesta_producto_no_encontrado(datos.pregunta)

                if no_encontrado is not None:
                    print("[BÚSQUEDA] Sin coincidencias en el inventario.", flush=True)

                    return crear_respuesta_con_contexto(no_encontrado, contexto)

    estado_consulta.intencion = intencion
    estado_consulta.producto = producto
    return None


def etapa_productos_universales(estado_consulta: EstadoConsulta):
    """Lista de productos universales."""
    contexto = estado_consulta.contexto
    datos = estado_consulta.datos
    productos_actuales = estado_consulta.productos_actuales

    # 3. Respuestas exactas, sin intervención de Qwen
    # Evitar consultas ambiguas de inventario.
    
    
    # Consulta general: mostrar todos los productos universales.
    pregunta_universal = normalizar(datos.pregunta)

    consultas_universales = (
        "que productos son universales",
        "qué productos son universales",
        "cuales productos son universales",
        "cuáles productos son universales",
        "que refacciones son universales",
        "qué refacciones son universales",
        "cuales refacciones son universales",
        "cuáles refacciones son universales",
        "mostrar productos universales",
        "listar productos universales",
        "productos universales",
        "refacciones universales",
    )
    
    print(
        f"[DEBUG UNIVERSALES] Texto: {pregunta_universal.strip(' ¿?¡!.,')!r}",
        flush=True,
    )

    if pregunta_universal.strip(" ¿?¡!.,") in consultas_universales:

        productos_universales = [
            p for p in productos_actuales
            if p.get("universal") is True
        ]

        if not productos_universales:
            respuesta = (
                "Actualmente no hay productos registrados "
                "como universales en el inventario de El Pistón."
            )
        else:
            lineas = ["Productos registrados como universales:"]

            for p in productos_universales:
                lineas.append(
                    f"• {p.get('nombre')} ({p.get('codigo')})"
                )

            total = len(productos_universales)

            lineas.append(
                f"Total: {total} "
                f"{'producto' if total == 1 else 'productos'}."
            )

            lineas.append(
                "Nota: que un producto esté registrado como "
                "universal no garantiza su compatibilidad "
                "con todos los vehículos."
            )

            respuesta = "\n".join(lineas)

        print(
            "[VALIDADOR] Consulta general de productos universales",
            flush=True,
        )

        return crear_respuesta_con_contexto(
            respuesta,
            contexto,
        )

    return None


def etapa_consulta_ambigua(estado_consulta: EstadoConsulta):
    """Pide el código si no se identificó el producto."""
    contexto = estado_consulta.contexto
    datos = estado_consulta.datos
    intencion = estado_consulta.intencion
    producto = estado_consulta.producto

    # Detectar solicitudes generales de listado de inventario.
    pregunta_inventario = normalizar(datos.pregunta)

    expresiones_listado_inventario = (
        "que refacciones tenemos",
        "que productos tenemos",
        "refacciones disponibles",
        "productos disponibles",
        "listar refacciones",
        "listar productos",
        "lista de refacciones",
        "lista de productos",
        "mostrar inventario",
        "ver inventario",
    )

    es_listado_inventario = any(
        expresion in pregunta_inventario
        for expresion in expresiones_listado_inventario
    )

    
    if producto is None and not es_listado_inventario and intencion in (
        "existencia",
        "precio",
        "compatibilidad",
        "universalidad",
    ):
        print(
            f"[SEGURIDAD] Consulta ambigua: {datos.pregunta}",
            flush=True,
        )

        return crear_respuesta_con_contexto(
            (
                "No pude identificar con seguridad la refacción. "
                "Indícame su nombre o código, por ejemplo ACE-001."
            ),
            contexto,
        )

    return None


def etapa_respuestas_validadas(estado_consulta: EstadoConsulta):
    """Existencia, precio, universalidad, compatibilidad y ficha del producto."""
    contexto = estado_consulta.contexto
    datos = estado_consulta.datos
    intencion = estado_consulta.intencion
    producto = estado_consulta.producto

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
            # Mismas reglas que el resto del asistente: rechaza
            # negativos, decimales (10.7) y texto inválido.
            cantidad = obtener_existencia(producto)

            if cantidad is not None:
                respuesta += (
                    f"\nExistencias disponibles: {cantidad} "
                    f"{'pieza' if cantidad == 1 else 'piezas'}."
                )
            else:
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
    
     # Consultar si una refacción está registrada como universal.
    if intencion == "universalidad":

        if producto is None:
            return crear_respuesta_con_contexto(
                "No pude identificar la refacción. "
                "Indícame su nombre o código para verificar "
                "si está registrada como universal.",
                contexto,
            )

        universal = producto.get("universal")

        if not isinstance(universal, bool):
            respuesta = (
                "No se pudo verificar si esta refacción "
                "está registrada como universal."
            )
        elif universal:
            respuesta = (
                f"El producto {producto.get('nombre')} "
                f"({producto.get('codigo')}) está registrado "
                "como universal en el inventario. "
                "Esto no garantiza su compatibilidad con "
                "todos los vehículos."
            )
        else:
            respuesta = (
                f"El producto {producto.get('nombre')} "
                f"({producto.get('codigo')}) no está registrado "
                "como universal en el inventario."
            )

        print(
            "[VALIDADOR] Universalidad verificada: "
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

        # "¿Para qué autos sirve?", "autos compatibles para esa pieza":
        # se listan los vehículos registrados del producto.
        if vehiculo is None and pide_lista_vehiculos(datos.pregunta):
            print(f"[VALIDADOR] Vehículos registrados: {producto.get('codigo')}", flush=True)
            return crear_respuesta_con_contexto(
                vehiculos_registrados(producto),
                contexto,
                producto,
            )

        # Si no lo dijo, usar el vehículo recordado de la conversación.
        if vehiculo is None:
            vehiculo = describir_vehiculo_contexto(contexto)

        # Sin vehículo: mostrar los registrados en lugar de solo pedirlo.
        if vehiculo is None:
            return crear_respuesta_con_contexto(
                vehiculos_registrados(producto),
                contexto,
                producto,
            )

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

    # 4. Ficha del producto: "dame el filtro de aceite",
    # "¿hay ACE-001?", "info del FIL-001" o solo el código.
    # (El cambio de idioma ya se bloqueó al inicio.)
    if (
        producto is not None
        and intencion is None
        and es_pedido_de_producto(datos.pregunta, producto)
    ):
        print(
            "[VALIDADOR] Ficha de producto: "
            f"{producto.get('codigo')}",
            flush=True,
        )

        return crear_respuesta_con_contexto(
            ficha_producto(producto),
            contexto,
            producto,
        )

    return None


def etapa_solo_vehiculo(estado_consulta: EstadoConsulta):
    """"nissan versa 2015": refacciones registradas para ese vehículo."""
    datos = estado_consulta.datos
    contexto = estado_consulta.contexto

    if not es_solo_vehiculo(datos.pregunta, estado_consulta.productos_actuales):
        return None

    # "¿le queda al ACE-001?" -> "toyota 2014": sigue la pregunta anterior
    # de compatibilidad de ESE producto (la atiende la reescritura).
    # Si lo anterior fue una lista de vehículos o de refacciones por
    # vehículo, "nissan versa" es una búsqueda nueva.
    ultimo = normalizar(ultimo_mensaje_asistente(datos.historial))
    seleccionado = normalizar(contexto.codigo_seleccionado or "")
    if (
        seleccionado
        and "compatib" in ultimo
        and seleccionado in ultimo
        and "en estos modelos" not in ultimo
        and "con compatibilidad registrada para" not in ultimo
    ):
        return None

    respuesta = consultar_inventario_inteligente(
        f"¿qué refacciones tienes para un {datos.pregunta.strip(' ¿?¡!.,')}?",
        estado_consulta.productos_actuales,
        contexto,
        datos.historial,
    )
    if respuesta is None:
        return None

    print("[VEHÍCULO] Refacciones para el vehículo.", flush=True)
    return crear_respuesta_con_contexto(respuesta, contexto)


def etapa_respuestas_rapidas(estado_consulta: EstadoConsulta):
    """Respuestas rápidas de mecánica ya revisadas."""
    contexto = estado_consulta.contexto
    datos = estado_consulta.datos
    productos_actuales = estado_consulta.productos_actuales

    # SEGUIMIENTO DE MECÁNICA: "¿por qué rechinan las balatas?" y luego
    # "¿y si es un Versa 2015?". Se guarda la pregunta y respuesta
    # anteriores para que el modelo entienda de qué se habla.
    seguimiento_mecanico = detectar_seguimiento_mecanico(
        datos.historial,
        datos.pregunta,
        productos_actuales,
    )

    if seguimiento_mecanico is not None:
        print("[MECÁNICA] Pregunta de seguimiento detectada.", flush=True)

    # RESPUESTAS RÁPIDAS de mecánica (conocimientos_mecanicos.py):
    # preguntas frecuentes con respuesta ya revisada, sin pasar por el modelo.
    # En un seguimiento no se usan: la respuesta rápida no conoce
    # la pregunta anterior.
    if detectar_intencion(datos.pregunta) is None and seguimiento_mecanico is None:
        respuesta_base = buscar_respuesta_rapida(datos.pregunta)

        if respuesta_base is not None:
            print("[MECÁNICA] Respuesta rápida verificada.", flush=True)

            return crear_respuesta_con_contexto(
                respuesta_base,
                contexto,
            )

        # "Falla mi volante": sin síntoma, se pregunta cuál (sin inventar).
        respuesta_falla = respuesta_falla_sin_sintoma(datos.pregunta)
        if respuesta_falla is not None:
            print("[MECÁNICA] Falla sin síntoma: se pide el síntoma.", flush=True)
            return crear_respuesta_con_contexto(respuesta_falla, contexto)

    estado_consulta.seguimiento_mecanico = seguimiento_mecanico
    return None


async def etapa_modelo(estado_consulta: EstadoConsulta):
    """Consulta a Qwen (inventario con herramientas o mecánica)."""
    contexto = estado_consulta.contexto
    datos = estado_consulta.datos
    inicio_consulta = estado_consulta.inicio_consulta
    productos_actuales = estado_consulta.productos_actuales
    seguimiento_mecanico = estado_consulta.seguimiento_mecanico

    # 5. Consultas que requieren comprensión de lenguaje.
    # El modelo se elige en configuracion.py (variable PISTON_MODELO).
    modelo = OllamaChatCompletionClient(**argumentos_ollama())
    
    try:
        # Herramientas del inventario para el modelo
        # (consultar_producto, listar_productos_activos, calcular_venta).
        herramientas_inventario = list(
            crear_herramientas_inventario(
                datos.inventario
            )
        )
        
        # Determinar si la consulta requiere herramientas.
        intencion_inventario = detectar_intencion(datos.pregunta)

        requiere_herramientas = (
            intencion_inventario is not None
            or menciona_inventario(datos.pregunta)
        )

        herramientas_activas = (
            herramientas_inventario
            if requiere_herramientas
            else []
        )
        
        # Instrucciones del modelo (ver asistente/prompts.py).
        mensaje_sistema = REGLA_IDIOMA + (
            INSTRUCCIONES_INVENTARIO
            if requiere_herramientas
            else INSTRUCCIONES_MECANICA
        )

        agente = AssistantAgent(
            name="AsistenteElPiston",
            model_client=modelo,
            tools=herramientas_activas,
            reflect_on_tool_use=True,
            system_message=mensaje_sistema,
        )

        conversacion = "\n".join(
            (
                f"{'Vendedor' if m.rol == 'user' else 'Asistente'}: "
                f"{m.texto}"
            )
            for m in datos.historial[-20:]
            if m.rol in ("user", "model")
        )

        
        
        # Texto del tema (pregunta actual + anteriores en un seguimiento);
        # lo usa también el filtro de seguridad de la respuesta.
        texto_busqueda = datos.pregunta
        conocimiento = None

        if requiere_herramientas:
            tarea = tarea_inventario(
                conversacion,
                datos.pregunta,
            )

        else:
            pregunta_tecnica = normalizar_terminos_automotrices(
                datos.pregunta
            )

            # En un seguimiento ("¿y si es un Versa?") la pregunta sola
            # no dice el tema; se busca junto con las anteriores.
            # Solo se pasan las PREGUNTAS anteriores, no la respuesta:
            # Qwen 3B copia la respuesta anterior y a veces se pasa
            # a portugués a media copia.
            tema_anterior = None
            if seguimiento_mecanico is not None:
                tema_anterior, _ = seguimiento_mecanico
                tema_anterior = normalizar_terminos_automotrices(tema_anterior)
                texto_busqueda = normalizar_terminos_automotrices(
                    f"{tema_anterior} {datos.pregunta}"
                )
            else:
                texto_busqueda = pregunta_tecnica

            conocimiento = buscar_conocimiento(texto_busqueda)

            # Sin documentación técnica, el modelo de 3B inventa respuestas
            # ("el aditivo no actúa como limpiador"). Mejor decirlo claro.
            if conocimiento is None and seguimiento_mecanico is None:
                print("[MECÁNICA] Sin documentación: respuesta fija.", flush=True)

                # "Hallo", "asd qwe": no es una pregunta de mecánica.
                corto = len(re.findall(r"\w+", datos.pregunta)) <= 2

                return crear_respuesta_con_contexto(
                    MENSAJE_NO_ENTENDI if corto else MENSAJE_SIN_DOCUMENTACION,
                    contexto,
                )

            tarea = tarea_mecanica(conocimiento, tema_anterior, pregunta_tecnica)


        inicio_qwen = time.perf_counter()
        
        resultado = await agente.run(task=tarea)

        tiempo_qwen = time.perf_counter() - inicio_qwen
        
        print(
            f"[RENDIMIENTO] {MODELO} respondió en "
            f"{tiempo_qwen:.2f} segundos",
            flush=True,
        )
        
        tiempo_total = time.perf_counter() - inicio_consulta
        
        print(
            f"[RENDIMIENTO] Preparación previa a Qwen: "
            f"{tiempo_total - tiempo_qwen:.2f} segundos",
            flush=True,
        )
        
        respuesta = quitar_razonamiento(str(
            resultado.messages[-1].content
        ))

        if not respuesta:
            raise ValueError(
                "AutoGen no devolvió una respuesta."
            )

        # GUARDIA DE IDIOMA: si el modelo se cambió de idioma
        # por su cuenta (Qwen a veces escribe en inglés o chino),
        # se le pide otra vez en español; si vuelve a fallar,
        # se bloquea la respuesta.
        if not es_texto_en_espanol(respuesta):
            print(
                "[IDIOMA] Respuesta fuera de español. Reintentando.",
                flush=True,
            )

            agente_espanol = AssistantAgent(
                name="AsistenteElPistonEspanol",
                model_client=modelo,
                tools=herramientas_activas,
                reflect_on_tool_use=True,
                system_message=mensaje_sistema,
            )

            resultado = await agente_espanol.run(
                task=(
                    "IMPORTANTE: tu respuesta anterior no estaba en "
                    "español. Responde de nuevo ÚNICAMENTE en español "
                    "de México.\n\n" + tarea
                )
            )

            respuesta = quitar_razonamiento(str(
                resultado.messages[-1].content
            ))

            if not respuesta or not es_texto_en_espanol(respuesta):
                print(
                    "[IDIOMA] Respuesta bloqueada por no estar en español.",
                    flush=True,
                )

                respuesta = (
                    "No pude generar una respuesta adecuada. Por favor "
                    "reformula tu consulta sobre refacciones, inventario, "
                    "precios o mecánica automotriz."
                )
            
        # VALIDACIÓN DE INVENTARIO: todo precio, existencia o código que
        # escriba el modelo debe salir del inventario o de una herramienta.
        # Si inventó algo, se descarta y se responde con datos reales.
        if requiere_herramientas:
            validacion = validar_respuesta_inventario(
                respuesta,
                productos_actuales,
                textos_de_herramientas(resultado.messages),
                pregunta=datos.pregunta,
            )

            if not validacion.valida:
                print(
                    "[VALIDADOR] Respuesta del modelo descartada: "
                    + "; ".join(validacion.motivos),
                    flush=True,
                )

                respuesta = respuesta_de_respaldo(
                    datos.pregunta,
                    productos_actuales,
                )

        # Correcciones a la respuesta de mecánica (ver filtros_respuesta.py).
        if not requiere_herramientas:
            respuesta = ajustar_respuesta_mecanica(
                respuesta, datos.pregunta, texto_busqueda, conocimiento
            )

            # Si el modelo mencionó síntomas o piezas que no vienen de la
            # pregunta ni de la documentación, inventó: se contesta con la
            # documentación revisada (ver validador_mecanica.py).
            if conocimiento:
                inventados = terminos_inventados(
                    respuesta, f"{datos.pregunta} {texto_busqueda}", conocimiento
                )
                if inventados:
                    respaldo = respuesta_desde_documentacion(conocimiento)
                    if respaldo:
                        print(
                            "[VALIDADOR MECÁNICA] Respuesta descartada; inventó: "
                            + ", ".join(inventados),
                            flush=True,
                        )
                        respuesta = respaldo

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












