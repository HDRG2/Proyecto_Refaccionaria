# Base de conocimiento automotriz de El Pistón.
# Información orientativa: no sustituye un diagnóstico presencial ni manual del fabricante.
import re
import unicodedata

DOCUMENTACION_AUTOMOTRIZ = {
   "sistema_frenos": {
        "palabras_clave": [
            "freno", "frenos", "balata", "balatas",
            "pastilla", "pastillas", "disco de freno",
            "liquido de frenos", "abs", "pedal de freno",
            "caliper", "pinza de freno", "frenado",
            "chirrido", "rechinido", "ruido al frenar"
        ],
        "contenido": (
            "FUNCIÓN: El sistema de frenos permite reducir la "
            "velocidad y detener el vehículo. En los frenos "
            "de disco, las pastillas presionan el disco para "
            "generar fricción. El líquido de frenos transmite "
            "la presión hidráulica desde el pedal. "

            "SÍNTOMAS: Chirridos, rechinidos metálicos, "
            "vibraciones al frenar, pedal esponjoso, "
            "desviación lateral, aumento de la distancia "
            "de frenado o pérdida de eficacia. "

            "CAUSAS DE RUIDOS: Un chirrido puede relacionarse "
            "con desgaste de pastillas, indicadores de desgaste, "
            "contaminación, vibración o condiciones de contacto. "
            "Un rechinido metálico intenso puede indicar "
            "contacto entre superficies metálicas. "
            "El ruido por sí solo no confirma una pieza dañada. "

            "CAUSAS DE VIBRACIÓN: Pueden incluir variaciones "
            "en el espesor del disco, irregularidades "
            "de contacto u otros problemas mecánicos. "
            "No se debe confirmar un disco deformado "
            "únicamente por sentir vibraciones. "

            "CAUSAS DE PEDAL ESPONJOSO: Puede existir aire "
            "en el circuito hidráulico, fugas u otros "
            "problemas del sistema. Un pedal esponjoso "
            "no debe atribuirse automáticamente al "
            "desgaste de las balatas. "

            "CONSECUENCIAS: Las pastillas excesivamente "
            "desgastadas pueden dañar los discos. "
            "Las fugas hidráulicas pueden reducir "
            "gravemente la capacidad de frenado. "

            "DIAGNÓSTICO: Inspeccionar el espesor de "
            "pastillas y discos, comprobar fugas, "
            "nivel y estado del líquido, funcionamiento "
            "de las pinzas y códigos del ABS cuando "
            "corresponda. Confirmar las causas mediante "
            "una inspección adecuada. "

            "SEGURIDAD: Si existe pérdida notable "
            "de frenado, pedal sin presión o fuga "
            "hidráulica importante, no continuar "
            "conduciendo y solicitar asistencia."
        ),
    },
     "sistema_suspension": {
        "palabras_clave": [
            "suspension", "amortiguador", "amortiguadores",
            "resorte", "resortes", "rotula", "rotulas",
            "buje", "bujes", "estabilizadora",
            "rebote", "rebotes", "golpeteo",
            "baches", "desgaste de llantas"
        ],
        "contenido": (
            "FUNCIÓN: La suspensión contribuye a mantener "
            "el contacto de las llantas con el pavimento "
            "y favorece la estabilidad, el control "
            "y la comodidad del vehículo. "

            "DIFERENCIA ENTRE RESORTE Y AMORTIGUADOR: "
            "El resorte soporta parte del peso del vehículo "
            "y absorbe movimientos verticales. "
            "El amortiguador controla las oscilaciones "
            "del resorte y la suspensión. "
            "No realizan exactamente la misma función. "

            "SÍNTOMAS: Rebotes excesivos, golpeteos "
            "al pasar baches, inclinación anormal, "
            "inestabilidad, movimientos excesivos "
            "de la carrocería o desgaste irregular "
            "de las llantas. "

            "CAUSAS DE REBOTES: Pueden relacionarse "
            "con amortiguadores que han perdido "
            "capacidad de amortiguación. "
            "Sin embargo, los rebotes no confirman "
            "por sí solos una falla específica. "

            "CAUSAS DE GOLPETEOS: Pueden incluir "
            "bujes deteriorados, rótulas con holgura, "
            "soportes dañados, componentes flojos "
            "u otros elementos de suspensión. "
            "No atribuir todos los golpes "
            "a los amortiguadores. "

            "CONSECUENCIAS: Una suspensión deteriorada "
            "puede reducir la estabilidad y la "
            "adherencia, afectar el control del "
            "vehículo y acelerar el desgaste "
            "de las llantas. "

            "DIAGNÓSTICO: Revisar holguras, fugas "
            "en amortiguadores, estado de resortes, "
            "bujes, rótulas, soportes, llantas "
            "y alineación cuando corresponda. "

            "SEGURIDAD: Si existen componentes "
            "sueltos, inestabilidad severa o "
            "pérdida de control, no continuar "
            "conduciendo hasta revisar el vehículo."
        ),
    },

    "sistema_electrico": {
        "palabras_clave": [
            "alternador", "bateria", "arranque",
            "fusible", "fusibles", "cableado",
            "voltaje", "motor de arranque",
            "no enciende", "luces tenues",
            "se descarga", "testigo de bateria",
            "sistema de carga"
        ],
        "contenido": (
            "FUNCIÓN: La batería suministra energía "
            "eléctrica para el arranque y otros "
            "sistemas. El alternador genera "
            "electricidad con el motor en marcha "
            "y contribuye a recargar la batería. "

            "SÍNTOMAS: Arranque lento, dificultad "
            "para encender, luces tenues, "
            "testigo de batería, fallas eléctricas "
            "o descarga recurrente. "

            "CAUSAS DE DESCARGA: Una batería "
            "envejecida, alternador o regulador "
            "defectuoso, conexiones deficientes, "
            "correa dañada o consumo eléctrico "
            "excesivo con el vehículo apagado. "

            "DIFERENCIA ENTRE BATERÍA Y ALTERNADOR: "
            "La batería almacena energía. "
            "El alternador genera energía "
            "mientras el motor está funcionando. "
            "Una batería descargada no demuestra "
            "automáticamente que el alternador "
            "esté defectuoso. "

            "CAUSAS DE FALLAS DE ARRANQUE: "
            "Pueden relacionarse con batería "
            "descargada, conexiones deficientes, "
            "motor de arranque o circuitos "
            "de control. Se debe distinguir "
            "entre un motor que no gira "
            "y uno que gira pero no enciende. "

            "CONSECUENCIAS: Un problema en el "
            "sistema de carga puede descargar "
            "la batería y provocar fallas "
            "eléctricas o la detención "
            "del vehículo. "

            "DIAGNÓSTICO: Comprobar el estado de la batería, "
            "terminales, conexiones eléctricas, correa de "
            "accesorios que acciona el alternador cuando "
            "corresponda, voltaje del sistema de carga y "
            "consumo eléctrico en reposo según las "
            "especificaciones del fabricante. "
            "No confundir la correa de accesorios con "
            "la correa de distribución. "

            "SEGURIDAD: Evitar cortocircuitos, "
            "respetar la polaridad y seguir "
            "el procedimiento del fabricante "
            "antes de intervenir componentes "
            "eléctricos."
        ),
    },
    "sistema_refrigeracion": {
        "palabras_clave": [
            "sobrecalentamiento", "sobrecalienta",
            "radiador", "termostato",
            "anticongelante", "refrigerante",
            "bomba de agua", "temperatura del motor",
            "ventilador", "ventiladores",
            "se calienta", "fuga de refrigerante"
        ],
        "contenido": (
            "FUNCIÓN: El sistema de refrigeración "
            "regula la temperatura del motor. "
            "El refrigerante transporta calor "
            "y componentes como radiador, "
            "bomba de agua, termostato "
            "y ventiladores ayudan a disiparlo. "

            "SÍNTOMAS: Temperatura elevada, "
            "vapor, pérdida de refrigerante, "
            "fugas, funcionamiento irregular "
            "de la calefacción o advertencias "
            "de temperatura. "

            "CAUSAS POSIBLES: Nivel insuficiente "
            "de refrigerante, fugas, termostato "
            "atascado, radiador obstruido, "
            "ventilador defectuoso, problemas "
            "de circulación o bomba de agua "
            "deteriorada. "

            "CONSECUENCIAS: Continuar utilizando "
            "un motor sobrecalentado puede "
            "provocar daños en la junta "
            "de culata, deformaciones "
            "de componentes o averías "
            "internas graves. "

            "DIAGNÓSTICO: Comprobar el nivel "
            "de refrigerante con el motor frío, "
            "inspeccionar fugas y revisar "
            "el funcionamiento de ventiladores, "
            "termostato y circulación "
            "según procedimientos técnicos. "
            "Una temperatura elevada "
            "no confirma por sí sola "
            "que el termostato esté dañado. "

            "SEGURIDAD: Si el motor presenta "
            "sobrecalentamiento, detenerse "
            "de manera segura y apagarlo. "
            "Nunca abrir la tapa de un "
            "sistema de refrigeración "
            "presurizado mientras esté caliente, "
            "debido al riesgo de quemaduras."
        ),
    },
   "sistema_lubricacion": {
        "palabras_clave": [
            "aceite", "aceite de motor",
            "lubricacion", "presion de aceite",
            "baja presion de aceite",
            "bomba de aceite", "filtro de aceite",
            "testigo de aceite", "sensor de aceite",
            "sensor de presion de aceite",
            "fuga de aceite"
        ],
        "contenido": (
            "FUNCIÓN: El sistema de lubricación "
            "distribuye aceite para reducir "
            "la fricción y el desgaste "
            "de componentes internos "
            "del motor. También contribuye "
            "a disipar calor y transportar "
            "contaminantes hacia el filtro. "

            "SÍNTOMAS: Encendido del testigo "
            "de presión de aceite, ruidos "
            "metálicos, nivel bajo, "
            "fugas o consumo excesivo "
            "de aceite. "

            "CAUSAS DE BAJA PRESIÓN REAL: "
            "Nivel insuficiente de aceite, "
            "problemas de alimentación "
            "o circulación, bomba de aceite "
            "defectuosa, obstrucciones "
            "o desgaste interno del motor. "
            "La viscosidad inadecuada "
            "también puede afectar "
            "la presión según las condiciones. "

            "FALLAS DEL SENSOR: Un sensor "
            "de presión defectuoso, "
            "problemas de cableado "
            "o fallas del circuito "
            "de medición pueden provocar "
            "una advertencia incorrecta. "
            "Una falla del sensor "
            "no significa necesariamente "
            "que la presión real "
            "del aceite sea baja. "

            "DIFERENCIA IMPORTANTE: "
            "La baja presión real "
            "y una lectura incorrecta "
            "son problemas distintos. "
            "No atribuir una presión "
            "realmente baja al desgaste "
            "del sensor. Tampoco asumir "
            "que una advertencia "
            "es falsa sin comprobarla. "

            "CONSECUENCIAS: Una presión "
            "realmente baja puede impedir "
            "la lubricación adecuada "
            "de componentes internos, "
            "provocar desgaste acelerado, "
            "daños graves o agarrotamiento "
            "del motor. "

            "DIAGNÓSTICO: Verificar nivel "
            "y especificación del aceite, "
            "inspeccionar fugas y medir "
            "la presión real con equipo "
            "adecuado conforme al fabricante. "
            "Si la presión medida "
            "es correcta, revisar "
            "el sensor y su circuito. "
            "No confirmar una bomba "
            "defectuosa únicamente "
            "por el testigo encendido. "

            "SEGURIDAD: Si aparece "
            "la advertencia de baja "
            "presión de aceite "
            "con el motor funcionando, "
            "detenerse en un lugar seguro "
            "y apagar el motor. "
            "No continuar conduciendo "
            "ni mantenerlo funcionando "
            "hasta determinar la causa."
        ),
    },
    "sistema_combustible": {
        "palabras_clave": [
            "bomba de gasolina", "bomba de combustible",
            "gasolina", "combustible",
            "inyector", "inyectores",
            "presion de combustible",
            "filtro de gasolina", "mezcla pobre",
            "falta de potencia", "se apaga el motor",
            "falla de bomba de gasolina",
            "sistema de combustible"
        ],
        "contenido": (
            "FUNCIÓN: El sistema de combustible "
            "almacena y suministra combustible "
            "al motor. La bomba proporciona "
            "el caudal y la presión requeridos "
            "según el diseño, mientras "
            "los inyectores dosifican "
            "el combustible en motores "
            "con inyección. "

            "SÍNTOMAS DE FALLAS DE SUMINISTRO: "
            "Dificultad para arrancar, "
            "pérdida de potencia, tirones, "
            "funcionamiento irregular, "
            "apagones o respuesta deficiente "
            "al acelerar. Estos síntomas "
            "no confirman por sí solos "
            "que la bomba esté defectuosa. "

            "CAUSAS POSIBLES: Bomba debilitada, "
            "filtro obstruido, alimentación "
            "eléctrica insuficiente, "
            "regulador defectuoso, "
            "inyectores con problemas "
            "u otras fallas relacionadas. "
            "Los mismos síntomas también "
            "pueden tener causas externas "
            "al sistema de combustible. "

            "CONSECUENCIAS: Una bomba "
            "defectuosa no produce "
            "automáticamente daños "
            "internos en el motor. "
            "En determinadas condiciones "
            "de carga y funcionamiento, "
            "una entrega insuficiente "
            "de combustible puede generar "
            "mezcla excesivamente pobre, "
            "temperaturas elevadas "
            "o detonación y aumentar "
            "el riesgo de daño "
            "en ciertos motores. "
            "También puede ocasionar "
            "fallos de combustión "
            "o apagones. "

            "DIAGNÓSTICO: Revisar códigos "
            "y datos de funcionamiento, "
            "alimentación eléctrica "
            "de la bomba, presión "
            "y caudal de combustible "
            "según especificaciones "
            "del fabricante. "
            "Comprobar filtros, inyectores "
            "y otras posibles causas "
            "antes de reemplazar la bomba. "

            "SEGURIDAD: Si el motor "
            "se apaga durante la marcha "
            "o presenta pérdida "
            "importante de potencia, "
            "detenerse en un lugar seguro "
            "y solicitar revisión. "
            "Si existe olor fuerte "
            "a combustible, evitar "
            "chispas, llamas "
            "y posibles fuentes "
            "de ignición."
            
            
           "ACLARACIÓN SOBRE LA BOMBA DE COMBUSTIBLE: "
            "La dificultad de arranque, los tirones "
            "y la pérdida de potencia pueden "
            "relacionarse con una presión o un "
            "suministro de combustible insuficiente, "
            "pero no confirman por sí solos "
            "una falla de la bomba. "

            "Se deben distinguir las posibles causas: "
            "bomba con funcionamiento deficiente, "
            "filtro de combustible restringido, "
            "problemas de alimentación eléctrica, "
            "conexiones defectuosas, regulador de "
            "presión cuando corresponda y otras "
            "fallas del sistema. "

            "No afirmar que la bomba está obstruida "
            "sin evidencia específica. "
            "Una obstrucción del filtro o de una "
            "línea de combustible no equivale "
            "automáticamente a una avería de la bomba. "

            "Para confirmar la causa se deben "
            "realizar comprobaciones apropiadas "
            "de presión, caudal y alimentación "
            "eléctrica, siguiendo las especificaciones "
            "del fabricante y las medidas de "
            "seguridad correspondientes. "
            "No manipular líneas presurizadas "
            "ni realizar pruebas improvisadas "
            "cerca de fuentes de ignición. "
        ),
    },
    
    "sistema_transmision": {
        "palabras_clave": [
            "transmision",
            "caja de cambios",
            "embrague",
            "clutch",
            "convertidor de par",
            "patina el clutch",
            "clutch patina",
            "disco de embrague",
            "pedal de embrague",
        ],
        "contenido": (
            "FUNCIONAMIENTO: La transmisión transmite y adapta "
            "la fuerza del motor hacia las ruedas motrices. "
            "En vehículos con transmisión manual, el embrague "
            "permite acoplar y desacoplar temporalmente el motor "
            "de la transmisión. "

            "PATINAMIENTO DEL CLUTCH: Ocurre cuando el embrague "
            "no transmite correctamente el par del motor. "
            "Un síntoma característico es que las revoluciones "
            "del motor aumentan sin un incremento proporcional "
            "de la velocidad del vehículo. "

            "CAUSAS POSIBLES: Desgaste del material de fricción "
            "del disco de embrague, contaminación del disco "
            "con aceite o grasa, pérdida de fuerza de sujeción "
            "del mecanismo de presión o problemas en el sistema "
            "de accionamiento que impidan el acoplamiento completo. "

            "CONSECUENCIAS: El patinamiento puede generar calor "
            "excesivo, acelerar el desgaste del disco y afectar "
            "el plato de presión o la superficie del volante "
            "del motor. También puede reducir la capacidad "
            "de aceleración del vehículo. "

            "DIAGNOSTICO: Verificar los síntomas durante "
            "el funcionamiento, revisar el accionamiento "
            "del embrague y comprobar el estado de los "
            "componentes según el procedimiento del fabricante. "
            "No se debe confirmar una pieza defectuosa "
            "sin realizar una inspección. "

            "ACLARACIONES: El patinamiento de un embrague manual "
            "convencional no debe atribuirse automáticamente "
            "a un supuesto nivel de aceite de clutch. "
            "Algunos vehículos utilizan líquido hidráulico "
            "en el sistema de accionamiento, pero este no "
            "lubrica las superficies de fricción del embrague. "
            "No se deben inventar componentes como una "
            "bobina de embrague o una válvula de desacoplamiento "
            "como causas generales del patinamiento. "

            "SEGURIDAD: Si el vehículo presenta patinamiento "
            "importante, olor a material de fricción quemado "
            "o dificultad para transmitir potencia, se "
            "recomienda evitar continuar conduciendo "
            "y solicitar una revisión profesional."
        ),
    },

}



