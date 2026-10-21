import os
import re

# Modelo local de Ollama. Para probar otro sin tocar el código:
#   Windows (PowerShell):  $env:PISTON_MODELO = "qwen3.5:4b"
#   Windows (cmd):         set PISTON_MODELO=qwen3.5:4b
# y vuelve a arrancar el servidor.
MODELO = os.getenv("PISTON_MODELO", "qwen2.5:3b").strip()

OLLAMA_HOST = os.getenv("PISTON_OLLAMA_HOST", "http://127.0.0.1:11434").strip()

TEMPERATURA = float(os.getenv("PISTON_TEMPERATURA", "0.1"))


# Los modelos nuevos de Qwen (qwen3, qwen3.5, ...) "piensan" antes de
# responder: tardan mucho más y a veces dejan el razonamiento en la
# respuesta. Para este asistente se apaga.
# qwen2.5 no piensa, y si se le manda think=False Ollama puede
# rechazar la consulta, así que solo se manda a los que sí piensan.
_FAMILIAS_QUE_PIENSAN = re.compile(r"^(?:qwen3|deepseek-r1|qwq|gpt-oss|magistral)", re.IGNORECASE)


def modelo_piensa(modelo: str = MODELO) -> bool:
    return _FAMILIAS_QUE_PIENSAN.match(modelo) is not None


def argumentos_ollama(modelo: str = MODELO) -> dict:
    # Argumentos para OllamaChatCompletionClient.
    argumentos = {
        "model": modelo,
        "host": OLLAMA_HOST,
        "options": {"temperature": TEMPERATURA, "num_ctx": 4096},
        "model_info": {
            "vision": False,
            "function_calling": True,
            "json_output": False,
            "family": "unknown",
            "structured_output": False,
        },
    }
    if modelo_piensa(modelo):
        # Requiere el paquete "ollama" >= 0.5 (pip install -U ollama).
        # Si es más viejo, autogen descarta este argumento sin avisar;
        # por eso filtros_respuesta.quitar_razonamiento() limpia
        # cualquier <think>...</think> que llegue en la respuesta.
        argumentos["think"] = False
    return argumentos
