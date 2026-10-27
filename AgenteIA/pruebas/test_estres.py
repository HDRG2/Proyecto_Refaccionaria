import contextlib
import io
import json

import pytest

from AgenteIA.asistente.texto import preparar_pregunta
from AgenteIA.mecanica.buscador_mecanico import buscar_conocimiento
from AgenteIA.mecanica.conocimientos_mecanicos import buscar_respuesta_rapida
from AgenteIA.servidor import ETAPAS, Consulta, EstadoConsulta


INVENTARIO = [
    {"codigo": "ACE-001", "nombre": "Aceite de Motor 5W-30", "marca": "Mobil", "categoria": "Aceites", "precio": 749, "existencia": 3, "universal": True},
    {"codigo": "PRU-009", "nombre": "Alternador", "marca": "Bosch", "categoria": "Sistema eléctrico", "precio": 3250, "existencia": 6},
    {"codigo": "AMO-005", "nombre": "Amortiguador Delantero", "marca": "Monroe", "categoria": "Suspensión", "precio": 1450, "existencia": 7,
     "vehiculosCompatibles": ["Toyota Corolla (2014-2019)", "Toyota Yaris (2016-2020)"]},
    {"codigo": "BAL-002", "nombre": "Balatas delanteras Ceramitas", "marca": "Brembo", "categoria": "Frenos", "precio": 1249, "existencia": 15,
     "vehiculosCompatibles": ["Nissan Versa 2012-2019"]},
    {"codigo": "PRU-012", "nombre": "Banda de accesorios", "marca": "Gates", "categoria": "Motor", "precio": 420, "existencia": 10},
    {"codigo": "PRU-008", "nombre": "Batería de 12V", "marca": "LTH", "categoria": "Sistema eléctrico", "precio": 2100, "existencia": 8},
    {"codigo": "PRU-015", "nombre": "Bobina de Encendido", "marca": "Bosch", "categoria": "Encendido", "precio": 890, "existencia": 12},
    {"codigo": "PRU-011", "nombre": "Bomba de Agua", "marca": "Gates", "categoria": "Enfriamiento", "precio": 1300, "existencia": 9},
    {"codigo": "BUJ-003", "nombre": "Bujia de encendido", "marca": "NGK", "categoria": "Encendido", "precio": 120, "existencia": 40},
    {"codigo": "FIL-001", "nombre": "Filtro de Aceite", "marca": "Gonher", "categoria": "Filtros", "precio": 95, "existencia": 20, "universal": True},
    {"codigo": "PRU-006", "nombre": "Filtro de aire", "marca": "Gonher", "categoria": "Filtros", "precio": 180, "existencia": 15},
    {"codigo": "PRU-007", "nombre": "Filtro de Combustible", "marca": "Gonher", "categoria": "Filtros", "precio": 350, "existencia": 12},
    {"codigo": "PRU-010", "nombre": "Radiador de motor", "marca": "Denso", "categoria": "Enfriamiento", "precio": 2800, "existencia": 4},
    {"codigo": "PRU-013", "nombre": "Sensor de Oxigeno", "marca": "Denso", "categoria": "Escape", "precio": 1150, "existencia": 9},
    {"codigo": "PRU-014", "nombre": "Termostato de Motor", "marca": "Bosch", "categoria": "Enfriamiento", "precio": 420, "existencia": 16},
]


def _turno(pregunta, historial=(), contexto=None):
    datos = Consulta(
        pregunta=pregunta,
        inventario=json.dumps(INVENTARIO),
        historial=list(historial),
        contexto=contexto or {},
    )
    estado = EstadoConsulta(datos=datos)
    with contextlib.redirect_stdout(io.StringIO()):
        for etapa in ETAPAS:
            respuesta = etapa(estado)
            if respuesta is not None:
                return respuesta.get("respuesta", ""), respuesta.get("contexto") or {}
    return "<MODELO>", contexto or {}


