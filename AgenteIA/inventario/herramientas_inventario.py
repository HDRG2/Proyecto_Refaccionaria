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

        import re
        import unicodedata

        def normalizar_busqueda(valor):
            texto = unicodedata.normalize("NFKD", str(valor))
            texto = "".join(
                caracter for caracter in texto
                if not unicodedata.combining(caracter)
            )
            return texto.casefold().strip()

        termino = normalizar_busqueda(busqueda)

        if not termino:
            return json.dumps({
                "error": "Debes indicar un producto o categoría."
            }, ensure_ascii=False)

        # 1. Prioridad a coincidencias exactas por código o nombre.
        exactos = [
            producto
            for producto in productos
            if any(
                normalizar_busqueda(producto.get(campo, "")) == termino
                for campo in ("codigo", "nombre")
            )
        ]

        if exactos:
            encontrados = exactos

        else:
            # 2. Buscar frases completas dentro del nombre.
            coincidencias_nombre = [
                producto
                for producto in productos
                if re.search(
                    r"(?<!\w)" + re.escape(termino) + r"(?!\w)",
                    normalizar_busqueda(producto.get("nombre", ""))
                )
            ]

            if coincidencias_nombre:
                encontrados = coincidencias_nombre

            else:
                # 3. Mantener búsquedas por marca y categoría.
                encontrados = [
                    producto
                    for producto in productos
                    if any(
                        termino in normalizar_busqueda(
                            producto.get(campo, "")
                        )
                        for campo in ("marca", "categoria")
                    )
                ]

        if not encontrados:
            return json.dumps({
                "encontrados": 0,
                "mensaje": (
                    "No se encontró una refacción que coincida "
                    "con la búsqueda solicitada. No utilices "
                    "el precio de otro producto."
                )
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
