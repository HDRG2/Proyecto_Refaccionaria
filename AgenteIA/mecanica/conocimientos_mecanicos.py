import re
import unicodedata


CONOCIMIENTOS_MECANICOS = {
    # --- Respuestas originales (el servidor las sigue usando) ---
    "amortiguador_resorte": (
        "El resorte de suspensión soporta parte del peso del vehículo, "
        "permite que la suspensión se comprima y se extienda, y ayuda a "
        "mantener la altura del automóvil. El amortiguador controla las "
        "oscilaciones del resorte y de la suspensión mediante resistencia "
        "hidráulica, evitando rebotes excesivos. Ambos componentes trabajan "
        "juntos para mejorar la estabilidad y mantener el contacto de los "
        "neumáticos con el pavimento."
    ),

    "riesgos_amortiguadores": (
        "Conducir con amortiguadores en mal estado puede provocar rebotes "
        "excesivos, menor estabilidad y pérdida de adherencia de los "
        "neumáticos en determinadas condiciones. También puede aumentar la "
        "distancia de frenado en ciertas situaciones y favorecer el desgaste "
        "irregular de las llantas. Se recomienda revisar la suspensión con "
        "un mecánico y reemplazar los componentes defectuosos."
    ),

    "riesgos_balatas": (
        "Conducir con balatas desgastadas puede reducir la eficacia del "
        "frenado y aumentar la distancia necesaria para detener el vehículo. "
        "Si el material de fricción se agota, el contacto metálico puede "
        "dañar los discos de freno. También pueden presentarse ruidos, "
        "vibraciones y mayor riesgo de accidentes. Es importante realizar "
        "una revisión profesional y reemplazar las balatas cuando corresponda."
    ),

    # --- Respuestas nuevas ---
    "bateria_alternador": (
        "La batería (acumulador) almacena energía y la entrega para arrancar "
        "el motor. El alternador genera electricidad mientras el motor está "
        "funcionando y recarga la batería. Una batería descargada no "
        "demuestra por sí sola que el alternador esté mal: puede deberse a "
        "una batería envejecida, conexiones deficientes o consumo eléctrico "
        "con el auto apagado. Para saberlo se mide el voltaje del sistema "
        "de carga y el estado de la batería."
    ),

    "banda_distribucion_accesorios": (
        "La banda (o cadena) de distribución sincroniza el cigüeñal con los "
        "árboles de levas; si se rompe, en muchos motores puede causar daños "
        "internos graves, por eso se cambia según el intervalo del "
        "fabricante. La banda de accesorios mueve componentes como el "
        "alternador, la bomba de dirección o el compresor del clima. "
        "No son la misma pieza."
    ),

    "check_engine": (
        "El testigo de check engine indica que la computadora detectó una "
        "falla relacionada con el motor o las emisiones. Si está encendido "
        "fijo, conviene revisarlo pronto con un escáner. Si parpadea, suele "
        "indicar una falla de encendido importante que puede dañar el "
        "catalizador: reduce la carga del motor, evita acelerar fuerte y "
        "solicita revisión lo antes posible. El código de falla orienta, "
        "pero no siempre indica qué pieza cambiar."
    ),

    "presion_llantas": (
        "La presión correcta de las llantas la indica el fabricante del "
        "vehículo, normalmente en una etiqueta en el marco de la puerta del "
        "conductor o en el manual. Se mide con las llantas frías. No se "
        "debe usar la presión máxima que viene impresa en la llanta como "
        "presión de uso."
    ),

    "aceite_sintetico_mineral": (
        "El aceite mineral se obtiene directamente de la refinación del "
        "petróleo; el sintético se elabora con bases más refinadas o "
        "fabricadas, que suelen soportar mejor las temperaturas altas y "
        "conservar sus propiedades por más tiempo. El semisintético es una "
        "mezcla. El tipo y la viscosidad correctos los indica el fabricante "
        "del motor; no conviene elegir solo por precio o por ser sintético."
    ),

    "intervalo_aceite": (
        "El intervalo de cambio de aceite y filtro lo define el fabricante "
        "según el motor, el tipo de aceite y las condiciones de uso (tráfico "
        "pesado, carreteras con polvo, remolque). No existe un kilometraje "
        "único para todos los autos; consulta el manual del vehículo y "
        "revisa el nivel de aceite periódicamente."
    ),

    "funcion_termostato": (
        "El termostato regula el paso del refrigerante hacia el radiador "
        "según la temperatura del motor: se mantiene cerrado mientras el "
        "motor está frío para que se caliente más rápido, y se abre cuando "
        "alcanza su temperatura de trabajo. Un termostato atascado puede "
        "provocar sobrecalentamiento o que el motor tarde en calentarse, "
        "pero una temperatura alta no confirma por sí sola que el "
        "termostato esté dañado."
    ),

    "funcion_abs": (
        "El ABS (sistema antibloqueo de frenos) evita que las ruedas se "
        "bloqueen durante un frenado fuerte, para que el conductor conserve "
        "el control de la dirección. Si el testigo del ABS se enciende, el "
        "freno normal suele seguir funcionando, pero el sistema antibloqueo "
        "puede no estar activo; conviene revisarlo con escáner."
    ),

    "funcion_filtro_aceite": (
        "El filtro de aceite retiene partículas y contaminantes que el "
        "aceite arrastra del motor, para que el aceite que vuelve a "
        "circular esté limpio. Normalmente se cambia junto con el aceite, "
        "según el programa del fabricante."
    ),

    "funcion_bujias": (
        "Las bujías generan la chispa que enciende la mezcla de aire y "
        "combustible dentro de cada cilindro. Bujías desgastadas pueden "
        "causar tirones, marcha irregular, mayor consumo y dificultad para "
        "arrancar. El intervalo de cambio y el tipo correcto dependen del "
        "motor; se consultan en el manual del fabricante."
    ),

    "que_hacer_sobrecalentamiento": (
        "Si el motor se sobrecalienta: detente en un lugar seguro y apaga "
        "el motor. No abras la tapa del radiador ni del depósito de "
        "refrigerante mientras estén calientes, porque el sistema está a "
        "presión y hay riesgo de quemaduras. Espera a que el motor se "
        "enfríe por completo antes de revisar el nivel de refrigerante o "
        "buscar fugas, y solicita una revisión profesional antes de seguir "
        "manejando."
    ),

    "ruido_al_frenar": (
        "Un rechinido o chirrido al frenar suele relacionarse con las "
        "balatas: muchas traen un indicador metálico que rechina cuando ya "
        "están por terminarse. También puede deberse a discos rayados o "
        "cristalizados, balatas contaminadas o de baja calidad, o falta de "
        "lubricación en las guías de la pinza. Un ruido metálico fuerte "
        "puede indicar contacto de metal con metal, que daña los discos. "
        "El ruido por sí solo no confirma qué pieza falla: conviene revisar "
        "pronto el espesor de las balatas y el estado de los discos."
    ),

    "juego_volante": (
        "El juego u holgura en el volante (cuando gira un poco sin que las "
        "ruedas respondan) suele deberse a desgaste en terminales de "
        "dirección, rótulas, bujes o en la caja o cremallera de dirección. "
        "Una dirección con holgura reduce el control del vehículo, así que "
        "conviene revisarla pronto en un taller antes de cambiar piezas."
    ),

    "volante_duro": (
        "Un volante duro suele relacionarse con la asistencia de la "
        "dirección: nivel bajo o fugas de líquido en direcciones "
        "hidráulicas, bomba de dirección con fallas o banda de accesorios "
        "floja o dañada; en direcciones eléctricas, una falla del sistema "
        "de asistencia. La presión baja de las llantas también lo endurece. "
        "Si se endurece de golpe al manejar, conviene detenerse en un lugar "
        "seguro y revisarlo."
    ),

    "vibracion_al_frenar": (
        "Si el volante o el pedal vibran al frenar, una causa frecuente es "
        "una variación en el espesor de los discos de freno (lo que suele "
        "llamarse disco alabeado). También pueden influir las llantas o "
        "componentes de suspensión en mal estado. La vibración por sí sola "
        "no confirma que el disco esté dañado; conviene medir los discos y "
        "revisar los frenos pronto."
    ),

    "vibracion_en_velocidad": (
        "Una vibración que aparece a cierta velocidad, por ejemplo en "
        "carretera, y se siente en el volante suele relacionarse con el "
        "balanceo de las llantas delanteras. También puede deberse a una "
        "llanta deformada o dañada, un rin golpeado o desgaste en rótulas "
        "y terminales de dirección. Si vibra sobre todo al frenar, se "
        "revisan los discos. Lo recomendable es revisar balanceo y estado "
        "de llantas y rines antes de cambiar otras piezas."
    ),

    "que_hacer_testigo_aceite": (
        "Si se enciende el testigo de presión de aceite con el motor "
        "funcionando, detente en un lugar seguro y apaga el motor. Puede "
        "tratarse de una presión realmente baja (por ejemplo, nivel "
        "insuficiente) o de una falla del sensor, pero no se debe asumir "
        "que es una falsa alarma sin comprobarlo. No continúes manejando "
        "hasta revisar el nivel de aceite y determinar la causa."
    ),
}