def normalizar(texto: str) -> str:
    # Normaliza texto para buscar coincidencias.
    texto = unicodedata.normalize("NFKD", str(texto).casefold())
    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )
    return re.sub(r"\s+", " ", texto).strip()


def contiene_termino(texto: str, termino: str) -> bool:
    # Evita coincidencias dentro de otras palabras.
    termino = normalizar(termino)
    patron = r"(?<!\w)" + re.escape(termino) + r"(?!\w)"
    return bool(re.search(patron, texto))


EXPRESIONES_SISTEMAS = {
    "sistema_frenos": [
        "chillan los frenos",
        "rechinan los frenos",
        "ruido al frenar",
        "pedal esponjoso",
    ],
    "sistema_suspension": [
        "rebota demasiado",
        "rebota mucho",
        "golpes en los baches",
        "golpeteos al pasar baches",
    ],
    "sistema_electrico": [
        "se descarga la bateria",
        "no carga la bateria",
        "falla el alternador",
        "no da marcha",
    ],
    "sistema_refrigeracion": [
        "se sobrecalienta",
        "se calienta el motor",
        "temperatura muy alta",
        "hierve el anticongelante",
    ],
    "sistema_lubricacion": [
        "baja presion de aceite",
        "testigo de aceite",
        "sensor de presion de aceite",
    ],
    "sistema_combustible": [
        "bomba de gasolina",
        "bomba de combustible",
        "presion de combustible",
    ],
    "sistema_transmision": [
        "patina el clutch",
        "patina el embrague",
        "clutch patina",
        "no entran los cambios",
    ],
}


