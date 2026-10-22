import os
import re
import unicodedata
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path


# =====================================================================
# 1. TABLAS DE EQUIVALENCIAS
#    (forma coloquial, forma estándar). Se escriben SIN acentos y en
#    minúsculas: el patrón acepta igual "cómo", "COMO" o "como".
#    Las frases largas van antes que las cortas que contienen.
# =====================================================================

# --- Abreviaturas y faltas de ortografía comunes --------------------
ABREVIATURAS = [
    ("xq", "por que"), ("pq", "por que"), ("porq", "por que"), ("xk", "por que"),
    ("q", "que"), ("k", "que"), ("ke", "que"),
    ("tmbn", "tambien"), ("tmb", "tambien"), ("tbn", "tambien"), ("tb", "tambien"),
    ("xfavor", "por favor"), ("xfa", "por favor"), ("porfas", "por favor"),
    ("porfi", "por favor"),
    ("pa'l", "para el"), ("pal", "para el"), ("pa'", "para"), ("pa", "para"),
    ("kuanto", "cuanto"), ("qanto", "cuanto"), ("qnto", "cuanto"),
    ("cnto", "cuanto"), ("cuantoo", "cuanto"),
    ("kuantos", "cuantos"), ("kuantas", "cuantas"),
    ("kuesta", "cuesta"), ("questa", "cuesta"), ("cuezta", "cuesta"),
    ("kuestan", "cuestan"), ("questan", "cuestan"),
    ("nesesito", "necesito"), ("nececito", "necesito"),
    ("nesecito", "necesito"), ("necsito", "necesito"),
    ("kiero", "quiero"), ("qiero", "quiero"),
    ("tienez", "tienes"), ("tines", "tienes"), ("tiens", "tienes"),
    ("aver", "a ver"),
    ("nomas", "solo"), ("namas", "solo"), ("na mas", "solo"),
    ("refas", "refacciones"), ("refa", "refaccion"),
    ("refaxiones", "refacciones"), ("refaciones", "refacciones"),
    ("refaccion", "refaccion"),
]

# --- Precio ----------------------------------------------------------
PRECIO = [
    ("cuanto le cobro por", "cual es el precio de"),
    ("cuanto le cobro de", "cual es el precio de"),
    ("cuanto le cobro", "cual es el precio de"),
    ("cuanto le cobramos por", "cual es el precio de"),
    ("cuanto le cobramos", "cual es el precio de"),
    ("que precio trae", "cual es el precio de"),
    ("que precio traen", "cual es el precio de"),
    ("que precio maneja", "cual es el precio de"),
    ("que precio manejas", "cual es el precio de"),
    ("que precio manejan", "cual es el precio de"),
    ("a como me lo das", "cual es el precio de"),
    ("a como me dejas", "cual es el precio de"),
    ("a como dejas", "cual es el precio de"),
    ("en cuanto me dejas", "cual es el precio de"),
    ("en cuanto dejas", "cual es el precio de"),
    ("a como das", "cual es el precio de"),
    ("a como me las das", "cual es el precio de"),
    ("a como me los das", "cual es el precio de"),
    ("a como me la das", "cual es el precio de"),
    ("a como las das", "cual es el precio de"),
    ("a como los das", "cual es el precio de"),
    ("a como la das", "cual es el precio de"),
    ("a como andan", "cual es el precio de"),
    ("a como estan", "cual es el precio de"),
    ("en cuanto me queda", "cual es el precio de"),
    ("en cuanto quedan", "cual es el precio de"),
    ("en cuanto queda", "cual es el precio de"),
    ("en cuanto salen", "cual es el precio de"),
    ("en cuanto estan", "cual es el precio de"),
    ("en cuanto andan", "cual es el precio de"),
    ("cuanto salen", "cual es el precio de"),
    ("cuanta lana es", "cuanto cuesta"),
    ("cuanta lana", "cuanto cuesta"),
    ("cuanta feria es", "cuanto cuesta"),
    ("cuanta feria", "cuanto cuesta"),
    ("cuanto varo es", "cuanto cuesta"),
    ("cuanto varo", "cuanto cuesta"),
    ("cuantos varos", "cuanto cuesta"),
    ("cuanto baro", "cuanto cuesta"),
    ("cuantos baros", "cuanto cuesta"),
    ("cuanto dinero es", "cuanto cuesta"),
    ("que tanto cuesta", "cuanto cuesta"),
    ("que tanto cuestan", "cuanto cuestan"),
    ("cuanto cuesta cada", "cuanto cuesta"),
]

