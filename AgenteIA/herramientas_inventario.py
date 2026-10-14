import json

def crear_herramientas_inventario(inventario_json: str):
    
    productos = json.loads(inventario_json)

    if not isinstance(productos, list):
        raise ValueError("El inventario debe ser una lista JSON.")

    def consultar_producto(busqueda: str) -> str:
        
        print(
            f"[AUTOGEN] Se ejecuto consultar_producto('{busqueda}')",
            flush=True
        )
        
        termino = busqueda.strip().casefold()

        if not termino:
            return json.dumps({
                "error": "Debes indicar un producto o categoría."
            }, ensure_ascii=False)

        encontrados = [
            producto
            for producto in productos
            if any(
                termino in str(producto.get(campo, "")).casefold()
                for campo in ("codigo", "nombre", "marca", "categoria")
            )
        ]

        if not encontrados:
            return json.dumps({
                "encontrados": 0,
                "mensaje": "No se encontraron productos activos."
            }, ensure_ascii=False)

        return json.dumps({
            "encontrados": len(encontrados),
            "productos": encontrados
        }, ensure_ascii=False)

    def listar_productos_activos() -> str:
        
        print(
            "[AUTOGEN] Se ejecuto listar_productos_activos()",
            flush=True
        )
      
        return json.dumps({
            "total": len(productos),
            "productos": productos
        }, ensure_ascii=False)

    return consultar_producto, listar_productos_activos
