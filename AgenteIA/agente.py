import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient


async def main():
    modelo = OllamaChatCompletionClient(
        model="qwen2.5:3b",
        model_info={
            "vision": False,
            "function_calling": False,
            "json_output": False,
            "family": "unknown",
            "structured_output": False,
        },
    )

    agente = AssistantAgent(
        name="AsistenteElPiston",
        model_client=modelo,
        system_message=(
            "Eres el asistente virtual de El Pistón, "
            "una refaccionaria automotriz. "
            "Responde siempre en español de México. "
            "Ayuda a los vendedores con preguntas sobre refacciones. "
            "No inventes precios, existencias ni compatibilidades. "
            "Si no tienes acceso al inventario, indícalo."
        ),
    )

    try:
        resultado = await agente.run(
            task="¿Para qué sirve un amortiguador delantero?"
        )

        print("\n===== RESPUESTA DE AUTOGEN =====\n")
        print(resultado.messages[-1].content)

    finally:
        await modelo.close()


if __name__ == "__main__":
    asyncio.run(main())