# --- Existencia / disponibilidad ------------------------------------
EXISTENCIA = [
    ("cuentas con", "tienes"), ("cuentan con", "tienen"),
    ("traes", "tienes"), ("traen", "tienen"), ("traemos", "tenemos"),
    ("tendras", "tienes"), ("tendran", "tienen"), ("tendra", "tiene"),
    ("me consigues", "tienes"), ("me consiguen", "tienen"),
    ("manejaras", "manejas"), ("habra", "hay"), ("habran", "hay"),
    ("en bodega", "en existencia"), ("en almacen", "en existencia"),
    ("en el almacen", "en existencia"), ("en la bodega", "en existencia"),
]

# --- Refacciones -----------------------------------------------------
REFACCIONES = [
    ("pastillas de frenos", "balatas"), ("pastillas de freno", "balatas"),
    ("pastilla de freno", "balata"), ("pastillas", "balatas"),
    ("pastilla", "balata"), ("balatitas", "balatas"), ("balatita", "balata"),
    ("filtritos", "filtros"), ("filtrito", "filtro"),
    ("aceitito", "aceite"), ("bujitas", "bujias"), ("bujiitas", "bujias"),
    ("bandita", "banda"),
    ("amortiguas", "amortiguadores"), ("amortis", "amortiguadores"),
    ("shocks", "amortiguadores"), ("shock", "amortiguador"),
    ("pilas", "baterias"), ("pila", "bateria"),
    ("acumuladores", "baterias"), ("acumulador", "bateria"),
    ("chicotes", "cables"), ("chicote", "cable"),
    ("sencores", "sensores"), ("sencor", "sensor"),
    ("sonda de oxigeno", "sensor de oxigeno"), ("sonda lambda", "sensor de oxigeno"),
    ("sensor lambda", "sensor de oxigeno"), ("sonda", "sensor"),
    ("correas", "bandas"), ("correa", "banda"),
    ("cloche", "clutch"), ("cloch", "clutch"), ("cluch", "clutch"),
    ("kloch", "clutch"), ("clotch", "clutch"),
    ("filtro de la gasolina", "filtro de combustible"),
    ("filtro de gasolina", "filtro de combustible"),
    ("filtro de gas", "filtro de combustible"),
    ("filtro de nafta", "filtro de combustible"),
    ("filtro de diesel", "filtro de combustible"),
    ("filtro del aire", "filtro de aire"),
    ("filtro del aceite", "filtro de aceite"),
    ("bomba de gas", "bomba de gasolina"),
    ("bomba del agua", "bomba de agua"),
    ("banda del tiempo", "banda de distribucion"),
    ("banda de tiempo", "banda de distribucion"),
    ("correa de tiempo", "banda de distribucion"),
    ("empaque de la cabeza", "junta de culata"),
    ("empaque de cabeza", "junta de culata"),
    ("junta de cabeza", "junta de culata"),
    ("la liga de frenos", "el liquido de frenos"),
    ("la liga del freno", "el liquido de frenos"),
    ("liga de frenos", "liquido de frenos"),
    ("liga del freno", "liquido de frenos"),
    ("agua del radiador", "refrigerante"),
    ("agua verde", "anticongelante"), ("liquido verde", "anticongelante"),
    ("liquido rosa", "anticongelante"), ("liquido naranja", "anticongelante"),
    ("foquito del motor", "check engine"), ("foco del motor", "check engine"),
    ("luz del motor", "check engine"), ("foquitos", "focos"),
    ("foquito", "foco"),
    ("llanta ponchada", "ponchadura de llanta"),
]

