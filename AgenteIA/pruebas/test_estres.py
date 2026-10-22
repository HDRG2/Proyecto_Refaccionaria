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


