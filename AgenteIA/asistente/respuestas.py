from AgenteIA.inventario.contexto_inventario import (
    ContextoInventario,
    contexto_a_diccionario,
)


def crear_respuesta_con_contexto(
    respuesta: str,
    contexto: ContextoInventario,
    producto: dict | None = None,
) -> dict:

    if producto is not None:
        contexto.codigo_seleccionado = str(
            producto.get("codigo", "")
        ).strip() or None

        # Recordar también su categoría ("¿y otra más barata?").
        if producto.get("categoria") and hasattr(contexto, "categoria_consultada"):
            contexto.categoria_consultada = str(producto.get("categoria"))

    return {
        "respuesta": respuesta,
        "contexto": contexto_a_diccionario(contexto),
    }


def respuesta_sin_cambios(texto: str, datos) -> dict:
    # Respuesta que conserva el contexto tal como llegó.
    return {
        "respuesta": texto,
        "contexto": contexto_a_diccionario(datos.contexto),
    }