# --- Vehículo --------------------------------------------------------
VEHICULOS = [
    ("carcachita", "carro"), ("carcacha", "carro"), ("cacharro", "carro"),
    ("ranfla", "carro"), ("nave", "carro"), ("carrucha", "carro"),
    ("carrito", "carro"),
    ("trokita", "camioneta"), ("troquita", "camioneta"),
    ("trocka", "camioneta"), ("troca", "camioneta"), ("trocota", "camioneta"),
    ("vochito", "volkswagen sedan"), ("vocho", "volkswagen sedan"),
    ("tsurito", "tsuru"), ("tsurillo", "tsuru"), ("jettita", "jetta"),
    ("aveito", "aveo"), ("versita", "versa"), ("chevito", "chevy"),
]

# --- Síntomas mecánicos ---------------------------------------------
# Se traducen a las expresiones que ya conoce la documentación.
SINTOMAS = [
    ("se le sube la aguja", "sube la temperatura"),
    ("se sube la aguja", "sube la temperatura"),
    ("se le subio la aguja", "sube la temperatura"),
    ("se pone bien caliente", "se calienta mucho"),
    ("se pone muy caliente", "se calienta mucho"),
    ("se pone caliente", "se calienta"),
    ("esta hirviendo", "se sobrecalienta"),
    ("se hirvio", "se sobrecalienta"), ("hirvio", "se sobrecalienta"),
    ("traga mucha gasolina", "gasta mucha gasolina"),
    ("chupa mucha gasolina", "gasta mucha gasolina"),
    ("se bebe la gasolina", "gasta mucha gasolina"),
    ("se traga la gasolina", "gasta mucha gasolina"),
    ("se come la gasolina", "gasta mucha gasolina"),
    ("chorrea aceite", "tira aceite"), ("escurre aceite", "tira aceite"),
    ("pierde aceite", "tira aceite"), ("bota aceite", "tira aceite"),
    ("suelta aceite", "tira aceite"),
    ("se come el aceite", "consume aceite"), ("come aceite", "consume aceite"),
    ("quema aceite", "consume aceite"), ("se traga el aceite", "consume aceite"),
    ("se chupa el aceite", "consume aceite"),
    ("hace un ruidito", "hace ruido"), ("hace ruidito", "hace ruido"),
    ("hace un ruidazo", "hace ruido"), ("hace ruidajo", "hace ruido"),
    ("suena feo", "hace ruido"), ("suena raro", "hace ruido"),
    ("ruidito", "ruido"), ("ruidajo", "ruido"), ("ruidazo", "ruido"),
    ("no tiene jalon", "pierde potencia"), ("no tiene pique", "pierde potencia"),
    ("le falta pique", "pierde potencia"), ("no camina", "pierde potencia"),
    ("da jaloncitos", "da tirones"), ("da jalones", "da tirones"),
    ("se jalonea", "da tirones"),
    ("avienta aire caliente", "no enfria"),
    ("echa aire caliente", "no enfria"),
    ("sale aire caliente", "no enfria"),
    ("no echa frio", "no enfria"), ("no echa aire frio", "no enfria"),
    ("se me poncho", "ponchadura de llanta"), ("se poncho", "ponchadura de llanta"),
]

# --- Cálculos de venta ----------------------------------------------
CALCULOS = [
    ("descuentito", "descuento"), ("descuentazo", "descuento"),
    ("con todo e iva", "con iva"), ("con todo y iva", "con iva"),
    ("ya con iva", "con iva"), ("iva incluido", "con iva"),
    ("incluyendo iva", "con iva"), ("incluyendo el iva", "con iva"),
    ("con impuestos", "con iva"), ("con impuesto", "con iva"),
    ("sin el iva", "sin iva"), ("antes de iva", "sin iva"),
    ("sin impuestos", "sin iva"), ("sin impuesto", "sin iva"),
    ("antes de impuestos", "sin iva"),
    ("un parcito", "un par"),
]

