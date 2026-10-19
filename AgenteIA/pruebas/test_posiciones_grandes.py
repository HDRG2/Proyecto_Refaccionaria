from AgenteIA.inventario.contexto_inventario import (
    ContextoInventario,
    resolver_posicion_lista,
)

# Crear 15 productos únicamente para la prueba.
productos = [
    {
        "codigo": f"PRU-{numero:03d}",
        "nombre": f"Producto de prueba {numero}",
        "existencia": 20,
        "precio": numero * 100,
    }
    for numero in range(1, 16)
]

# Simular la lista que el chatbot guarda.
contexto = ContextoInventario(
    codigo_seleccionado=None,
    codigos_lista=[
        producto["codigo"]
        for producto in productos
    ],
)

preguntas = [
    "¿Cuánto cuesta el producto número 12?",
    "¿Cuántas piezas tiene el producto 15?",
    "¿Qué precio tiene el número 11?",
    "¿Cuánto cuesta el producto número 20?",
]

for pregunta in preguntas:
    estado, producto = resolver_posicion_lista(
        pregunta,
        contexto,
        productos,
    )

    print(f"\nPregunta: {pregunta}")
    print(f"Estado: {estado}")

    if producto is not None:
        print(f"Producto: {producto['nombre']}")
        print(f"Código: {producto['codigo']}")
    else:
        print("No se encontró un producto en esa posición.")