def detectar_enfoque(pregunta: str) -> str:
    # Identifica qué información necesita el usuario.
    texto = normalizar(pregunta)

    if any(contiene_termino(texto, frase) for frase in [
        "como saber", "como revisar", "como diagnosticar",
        "como comprobar", "como verificar", "que revisar",
    ]):
        return "diagnostico"

    if any(contiene_termino(texto, frase) for frase in [
        "que pasa si", "que consecuencias", "que danos",
        "puede danar", "que riesgos", "es peligroso",
    ]):
        return "consecuencias"

    if any(contiene_termino(texto, frase) for frase in [
        "que sintomas", "cuales son los sintomas",
        "que senales", "como se manifiesta",
    ]):
        return "sintomas"

    if any(contiene_termino(texto, frase) for frase in [
        "por que", "que provoca", "que causa",
        "a que se debe", "cuales son las causas",
    ]):
        return "causas"

    return "general"


def separar_apartados(contenido: str) -> dict:
    # Divide la documentación por sus encabezados.
    encabezados = (
        r"FUNCIÓN|FUNCIONAMIENTO|SÍNTOMAS(?: DE FALLAS DE SUMINISTRO)?|"
        r"CAUSAS(?: POSIBLES| DE [A-ZÁÉÍÓÚÑ ]+)?|"
        r"CONSECUENCIAS(?: DEL PATINAMIENTO)?|"
        r"DIAGNÓSTICO|DIAGNOSTICO|SEGURIDAD|"
        r"FALLAS DEL SENSOR|DIFERENCIA IMPORTANTE|"
        r"DIFERENCIA ENTRE [A-ZÁÉÍÓÚÑ ]+|"
        r"PATINAMIENTO DEL CLUTCH|"
        r"TRANSMISIÓN MANUAL|TRANSMISIÓN AUTOMÁTICA|"
        r"ACLARACION|ACLARACIÓN TÉCNICA"
    )

    patron = re.compile(
        rf"(?<!\w)({encabezados}):\s*",
        re.IGNORECASE
    )

    partes = patron.split(contenido)
    apartados = {}

    for indice in range(1, len(partes), 2):
        titulo = partes[indice].strip()
        texto = partes[indice + 1].strip()
        apartados[titulo] = texto

    return apartados