TABLAS = (ABREVIATURAS, PRECIO, EXISTENCIA, REFACCIONES, VEHICULOS,
          SINTOMAS, CALCULOS)


# Patrones que necesitan mirar alrededor (no son una simple frase).
PATRONES = [
    # "500 varos", "mil bolas" -> "500 pesos"
    (r"(\d[\d,.]*|\bmil)\s+(?:varos|baros|bolas|pesitos|morlacos)\b", r"\1 pesos"),
    # "a cómo las balatas", "a cuánto el filtro"
    (r"\ba\s+(?:como|cuanto)\s+(?=(?:el|la|los|las|tus|sus|esos|esas)\b)",
     "cual es el precio de "),
    # "¿cuánto por el filtro?"
    (r"\bcuanto\s+por\s+(?=(?:el|la|los|las|un|una|este|esta|ese|esa)\b)",
     "cual es el precio de "),
    # "¿ay balatas?" -> "¿hay balatas?"
    (r"(?<!\w)ay(?=\s+(?!no\b|que\b|dios\b)[a-z0-9])", "hay"),
    # "se me murió", "se le muere" -> se apaga solo (pero no la batería)
    (r"\bse\s+(?:me\s+|le\s+)?(?:muere|murio|apaga y ya)\b"
     r"(?!\s+(?:la|el)\s+(?:bateria|pila|acumulador|alternador|marcha))",
     "se apaga solo"),
    (r"\bse\s+(?:me\s+|le\s+)?(?:muere|murio)\s+(?:la|el)\s+(?:bateria|pila|acumulador)\b",
     "se descarga la bateria"),
]


# =====================================================================
# MOTOR DE REEMPLAZO
# =====================================================================