def _cumple(esperado, texto, pregunta):
    if esperado == "MEC":
        if texto == "<MODELO>":
            p = preparar_pregunta(pregunta)
            return bool(buscar_respuesta_rapida(p) or buscar_conocimiento(p))
        return "No entendí" not in texto and not texto.startswith("Productos activos")
    if texto == "<MODELO>":
        return False
    if esperado == "NO":
        return texto.startswith(("No hay", "No encontr", "No tengo"))
    if esperado == "SOC":
        return any(k in texto for k in ("Hola", "hola", "nada", "Puedo ayudarte", "No entendí", "gusto", "¡"))
    if esperado == "LISTA":
        return "Productos activos" in texto
    if esperado == "VEH":
        return "compatibilidad registrada" in texto
    if esperado == "CATS":
        return texto.startswith("Categorías que")
    if esperado == "MARCAS":
        return texto.startswith("Marcas que")
    if esperado.startswith("CAT:"):
        return f"categoría {esperado[4:]}" in texto
    if esperado in ("barato", "caro", "agotad", "stock bajo", "compatib"):
        return esperado in texto.casefold()
    codigo = esperado.lstrip("$#=")
    if codigo not in texto or "Productos activos" in texto:
        return False
    if esperado[0] == "$":
        return "$" in texto
    if esperado[0] == "#":
        return "pieza" in texto
    if esperado[0] == "=":
        return "Total" in texto or "Subtotal" in texto
    return True


def _tabla(bloque):
    return [
        tuple(x.strip() for x in linea.split("|"))
        for linea in bloque.strip().splitlines()
        if "|" in linea and not linea.lstrip().startswith("#")
    ]


