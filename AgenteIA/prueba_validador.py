from AgenteIA.validador_inventario import (
    responder_existencia,
    responder_precio,
    responder_compatibilidad,
)


producto = {
    "codigo": "ACE-001",
    "nombre": "Aceite de Motor 5W-30",
    "precioMXN": 749,
    "existencia": 5,
    "universal": True,
    "vehiculosCompatibles": ["Universal"]
}

print("\n===== EXISTENCIAS =====")
print(responder_existencia(producto))

print("\n===== PRECIO =====")
print(responder_precio(producto))

print("\n===== COMPATIBILIDAD =====")
print(responder_compatibilidad(producto, "Toyota Corolla 2016"))

# Simular una venta de dos unidades
producto["existencia"] = 3

print("\n===== DESPUÉS DE LA VENTA =====")
print(responder_existencia(producto))