def _sin_acentos(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(c for c in texto if not unicodedata.combining(c))


_EQUIV_LETRAS = {
    "a": "[aáà]", "e": "[eéè]", "i": "[iíì]",
    "o": "[oóò]", "u": "[uúüù]", "n": "[nñ]",
}


def _patron(frase: str) -> re.Pattern:
    partes = []
    for c in frase:
        if c == " ":
            partes.append(r"\s+")
        elif c == "'":
            partes.append(r"['’]")
        else:
            partes.append(_EQUIV_LETRAS.get(c, re.escape(c)))
    # No se toca lo que va pegado a guiones, puntos o diagonales:
    # "-q", "BAL-001", "5w-30", "k.o." se quedan igual.
    final = r"(?![\w\-/]|\.\w)" if frase[-1].isalnum() else ""
    return re.compile(r"(?<![\w'\-/.@])" + "".join(partes) + final, re.IGNORECASE)


def _compilar(tablas):
    pares = [par for tabla in tablas for par in tabla]
    # Primero las frases más largas: "pastillas de freno" antes que "pastillas".
    pares.sort(key=lambda par: len(par[0]), reverse=True)
    return [(_patron(f), r) for f, r in pares if f != r]


# Las abreviaturas van primero ("q precio trae" -> "que precio trae")
# para que luego las demás tablas reconozcan la frase completa.
_ABREVIATURAS = _compilar([ABREVIATURAS])
_REEMPLAZOS = _compilar([t for t in TABLAS if t is not ABREVIATURAS])
_PATRONES = [(re.compile(p, re.IGNORECASE), r) for p, r in PATRONES]


def traducir_coloquial(texto: str) -> str:
    """Convierte modismos, apodos y abreviaturas en la forma estándar."""
    if not texto:
        return texto

    # Los patrones con números/contexto se aplican sobre el texto sin
    # acentos para no depender de cómo escribió el vendedor.
    for patron, reemplazo in _ABREVIATURAS:
        texto = patron.sub(reemplazo, texto)

    for patron, reemplazo in _PATRONES:
        if patron.search(_sin_acentos(texto)):
            texto = patron.sub(reemplazo, _sin_acentos(texto))

    for patron, reemplazo in _REEMPLAZOS:
        texto = patron.sub(reemplazo, texto)

    return " ".join(texto.split())


# =====================================================================
# 2. CORRECCIÓN DE ERRORES DE DEDO
# =====================================================================

def _clave_fonetica(palabra: str) -> str:
    # Cómo "suena" la palabra en español de México: así "valatas",
    # "balatas" y "balatasz" terminan iguales.
    p = _sin_acentos(palabra).casefold()
    p = p.replace("ch", "\x02").replace("ll", "y")
    p = p.replace("gue", "\x01e").replace("gui", "\x01i")
    p = p.replace("ge", "je").replace("gi", "ji").replace("\x01", "g")
    p = p.replace("qu", "k").replace("ce", "se").replace("ci", "si")
    p = p.replace("c", "k").replace("z", "s").replace("v", "b").replace("w", "u")
    p = p.replace("j", "g")  # "embrage" suena igual que "embrague"
    p = p.replace("h", "").replace("\x02", "ch")
    return re.sub(r"(.)\1+", r"\1", p)


def _palabras(texto: str) -> list[str]:
    return re.findall(r"[a-zñ]+", _sin_acentos(texto).casefold())


def _plurales(palabra: str) -> set[str]:
    formas = {palabra}
    if palabra.endswith("s"):
        return formas
    formas.add(palabra + ("s" if palabra[-1] in "aeiou" else "es"))
    return formas


# Palabras de pregunta y de uso diario que NO se corrigen aunque se
# parezcan a una refacción ("acepte" no es "aceite").
_COMUNES = set("""
que cual cuales cuanto cuanta cuantos cuantas como cuando donde quien
porque para pero tambien todavia ahora antes despues siempre nunca
tiene tienes tienen tenemos tengo hay habia queda quedan quedo sirve
sirven funciona puede puedo puedes quiero quiere quieren necesito
necesita ocupo ocupa busco busca vendo vende venden vendi vendimos
compro compra cobro cobra precio precios cuesta cuestan vale valen
dame dime pasame muestrame ensename mandame dimelo dejame
este esta estos estas ese esa esos esas aquel aquella otro otra otros
otras mismo misma algun alguna alguno algunos algunas ninguno ninguna
nada todo todos todas mucho mucha muchos muchas poco poca pocos pocas
mas menos muy bien mal mejor peor barato barata baratos baratas caro
cara caros caras nuevo nueva cliente clientes senor senora joven
gracias favor hola buenas buenos dias tardes noches oye mira
primero primera segundo segunda tercero tercera ultimo ultima
lista listado producto productos pieza piezas unidad unidades
existencia existencias inventario codigo nombre marca marcas
categoria categorias modelo modelos carro carros coche auto vehiculo
camioneta total subtotal descuento rebaja iva pesos peso numero
acepte acepto aceptar siento sienta sentir cambio cambia cambiar
llanta llantas manda mande mando paso pase pasa pasar sale salen
salio quedo deja dejas dejo cada entonces seria serian sumalo suma
tuvo hubo estuvo anduvo puso hizo vino dijo trajo traje fue fui iba
piensa pienso pensar creo cree crees parece parecia sabes sabe saber
cierra cierro abre abro cambie cambio cambiaron haga hago hice hace
haces puse saque saca llevo lleva llevan llevar traigo trae traer
compre compro vaya voy vamos venga viene vienen veo vio ver mire
revise reviso revisar pregunta preguntas respuesta problema falla
fallas ruido ruidos motor turbo turbina tubo tubos vela velas base
bases vaso vasos cabe cave valla vaya balla callo cayo casa caza
vez veces bello vello grave grabe tasa taza cesta sesta siento ciento
cien sien hola ola echo hecho hecha echa asta hasta abia habia
""".split())


def _vocabulario_objetivo(productos: list[dict]) -> dict[str, str]:
    # Palabras a las que SÍ se corrige: nombres, marcas y categorías del
    # inventario, modelos de auto registrados y términos de mecánica.
    from AgenteIA.mecanica.documentacion_automotriz import DOCUMENTACION_AUTOMOTRIZ

    objetivos: set[str] = set()

    for producto in productos or []:
        for campo in ("nombre", "marca", "categoria"):
            objetivos.update(_palabras(producto.get(campo, "")))
        compatibles = producto.get("vehiculosCompatibles") or []
        if isinstance(compatibles, list):
            for vehiculo in compatibles:
                objetivos.update(_palabras(str(vehiculo)))

    for datos in DOCUMENTACION_AUTOMOTRIZ.values():
        for frase in datos.get("palabras_clave", []):
            objetivos.update(_palabras(frase))

    objetivos.update((
        "balata", "amortiguador", "bujia", "bateria", "alternador",
        "radiador", "termostato", "filtro", "aceite", "anticongelante",
        "refrigerante", "embrague", "clutch", "transmision", "suspension",
        "direccion", "banda", "correa", "manguera", "bomba", "sensor",
        "bobina", "inyector", "marcha", "disco", "tambor", "zapata",
        "rotula", "terminal", "horquilla", "buje", "silenciador", "mofle",
        "catalizador", "escape", "faro", "foco", "calavera", "llanta",
        "neumatico", "rin", "fusible", "relevador", "cable", "junta",
        "empaque", "valvula", "piston", "ciguenal", "cremallera",
        "compresor", "condensador", "evaporador", "ventilador",
        "sobrecalienta", "sobrecalentamiento", "rechina", "vibra",
        "tiembla", "jalonea", "cascabelea", "frenar", "frenos",
        "compatible", "compatibles", "universal", "universales",
    ))

    vocabulario = {}
    for palabra in objetivos:
        if len(palabra) < 4 or palabra.isdigit():
            continue
        for forma in _plurales(palabra):
            vocabulario[forma] = forma
    return vocabulario


def _conocidas() -> set[str]:
    # Palabras correctas que NO se tocan: todo el texto de la documentación
    # y las respuestas de mecánica (miles de palabras en español) + comunes.
    global _CONOCIDAS_CACHE
    if _CONOCIDAS_CACHE is None:
        from AgenteIA.mecanica.conocimientos_mecanicos import CONOCIMIENTOS_MECANICOS
        from AgenteIA.mecanica.documentacion_automotriz import DOCUMENTACION_AUTOMOTRIZ

        textos = list(CONOCIMIENTOS_MECANICOS.values())
        for datos in DOCUMENTACION_AUTOMOTRIZ.values():
            textos.append(datos.get("contenido", ""))
            textos.extend(datos.get("expresiones", []))
        conocidas = set(_COMUNES)
        for texto in textos:
            conocidas.update(_palabras(texto))
        # Las formas estándar de las tablas también son correctas.
        for tabla in TABLAS:
            for _, estandar in tabla:
                conocidas.update(_palabras(estandar))
        _CONOCIDAS_CACHE = conocidas
    return _CONOCIDAS_CACHE


_CONOCIDAS_CACHE: set[str] | None = None


def _mejor_correccion(palabra: str, vocabulario: dict[str, str]) -> str | None:
    if len(palabra) < 4 or palabra in vocabulario or palabra in _conocidas():
        return None

    clave = _clave_fonetica(palabra)

    # a) Suena igual: "valatas" = "balatas", "vujias" = "bujias".
    mismas = [v for v in vocabulario if _clave_fonetica(v) == clave]
    if len(mismas) == 1:
        return mismas[0]
    if len(mismas) > 1:
        return None

    # b) Una letra de más, de menos o dos letras volteadas:
    #    "acete", "fltro", "termostatoo", "filtor", "bateira".
    #    Cambiar una letra por OTRA no cuenta como error de dedo en
    #    palabras cortas, porque casi siempre forma otra palabra real
    #    ("borra"/"barra", "reporte"/"resorte", "corta"/"correa").
    #    Solo las palabras muy largas aceptan un cambio: "anticongelamte".
    if len(palabra) < 5:
        return None
    limite = 1 if len(palabra) < 9 else 2
    candidatos = []
    for v in vocabulario:
        if abs(len(v) - len(palabra)) > limite:
            continue
        clave_v = _clave_fonetica(v)
        if clave_v[0] != clave[0]:
            continue
        distancia = _distancia(clave, clave_v)
        if distancia <= limite:
            candidatos.append((distancia, -SequenceMatcher(None, palabra, v).ratio(), v))
    if not candidatos:
        return None
    candidatos.sort()
    mejor = candidatos[0][2]
    # Si dos palabras DISTINTAS quedan igual de cerca, no se adivina.
    # Singular y plural de la misma ("radiador"/"radiadores") no cuentan
    # como empate.
    for distancia, _, otra in candidatos[1:]:
        if distancia > candidatos[0][0]:
            break
        if otra.startswith(mejor) or mejor.startswith(otra):
            continue
        return None
    return mejor


def _distancia(a: str, b: str) -> int:
    # Distancia de edición: quitar, poner o voltear una letra cuesta 1;
    # cambiar una letra por otra cuesta 2 ("filtor" -> "filtro" = 1,
    # "borra" -> "barra" = 2).
    filas = [list(range(len(b) + 1))]
    for i in range(1, len(a) + 1):
        fila = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            costo = 0 if a[i - 1] == b[j - 1] else 2
            fila[j] = min(filas[i - 1][j] + 1, fila[j - 1] + 1, filas[i - 1][j - 1] + costo)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                fila[j] = min(fila[j], filas[i - 2][j - 2] + 1)
        filas.append(fila)
    return filas[-1][-1]


def corregir_ortografia(texto: str, productos: list[dict]) -> str:
    """Corrige errores de dedo en palabras de refacciones y mecánica."""
    if not texto:
        return texto

    vocabulario = _vocabulario_objetivo(productos)
    cambios = {}

    for palabra in set(_palabras(texto)):
        correccion = _mejor_correccion(palabra, vocabulario)
        if correccion and correccion != palabra:
            cambios[palabra] = correccion

    if not cambios:
        return texto

    def reemplazar(m: re.Match) -> str:
        original = m.group(0)
        clave = _sin_acentos(original).casefold()
        return cambios.get(clave, original)

    # Se reemplaza palabra por palabra; códigos como "BAL-001" no se tocan
    # porque llevan números.
    return re.sub(r"(?<![\w-])[^\W\d_]+(?![\w-])", reemplazar, texto)


# =====================================================================
# 3. REGISTRO DE PREGUNTAS NO ENTENDIDAS
# =====================================================================

CARPETA_REGISTRO = Path(__file__).resolve().parents[1] / "registro"
ARCHIVO_NO_ENTENDIDAS = CARPETA_REGISTRO / "preguntas_no_entendidas.txt"


def registrar_no_entendida(pregunta: str, motivo: str, reescrita: str | None = None) -> None:
    """Agrega una línea al registro. Nunca interrumpe la consulta."""
    # Las pruebas automáticas no escriben en el registro real.
    if os.environ.get("PISTON_SIN_REGISTRO"):
        return
    try:
        CARPETA_REGISTRO.mkdir(parents=True, exist_ok=True)
        linea = (
            f"{datetime.now():%Y-%m-%d %H:%M}\t{motivo}\t"
            f"{' '.join(str(pregunta).split())}"
            + (f"\t-> {reescrita}" if reescrita else "")
            + "\n"
        )
        with open(ARCHIVO_NO_ENTENDIDAS, "a", encoding="utf-8") as archivo:
            archivo.write(linea)
    except OSError:
        pass


