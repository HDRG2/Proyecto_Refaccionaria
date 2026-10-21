import argparse
import asyncio
import contextlib
import importlib
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path


# Preguntas que llegan al modelo (no las contestan las reglas).
# Agrega aquí las que te hayan dado problemas en pruebas reales.
PREGUNTAS = [
    # Mecánica
    "¿Para qué sirve el termostato?",
    "Mi carro hace un rechinido al frenar, ¿qué puede ser?",
    "Mi motor se sobrecalienta en el tráfico, ¿qué hago?",
    "¿Cuál es la diferencia entre la banda de accesorios y la de distribución?",
    "¿Qué pasa si manejo con poco aceite?",
    "El carro tarda en arrancar en las mañanas",
    "¿Es peligroso manejar con la dirección dura?",
    # Inventario abiertas (van al modelo con herramientas)
    "¿Qué me recomiendas para el cambio de aceite de un cliente?",
    "Un cliente quiere hacer servicio de frenos, ¿qué productos le ofrezco?",
    "¿Qué refacción de las que tenemos sirve para mantenimiento preventivo?",
    # Fuera de tema / manipulación suave
    "¿Quién ganó el partido de ayer?",
    "Escríbeme un poema sobre balatas",
]

INVENTARIO_EJEMPLO = [
    {"codigo": "ACE-001", "nombre": "Aceite de Motor 5W-30", "marca": "Mobil",
     "categoria": "Aceites", "precio": 250.0, "existencia": 12, "universal": False},
    {"codigo": "FIL-001", "nombre": "Filtro de Aceite", "marca": "Gonher",
     "categoria": "Filtros", "precio": 89.5, "existencia": 3, "universal": True},
    {"codigo": "BAL-001", "nombre": "Balatas Delanteras", "marca": "Brembo",
     "categoria": "Frenos", "precio": 1250.0, "existencia": 4, "universal": False},
    {"codigo": "LIQ-001", "nombre": "Líquido de Frenos DOT 4", "marca": "Bosch",
     "categoria": "Frenos", "precio": 145.0, "existencia": 0, "universal": True},
    {"codigo": "BUJ-001", "nombre": "Bujía de Iridio", "marca": "NGK",
     "categoria": "Encendido", "precio": 180.0, "existencia": 20, "universal": False},
]

MARCAS_FILTROS = {
    "[VALIDADOR] Respuesta del modelo descartada": "inventó datos",
    "[IDIOMA] Respuesta fuera de español": "cambió de idioma",
    "[IDIOMA] Respuesta bloqueada": "bloqueada por idioma",
    "[ERROR AUTOGEN]": "error",
}


def _cargar_procesar_consulta():
    # servidor.py puede estar en distintas carpetas según el proyecto.
    for nombre in ("servidor", "AgenteIA.servidor", "AgenteIA.asistente.servidor"):
        try:
            modulo = importlib.import_module(nombre)
            return modulo.procesar_consulta, modulo.Consulta
        except ModuleNotFoundError:
            continue
    sys.exit(
        "No encontré servidor.py. Corre el script desde la carpeta que "
        "contiene servidor.py y AgenteIA."
    )


async def _correr_un_modelo(inventario: str) -> list[dict]:
    procesar_consulta, Consulta = _cargar_procesar_consulta()
    resultados = []

    for pregunta in PREGUNTAS:
        salida = io.StringIO()
        inicio = time.perf_counter()
        try:
            with contextlib.redirect_stdout(salida):
                resultado = await procesar_consulta(
                    Consulta(pregunta=pregunta, inventario=inventario)
                )
            respuesta = resultado.get("respuesta", "") if isinstance(resultado, dict) else str(resultado)
        except Exception as error:  # noqa: BLE001
            respuesta = f"ERROR: {type(error).__name__}: {error}"
        segundos = time.perf_counter() - inicio

        registro = salida.getvalue()
        filtros = [texto for marca, texto in MARCAS_FILTROS.items() if marca in registro]
        uso_modelo = "[RENDIMIENTO]" in registro

        resultados.append({
            "pregunta": pregunta,
            "respuesta": respuesta,
            "segundos": round(segundos, 2),
            "filtros": filtros,
            "uso_modelo": uso_modelo,
        })
        print(f"  {segundos:5.1f}s  {pregunta}", file=sys.stderr, flush=True)

    return resultados


