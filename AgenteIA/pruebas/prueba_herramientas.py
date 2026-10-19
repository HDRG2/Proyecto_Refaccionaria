
import json

from AgenteIA.inventario.herramientas_inventario import crear_herramientas_inventario


# Inventario de ejemplo para comprobar la herramienta
inventario = json.dumps([
    {
        "codigo": "ACE-001",
        "nombre": "Aceite de Motor 5W-30",
        "precioMXN": 749,
        "existencia": 5
    }
])

# Crear las herramientas
consultar, listar = crear_herramientas_inventario(inventario)

# Consultar el aceite
print("\n===== CONSULTA DE PRODUCTO =====")
print(consultar("ACE-001"))

# Listar todos los productos
print("\n===== PRODUCTOS ACTIVOS =====")
print(listar())