CASOS = _tabla("""
# --- pieza sola / con relleno ---
termostato | PRU-014
el termostato | PRU-014
termostatos | PRU-014
un termostato | PRU-014
tienes termostato? | PRU-014
hay termostatos | PRU-014
manejas termostatos? | PRU-014
busco un termostato | PRU-014
necesito un termostato | PRU-014
ocupo termostato | PRU-014
me das info del termostato | PRU-014
datos del termostato | PRU-014
el termostato que tienes | PRU-014
termostato de motor | PRU-014
sensor | PRU-013
sensor de oxígeno | PRU-013
sonda de oxigeno | PRU-013
bomba de agua | PRU-011
bomba | PRU-011
radiador | PRU-010
alternador | PRU-009
marcha | NO
batería | PRU-008
acumulador | PRU-008
pila | PRU-008
bobina | PRU-015
bobinas | PRU-015
bujías | BUJ-003
bujia ngk | BUJ-003
ngk | BUJ-003
amortiguador | AMO-005
amortiguadores | AMO-005
amortis | AMO-005
monroe | AMO-005
balatas | BAL-002
pastillas | BAL-002
pastillas de freno | BAL-002
brembo | BAL-002
banda | PRU-012
banda de accesorios | PRU-012
correa | PRU-012
filtro de aire | PRU-006
filtro de combustible | PRU-007
filtro de gasolina | PRU-007
filtro de aceite | FIL-001
llantas | NO
mofle | NO
rotulas | NO
discos de freno | NO
# --- precio ---
precio del termostato | $PRU-014
cuanto cuesta el termostato | $PRU-014
cuánto vale el termostato | $PRU-014
cuanto sale el termostato | $PRU-014
a cómo el termostato | $PRU-014
en cuanto el termostato | $PRU-014
qué precio tiene el termostato | $PRU-014
termostato precio | $PRU-014
termostato cuanto | $PRU-014
cuanto el sensor | $PRU-013
precio sensor oxigeno | $PRU-013
cuanto cuestan las bujias | $BUJ-003
y la bobina cuanto | $PRU-015
cuanto me cuesta la bateria | $PRU-008
cuánto le cobro de la banda | $PRU-012
precio de la bomba de agua | $PRU-011
cuanto cuesta el ACE-001 | $ACE-001
precio ace001 | $ACE-001
precio ace 001 | $ACE-001
cuanto el bal 002 | $BAL-002
# --- existencia ---
cuantos termostatos hay | #PRU-014
cuantos termostatos quedan | #PRU-014
cuántas bujías tenemos | #BUJ-003
quedan bujias? | #BUJ-003
existencia del radiador | #PRU-010
stock del alternador | #PRU-009
cuantas baterias quedan | #PRU-008
hay sensores de oxigeno en existencia | #PRU-013
cuantas piezas del BAL-002 | #BAL-002
existencias ace 001 | #ACE-001
# --- cálculo ---
3 termostatos | =PRU-014
cuanto son 3 termostatos | =PRU-014
3 termostatos con iva | =PRU-014
si vendo 3 termostatos | =PRU-014
me llevo 2 baterias | =PRU-008
cuanto es 4 bujias con iva | =BUJ-003
dame el total de 5 bujias | =BUJ-003
2 balatas con 10% de descuento | =BAL-002
vendo 2 del ACE-001 | =ACE-001
cuánto sería por 6 filtros de aire | =PRU-006
# --- vehículo ---
que tienes para un versa 2015 | VEH
refacciones para corolla | VEH
algo para mi corolla 2016 | VEH
que le queda a un versa | VEH
piezas para toyota corolla | VEH
corolla 2015 | VEH
versa | VEH
nissan versa 2018 | VEH
toyota 2016 | VEH
balatas para versa 2015 | VEH
amortiguadores para corolla 2017 | VEH
que le sirve a un yaris 2018 | VEH
# --- categorías / listas ---
frenos | CAT:Frenos
cosas de frenos | CAT:Frenos
lo de suspension | CAT:Suspensión
que hay de motor | CAT:Motor
productos de encendido | CAT:Encendido
enfriamiento | CAT:Enfriamiento
filtros | CAT:Filtros
categorias | CATS
que categorias manejas | CATS
marcas | MARCAS
que tenemos en inventario | LISTA
todo el inventario | LISTA
muestrame todos los productos | LISTA
lista de productos | LISTA
que productos hay | LISTA
lo mas barato | barato
el producto mas caro | caro
que esta agotado | agotad
que se esta acabando | stock bajo
productos con poco stock | stock bajo
# --- mecánica ---
mi carro se calienta | MEC
rechinan los frenos | MEC
el carro no arranca | MEC
el carro vibra en carretera | MEC
el volante esta duro | MEC
falla mi manguera | MEC
la transmision falla | MEC
huele a gasolina | MEC
sale humo blanco | MEC
se prendio el check engine | MEC
el clutch patina | MEC
para que sirve el termostato | MEC
que hace el alternador | MEC
diferencia entre bateria y alternador | MEC
cada cuanto se cambia el aceite | MEC
el clima no enfria | MEC
el carro jalonea | MEC
se descarga la bateria | MEC
truena la suspension | MEC
la direccion tiene juego | MEC
# --- social / raro ---
hola | SOC
buenas tardes | SOC
gracias | SOC
ayuda | SOC
que puedes hacer | SOC
hablame de autos | SOC
asdfgh | SOC

termostto | PRU-014
termosato | PRU-014
el termo | PRU-014
sensro | PRU-013
alternado | PRU-009
amortiguadro | AMO-005
vujias | BUJ-003
q tienes de frenos | CAT:Frenos
ay balatas? | BAL-002
cuanto cuesta el termostato porfa | $PRU-014
oye cuanto cuesta el termostato | $PRU-014
precio del termostato x favor | $PRU-014
cuanto cuesta un termostato de motor | $PRU-014
a como dejas el radiador | $PRU-010
cuanto le cobro al cliente por el radiador | $PRU-010
cuánto cuesta la batería con iva | $PRU-008
traes baterias? | PRU-008
tendras bujias ngk? | BUJ-003
me llevo 3 bujias | =BUJ-003
cuanto serian 4 bujias | =BUJ-003
si se lleva 2 radiadores con iva | =PRU-010
dos baterias | =PRU-008
tres termostatos con iva | =PRU-014
hay algo para un corolla 2016? | VEH
que le queda a mi versa 2015 | VEH
pa un versa 2015 que tienes | VEH
refacciones pa mi corolla | VEH
lo que tengas de suspension | CAT:Suspensión
dame lo de encendido | CAT:Encendido
que hay en el inventario | LISTA
mi nave se calienta | MEC
mi carro tira aceite | MEC
la troca no tiene jalon | MEC
chillan las balatas | MEC
el foquito del aceite se prendio | MEC

por que rechinan las balatas | MEC
el termostato falla | MEC
que es un termostato | MEC
termostato pegado | MEC
la bateria no carga | MEC
que hace el sensor de oxigeno | MEC
cada cuando se cambian las bujias | MEC
para que sirve la bomba de agua | MEC
""")


