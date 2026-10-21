DOCUMENTACION_AUTOMOTRIZ = {

    # =================================================================
    "sistema_frenos": {
        "palabras_clave": [
            "freno", "frenos", "balata", "balatas", "pastilla", "pastillas",
            "disco de freno", "discos de freno", "liquido de frenos", "abs",
            "pedal de freno", "caliper", "caliper de freno", "pinza de freno",
            "frenado", "tambor", "tambores", "zapata", "zapatas",
            "freno de mano", "freno de estacionamiento", "chirrido",
            "rechinido", "ruido al frenar", "cilindro maestro", "booster",
        ],
        "expresiones": [
            "no frena", "frena poco", "frena mal", "tarda en frenar",
            "chillan los frenos", "rechinan los frenos", "suenan los frenos",
            "truenan los frenos", "ruido al frenar", "vibra al frenar",
            "tiembla al frenar", "se va de lado al frenar", "jala al frenar",
            "pedal esponjoso", "pedal aguado", "pedal suave",
            "el pedal se va hasta el fondo", "pedal hasta el piso",
            "huele a quemado al frenar", "foco del abs", "testigo del abs",
            "testigo de frenos",
        ],
        "apartados": {
            "FUNCIÓN": (
                "El sistema de frenos permite reducir la velocidad y detener "
                "el vehículo. En los frenos de disco, las pastillas (balatas) "
                "presionan el disco para generar fricción; en los de tambor, "
                "las zapatas presionan el tambor. El líquido de frenos "
                "transmite la presión hidráulica desde el pedal. El ABS "
                "ayuda a evitar que las ruedas se bloqueen en un frenado fuerte."
            ),
            "SÍNTOMAS": (
                "Chirridos, rechinidos metálicos, vibraciones al frenar, "
                "pedal esponjoso o que baja demasiado, desviación lateral, "
                "aumento de la distancia de frenado, olor a quemado o "
                "testigos de frenos o ABS encendidos."
            ),
            "CAUSAS DE RUIDOS": (
                "Un chirrido puede relacionarse con desgaste de pastillas, "
                "indicadores de desgaste, contaminación, vibración o "
                "condiciones de contacto. Un rechinido metálico intenso "
                "puede indicar contacto entre superficies metálicas. "
                "El ruido por sí solo no confirma una pieza dañada."
            ),
            "CAUSAS DE VIBRACIÓN": (
                "Pueden incluir variaciones en el espesor del disco, "
                "irregularidades de contacto, componentes de suspensión "
                "o llantas en mal estado. No se debe confirmar un disco "
                "deformado únicamente por sentir vibraciones."
            ),
            "CAUSAS DE PEDAL ESPONJOSO": (
                "Puede existir aire en el circuito hidráulico, fugas, "
                "líquido de frenos degradado u otros problemas del sistema. "
                "Un pedal esponjoso no debe atribuirse automáticamente al "
                "desgaste de las balatas."
            ),
            "CAUSAS DE DESVIACIÓN AL FRENAR": (
                "Puede relacionarse con frenado desigual entre ruedas, "
                "una pinza que no trabaja correctamente, contaminación de "
                "pastillas, presión de llantas desigual o problemas de "
                "suspensión y alineación."
            ),
            "CONSECUENCIAS": (
                "Las pastillas excesivamente desgastadas pueden dañar los "
                "discos y reducir la eficacia del frenado. Las fugas "
                "hidráulicas pueden reducir gravemente la capacidad de frenado."
            ),
            "MANTENIMIENTO": (
                "La revisión de pastillas, discos y líquido de frenos debe "
                "hacerse según el programa del fabricante o cuando aparezcan "
                "síntomas. El desgaste depende del manejo, el tipo de uso y "
                "el vehículo, por lo que no existe un kilometraje único "
                "para todos los autos."
            ),
            "DIAGNÓSTICO": (
                "Inspeccionar el espesor de pastillas y discos, comprobar "
                "fugas, nivel y estado del líquido, funcionamiento de las "
                "pinzas y códigos del ABS cuando corresponda. Confirmar las "
                "causas mediante una inspección adecuada."
            ),
            "SEGURIDAD": (
                "Si existe pérdida notable de frenado, pedal sin presión o "
                "fuga hidráulica importante, no continuar conduciendo y "
                "solicitar asistencia."
            ),
        },
        "apartados_especificos": {
            "CAUSAS DE RUIDOS": ["ruido", "rechin", "chill", "chirri", "suenan", "truenan"],
            "CAUSAS DE VIBRACIÓN": ["vibra", "tiembla"],
            "CAUSAS DE PEDAL ESPONJOSO": ["esponjoso", "aguado", "suave", "hasta el fondo", "hasta el piso"],
            "CAUSAS DE DESVIACIÓN AL FRENAR": ["de lado", "jala", "se va"],
        },
    },

    # =================================================================
    "sistema_suspension": {
        "palabras_clave": [
            "suspension", "amortiguador", "amortiguadores", "resorte",
            "resortes", "muelle", "muelles", "rotula", "rotulas", "buje",
            "bujes", "barra estabilizadora", "estabilizadora", "horquilla",
            "tijera", "base de amortiguador", "rebote", "rebotes",
            "golpeteo", "golpeteos", "baches", "topes",
        ],
        "expresiones": [
            "rebota mucho", "rebota demasiado", "brinca mucho",
            "golpes al pasar baches", "golpes en los baches",
            "golpeteos al pasar baches", "ruido en los baches",
            "truena al pasar topes", "suena al pasar topes",
            "se siente inestable", "se ladea", "se inclina mucho",
            "se siente flotando", "esta caido de un lado",
        ],
        "apartados": {
            "FUNCIÓN": (
                "La suspensión contribuye a mantener el contacto de las "
                "llantas con el pavimento y favorece la estabilidad, el "
                "control y la comodidad del vehículo."
            ),
            "DIFERENCIA ENTRE RESORTE Y AMORTIGUADOR": (
                "El resorte soporta parte del peso del vehículo y absorbe "
                "movimientos verticales. El amortiguador controla las "
                "oscilaciones del resorte y de la suspensión mediante "
                "resistencia hidráulica. No realizan la misma función."
            ),
            "SÍNTOMAS": (
                "Rebotes excesivos, golpeteos al pasar baches o topes, "
                "inclinación anormal, inestabilidad, movimientos excesivos "
                "de la carrocería o desgaste irregular de las llantas."
            ),
            "CAUSAS DE REBOTES": (
                "Pueden relacionarse con amortiguadores que han perdido "
                "capacidad de amortiguación. Sin embargo, los rebotes no "
                "confirman por sí solos una falla específica."
            ),
            "CAUSAS DE GOLPETEOS": (
                "Pueden incluir bujes deteriorados, rótulas con holgura, "
                "bases o soportes dañados, componentes flojos u otros "
                "elementos de suspensión. No atribuir todos los golpes "
                "a los amortiguadores."
            ),
            "CONSECUENCIAS": (
                "Una suspensión deteriorada puede reducir la estabilidad y "
                "la adherencia, aumentar la distancia de frenado en ciertas "
                "situaciones, afectar el control del vehículo y acelerar el "
                "desgaste de las llantas."
            ),
            "DIAGNÓSTICO": (
                "Revisar holguras, fugas en amortiguadores, estado de "
                "resortes, bujes, rótulas, soportes, llantas y alineación "
                "cuando corresponda."
            ),
            "SEGURIDAD": (
                "Si existen componentes sueltos, inestabilidad severa o "
                "pérdida de control, no continuar conduciendo hasta revisar "
                "el vehículo."
            ),
        },
        "apartados_especificos": {
            "CAUSAS DE REBOTES": ["rebota", "rebote", "brinca", "flotando"],
            "CAUSAS DE GOLPETEOS": ["golpe", "golpeteo", "baches", "topes", "truena", "suena"],
            "DIFERENCIA ENTRE RESORTE Y AMORTIGUADOR": ["diferencia", "resorte"],
        },
    },

    # =================================================================
    "sistema_direccion": {
        "palabras_clave": [
            "direccion", "volante", "cremallera", "caja de direccion",
            "terminal de direccion", "terminales", "bomba de direccion",
            "direccion hidraulica", "direccion electrica",
            "liquido de direccion", "columna de direccion",
        ],
        "expresiones": [
            "el volante esta duro", "volante duro", "direccion dura",
            "cuesta trabajo girar", "juego en el volante",
            "el volante tiene juego", "el volante esta chueco",
            "volante chueco", "zumba al girar", "chilla al girar",
            "ruido al girar", "truena al dar vuelta",
        ],
        "apartados": {
            "FUNCIÓN": (
                "La dirección transmite el giro del volante a las ruedas "
                "delanteras. Puede ser mecánica, hidráulica o eléctrica "
                "(asistida), según el vehículo."
            ),
            "SÍNTOMAS": (
                "Volante duro, juego excesivo en el volante, ruidos al "
                "girar, volante desalineado al ir derecho o fugas de "
                "líquido de dirección en sistemas hidráulicos."
            ),
            "CAUSAS POSIBLES": (
                "Nivel bajo o fugas de líquido en dirección hidráulica, "
                "bomba de dirección con problemas, banda de accesorios en "
                "mal estado, terminales o componentes con holgura, fallas "
                "en la asistencia eléctrica o presión de llantas baja. "
                "Un volante chueco suele relacionarse con alineación, pero "
                "debe comprobarse."
            ),
            "CONSECUENCIAS": (
                "Una dirección con holguras o sin asistencia puede reducir "
                "el control del vehículo y aumentar el esfuerzo al manejar."
            ),
            "DIAGNÓSTICO": (
                "Revisar nivel y fugas de líquido cuando aplique, estado de "
                "la banda, holguras en terminales y componentes, presión de "
                "llantas y alineación, y códigos de falla en direcciones "
                "eléctricas."
            ),
            "SEGURIDAD": (
                "Si la dirección se endurece de golpe, presenta mucha holgura "
                "o hay pérdida de control, detenerse en un lugar seguro y "
                "solicitar revisión antes de seguir manejando."
            ),
        },
        "apartados_especificos": {},
    },

    # =================================================================
    "llantas_y_alineacion": {
        "palabras_clave": [
            "llanta", "llantas", "neumatico", "neumaticos", "rin", "rines",
            "alineacion", "balanceo", "presion de llantas",
            "presion de aire", "desgaste de llantas", "ponchadura",
            "rotacion de llantas",
        ],
        "expresiones": [
            "se va de lado", "se jala de lado", "jala para un lado",
            "se carga de un lado", "vibra a cierta velocidad",
            "vibra a alta velocidad", "vibra a altas velocidades",
            "vibra en autopista", "vibra el volante", "volante vibra",
            "tiembla el volante", "volante tiembla", "a alta velocidad",
            "tiembla en carretera", "vibra en carretera",
            "se gastan las llantas", "se acaban las llantas",
            "llanta baja", "pierde aire", "cuanto aire",
        ],
        "apartados": {
            "FUNCIÓN": (
                "Las llantas son el único contacto del vehículo con el "
                "pavimento. La alineación ajusta los ángulos de las ruedas "
                "y el balanceo compensa diferencias de peso en el conjunto "
                "llanta-rin."
            ),
            "SÍNTOMAS": (
                "El vehículo se va de lado, vibración a cierta velocidad, "
                "volante chueco, desgaste irregular de las llantas o "
                "pérdida de aire."
            ),
            "CAUSAS POSIBLES": (
                "Una vibración a velocidad constante suele relacionarse con "
                "balanceo, aunque también puede deberse a llantas o rines "
                "dañados. Que el auto se vaya de lado puede relacionarse con "
                "alineación, presión desigual de llantas, frenos o suspensión. "
                "El desgaste irregular puede deberse a alineación, presión "
                "incorrecta o suspensión en mal estado."
            ),
            "MANTENIMIENTO": (
                "La presión correcta de las llantas la indica el fabricante, "
                "normalmente en una etiqueta en el marco de la puerta del "
                "conductor o en el manual, y se mide con las llantas frías. "
                "No se debe usar como referencia la presión máxima impresa "
                "en la llanta."
            ),
            "CONSECUENCIAS": (
                "Llantas con presión incorrecta o desgastadas reducen la "
                "adherencia, aumentan la distancia de frenado y pueden "
                "provocar un desgaste prematuro o una falla de la llanta."
            ),
            "DIAGNÓSTICO": (
                "Revisar presión, profundidad y forma del desgaste, daños "
                "visibles en llantas y rines, y realizar alineación y "
                "balanceo con equipo adecuado cuando corresponda."
            ),
            "SEGURIDAD": (
                "Si una llanta tiene protuberancias, cortes profundos o "
                "pierde aire rápidamente, no circular a velocidad y "
                "reemplazarla o repararla antes de seguir."
            ),
        },
        "apartados_especificos": {},
    },

    # =================================================================
    "sistema_electrico": {
        "palabras_clave": [
            "alternador", "bateria", "acumulador", "marcha",
            "motor de arranque", "arranque", "fusible", "fusibles",
            "cableado", "voltaje", "terminales de bateria", "luces tenues",
            "testigo de bateria", "sistema de carga", "regulador de voltaje",
            "corriente", "relevador", "relay",
        ],
        "expresiones": [
            "no carga la bateria", "se descarga la bateria",
            "se descarga el acumulador", "se baja la bateria",
            "falla el alternador", "no da marcha", "no prende",
            "no enciende", "no arranca", "tarda en arrancar",
            "no quiere arrancar", "no quiere prender", "no quiere encender",
            "no quiere dar marcha", "no da chispa", "batería muerta",
            "bateria muerta", "se quedo sin bateria",
            "le cuesta arrancar", "hace clic y no arranca", "hace click",
            "luces parpadean", "luces debiles", "luces tenues",
            "se apagan las luces", "foco de la bateria",
            "testigo de bateria",
        ],
        "apartados": {
            "FUNCIÓN": (
                "La batería (acumulador) suministra energía eléctrica para "
                "el arranque y otros sistemas. El alternador genera "
                "electricidad con el motor en marcha y contribuye a recargar "
                "la batería. El motor de arranque (marcha) hace girar el "
                "motor para encenderlo."
            ),
            "SÍNTOMAS": (
                "Arranque lento, dificultad para encender, clics al girar la "
                "llave, luces tenues, testigo de batería, fallas eléctricas "
                "o descarga recurrente."
            ),
            "CAUSAS DE DESCARGA": (
                "Una batería envejecida, alternador o regulador defectuoso, "
                "conexiones deficientes, correa de accesorios dañada o "
                "consumo eléctrico excesivo con el vehículo apagado."
            ),
            "DIFERENCIA ENTRE BATERÍA Y ALTERNADOR": (
                "La batería almacena energía. El alternador genera energía "
                "mientras el motor está funcionando. Una batería descargada "
                "no demuestra automáticamente que el alternador esté "
                "defectuoso."
            ),
            "CAUSAS DE FALLAS DE ARRANQUE": (
                "Pueden relacionarse con batería descargada, conexiones "
                "deficientes, motor de arranque o circuitos de control. Se "
                "debe distinguir entre un motor que no gira y uno que gira "
                "pero no enciende; este último puede deberse también a "
                "combustible o encendido."
            ),
            "CONSECUENCIAS": (
                "Un problema en el sistema de carga puede descargar la "
                "batería y provocar fallas eléctricas o la detención del "
                "vehículo."
            ),
            "DIAGNÓSTICO": (
                "Comprobar el estado de la batería, terminales, conexiones "
                "eléctricas, correa de accesorios que acciona el alternador "
                "cuando corresponda, voltaje del sistema de carga y consumo "
                "eléctrico en reposo según las especificaciones del "
                "fabricante. No confundir la correa de accesorios con la "
                "correa de distribución."
            ),
            "SEGURIDAD": (
                "Evitar cortocircuitos, respetar la polaridad y seguir el "
                "procedimiento del fabricante antes de intervenir "
                "componentes eléctricos o pasar corriente."
            ),
        },
        "apartados_especificos": {
            "CAUSAS DE DESCARGA": ["descarga", "se baja", "no carga"],
            "CAUSAS DE FALLAS DE ARRANQUE": ["arranca", "arranque", "prende", "enciende", "marcha", "clic", "click"],
            "DIFERENCIA ENTRE BATERÍA Y ALTERNADOR": ["diferencia", "alternador o bateria", "bateria o alternador"],
        },
    },

    # =================================================================
    "sistema_encendido": {
        "palabras_clave": [
            "bujia", "bujias", "bobina", "bobinas", "cables de bujia",
            "cables de alta", "encendido", "afinacion", "distribuidor",
            "falla de cilindro", "chispa", "sensor de cigueñal",
            "sensor de arbol de levas",
        ],
        "expresiones": [
            "se jalonea", "da tirones", "jalonea", "cascabelea",
            "cascabeleo", "tiembla en ralenti", "tiembla parado",
            "vibra en marcha minima", "falla un cilindro", "se ahoga",
            "check engine parpadea", "check engine parpadeando",
            "foco parpadeando", "humo con olor a gasolina",
        ],
        "apartados": {
            "FUNCIÓN": (
                "El sistema de encendido genera la chispa que inflama la "
                "mezcla de aire y combustible en cada cilindro. Incluye "
                "bujías, bobinas, cables (en algunos vehículos) y sensores "
                "que indican a la computadora cuándo generar la chispa."
            ),
            "SÍNTOMAS": (
                "Tirones o jaloneos, marcha mínima irregular, vibración con "
                "el auto detenido, pérdida de potencia, mayor consumo de "
                "combustible, dificultad para arrancar o testigo de check "
                "engine encendido o parpadeando."
            ),
            "CAUSAS POSIBLES": (
                "Bujías desgastadas o con calibración incorrecta, bobinas o "
                "cables defectuosos, sensores con fallas o problemas de "
                "combustible o admisión que producen síntomas parecidos. "
                "Un tirón no confirma por sí solo que las bujías estén mal."
            ),
            "CONSECUENCIAS": (
                "Una falla de encendido puede enviar combustible sin quemar "
                "al escape, dañar el convertidor catalítico, aumentar el "
                "consumo y reducir la potencia."
            ),
            "MANTENIMIENTO": (
                "El intervalo de cambio de bujías depende del tipo de bujía "
                "y del motor; se debe consultar el manual del fabricante. "
                "Las bujías de reemplazo deben coincidir con la "
                "especificación del motor."
            ),
            "DIAGNÓSTICO": (
                "Leer códigos de falla con escáner, inspeccionar bujías, "
                "bobinas y cables, y descartar problemas de combustible y "
                "admisión antes de reemplazar piezas."
            ),
            "SEGURIDAD": (
                "Si el check engine parpadea, suele indicar una falla de "
                "encendido importante: reducir la carga del motor, evitar "
                "acelerar fuerte y solicitar revisión lo antes posible."
            ),
        },
        "apartados_especificos": {},
    },

    # =================================================================
    "sistema_refrigeracion": {
        "palabras_clave": [
            "sobrecalentamiento", "sobrecalienta", "radiador", "termostato",
            "anticongelante", "refrigerante", "bomba de agua",
            "temperatura del motor", "ventilador", "ventiladores",
            "fuga de refrigerante", "deposito de refrigerante",
            "mangueras del radiador", "tapon del radiador",
        ],
        "expresiones": [
            "se calienta", "se calienta el motor", "se sobrecalienta",
            "se esta calentando", "se calienta mucho", "motor muy caliente",
            "temperatura muy alta", "temperatura del motor alta",
            "sube la temperatura", "sube la aguja", "hierve el anticongelante",
            "sale vapor", "echa vapor", "pierde refrigerante",
            "tira agua", "tira anticongelante", "no prende el ventilador",
        ],
        "apartados": {
            "FUNCIÓN": (
                "El sistema de refrigeración regula la temperatura del motor. "
                "El refrigerante transporta el calor y componentes como "
                "radiador, bomba de agua, termostato y ventiladores ayudan "
                "a disiparlo. El termostato regula el paso del refrigerante "
                "hacia el radiador según la temperatura."
            ),
            "SÍNTOMAS": (
                "Temperatura elevada, vapor, pérdida de refrigerante, fugas, "
                "funcionamiento irregular de la calefacción o advertencias "
                "de temperatura."
            ),
            "CAUSAS POSIBLES": (
                "Nivel insuficiente de refrigerante, fugas, termostato "
                "atascado, radiador obstruido, ventilador defectuoso, "
                "problemas de circulación o bomba de agua deteriorada."
            ),
            "CONSECUENCIAS": (
                "Continuar utilizando un motor sobrecalentado puede provocar "
                "daños en la junta de culata, deformaciones de componentes "
                "o averías internas graves."
            ),
            "MANTENIMIENTO": (
                "Usar el tipo de refrigerante que indica el fabricante y "
                "revisar su nivel con el motor frío. El intervalo de cambio "
                "depende del tipo de refrigerante y del vehículo."
            ),
            "DIAGNÓSTICO": (
                "Comprobar el nivel de refrigerante con el motor frío, "
                "inspeccionar fugas y revisar el funcionamiento de "
                "ventiladores, termostato y circulación según procedimientos "
                "técnicos. Una temperatura elevada no confirma por sí sola "
                "que el termostato esté dañado."
            ),
            "SEGURIDAD": (
                "Si el motor presenta sobrecalentamiento, detenerse de manera "
                "segura y apagarlo. Nunca abrir la tapa de un sistema de "
                "refrigeración presurizado mientras esté caliente, debido al "
                "riesgo de quemaduras."
            ),
        },
        "apartados_especificos": {},
    },

    # =================================================================
    "sistema_lubricacion": {
        "palabras_clave": [
            "aceite", "aceite de motor", "lubricacion", "presion de aceite",
            "baja presion de aceite", "bomba de aceite", "filtro de aceite",
            "testigo de aceite", "sensor de aceite",
            "sensor de presion de aceite", "fuga de aceite",
            "cambio de aceite", "viscosidad", "aceite sintetico",
            "aceite mineral", "carter",
        ],
        "expresiones": [
            "se prende el foco del aceite", "foco del aceite",
            "testigo del aceite", "tira aceite", "gotea aceite",
            "consume aceite", "se acaba el aceite", "le falta aceite",
            "sin aceite", "falta de lubricacion",
            "cada cuanto cambio el aceite", "cada cuanto se cambia el aceite",
        ],
        "apartados": {
            "FUNCIÓN": (
                "El sistema de lubricación distribuye aceite para reducir la "
                "fricción y el desgaste de componentes internos del motor. "
                "También contribuye a disipar calor y a transportar "
                "contaminantes hacia el filtro de aceite, que los retiene."
            ),
            "SÍNTOMAS": (
                "Encendido del testigo de presión de aceite, ruidos "
                "metálicos, nivel bajo, fugas o consumo excesivo de aceite."
            ),
            "CAUSAS DE BAJA PRESIÓN REAL": (
                "Nivel insuficiente de aceite, problemas de alimentación o "
                "circulación, bomba de aceite defectuosa, obstrucciones o "
                "desgaste interno del motor. La viscosidad inadecuada "
                "también puede afectar la presión según las condiciones."
            ),
            "FALLAS DEL SENSOR": (
                "Un sensor de presión defectuoso, problemas de cableado o "
                "fallas del circuito de medición pueden provocar una "
                "advertencia incorrecta. Una falla del sensor no significa "
                "necesariamente que la presión real del aceite sea baja."
            ),
            "DIFERENCIA IMPORTANTE": (
                "La baja presión real y una lectura incorrecta son problemas "
                "distintos. No atribuir una presión realmente baja al "
                "sensor, ni asumir que una advertencia es falsa sin "
                "comprobarla."
            ),
            "CONSECUENCIAS": (
                "Una presión realmente baja puede impedir la lubricación "
                "adecuada, provocar desgaste acelerado, daños graves o "
                "agarrotamiento del motor."
            ),
            "MANTENIMIENTO": (
                "El intervalo de cambio de aceite y filtro, la viscosidad y "
                "el tipo de aceite (mineral, semisintético o sintético) los "
                "define el fabricante según el motor y las condiciones de "
                "uso. No existe un kilometraje único para todos los autos; "
                "conviene revisar el nivel periódicamente."
            ),
            "DIAGNÓSTICO": (
                "Verificar nivel y especificación del aceite, inspeccionar "
                "fugas y medir la presión real con equipo adecuado conforme "
                "al fabricante. Si la presión medida es correcta, revisar el "
                "sensor y su circuito. No confirmar una bomba defectuosa "
                "únicamente por el testigo encendido."
            ),
            "SEGURIDAD": (
                "Si aparece la advertencia de baja presión de aceite con el "
                "motor funcionando, detenerse en un lugar seguro y apagar el "
                "motor. No continuar conduciendo ni mantenerlo funcionando "
                "hasta determinar la causa."
            ),
        },
        "apartados_especificos": {
            "FALLAS DEL SENSOR": ["sensor"],
            "CAUSAS DE BAJA PRESIÓN REAL": ["presion", "foco", "testigo"],
        },
    },

    # =================================================================
    "sistema_combustible": {
        "palabras_clave": [
            "bomba de gasolina", "bomba de combustible", "gasolina",
            "combustible", "inyector", "inyectores", "presion de combustible",
            "filtro de gasolina", "filtro de combustible", "mezcla pobre",
            "falta de potencia", "cuerpo de aceleracion", "tanque de gasolina",
            "sistema de combustible", "rendimiento de gasolina",
        ],
        "expresiones": [
            "se apaga el motor", "se apaga solo", "se me apaga",
            "pierde potencia", "perdida de potencia", "no tiene fuerza",
            "le falta fuerza", "no jala", "no agarra velocidad",
            "gasta mucha gasolina", "consume mucha gasolina",
            "huele a gasolina", "olor a gasolina", "olor a combustible",
            "da marcha pero no arranca", "gira pero no prende",
            "falla de inyectores", "falta de gasolina",
        ],
        "apartados": {
            "FUNCIÓN": (
                "El sistema de combustible almacena y suministra combustible "
                "al motor. La bomba proporciona el caudal y la presión "
                "requeridos según el diseño, mientras los inyectores "
                "dosifican el combustible en motores con inyección."
            ),
            "SÍNTOMAS DE FALLAS DE SUMINISTRO": (
                "Dificultad para arrancar, pérdida de potencia, tirones, "
                "funcionamiento irregular, apagones o respuesta deficiente "
                "al acelerar. Estos síntomas no confirman por sí solos que "
                "la bomba esté defectuosa."
            ),
            "CAUSAS POSIBLES": (
                "Bomba debilitada, filtro obstruido, alimentación eléctrica "
                "insuficiente, regulador defectuoso, inyectores con problemas "
                "u otras fallas relacionadas. Los mismos síntomas también "
                "pueden tener causas externas al sistema de combustible, "
                "como encendido o admisión de aire."
            ),
            "ACLARACIÓN SOBRE LA BOMBA DE COMBUSTIBLE": (
                "La dificultad de arranque, los tirones y la pérdida de "
                "potencia pueden relacionarse con un suministro insuficiente, "
                "pero no confirman una falla de la bomba. Un filtro "
                "restringido, problemas eléctricos o del regulador producen "
                "síntomas similares. No afirmar que la bomba está obstruida "
                "sin evidencia; se deben medir presión, caudal y alimentación "
                "eléctrica según el fabricante."
            ),
            "CONSECUENCIAS": (
                "Una bomba defectuosa no produce automáticamente daños "
                "internos en el motor. En ciertas condiciones, una entrega "
                "insuficiente de combustible puede generar mezcla pobre, "
                "temperaturas elevadas o detonación, fallos de combustión "
                "o apagones."
            ),
            "DIAGNÓSTICO": (
                "Revisar códigos y datos de funcionamiento, alimentación "
                "eléctrica de la bomba, presión y caudal de combustible según "
                "especificaciones del fabricante. Comprobar filtros, "
                "inyectores y otras posibles causas antes de reemplazar la "
                "bomba."
            ),
            "SEGURIDAD": (
                "Si el motor se apaga durante la marcha o presenta pérdida "
                "importante de potencia, detenerse en un lugar seguro y "
                "solicitar revisión. Si existe olor fuerte a combustible, "
                "evitar chispas, llamas y posibles fuentes de ignición, y no "
                "manipular líneas presurizadas."
            ),
        },
        "apartados_especificos": {
            "ACLARACIÓN SOBRE LA BOMBA DE COMBUSTIBLE": ["bomba"],
        },
    },

    # =================================================================
    "sistema_transmision": {
        "palabras_clave": [
            "transmision", "caja de cambios", "caja de velocidades",
            "embrague", "clutch", "convertidor de par", "disco de embrague",
            "pedal de embrague", "collarin", "plato de presion",
            "transmision automatica", "transmision manual", "cvt",
            "aceite de transmision", "flecha", "flechas", "homocinetica",
        ],
        "expresiones": [
            "patina el clutch", "clutch patina", "patina el embrague",
            "patina la transmision", "no entran los cambios",
            "no entran las velocidades", "truena al meter velocidad",
            "rechina al meter los cambios", "se pega el clutch",
            "el clutch esta duro", "da tirones al cambiar",
            "tarda en cambiar", "se queda en una velocidad",
            "problemas al cambiar de marcha", "truena al dar vuelta",
        ],
        "apartados": {
            "FUNCIONAMIENTO": (
                "La transmisión transmite y adapta la fuerza del motor hacia "
                "las ruedas motrices. En transmisiones manuales, el embrague "
                "(clutch) permite acoplar y desacoplar temporalmente el motor "
                "de la transmisión. En las automáticas, el cambio de "
                "relaciones se hace de forma automática."
            ),
            "PATINAMIENTO DEL CLUTCH": (
                "Ocurre cuando el embrague no transmite correctamente el par "
                "del motor. Un síntoma característico es que las "
                "revoluciones aumentan sin un incremento proporcional de la "
                "velocidad del vehículo."
            ),
            "CAUSAS POSIBLES": (
                "En el clutch: desgaste del material de fricción del disco, "
                "contaminación con aceite o grasa, pérdida de fuerza del "
                "plato de presión o problemas de accionamiento. En "
                "transmisiones automáticas: nivel o estado del líquido "
                "inadecuado, fallas de control o desgaste interno. Un ruido "
                "al dar vuelta puede relacionarse con las juntas "
                "homocinéticas (flechas)."
            ),
            "CONSECUENCIAS": (
                "El patinamiento puede generar calor excesivo, acelerar el "
                "desgaste del disco y afectar el plato de presión o el "
                "volante del motor. También puede reducir la capacidad de "
                "aceleración."
            ),
            "DIAGNÓSTICO": (
                "Verificar los síntomas durante el funcionamiento, revisar el "
                "accionamiento del embrague, el nivel y estado del líquido "
                "de transmisión cuando aplique y los códigos de falla, según "
                "el procedimiento del fabricante. No confirmar una pieza "
                "defectuosa sin inspección."
            ),
            "ACLARACIONES": (
                "El patinamiento de un embrague manual no debe atribuirse a "
                "un supuesto nivel de aceite de clutch. Algunos vehículos "
                "usan líquido hidráulico para accionarlo, pero no lubrica "
                "las superficies de fricción. No inventar componentes como "
                "una bobina de embrague."
            ),
            "SEGURIDAD": (
                "Si hay patinamiento importante, olor a material de fricción "
                "quemado o dificultad para transmitir potencia, evitar "
                "continuar conduciendo y solicitar revisión profesional."
            ),
        },
        "apartados_especificos": {
            "PATINAMIENTO DEL CLUTCH": ["patina", "clutch", "embrague"],
        },
    },

    # =================================================================
    "sistema_escape": {
        "palabras_clave": [
            "escape", "mofle", "silenciador", "catalizador",
            "convertidor catalitico", "sensor de oxigeno", "tubo de escape",
            "multiple de escape", "humo", "emisiones", "verificacion",
        ],
        "expresiones": [
            "sale humo", "echa humo", "humo blanco", "humo azul",
            "humo negro", "suena mucho el escape", "truena el escape",
            "ruido en el escape", "el mofle suena", "huele a huevo podrido",
            "no paso la verificacion", "olor a escape dentro del carro",
        ],
        "apartados": {
            "FUNCIÓN": (
                "El sistema de escape conduce los gases del motor fuera del "
                "vehículo, reduce el ruido (mofle o silenciador) y disminuye "
                "las emisiones contaminantes (convertidor catalítico). Los "
                "sensores de oxígeno ayudan a controlar la mezcla."
            ),
            "SÍNTOMAS": (
                "Ruido fuerte o golpeteo en el escape, humo de colores "
                "anormales, olor a gases dentro del vehículo, pérdida de "
                "potencia o falla en la verificación de emisiones."
            ),
            "COLOR DEL HUMO": (
                "Un poco de vapor blanco al arrancar en frío puede ser normal. "
                "Humo blanco denso y continuo con olor dulce puede relacionarse "
                "con refrigerante quemándose. Humo azulado puede relacionarse "
                "con consumo de aceite. Humo negro puede relacionarse con "
                "exceso de combustible. El color orienta, pero no confirma "
                "una falla."
            ),
            "CAUSAS POSIBLES": (
                "Fugas o perforaciones en tubos y mofle, soportes rotos, "
                "catalizador obstruido o dañado, sensores de oxígeno con "
                "fallas o problemas de combustión del motor."
            ),
            "CONSECUENCIAS": (
                "Una fuga de escape puede permitir que gases entren al "
                "habitáculo. Un catalizador obstruido puede reducir mucho la "
                "potencia."
            ),
            "DIAGNÓSTICO": (
                "Inspeccionar fugas, soportes y estado del mofle, leer "
                "códigos de falla y revisar el funcionamiento de sensores y "
                "catalizador con equipo adecuado."
            ),
            "SEGURIDAD": (
                "Si hay olor a gases de escape dentro del vehículo, ventilar, "
                "evitar circular con las ventanas cerradas y revisar el "
                "sistema lo antes posible: el monóxido de carbono es tóxico "
                "y no tiene olor."
            ),
        },
        "apartados_especificos": {
            "COLOR DEL HUMO": ["humo"],
        },
    },

    # =================================================================
    "testigos_tablero": {
        "palabras_clave": [
            "check engine", "testigo", "testigos", "foco del tablero",
            "luz del tablero", "tablero", "indicador", "codigo de falla",
            "escaner", "mil",
        ],
        "expresiones": [
            "se prendio un foco", "se prende un foco", "prendio una luz",
            "se encendio una luz", "foquito en el tablero",
            "luz amarilla", "luz roja", "se prendio el check",
            "se prende el check engine",
        ],
        "apartados": {
            "FUNCIÓN": (
                "Los testigos del tablero avisan de fallas o condiciones del "
                "vehículo. Los de color rojo suelen indicar algo urgente "
                "(presión de aceite, temperatura, frenos, carga), y los "
                "amarillos o ámbar indican que se requiere revisión."
            ),
            "CHECK ENGINE": (
                "El testigo de check engine indica que la computadora detectó "
                "una falla relacionada con el motor o las emisiones. Encendido "
                "fijo: revisar pronto con escáner. Parpadeando: suele indicar "
                "una falla de encendido importante que puede dañar el "
                "catalizador. Un tapón de gasolina mal cerrado también puede "
                "encenderlo en algunos vehículos."
            ),
            "DIAGNÓSTICO": (
                "Leer los códigos de falla con un escáner y confirmar la "
                "causa con pruebas. El código orienta, pero no siempre "
                "indica qué pieza reemplazar."
            ),
            "SEGURIDAD": (
                "Si se enciende un testigo rojo de presión de aceite, "
                "temperatura o frenos, detenerse en un lugar seguro y no "
                "continuar hasta revisar. Si el check engine parpadea, "
                "reducir la carga del motor y solicitar revisión."
            ),
        },
        "apartados_especificos": {
            "CHECK ENGINE": ["check", "engine"],
        },
    },

    # =================================================================
    "sistema_iluminacion": {
        "palabras_clave": [
            "faro", "faros", "foco", "focos", "luces", "calavera",
            "calaveras", "direccionales", "intermitentes", "luz de freno",
            "luces altas", "luces bajas", "halogeno", "led", "xenon",
        ],
        "expresiones": [
            "no prende un faro", "se fundio un foco", "no sirven las luces",
            "no prenden las direccionales", "direccional rapida",
            "faros opacos", "faros amarillos", "alumbran poco",
        ],
        "apartados": {
            "FUNCIÓN": (
                "La iluminación permite ver y ser visto: faros, luces de "
                "freno, direccionales e intermitentes."
            ),
            "CAUSAS POSIBLES": (
                "Foco fundido, fusible o relevador dañado, conectores "
                "sulfatados o cableado defectuoso. Si una direccional "
                "parpadea más rápido de lo normal, suele indicar un foco "
                "fundido en ese lado. Faros opacos reducen la iluminación "
                "aunque el foco funcione."
            ),
            "DIAGNÓSTICO": (
                "Revisar foco, fusible, relevador y conector. Al reemplazar "
                "focos, usar el tipo y la potencia que indica el fabricante."
            ),
            "SEGURIDAD": (
                "Circular con luces de freno o faros fundidos reduce la "
                "visibilidad y el aviso a otros conductores; conviene "
                "reemplazarlos pronto."
            ),
        },
        "apartados_especificos": {},
    },

    # =================================================================
    "aire_acondicionado": {
        "palabras_clave": [
            "aire acondicionado", "clima", "compresor", "gas refrigerante",
            "filtro de cabina", "filtro de polen", "condensador",
            "evaporador", "calefaccion", "ventilacion",
        ],
        "expresiones": [
            "no enfria", "no enfria el clima", "el clima no enfria",
            "el aire no enfria", "huele feo el aire", "huele a humedad",
            "no sale aire", "sale poco aire", "no calienta la calefaccion",
        ],
        "apartados": {
            "FUNCIÓN": (
                "El aire acondicionado enfría y deshumidifica el aire del "
                "habitáculo mediante un circuito con gas refrigerante, "
                "compresor, condensador y evaporador."
            ),
            "CAUSAS POSIBLES": (
                "Gas refrigerante bajo por fugas, compresor o embrague del "
                "compresor con fallas, ventilador del condensador "
                "defectuoso, problemas eléctricos o filtro de cabina sucio "
                "(que reduce el flujo de aire y puede causar mal olor)."
            ),
            "DIAGNÓSTICO": (
                "Medir presiones con equipo adecuado, buscar fugas antes de "
                "recargar, revisar el funcionamiento del compresor y del "
                "ventilador, y el estado del filtro de cabina. Recargar sin "
                "reparar una fuga solo resuelve el problema temporalmente."
            ),
            "SEGURIDAD": (
                "El gas refrigerante está a presión y debe manipularlo "
                "personal capacitado con equipo adecuado."
            ),
        },
        "apartados_especificos": {},
    },

    # =================================================================
    "mantenimiento_preventivo": {
        "palabras_clave": [
            "mantenimiento", "servicio", "afinacion", "mantenimiento preventivo",
            "revision general", "filtro de aire", "banda de distribucion",
            "cadena de distribucion", "correa de distribucion",
            "banda de accesorios", "correa de accesorios", "fluidos",
            "carretera", "viaje", "salir a carretera",
        ],
        "expresiones": [
            "que incluye una afinacion", "que lleva una afinacion",
            "que le hago a mi carro", "que revisar antes de salir a carretera",
            "antes de un viaje",
        ],
        "apartados": {
            "FUNCIÓN": (
                "El mantenimiento preventivo consiste en revisar y reemplazar "
                "componentes de desgaste antes de que fallen, siguiendo el "
                "programa del fabricante."
            ),
            "MANTENIMIENTO": (
                "Los intervalos de aceite, filtros, bujías, banda o cadena de "
                "distribución, líquido de frenos y refrigerante dependen del "
                "vehículo y de las condiciones de uso; se deben consultar en "
                "el manual del fabricante. Lo que incluye una 'afinación' "
                "varía según el taller y el motor, por lo que conviene pedir "
                "el detalle de lo que se revisa y reemplaza."
            ),
            "DIFERENCIA ENTRE BANDA DE DISTRIBUCIÓN Y BANDA DE ACCESORIOS": (
                "La banda (o cadena) de distribución sincroniza el giro del "
                "cigüeñal con el de los árboles de levas; si se rompe, en "
                "muchos motores puede causar daños internos graves. La banda "
                "de accesorios mueve componentes como alternador, bomba de "
                "dirección o compresor del clima. No son la misma pieza."
            ),
            "ANTES DE CARRETERA": (
                "Revisar nivel de aceite y refrigerante, presión y estado de "
                "llantas (incluida la de refacción), frenos, luces, "
                "limpiaparabrisas y que no haya testigos encendidos."
            ),
            "SEGURIDAD": (
                "Posponer el mantenimiento de frenos, llantas o dirección "
                "puede comprometer la seguridad del vehículo."
            ),
        },
        "apartados_especificos": {
            "DIFERENCIA ENTRE BANDA DE DISTRIBUCIÓN Y BANDA DE ACCESORIOS": ["distribucion", "accesorios", "banda", "correa"],
            "ANTES DE CARRETERA": ["carretera", "viaje"],
        },
    },
}


# ---------------------------------------------------------------------
# Compatibilidad con la versión anterior: algunos módulos esperaban
# un texto "contenido" por sistema. Se arma automáticamente a partir
# de los apartados, para no tener la información duplicada.
# ---------------------------------------------------------------------
for _datos in DOCUMENTACION_AUTOMOTRIZ.values():
    _datos["contenido"] = " ".join(
        f"{titulo}: {texto}" for titulo, texto in _datos["apartados"].items()
    )


def buscar_conocimiento(pregunta: str, max_resultados: int = 2) -> str | None:
    # Antes este archivo tenía su propio buscador (duplicado y distinto
    # del de buscador_mecanico.py). Ahora solo redirige al buscador
    # oficial para que toda la búsqueda sea igual.
    from AgenteIA.mecanica.buscador_mecanico import buscar_conocimiento as _buscar
    return _buscar(pregunta, max_resultados=max_resultados)