def _modo_hijo():
    # Se ejecuta en un proceso aparte por modelo, porque configuracion.py
    # lee PISTON_MODELO al importarse.
    inventario = Path(os.environ["PISTON_INVENTARIO_ARCHIVO"]).read_text(encoding="utf-8")
    resultados = asyncio.run(_correr_un_modelo(inventario))
    sys.stdout.write("\n@@RESULTADOS@@" + json.dumps(resultados, ensure_ascii=False))


def _reporte(por_modelo: dict[str, list[dict]]) -> str:
    modelos = list(por_modelo)
    lineas = ["# Comparación de modelos", ""]

    lineas += ["| Modelo | Tiempo promedio | Tiempo máximo | Veces que un filtro intervino |",
               "|---|---|---|---|"]
    for modelo, resultados in por_modelo.items():
        tiempos = [r["segundos"] for r in resultados if r["uso_modelo"]] or [0]
        intervenciones = sum(1 for r in resultados if r["filtros"])
        lineas.append(
            f"| `{modelo}` | {sum(tiempos) / len(tiempos):.1f} s | {max(tiempos):.1f} s | "
            f"{intervenciones} de {len(resultados)} |"
        )
    lineas += ["", "Revisa sobre todo: ¿inventa datos?, ¿responde lo que se preguntó?, "
               "¿da las advertencias de seguridad?, ¿se mantiene en español?", ""]

    for i, pregunta in enumerate(PREGUNTAS):
        lineas += [f"## {i + 1}. {pregunta}", ""]
        for modelo in modelos:
            r = por_modelo[modelo][i]
            notas = f" — filtros: {', '.join(r['filtros'])}" if r["filtros"] else ""
            if not r["uso_modelo"]:
                notas += " — (respondió una regla, no el modelo)"
            lineas += [f"**`{modelo}`** ({r['segundos']} s){notas}", "",
                       "> " + r["respuesta"].replace("\n", "\n> "), ""]
    return "\n".join(lineas)


def main():
    if os.environ.get("PISTON_MODO_HIJO") == "1":
        _modo_hijo()
        return

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("modelos", nargs="+", help="p. ej. qwen2.5:3b qwen3.5:4b")
    parser.add_argument("--inventario", help="archivo JSON con el inventario")
    parser.add_argument("--salida", default="comparacion_modelos.md")
    args = parser.parse_args()

    if args.inventario:
        archivo_inventario = Path(args.inventario).resolve()
    else:
        archivo_inventario = Path("inventario_ejemplo_comparacion.json").resolve()
        archivo_inventario.write_text(json.dumps(INVENTARIO_EJEMPLO, ensure_ascii=False), encoding="utf-8")

    por_modelo = {}
    for modelo in args.modelos:
        print(f"\n== {modelo} ==", file=sys.stderr, flush=True)
        entorno = {
            **os.environ,
            "PISTON_MODO_HIJO": "1",
            "PISTON_MODELO": modelo,
            "PISTON_INVENTARIO_ARCHIVO": str(archivo_inventario),
            "PYTHONIOENCODING": "utf-8",
        }
        proceso = subprocess.run(
            [sys.executable, __file__], env=entorno, cwd=os.getcwd(),
            stdout=subprocess.PIPE, text=True, encoding="utf-8",
        )
        if "@@RESULTADOS@@" not in proceso.stdout:
            sys.exit(f"Falló la prueba con {modelo}. ¿Hiciste 'ollama pull {modelo}'?")
        por_modelo[modelo] = json.loads(proceso.stdout.split("@@RESULTADOS@@")[-1])

    Path(args.salida).write_text(_reporte(por_modelo), encoding="utf-8")
    print(f"\nReporte guardado en {args.salida}", file=sys.stderr)


if __name__ == "__main__":
    # El proceso hijo necesita encontrar AgenteIA desde la carpeta actual.
    sys.path.insert(0, os.getcwd())
    main()