@pytest.mark.parametrize("pregunta, esperado", CASOS)
def test_formas_de_preguntar(pregunta, esperado):
    texto, _ = _turno(pregunta)
    assert _cumple(esperado, texto, pregunta), f"{pregunta!r} -> {texto[:200]!r}"


CONVERSACIONES = [
    [("termostato", "PRU-014"), ("cuanto cuesta", "$PRU-014"), ("dame 3", "=PRU-014"), ("con iva", "=PRU-014")],
    [("sensor", "PRU-013"), ("cuantos quedan", "#PRU-013"), ("y su precio", "$PRU-013")],
    [("bujias", "BUJ-003"), ("si vendo 10", "=BUJ-003")],
    [("filtros", "CAT:Filtros"), ("el segundo", "PRU-006"), ("cuanto cuesta", "$PRU-006")],
    [("que tienes para corolla", "VEH"), ("y para versa 2015", "VEH")],
    [("radiador", "PRU-010"), ("y el termostato", "PRU-014"), ("cuanto cuesta", "$PRU-014")],
    [("balatas", "BAL-002"), ("le queda a un versa 2015?", "compatib"), ("y a un corolla 2016?", "compatib")],
]



@pytest.mark.parametrize("conversacion", CONVERSACIONES)
def test_conversaciones(conversacion):
    historial, contexto = [], {}
    for pregunta, esperado in conversacion:
        texto, contexto = _turno(pregunta, historial, contexto)
        assert _cumple(esperado, texto, pregunta), f"{pregunta!r} -> {texto[:200]!r}"
        historial += [{"rol": "user", "texto": pregunta}, {"rol": "assistant", "texto": texto}]


@pytest.mark.parametrize("pregunta, cantidades", [
    ("me llevo 2 baterías y 1 alternador", {"PRU-008": 2, "PRU-009": 1}),
    ("3 bujias y 2 bobinas con iva", {"BUJ-003": 3, "PRU-015": 2}),
    ("si vendo dos termostatos y un radiador", {"PRU-014": 2, "PRU-010": 1}),
    ("me llevo 2 baterias, 1 alternador y 4 bujias", {"PRU-008": 2, "PRU-009": 1, "BUJ-003": 4}),
])
def test_varias_piezas_con_su_cantidad(pregunta, cantidades):
    texto, _ = _turno(pregunta)
    for codigo, cantidad in cantidades.items():
        assert f"({codigo}): {cantidad} ×" in texto, texto


@pytest.mark.parametrize("pregunta, esperado", [
    ("cada cuánto se cambia el aceite", "intervalo"),
    ("para qué autos sirve el amortiguador", "Toyota Corolla"),
    ("a que carros le queda el amortiguador", "Toyota Corolla"),
])
def test_no_confunde_cada_cuanto_ni_vehiculos(pregunta, esperado):
    texto, _ = _turno(pregunta)
    assert esperado in texto, texto


# ---------------------------------------------------------------------
# Vender TODO un grupo: categoría completa o la lista anterior
# ---------------------------------------------------------------------

def _conversar(preguntas, contexto=None):
    historial, contexto, respuestas = [], dict(contexto or {}), []
    for pregunta in preguntas:
        texto, contexto = _turno(pregunta, historial, contexto)
        respuestas.append(texto)
        historial += [{"rol": "user", "texto": pregunta}, {"rol": "assistant", "texto": texto}]
    return respuestas


@pytest.mark.parametrize("pregunta, categoria", [
    ("si vendo todo de escape", "Escape"),
    ("vendo todo el encendido", "Encendido"),
    ("suma todo de encendido", "Encendido"),
    ("vender todo de categoría enfriamiento", "Enfriamiento"),
    ("escape total", "Escape"),
])
def test_vender_toda_una_categoria(pregunta, categoria):
    # Aunque haya un producto viejo seleccionado, se usa la categoría.
    texto = _conversar([pregunta], {"codigo_seleccionado": "ACE-001"})[0]
    assert texto.startswith(f"Venta de toda la existencia de la categoría {categoria}"), texto
    assert "ACE-001" not in texto


def test_vender_todo_de_la_lista_anterior():
    respuestas = _conversar(["encendido", "vendo todo"])
    assert respuestas[1].startswith("Venta de toda la existencia de los productos de la lista anterior")
    assert "PRU-015" in respuestas[1] and "BUJ-003" in respuestas[1]