def seleccionar_apartados(apartados: dict, pregunta: str) -> str:
    # Prioriza apartados relacionados con la pregunta.
    enfoque = detectar_enfoque(pregunta)
    consulta = normalizar(pregunta)

    if enfoque == "diagnostico":
        prioridades = ["DIAGNOSTICO", "SINTOMAS"]
    elif enfoque == "consecuencias":
        prioridades = ["CONSECUENCIAS", "SEGURIDAD"]
    elif enfoque == "sintomas":
        prioridades = ["SINTOMAS", "DIAGNOSTICO"]
    elif enfoque == "causas":
        prioridades = ["CAUSAS", "DIAGNOSTICO"]
    else:
        prioridades = ["SINTOMAS", "CAUSAS", "DIAGNOSTICO"]

    seleccionados = []

    # Primero, buscar apartados específicos del síntoma.
    for titulo, texto in apartados.items():
        titulo_normalizado = normalizar(titulo)

        coincidencia_especifica = any(
            contiene_termino(consulta, termino)
            and termino in titulo_normalizado
            for termino in [
                "ruidos", "vibracion", "rebotes",
                "golpeteos", "pedal esponjoso",
                "arranque", "descarga", "sensor",
                "patinamiento", "clutch",
            ]
        )

        if coincidencia_especifica:
            seleccionados.append((titulo, texto))

    # Después, agregar los apartados del enfoque detectado.
    for prioridad in prioridades:
        for titulo, texto in apartados.items():
            if normalizar(titulo).startswith(
                normalizar(prioridad)
            ):
                if (titulo, texto) not in seleccionados:
                    seleccionados.append((titulo, texto))

    # Conservar advertencias de seguridad pertinentes.
    riesgo = any(
        contiene_termino(consulta, termino)
        for termino in [
            "sobrecalienta", "sobrecalentamiento",
            "baja presion de aceite",
            "testigo de aceite",
            "no frena", "perdida de frenado",
            "olor a combustible",
        ]
    )

    if riesgo:
        for titulo, texto in apartados.items():
            if normalizar(titulo) == "seguridad":
                if (titulo, texto) not in seleccionados:
                    seleccionados.append((titulo, texto))

    if not seleccionados:
        seleccionados = list(apartados.items())[:3]

    return "\n".join(
        f"{titulo}: {texto}"
        for titulo, texto in seleccionados
    )


def buscar_conocimiento(
    pregunta: str,
    max_resultados: int = 1
) -> str | None:
    # Recupera documentación relevante para una pregunta.
    consulta = normalizar(pregunta)

    if not consulta:
        return None

    puntuaciones = []

    for nombre, datos in DOCUMENTACION_AUTOMOTRIZ.items():
        puntos = 0

        for expresion in EXPRESIONES_SISTEMAS.get(nombre, []):
            if contiene_termino(consulta, expresion):
                puntos += 5

        for palabra in datos.get("palabras_clave", []):
            if contiene_termino(consulta, palabra):
                puntos += 2 + len(normalizar(palabra).split())

        if puntos > 0:
            puntuaciones.append((puntos, nombre, datos))

    if not puntuaciones:
        return None

    puntuaciones.sort(
        key=lambda elemento: elemento[0],
        reverse=True
    )

    resultados = []

    for _, nombre, datos in puntuaciones[:max(1, max_resultados)]:
        apartados = separar_apartados(datos["contenido"])
        informacion = seleccionar_apartados(apartados, pregunta)

        resultados.append(
            f"SISTEMA: {nombre}\n"
            f"DOCUMENTACIÓN RELEVANTE:\n{informacion}"
        )

    return "\n\n".join(resultados)