# ---------------------------------------------------------------------
# Cuándo usar cada respuesta.
# Cada respuesta tiene una lista de GRUPOS. La pregunta debe tener
# al menos una palabra de cada grupo. El orden importa: se usa la
# primera respuesta que coincida.
# ---------------------------------------------------------------------

_RIESGO = ["que pasa", "riesgo", "riesgos", "peligro", "peligroso",
           "consecuencia", "consecuencias", "puedo manejar", "puedo seguir",
           "es grave", "que le pasa", "dano", "danos"]

_DIFERENCIA = ["diferencia", "diferencias", "distingue", "es lo mismo",
               "son lo mismo", "vs", "versus", "cual es mejor"]

_FUNCION = ["para que sirve", "para que sirven", "que es", "que son",
            "que hace", "que hacen", "como funciona", "funcion", "para que es"]

_QUE_HAGO = ["que hago", "que debo hacer", "que hacer", "se prendio",
             "se prende", "se encendio", "se enciende", "esta prendido",
             "significa", "que quiere decir"]

PREGUNTAS_FRECUENTES = [
    ("que_hacer_sobrecalentamiento",
     [["sobrecalienta", "sobrecalento", "sobrecalentamiento", "se calienta",
       "se calento", "calentando", "sale vapor", "echa vapor"],
      ["que hago", "que debo hacer", "que hacer", "puedo seguir",
       "puedo manejar", "es peligroso"]]),

    ("que_hacer_testigo_aceite",
     [["testigo de aceite", "testigo del aceite", "foco del aceite",
       "foco de aceite", "luz del aceite", "luz de aceite",
       "presion de aceite"],
      _QUE_HAGO + ["puedo seguir", "puedo manejar"]]),

    ("amortiguador_resorte",
     [["amortiguador", "amortiguadores"], ["resorte", "resortes", "muelle"],
      _DIFERENCIA + _FUNCION]),

    ("riesgos_amortiguadores",
     [["amortiguador", "amortiguadores"], _RIESGO]),

    ("riesgos_balatas",
     [["balata", "balatas", "pastilla", "pastillas"], _RIESGO]),

    ("juego_volante",
     [["juego", "holgura", "flojo", "floja", "suelto", "suelta"],
      ["volante", "direccion"]]),

    ("volante_duro",
     [["duro", "dura", "pesado", "pesada", "cuesta trabajo", "cuesta girar",
       "se endurecio", "endurece"],
      ["volante", "direccion"]]),

    ("vibracion_al_frenar",
     [["vibra", "vibran", "vibracion", "tiembla", "tiemblan"],
      ["frenar", "frenando", "freno", "frenos", "frena"]]),

    ("ruido_al_frenar",
     [["rechina", "rechinan", "rechinido", "chilla", "chillan", "chirrido",
       "chirria", "ruido", "suena", "suenan", "truena", "truenan"],
      ["frenar", "frenando", "freno", "frenos", "frena", "balata",
       "balatas", "pastilla", "pastillas"]]),

    ("vibracion_en_velocidad",
     [["vibra", "vibran", "vibracion", "tiembla", "tiemblan"],
      ["velocidad", "carretera", "autopista", "km", "kilometros", "rapido"]]),

    ("bateria_alternador",
     [["bateria", "acumulador"], ["alternador"], _DIFERENCIA + _FUNCION]),

    ("banda_distribucion_accesorios",
     [["banda", "correa", "cadena"], ["distribucion", "tiempo"],
      _DIFERENCIA + ["accesorios"]]),

    ("check_engine",
     [["check engine", "check"], _QUE_HAGO + _FUNCION + ["por que"]]),

    ("presion_llantas",
     [["llanta", "llantas", "neumatico", "neumaticos"],
      ["presion", "aire", "libras", "psi"],
      ["cuanto", "cuanta", "cual", "que", "cuantas"]]),

    ("aceite_sintetico_mineral",
     [["sintetico"], ["mineral", "semisintetico", "normal", "convencional"]]),

    ("intervalo_aceite",
     [["aceite"], ["cada cuanto", "cada cuantos", "cuando cambio",
                   "cuando se cambia", "cuando debo cambiar", "cuanto dura"]]),

    ("funcion_termostato", [["termostato"], _FUNCION]),
    ("funcion_abs", [["abs"], _FUNCION + _QUE_HAGO]),
    ("funcion_filtro_aceite", [["filtro de aceite"], _FUNCION]),
    ("funcion_bujias", [["bujia", "bujias"], _FUNCION]),
]


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or "").casefold())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.split())


def _contiene(texto: str, frase: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(frase) + r"(?!\w)", texto) is not None


def buscar_respuesta_rapida(pregunta: str) -> str | None:
    # Devuelve una respuesta revisada si la pregunta coincide con
    # claridad con una pregunta frecuente; si no, None.
    texto = _normalizar(pregunta)

    if not texto:
        return None

    # Si pregunta por precio, existencia o venta, es del inventario.
    if re.search(r"\b(?:precio|cuesta|cuestan|vale|valen|existencia|stock|"
                 r"tienes|tienen|vendo|venden|codigo)\b|\bhay\b(?!\s+que)", texto):
        return None

    for clave, grupos in PREGUNTAS_FRECUENTES:
        if all(any(_contiene(texto, palabra) for palabra in grupo) for grupo in grupos):
            return CONOCIMIENTOS_MECANICOS[clave]

    return None