def test_total_despues_de_lista_no_suma_precios_unitarios():
    respuestas = _conversar(["frenos", "escape total"])
    assert "Suma de las cantidades" not in respuestas[1]
    assert "categoría Escape" in respuestas[1]


def test_cuanto_gano_aclara_que_falta_el_costo():
    respuestas = _conversar(["encendido", "si los vendo todo cuanto gano"])
    assert "costo de compra" in respuestas[1]


def test_venderlo_todo_tras_un_producto():
    respuestas = _conversar(["filtros", "termostato", "venderlo todo"])
    assert respuestas[2].startswith("Cálculo para Termostato de Motor (PRU-014)")


@pytest.mark.parametrize("pregunta", ["vendo todo de llantas", "si vendo todo de carroceria"])
def test_vender_todo_de_algo_que_no_hay(pregunta):
    texto = _conversar([pregunta])[0]
    assert texto.startswith("No hay productos registrados"), texto


# ---------------------------------------------------------------------
# Tipos de pregunta: comparar, contar por grupo, suficiencia, lista
# mostrada, recomendaciones por servicio y correcciones
# ---------------------------------------------------------------------

@pytest.mark.parametrize("pregunta, empieza", [
    ("cual es mas barato el termostato o el radiador", "El más barato es Termostato de Motor (PRU-014)"),
    ("que es mas caro la bateria o el alternador", "El más caro es Alternador (PRU-009)"),
    ("compara el BUJ-003 y el PRU-015", "El más barato es Bujia de encendido (BUJ-003)"),
])
def test_comparar_productos(pregunta, empieza):
    texto, _ = _turno(pregunta)
    assert texto.startswith(empieza), texto


def test_comparar_los_dos_ultimos_vistos():
    respuestas = _conversar(["bateria", "y el alternador?", "cual es mas barato"])
    assert respuestas[2].startswith("El más barato es Batería de 12V (PRU-008)")


@pytest.mark.parametrize("pregunta, debe", [
    ("cuantos productos hay de filtros", "En la categoría Filtros hay 3 productos"),
    ("cuantas piezas hay en total de encendido", "En la categoría Encendido hay 2 productos"),
    ("cuantas marcas manejamos", "Se manejan"),
    ("cuantos productos tenemos en total", "Actualmente hay 15 productos"),
    ("cuantas piezas de aceite quedan", "ACE-001"),
])
def test_contar_por_grupo(pregunta, debe):
    texto, _ = _turno(pregunta)
    assert debe in texto, texto


@pytest.mark.parametrize("pregunta, empieza", [
    ("hay suficiente bateria para vender 10", "No alcanza: solo hay 8 piezas"),
    ("me alcanza el stock para 20 bujias", "Sí alcanza: hay 40 piezas"),
])
def test_suficiencia(pregunta, empieza):
    texto, _ = _turno(pregunta)
    assert texto.startswith(empieza), texto


def test_sobre_la_lista_mostrada():
    respuestas = _conversar(["filtros", "el mas barato de esos", "cuantos quedan"])
    assert respuestas[1].startswith("El más barato de esa lista es Filtro de Aceite (FIL-001)")
    assert "FIL-001" in respuestas[2]


def test_existencias_de_esa_lista():
    respuestas = _conversar(["balatas para versa 2015", "y de esas cuantas hay"])
    assert respuestas[1].startswith("Existencia de los productos de esa lista")


@pytest.mark.parametrize("pregunta, servicio", [
    ("un cliente va a hacer afinacion que le vendo", "Para una afinación"),
    ("que le ofrezco a un cliente que quiere frenar mejor", "Para el servicio de frenos"),
])
def test_recomendacion_por_servicio(pregunta, servicio):
    texto, _ = _turno(pregunta)
    assert texto.startswith(servicio), texto
    assert "Para hacer el cálculo" not in texto


def test_que_pieza_le_vendo_usa_el_tema():
    respuestas = _conversar(["mi carro se calienta", "que pieza le vendo"])
    assert respuestas[1].startswith("Para el sistema de enfriamiento")
    assert "PRU-014" in respuestas[1]


