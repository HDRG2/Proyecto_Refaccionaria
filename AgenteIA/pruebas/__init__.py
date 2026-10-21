import os

# Las pruebas no escriben en registro/preguntas_no_entendidas.txt.
os.environ.setdefault("PISTON_SIN_REGISTRO", "1")