def test_correcciones_en_la_conversacion():
    respuestas = _conversar(["termostato", "no, el radiador", "cuanto cuesta"])
    assert "PRU-010" in respuestas[1] and "PRU-010" in respuestas[2]
    respuestas = _conversar(["si vendo 3 termostatos", "mejor 5", "quitale el iva"])
    assert "Cantidad: 5 piezas" in respuestas[1] and "Cantidad: 5 piezas" in respuestas[2]


def test_stock_bajo_de_una_categoria():
    texto, _ = _turno("que productos estan por agotarse de enfriamiento")
    assert "de la categoría Enfriamiento" in texto
    assert "ACE-001" not in texto


@pytest.mark.parametrize("pregunta", [
    "por que huele a quemado mi carro", "el carro hace ruido al dar vuelta",
    "el carro tiembla en neutral", "gotea liquido verde debajo del carro",
    "se escucha un chillido al arrancar",
])
def test_sintomas_nuevos_tienen_documentacion(pregunta):
    texto, _ = _turno(pregunta)
    assert _cumple("MEC", texto, pregunta), texto


# ---------------------------------------------------------------
# "Cuánto cuesta todo" después de una lista
# ---------------------------------------------------------------

def test_cuanto_cuesta_todo_de_la_lista_es_una_de_cada():
    texto = _conversar(["enfriamiento", "cuanto cuesta todo?"])[1]
    assert texto.startswith("Una pieza de cada uno de los productos de la lista anterior")
    assert "PRU-010" in texto and "PRU-011" in texto and "PRU-014" in texto
    assert "Si fuera toda la existencia" in texto


def test_compro_todos_los_de_la_lista_tras_no_entendi():
    # Aunque el último mensaje fue "No pude identificar...", se usa la
    # lista completa más reciente de la conversación.
    historial = []
    lista, _ = _turno("enfriamiento")
    historial += [{"rol": "user", "texto": "enfriamiento"}, {"rol": "assistant", "texto": lista}]
    historial += [{"rol": "user", "texto": "cuanto cuesta eso"},
                  {"rol": "assistant", "texto": "No pude identificar con seguridad la refacción."}]
    texto, _ = _turno("cuanto seria si compro todos los productos de la lista", historial, {})
    assert texto.startswith("Una pieza de cada uno"), texto
    assert "PRU-010" in texto and "PRU-011" in texto and "PRU-014" in texto


def test_lista_larga_no_se_corta_en_quince():
    # Inventario de 42 piezas solo para esta prueba; al final se
    # regresa el original.
    global INVENTARIO  # pylint: disable=global-statement
    original = INVENTARIO
    INVENTARIO = [
        {"codigo": f"PRO-{i:03d}", "nombre": f"Pieza prueba {i}", "marca": "Bosch",
         "categoria": "Motor", "precio": 100 + i, "existencia": 2, "universal": False,
         "vehiculosCompatibles": ["Chevrolet Aveo 2018-2024"]}
        for i in range(1, 43)
    ]
    try:
        respuestas = _conversar([
            "que productos tienen autos compatibles",
            "me refiero a cuanto seria si compro todos los productos de la lista",
        ])
    finally:
        INVENTARIO = original
    assert "• Productos: 42" in respuestas[1], respuestas[1][-300:]


def test_vender_todo_sigue_siendo_toda_la_existencia():
    texto = _conversar(["encendido", "vendo todo"])[1]
    assert texto.startswith("Venta de toda la existencia")


def test_cuanto_cuesta_todo_sin_lista_pregunta_de_que():
    assert _conversar(["cuanto cuesta todo?"])[0].startswith("¿Todo de qué?")


def test_cuanto_cuesta_todo_tras_un_producto_usa_ese_producto():
    texto = _conversar(["termostato", "cuanto cuesta todo"])[1]
    assert texto.startswith("Cálculo para Termostato de Motor")


def test_compro_con_cantidades():
    texto = _conversar(["compro 2 balatas y 1 radiador"])[0]
    assert texto.startswith("Suma de productos") and "BAL-002" in texto and "PRU-010" in texto


def test_precio_normal_no_cambia():
    assert _conversar(["cuanto cuesta el termostato"])[0].startswith("El precio de Termostato")


@pytest.mark.parametrize("pregunta, inicio", [
    ("fr3nos", "Productos de la categoría Frenos"),
    ("3nfri4miento", "Productos de la categoría Enfriamiento"),
    ("b4l4t4s", "Balatas delanteras Ceramitas"),
])
def test_numeros_en_lugar_de_letras_en_conversacion(pregunta, inicio):
    assert _conversar([pregunta])[0].startswith(inicio)


# ---------------------------------------------------------------
# "Si vendo los 55 productos" / "las 488 piezas" = todo el inventario
# ---------------------------------------------------------------

def _totales():
    return len(INVENTARIO), sum(p["existencia"] for p in INVENTARIO)


@pytest.mark.parametrize("plantilla", [
    "cuanto es el total si vendo los {productos} productos",
    "cuanto es el total si vendo los {piezas} productos",
    "total si vendo las {piezas} piezas",
    "si vendo todos los productos",
])
def test_vender_todo_el_inventario_por_numero(plantilla):
    productos, piezas = _totales()
    texto = _conversar([plantilla.format(productos=productos, piezas=piezas)])[0]
    assert texto.startswith("Valor de todo el inventario activo"), texto
    assert f"• Piezas: {piezas}" in texto


def test_numero_que_no_coincide_con_el_inventario():
    texto = _conversar(["si vendo los 100 productos"])[0]
    assert "no sé cuáles serían esos 100" in texto


def test_vender_todos_los_productos_tras_lista_usa_la_lista():
    texto = _conversar(["enfriamiento", "si vendo todos los productos"])[1]
    assert texto.startswith("Venta de toda la existencia de los productos de la lista anterior")


# ---------------------------------------------------------------
# Vender toda una categoría aunque un producto se llame parecido
# ---------------------------------------------------------------

_INVENTARIO_MOTOR = [
    {"codigo": "ELE-003", "nombre": "Motor de Arranque", "marca": "Bosch",
     "categoria": "Sistema eléctrico", "precio": 2890, "existencia": 2},
    {"codigo": "MOT-101", "nombre": "Junta de cabeza 1.6L", "marca": "Victor Reinz",
     "categoria": "Motor", "precio": 780, "existencia": 6},
    {"codigo": "MOT-102", "nombre": "Bomba de aceite", "marca": "Melling",
     "categoria": "Motor", "precio": 1450, "existencia": 3},
    {"codigo": "ENC-101", "nombre": "Bujía de iridio", "marca": "NGK",
     "categoria": "Encendido", "precio": 210, "existencia": 40},
    {"codigo": "FIL-101", "nombre": "Filtro de aceite", "marca": "Mann",
     "categoria": "Filtros", "precio": 140, "existencia": 25},
    {"codigo": "ACE-101", "nombre": "Aceite sintético 5W-30 (4 L)", "marca": "Castrol",
     "categoria": "Aceites", "precio": 890, "existencia": 18},
]


def _con_inventario_motor(preguntas):
    global INVENTARIO  # pylint: disable=global-statement
    original = INVENTARIO
    INVENTARIO = _INVENTARIO_MOTOR
    try:
        return _conversar(preguntas)
    finally:
        INVENTARIO = original


@pytest.mark.parametrize("pregunta", [
    "no no, yo hablo de vender todos los productos que están en el apartado de motor",
    "si vendo todo lo de motor",
    "vender todos los productos de la categoria motor",
    "cuanto gano si vendo todo lo que hay en motor",
])
def test_vender_categoria_motor_no_es_motor_de_arranque(pregunta):
    texto = _con_inventario_motor([pregunta])[0]
    assert texto.startswith("Venta de toda la existencia de la categoría Motor"), texto
    assert "ELE-003" not in texto


def test_vender_todo_el_motor_de_arranque_es_el_producto():
    texto = _con_inventario_motor(["vendo todo el motor de arranque"])[0]
    assert texto.startswith("Cálculo para Motor de Arranque"), texto


def test_vender_todos_los_productos_de_una_categoria():
    texto = _con_inventario_motor(["vendo todos los productos de encendido"])[0]
    assert texto.startswith("Venta de toda la existencia de la categoría Encendido"), texto


def test_vender_todo_el_filtro_de_aceite_no_es_categoria_aceites():
    texto = _con_inventario_motor(["vendo todo el filtro de aceite"])[0]
    assert "FIL-101" in texto and "categoría Aceites" not in texto, texto
