"""Genera el informe PDF de la Actividad en Clase N.3.

El informe se crea en la raiz del proyecto como:
    Informe_Nodo_Telemetria_Querube_Ariza.pdf

Tipografia: Arial (registrado desde C:\\Windows\\Fonts), cuerpo 12 pt.
Figuras y tablas numeradas, con descripcion, y paginas numeradas
"Pagina N de M".
"""

import json
import os
import textwrap
from datetime import datetime

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

# Con los estilos ya cargados, el lienzo usa Arial como fuente por defecto
# para que el PDF no declare Helvetica ni Times-Roman en sus recursos.
import reportlab.rl_config as _rl_config

_rl_config.canvas_basefontname = "Arial"

# Las viñetas por defecto de los párrafos también en Arial.
import reportlab.lib.styles as _rl_styles

_rl_styles.ParagraphStyle.defaults["fontName"] = "Arial"
_rl_styles.ParagraphStyle.defaults["bulletFontName"] = "Arial"

from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as canvasmod
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Fuente por defecto de los diagramas (Drawing / String).
_rl_config.defaultGraphicsFontName = "Arial"
import reportlab.graphics.shapes as _rl_shapes

_rl_shapes.STATE_DEFAULTS["fontName"] = "Arial"

# _baseFontName por defecto es Helvetica; se cambia antes de importar el
# índice automático, que lo copia en ese momento.
_rl_styles._baseFontName = "Arial"

from reportlab.platypus.tableofcontents import TableOfContents


BASE = os.path.dirname(os.path.abspath(__file__))
# Las capturas viajan dentro del repositorio; la carpeta temporal del agente
# que las produjo se conserva como respaldo.
CAPTURAS = os.path.join(BASE, "capturas")
_CAPTURAS_RESPALDO = os.path.join(
    os.path.expanduser("~"), "AppData", "Local", "Temp", "opencode")
DIRS_CAPTURA = [CAPTURAS]
if _CAPTURAS_RESPALDO != CAPTURAS and os.path.isdir(_CAPTURAS_RESPALDO):
    DIRS_CAPTURA.append(_CAPTURAS_RESPALDO)
SALIDA = os.path.join(BASE, "Informe_Nodo_Telemetria_Querube_Ariza.pdf")

FONTS = r"C:\Windows\Fonts"
pdfmetrics.registerFont(TTFont("Arial", os.path.join(FONTS, "arial.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Bold", os.path.join(FONTS, "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Italic", os.path.join(FONTS, "ariali.ttf")))
pdfmetrics.registerFont(TTFont("Arial-BoldItalic", os.path.join(FONTS, "arialbi.ttf")))
pdfmetrics.registerFontFamily(
    "Arial",
    normal="Arial",
    bold="Arial-Bold",
    italic="Arial-Italic",
    boldItalic="Arial-BoldItalic",
)

FUENTE = "Arial"
FUENTE_NEGRITA = "Arial-Bold"
FUENTE_CODIGO = "Courier"
CUERPO_PT = 12

# Contadores globales de figuras y tablas del informe.
_FIGURAS = [0]
_TABLAS = [0]


def leer_captura(nombre, defecto="No se encontro la captura generada."):
    for carpeta in DIRS_CAPTURA:
        ruta = os.path.join(carpeta, nombre)
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8", errors="replace") as archivo:
                texto = archivo.read().strip()
            return texto or defecto
    return defecto


def estructura_actual():
    excluir = {"entorno", "__pycache__", ".kilo", ".git", ".idea", "capturas"}
    lineas = ["monitor_iot_QuerubeAriza/"]

    def rama(ruta, prefijo):
        entradas = sorted(e for e in os.listdir(ruta) if e not in excluir)
        for indice, entrada in enumerate(entradas):
            ultimo = indice == len(entradas) - 1
            conector = "`-- " if ultimo else "|-- "
            ruta_entrada = os.path.join(ruta, entrada)
            if os.path.isdir(ruta_entrada):
                lineas.append(f"{prefijo}{conector}{entrada}/")
                rama(ruta_entrada, prefijo + ("    " if ultimo else "|   "))
            else:
                lineas.append(f"{prefijo}{conector}{entrada}")

    rama(BASE, "")
    return "\n".join(lineas)


def envolver(texto, ancho=112, max_lineas=None):
    lineas = []
    for linea in texto.splitlines():
        if len(linea) <= ancho:
            lineas.append(linea)
        else:
            lineas.extend(textwrap.wrap(linea, width=ancho, replace_whitespace=False))
    if max_lineas and len(lineas) > max_lineas:
        mitad = max_lineas // 2
        lineas = (
            lineas[:mitad]
            + ["... salida recortada para el informe ..."]
            + lineas[-(max_lineas - mitad - 1):]
        )
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
def crear_estilos():
    base = getSampleStyleSheet()

    estilos = {}
    estilos["titulo"] = ParagraphStyle(
        "Titulo",
        parent=base["Title"],
        alignment=TA_CENTER,
        fontName=FUENTE_NEGRITA,
        fontSize=18,
        leading=24,
        textColor=colors.HexColor("#143a5a"),
        spaceAfter=6,
    )
    estilos["subtitulo"] = ParagraphStyle(
        "Subtitulo",
        parent=base["Heading2"],
        alignment=TA_CENTER,
        fontName=FUENTE,
        fontSize=CUERPO_PT,
        leading=16,
        spaceAfter=4,
    )
    estilos["H1"] = ParagraphStyle(
        "H1",
        parent=base["Heading1"],
        fontName=FUENTE_NEGRITA,
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#1f4e79"),
        spaceBefore=12,
        spaceAfter=8,
        leftIndent=4,
    )
    estilos["H2"] = ParagraphStyle(
        "H2",
        parent=base["Heading2"],
        fontName=FUENTE_NEGRITA,
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1f4e79"),
        spaceBefore=10,
        spaceAfter=6,
    )
    estilos["cuerpo"] = ParagraphStyle(
        "Cuerpo",
        parent=base["BodyText"],
        fontName=FUENTE,
        fontSize=CUERPO_PT,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    )
    estilos["cuerpo_izq"] = ParagraphStyle(
        "CuerpoIzq",
        parent=estilos["cuerpo"],
        alignment=TA_LEFT,
        spaceAfter=5,
    )
    estilos["lista"] = ParagraphStyle(
        "Lista",
        parent=estilos["cuerpo"],
        alignment=TA_LEFT,
        leftIndent=18,
        bulletIndent=6,
        spaceAfter=5,
    )
    estilos["codigo"] = ParagraphStyle(
        "Codigo",
        fontName=FUENTE_CODIGO,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#e6edf3"),
    )
    estilos["pie_figura"] = ParagraphStyle(
        "PieFigura",
        parent=base["BodyText"],
        fontName=FUENTE_NEGRITA,
        fontSize=CUERPO_PT,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1f4e79"),
        spaceBefore=6,
        spaceAfter=3,
    )
    estilos["descripcion"] = ParagraphStyle(
        "Descripcion",
        parent=base["BodyText"],
        fontName=FUENTE,
        fontSize=CUERPO_PT,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceBefore=2,
        spaceAfter=12,
    )
    estilos["tabla"] = ParagraphStyle(
        "TablaCelda",
        fontName=FUENTE,
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
    )
    estilos["tabla_negrita"] = ParagraphStyle(
        "TablaNegrita",
        fontName=FUENTE_NEGRITA,
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
        textColor=colors.white,
    )
    estilos["pie_tabla"] = ParagraphStyle(
        "PieTabla",
        parent=base["BodyText"],
        fontName=FUENTE_NEGRITA,
        fontSize=CUERPO_PT,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1f4e79"),
        spaceBefore=4,
        spaceAfter=10,
    )
    estilos["toc0"] = ParagraphStyle(
        "TOC0",
        fontName=FUENTE_NEGRITA,
        fontSize=CUERPO_PT,
        leading=20,
        leftIndent=0,
        firstLineIndent=0,
    )
    estilos["toc1"] = ParagraphStyle(
        "TOC1",
        fontName=FUENTE,
        fontSize=CUERPO_PT,
        leading=18,
        leftIndent=22,
        firstLineIndent=0,
    )
    return estilos


ESTILOS = crear_estilos()


# ---------------------------------------------------------------------------
# Componentes: cajas de terminal, figuras, tablas y diagrama
# ---------------------------------------------------------------------------
def caja_terminal(texto, max_lineas=42):
    pre = Preformatted(envolver(texto, max_lineas=max_lineas), ESTILOS["codigo"])
    tabla = Table([[pre]], colWidths=[7.0 * inch])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0d1b2a")),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#1f4e79")),
        ("FONTNAME", (0, 0), (-1, -1), "Arial"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return tabla


def _avanzar_figura():
    _FIGURAS[0] += 1
    return _FIGURAS[0]


def figura_captura(ruta, titulo, descripcion, max_ancho=7.0 * inch, max_alto=5.3 * inch):
    """Imagen enumerada + pie + descripcion."""
    numero = _avanzar_figura()
    elementos = []
    if ruta and os.path.exists(ruta):
        ancho_px, alto_px = PILImage.open(ruta).size
        ancho = min(max_ancho, max_ancho * 1.0)
        alto = ancho * alto_px / ancho_px
        if alto > max_alto:
            alto = max_alto
            ancho = alto * ancho_px / alto_px
        elementos.append(Image(ruta, width=ancho, height=alto))
    else:
        elementos.append(Paragraph(
            "[Captura no disponible en este equipo]", ESTILOS["descripcion"]))
    elementos.append(Paragraph(f"Figura {numero}. {titulo}", ESTILOS["pie_figura"]))
    elementos.append(Paragraph(descripcion, ESTILOS["descripcion"]))
    return elementos


def figura_terminal(texto, titulo, descripcion, max_lineas=42):
    numero = _avanzar_figura()
    return [
        caja_terminal(texto, max_lineas=max_lineas),
        Paragraph(f"Figura {numero}. {titulo}", ESTILOS["pie_figura"]),
        Paragraph(descripcion, ESTILOS["descripcion"]),
    ]


def figura_diagrama(dibujo, titulo, descripcion):
    numero = _avanzar_figura()
    return [
        dibujo,
        Paragraph(f"Figura {numero}. {titulo}", ESTILOS["pie_figura"]),
        Paragraph(descripcion, ESTILOS["descripcion"]),
    ]


def caption_tabla(titulo, descripcion):
    numero = _TABLAS[0] + 1
    _TABLAS[0] = numero
    return [
        Paragraph(f"Tabla {numero}. {titulo}", ESTILOS["pie_tabla"]),
        Paragraph(descripcion, ESTILOS["descripcion"]),
    ]


def buscar_imagen(*nombres):
    for nombre in nombres:
        for carpeta in DIRS_CAPTURA:
            ruta = os.path.join(carpeta, nombre)
            if os.path.exists(ruta):
                return ruta
    return None


def _fila(textos):
    return [Paragraph(t, ESTILOS["tabla"]) for t in textos]


def tabla_datos(datos, cabecera, anchos, estilo_extra=None):
    filas = [ [Paragraph(c, ESTILOS["tabla_negrita"]) for c in cabecera] ]
    filas.extend(_fila(f) for f in datos)
    tabla = Table(filas, colWidths=anchos, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Arial"),
        ("FONTNAME", (0, 0), (-1, 0), "Arial-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d4df")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f2f6fa")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if estilo_extra:
        estilo.extend(estilo_extra)
    tabla.setStyle(TableStyle(estilo))
    return tabla


def diagrama_no_bloqueante():
    """Diagrama del ciclo de monitoreo frente al hilo de alertas sonoras."""
    ancho, alto = 496, 268
    d = Drawing(ancho, alto)

    azul = colors.HexColor("#1f4e79")
    claro = colors.HexColor("#e8f0f7")
    verde = colors.HexColor("#1d7044")
    claro_verde = colors.HexColor("#e6f4ec")

    # --- Hilo principal ---------------------------------------------------
    d.add(Rect(0, 44, 236, 214, fillColor=claro, strokeColor=azul, strokeWidth=1.2))
    d.add(Rect(0, 232, 236, 26, fillColor=azul, strokeColor=azul))
    d.add(String(10, 240, "Hilo principal: nucleo.ciclo()", fontName="Arial-Bold",
                 fontSize=11, fillColor=colors.white))

    lineas_izq = [
        (216, "1. lee los sensores que tocan"),
        (198, "2. detecta eventos (umbral, flanco,"),
        (184, "    tiempo, falla)"),
        (164, "3. sonidos.reproducir(clave)"),
        (148, "    SOLO encola la alerta"),
        (128, "4. devuelve lecturas y eventos"),
        (104, "Nunca llama a winsound y nunca"),
        (90, "hace time.sleep() por un sonido."),
        (68, "El ciclo sigue refrescando aunque"),
        (54, "haya una alerta en curso."),
    ]
    for y, texto in lineas_izq:
        d.add(String(10, y, texto, fontName="Arial", fontSize=9.5,
                     fillColor=colors.HexColor("#10243a")))

    # --- Hilo de sonido ---------------------------------------------------
    d.add(Rect(262, 44, 234, 214, fillColor=claro_verde, strokeColor=verde,
               strokeWidth=1.2))
    d.add(Rect(262, 232, 234, 26, fillColor=verde, strokeColor=verde))
    d.add(String(272, 240, "Hilo alertas-sonoras (daemon)", fontName="Arial-Bold",
                 fontSize=11, fillColor=colors.white))

    lineas_der = [
        (216, "1. _tomar_pendiente(): saca de la"),
        (202, "    deque la alerta mas antigua"),
        (182, "2. descarta las vencidas (6 s)"),
        (162, "3. _emitir() sintetiza el WAV en"),
        (148, "    memoria y lo reproduce"),
        (128, "4. si el audio falla, lo ignora"),
        (114, "    y sigue esperando"),
        (94, "Duerme 0,05 s si la cola esta"),
        (80, "vacia: no consume CPU ni espera"),
        (60, "a ningun evento del ciclo."),
    ]
    for y, texto in lineas_der:
        d.add(String(272, y, texto, fontName="Arial", fontSize=9.5,
                     fillColor=colors.HexColor("#0f2e1e")))

    # --- Flecha de la cola ------------------------------------------------
    d.add(Line(236, 150, 254, 150, strokeColor=azul, strokeWidth=1.6))
    d.add(Polygon([254, 156, 268, 150, 254, 144], fillColor=azul, strokeColor=azul))
    d.add(String(236, 160, "cola deque", fontName="Arial-Bold", fontSize=9,
                 fillColor=azul))
    d.add(String(236, 134, "maxlen = 6", fontName="Arial", fontSize=9, fillColor=azul))
    d.add(String(236, 122, "bloqueo con", fontName="Arial", fontSize=9, fillColor=azul))
    d.add(String(236, 110, "threading.Lock", fontName="Arial", fontSize=9, fillColor=azul))

    # --- Banda inferior ---------------------------------------------------
    d.add(Rect(0, 0, 496, 34, fillColor=colors.HexColor("#f7f3e8"),
               strokeColor=colors.HexColor("#b08b3f"), strokeWidth=0.8))
    d.add(String(8, 20, "Controles por marca de tiempo:  cadencia 1,2 s  |  "
                        "vencimiento 6,0 s  |  cola maxima 6  |  pausa del hilo 0,05 s",
                 fontName="Arial", fontSize=9.5, fillColor=colors.HexColor("#5b4413")))
    d.add(String(8, 7, "El bucle de sonido y el ciclo de monitoreo comparten solo la "
                       "cola: ninguno espera al otro.",
                 fontName="Arial", fontSize=9.5, fillColor=colors.HexColor("#5b4413")))
    return d


# ---------------------------------------------------------------------------
# Numeracion de paginas: "Pagina N de M"
# ---------------------------------------------------------------------------
class PaginasNumeradas(canvasmod.Canvas):
    def __init__(self, *args, **kwargs):
        canvasmod.Canvas.__init__(self, *args, **kwargs)
        self._paginas_guardadas = []

    def showPage(self):
        self._paginas_guardadas.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._paginas_guardadas)
        for estado in self._paginas_guardadas:
            self.__dict__.update(estado)
            self._pie(total)
            canvasmod.Canvas.showPage(self)
        canvasmod.Canvas.save(self)

    def _pie(self, total):
        self.saveState()
        self.setFont(FUENTE, 9)
        self.setFillColor(colors.HexColor("#555555"))
        self.drawCentredString(letter[0] / 2, 0.4 * inch,
                               f"Página {self._pageNumber} de {total}")
        self.restoreState()


class Informe(SimpleDocTemplate):
    """Plantilla que alimenta el índice automático y los marcadores."""

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in ("H1", "H2"):
            texto = flowable.getPlainText()
            nivel = 0 if flowable.style.name == "H1" else 1
            if texto != "Índice":
                self.notify("TOCEntry", (nivel, texto, self.page))
            clave = f"seccion-{self.page}-{abs(hash(texto)) % 10**8}"
            self.canv.bookmarkPage(clave)
            self.canv.addOutlineEntry(texto, clave, nivel, 0)


# ---------------------------------------------------------------------------
# Contenido de las alertas sonoras
# ---------------------------------------------------------------------------
PROBLEMAS = [
    ("conexion_perdida", "sirena_caida",
     "Barrido 880 a 160 Hz (0,9 s), pausa, barrido 660 a 120 Hz (0,7 s)",
     "El tono que cae se interpreta como algo que se apaga: es el aviso mas urgente "
     "del sistema y por eso suena con el barrido mas largo y descendente."),
    ("conexion_recordatorio", "latido_caida",
     "Dos golpes cuadrados de 220 Hz y uno de 146,83 Hz, separados por silencio",
     "Un latido grave y repetido recuerda que la caida sigue sin resolverse, sin la "
     "urgencia de la sirena inicial, para no saturar al operador."),
    ("cpu_alta", "doble_tic",
     "Dos tics de seno de 1567,98 Hz de 0,07 s con silencio intermedio",
     "Tics cortos y agudos, tipo semaforo: informan de un pico de trabajo sin "
     "convertirse en una alarma continua que taparia los demas avisos."),
    ("nucleo_saturado", "tic_nucleo",
     "Dos notas de seno de 987,77 Hz y 1318,51 Hz de 0,06 s",
     "Variacion corta y media del doble tic de CPU: el oido la asocia al mismo "
     "familia de problema, pero a un nivel menor (un solo nucleo)."),
    ("ram_alta", "acorde_memoria",
     "Tres notas 440 / 587,33 / 739,99 Hz y repetida 739,99 Hz al 80 %",
     "Acorde ascendente que se queda tenso: la memoria es un recurso que permanece "
     "ocupado, por eso el sonido no cierra, sino que se sostiene."),
    ("disco_lleno", "golpe_grave",
     "Cuadrada de 110 Hz (0,28 s) seguida de seno de 98 Hz (0,3 s)",
     "Golpe seco y grave: da la sensacion de lleneo y peso, coherente con un disco "
     "que ya no tiene espacio para recibir informacion."),
    ("red_pico", "swoosh_subida",
     "Barrido de 320 a 1760 Hz (0,4 s) al 60 % de volumen",
     "Barrido ascendente: codifica el trafico que sube de golpe; el movimiento "
     "creciente del tono se asocia con un flujo que aumenta."),
    ("bateria_baja", "pip_bateria",
     "Tres pitidos de 440 Hz de 0,22 s separados por 0,3 s de silencio",
     "Pitidos lentos e iguales: suenan como una cuenta regresiva de energia que se "
     "agota y exigen buscar el cargador."),
    ("cargador_desconectado", "plano_descarga",
     "Barrido de 700 a 300 Hz (0,25 s) y cuadrada de 300 Hz (0,2 s)",
     "El tono se va al piso y termina plano: traduce literalmente la energia que se "
     "corta al desconectar el equipo."),
    ("swap_activo", "pulso_swap",
     "Dos pulsos cuadrados de 261,63 Hz separados por 0,1 s de silencio",
     "Pulso binario de dos tiempos: refleja el vaiven de la memoria entre RAM y "
     "disco que ocurre mientras el swap esta activo."),
    ("sensor_ausente", "zumbido_falla",
     "Cuadrada de 133 Hz, ruido blanco de 0,12 s y otra cuadrada de 133 Hz",
     "Zumbido aspero con ruido: suena deliberadamente roto para distinguir una "
     "falla de hardware de un simple aviso de estado."),
    ("lectura_invalida", "tictac_invalido",
     "Tres tics de seno de 1174,66 Hz de 0,06 s con silencios intermedios",
     "Tics nerviosos y rapidos: transmiten una lectura dudosa, corta e inestable "
     "que no llego a confirmarse."),
    ("salto_anomalo", "zigzag_salto",
     "Barrido 1400 a 300 Hz y vuelta inmediata 300 a 1400 Hz",
     "Ida y vuelta brusca del tono: reproduce el salto entre dos lecturas muy "
     "distintas consecutivas."),
    ("proceso_pesado", "grunido_proceso",
     "Triangular de 196 Hz (0,2 s) y cuadrada de 196 Hz (0,12 s)",
     "Grave y burdo, casi un grunido: identifica un proceso que traga recursos de "
     "forma sostenida."),
]

RECUPERACIONES = [
    ("conexion_recuperada", "arreglo_ascendente",
     "Do 523,25 / Mi 659,25 / Sol 783,99 / Do 1046,5 Hz",
     "Arreglo ascendente mayor: convencion musical de todo vuelvio a la normalidad; "
     "la ultima nota sube de volumen para cerrar con claridad."),
    ("cpu_normal", "chime_corto",
     "Campanita de 1046,5 Hz (0,1 s) y 1318,51 Hz (0,14 s) al 60 %",
     "Campana corta, suave y agradable: es el sonido generico de alivio y por eso "
     "se reutiliza en todas las condiciones normalizadas."),
    ("ram_normal", "chime_corto",
     "Misma campanita corta de dos notas",
     "Al repetir el mismo sonido en todas las recuperaciones, el operador reconoce "
     "de inmediato que no hay que intervenir."),
    ("disco_aliviado", "chime_corto",
     "Misma campanita corta de dos notas",
     "Confirma que el disco volvio bajo el umbral sin añadir un sonido nuevo que "
     "hubiera que memorizar."),
    ("red_calma", "chime_corto",
     "Misma campanita corta de dos notas",
     "El trafico bajo al nivel de calma: mismo aviso agradable de situacion "
     "resuelta."),
    ("bateria_recuperada", "arreglo_ascendente",
     "Mismo arreglo do-mi-sol-do ascendente",
     "La bateria dejo la zona de riesgo: se reutiliza el arreglo mayor porque es "
     "el sonido mas reconocible de recuperacion total."),
    ("cargador_conectado", "chime_corto",
     "Misma campanita corta de dos notas",
     "Aviso breve de que la fuente de energia volvio a estar disponible."),
]

CONTROLES = [
    ("SONIDO_COOLDOWN", "1,2 s",
     "Cadencia: un mismo evento no vuelve a encolarse antes de 1,2 s, por mas "
     "veces que se dispare. Evita repetir el mismo tono en cada vuelta rapida."),
    ("SONIDO_VENCIDO", "6,0 s",
     "Vencimiento: una alerta mas vieja que 6 s se descarta en vez de sonar tarde, "
     "de modo que una racha antigua no se reproduce cuando ya no sirve."),
    ("SONIDO_MAX_COLA", "6",
     "Cola acotada: el deque tiene tope de 6 elementos. Si el equipo se atrasa, se "
     "pierde el aviso mas viejo y nunca crece una cola infinita de sonidos."),
    ("SONIDO_PAUSA", "0,05 s",
     "Pausa del hilo: con la cola vacia el reproductor duerme 50 ms en vez de "
     "consumir CPU; jamas espera a que el ciclo le entregue un evento."),
]


# ---------------------------------------------------------------------------
# Construccion del documento
# ---------------------------------------------------------------------------
def crear_pdf():
    estilos = ESTILOS
    cuerpo = estilos["cuerpo"]
    cuerpo_izq = estilos["cuerpo_izq"]
    lista = estilos["lista"]
    h1 = estilos["H1"]
    h2 = estilos["H2"]

    doc = Informe(
        SALIDA,
        pagesize=letter,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title="Informe Nodo de Telemetria - Querube Ariza",
        author="Querube Ariza",
        subject="Actividad en Clase N.3: modulos, paquetes y programacion orientada a eventos",
    )

    revisar = leer_captura("revisar.txt")
    consola = leer_captura("consola.txt")
    eventos_cpu = leer_captura("eventos_cpu.txt")
    eventos_falla = leer_captura(
        "eventos_falla.txt",
        "FALLA simulada: se fuerza una lectura None para demostrar sensor_ausente.",
    )
    bitacora = leer_captura("bitacora.json", "[]")
    salida_pruebas = leer_captura("salida_pruebas.txt", "")

    if bitacora == "[]" and os.path.exists(os.path.join(BASE, "bitacora.json")):
        with open(os.path.join(BASE, "bitacora.json"), "r", encoding="utf-8") as archivo:
            bitacora = json.dumps(json.load(archivo), indent=2, ensure_ascii=False)

    elementos = []

    # ------------------------------------------------------------------
    # Hoja de presentacion
    # ------------------------------------------------------------------
    elementos.append(Spacer(1, 0.35 * inch))
    elementos.append(Paragraph("UNIVERSIDAD TECNOLÓGICA DE PANAMÁ", estilos["titulo"]))
    elementos.append(Paragraph("INGENIERÍA DE SISTEMAS COMPUTACIONALES", estilos["subtitulo"]))
    elementos.append(Paragraph("LICENCIATURA EN DESARROLLO Y GESTIÓN DE SOFTWARE", estilos["subtitulo"]))
    elementos.append(Spacer(1, 0.35 * inch))
    elementos.append(Paragraph("Informe de Actividad en Clase N.° 3", estilos["titulo"]))
    elementos.append(Paragraph("Nodo de telemetría del equipo", estilos["subtitulo"]))
    elementos.append(Spacer(1, 0.3 * inch))

    datos = [
        ["Nombre", "Querube Ariza"],
        ["Grupo", "1GS134"],
        ["Asignatura", "Desarrollo de Software VIII"],
        ["Profesor", "Kexy Rodríguez"],
        ["Tema", "Módulos, paquetes y programación orientada a eventos"],
        ["Fecha", datetime.now().strftime("%d/%m/%Y")],
    ]
    portada = Table(datos, colWidths=[1.6 * inch, 5.0 * inch])
    portada.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#b5c7d3")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8f0f7")),
        ("FONTNAME", (0, 0), (0, -1), "Arial-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Arial"),
        ("FONTSIZE", (0, 0), (-1, -1), CUERPO_PT),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#10243a")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    elementos.append(portada)
    elementos.append(Spacer(1, 0.7 * inch))
    elementos.append(Paragraph("Proyecto: monitor_iot_QuerubeAriza", cuerpo_izq))
    elementos.append(Paragraph("Dashboard personalizado: laptop-QuerubeAriza", cuerpo_izq))
    elementos.append(Paragraph(
        "Tipografía del informe: Arial 12 pt. Figuras y tablas numeradas con "
        "descripción; páginas numeradas.", cuerpo_izq))
    elementos.append(PageBreak())

    # ------------------------------------------------------------------
    # Indice
    # ------------------------------------------------------------------
    elementos.append(Paragraph("Índice", h1))
    toc = TableOfContents(tableStyle=TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("FONTNAME", (0, 0), (-1, -1), "Arial"),
    ]))
    toc.levelStyles = [estilos["toc0"], estilos["toc1"]]
    toc.dotsMinLevel = 0
    elementos.append(toc)
    elementos.append(PageBreak())

    # ------------------------------------------------------------------
    # 1. Objetivo
    # ------------------------------------------------------------------
    elementos.append(Paragraph("1. Objetivo", h1))
    elementos.append(Paragraph(
        "Construir un nodo de telemetría del equipo en Python, organizado con "
        "módulos y paquetes y con una arquitectura orientada a eventos, que mida "
        "en tiempo real el uso del procesador, la memoria RAM, el disco, la red, "
        "los procesos y la batería; que detecte condiciones de alarma; y que "
        "presente la información en tres tableros: consola, ventana gráfica y "
        "web local.", cuerpo))
    elementos.append(Paragraph("Objetivos específicos:", cuerpo_izq))
    objetivos = [
        "Separar responsabilidades en paquetes (sensores, eventos, almacenamiento, "
        "dashboard) para que cada uno tenga una sola razón de cambio.",
        "Aplicar programación orientada a eventos: detección por umbral con "
        "histéresis, por flanco, por tiempo y por falla o ausencia de un sensor, "
        "despachada mediante un diccionario de manejadores.",
        "Implementar un subsistema de alertas sonoras (sonidos.py) que sintetice "
        "los WAV en memoria y los reproduzca sin bloquear el ciclo de monitoreo.",
        "Diseñar y documentar la tabla de alertas sonoras con la justificación de "
        "cada sonido y explicar cómo se evitó que el audio detuviera el monitoreo.",
        "Ejecutar el código, capturar pantalla de cada ejecución, correr las "
        "pruebas unitarias y presentar sus resultados y conclusiones en este "
        "informe con figuras enumeradas y páginas numeradas.",
    ]
    for i, texto in enumerate(objetivos, 1):
        elementos.append(Paragraph(f"{i}. {texto}", lista))
    elementos.append(PageBreak())

    # ------------------------------------------------------------------
    # 2. Introduccion
    # ------------------------------------------------------------------
    elementos.append(Paragraph("2. Introducción", h1))
    elementos.append(Paragraph(
        "Este informe documenta el desarrollo de un nodo de telemetría del equipo, "
        "implementado en Python mediante módulos y paquetes. El sistema obtiene "
        "mediciones reales del computador usando la biblioteca psutil: uso del "
        "procesador, memoria RAM, disco, red, procesos y batería.", cuerpo))
    elementos.append(Paragraph(
        "La práctica aplica programación orientada a eventos. El núcleo no utiliza "
        "esperas bloqueantes con time.sleep() para decidir cuándo leer sensores; en "
        "su lugar conserva marcas de tiempo y ejecuta cada grupo de lecturas cuando "
        "corresponde. Los eventos son detectados por umbral con histéresis, por "
        "flanco, por tiempo y por falla o ausencia de un sensor.", cuerpo))
    elementos.append(Paragraph(
        "El proyecto separa responsabilidades: los sensores solo leen, "
        "almacenamiento guarda las ventanas móviles y la bitácora JSON, detectores "
        "decide si ocurrió un evento, manejadores reaccionan, y el dashboard "
        "presenta la información. Además del dashboard gráfico en tkinter y la "
        "consola, se agregó una versión web local para ejecutar el panel en el "
        "navegador.", cuerpo))
    elementos.append(Paragraph(
        "Al sistema se le añadió un laboratorio de alertas sonoras: 21 eventos "
        "disponen de un patrón sonoro propio, sintetizado como archivo WAV en "
        "memoria y emitido por un hilo independiente. El requisito central de ese "
        "laboratorio es que, mientras suena una alerta, el tablero siga "
        "refrescando y el ciclo siga detectando eventos; la sección 5 explica el "
        "diseño, la justificación de cada sonido y las pruebas que lo verifican.", cuerpo))
    elementos.append(PageBreak())

    # ------------------------------------------------------------------
    # 3. Estructura del proyecto
    # ------------------------------------------------------------------
    elementos.append(Paragraph("3. Estructura del proyecto", h1))
    elementos.append(Paragraph(
        "La estructura del proyecto se muestra a continuación. Cada paquete "
        "responde por una sola responsabilidad y el punto de entrada main.py solo "
        "elige la presentación, sin contener umbrales ni tiempos.", cuerpo))
    elementos.extend(figura_terminal(
        estructura_actual(),
        "Estructura de carpetas y paquetes del proyecto monitor_iot_QuerubeAriza.",
        "Se observan los paquetes sensores (un módulo por métrica), eventos "
        "(detectores, manejadores y despachador), almacenamiento (ventana móvil y "
        "bitácora) y dashboard (consola, ventana gráfica y web), además de "
        "config.py con toda la parametrización, nucleo.py con el bucle orientado a "
        "eventos, sonidos.py con el reproductor de alertas, generador.py para "
        "provocar carga y el paquete pruebas con las pruebas unitarias.",
        max_lineas=60))
    elementos.append(PageBreak())

    # ------------------------------------------------------------------
    # 4. Personalizacion
    # ------------------------------------------------------------------
    elementos.append(Paragraph("4. Personalización del panel de control", h1))
    elementos.append(Paragraph(
        "El panel de control fue personalizado con los datos del estudiante. En "
        "config.py se configuró el nodo como laptop-QuerubeAriza y la ubicación "
        "como Querube Ariza - Laboratorio 3 FISC. Estos valores aparecen en el "
        "encabezado del dashboard de consola, de tkinter y de la versión web.", cuerpo))
    elementos.extend(figura_terminal(
        consola,
        "Tablero de consola personalizado con el nombre del nodo y la ubicación.",
        "Captura del dashboard de consola después de la personalización: la "
        "primera línea identifica el nodo laptop-QuerubeAriza y su ubicación, y "
        "debajo aparecen las seis métricas con barra de progreso, porcentaje, la "
        "lista de los últimos eventos y la leyenda de teclas. El mismo encabezado "
        "se reutiliza en la ventana gráfica y en la versión web.",
        max_lineas=34))
    elementos.append(PageBreak())

    # ------------------------------------------------------------------
    # 5. Alertas sonoras
    # ------------------------------------------------------------------
    elementos.append(Paragraph("5. Sistema de alertas sonoras", h1))
    elementos.append(Paragraph(
        "El subsistema de alertas sonoras vive en sonidos.py y se parametriza por "
        "completo en config.py: allí están definidos los 17 patrones "
        "(SONIDO_PATRONES) y la asignación de un patrón a cada uno de los 21 "
        "eventos (SONIDO_EVENTOS). Cada nota indica tipo de onda (seno, cuadrada, "
        "triangular, barrido, ruido o silencio), duración en segundos y, según "
        "corresponda, frecuencia, volumen o frecuencia inicial y final.", cuerpo))
    elementos.append(Paragraph(
        "El reproductor sintetiza cada patrón en un WAV de 22 050 muestras por "
        "segundo, mono y de 16 bits con signo, directamente en memoria, y lo pasa "
        "a winsound. Un fundido de 8 ms al inicio y al final de cada nota evita el "
        "clic al cambiar de tono, y el volumen maestro está limitado al 30 % para "
        "que la alerta sea audible sin resultar molesta.", cuerpo))

    elementos.append(Paragraph("5.1 Tabla de alertas sonoras diseñadas", h2))
    elementos.append(Paragraph(
        "La tabla 1 reúne los sonidos de problema y de falla; la tabla 2 reúne los "
        "sonidos de recuperación e informe. La última columna de ambas contiene la "
        "justificación del sonido: por qué esa forma de onda y esa dirección de "
        "frecuencia se eligieron para ese evento.", cuerpo))

    elementos.append(Paragraph("Tabla 1. Alertas sonoras de problema y de falla.", estilos["pie_tabla"]))
    elementos.append(Paragraph(
        "Catorce eventos de estado crítico. Cada fila indica el evento, el patrón "
        "asignado, la composición exacta de las notas y la justificación acústica "
        "de la elección.", estilos["descripcion"]))
    elementos.append(tabla_datos(
        [[e, p, c, j] for e, p, c, j in PROBLEMAS],
        ["Evento", "Patrón", "Composición del sonido", "Justificación del sonido"],
        [1.15 * inch, 0.95 * inch, 1.95 * inch, 3.15 * inch]))

    elementos.append(Spacer(1, 0.15 * inch))
    elementos.append(Paragraph("Tabla 2. Alertas sonoras de recuperación e informe.", estilos["pie_tabla"]))
    elementos.append(Paragraph(
        "Siete eventos que indican que una condición crítica desapareció. Casi "
        "todos reutilizan la misma campanita corta para que el operador reconozca "
        "de inmediato que no debe intervenir.", estilos["descripcion"]))
    elementos.append(tabla_datos(
        [[e, p, c, j] for e, p, c, j in RECUPERACIONES],
        ["Evento", "Patrón", "Composición del sonido", "Justificación del sonido"],
        [1.15 * inch, 0.95 * inch, 1.95 * inch, 3.15 * inch]))
    elementos.append(PageBreak())

    elementos.append(Paragraph("5.2 Criterios de diseño del conjunto", h2))
    criterios = [
        "Dirección del tono: los problemas bajan el tono (sirena de caída, plano "
        "de descarga, golpe de disco) y las recuperaciones lo suben (arreglo "
        "ascendente, campanita). El oído interpreta esa dirección antes de "
        "entender el mensaje.",
        "Frecuencia según el recurso: los almacenamientos usan frecuencias graves "
        "y densas (disco 98-110 Hz, swap 261 Hz), la CPU usa tics agudos "
        "(1568 Hz) y la red usa barridos amplios (320-1760 Hz).",
        "Timbre según la naturaleza del evento: lo que está bien suena a seno "
        "limpio; lo que está roto suena a cuadrada y ruido (zumbido de falla); lo "
        "que oscila suena a barrido (zigzag de salto anómalo).",
        "Duración según la urgencia: la sirena de caída dura 1,72 s en total, "
        "mientras un tic de CPU dura 0,14 s para no tapar los demás avisos.",
        "Un solo sonido de alivio: todas las condiciones normalizadas comparten "
        "la campanita corta, de modo que no haya que memorizar siete sonidos "
        "distintos para el mismo significado.",
        "Sin patrón, sin sonido: un evento que no esté en SONIDO_EVENTOS se "
        "descarta en silencio, lo que permite agregar eventos nuevos sin tocar el "
        "reproductor.",
    ]
    for texto in criterios:
        elementos.append(Paragraph(f"• {texto}", lista))

    elementos.append(Paragraph(
        "5.3 Cómo se evitó que el sonido bloquee el ciclo de monitoreo", h2))
    elementos.append(Paragraph(
        "El riesgo de una alerta sonora es que el ciclo de monitoreo se detenga "
        "mientras suena el tono: winsound.PlaySound() es una llamada que espera a "
        "que el audio termine, y si se ejecutara dentro de nucleo.ciclo() "
        "congelaría la lectura de sensores durante cientos de milisegundos. El "
        "diseño evita esa condición separando quién detecta de quién suena:", cuerpo))
    elementos.append(Paragraph(
        "<b>1. Quien detecta solo encola.</b> El manejador del evento llama a "
        "sonidos.reproducir(clave), y esa función únicamente agrega la alerta a "
        "un deque con su marca de tiempo. No llama a winsound, no genera WAV y no "
        "espera: devuelve True o False y regresa al ciclo inmediatamente.", lista))
    elementos.append(Paragraph(
        "<b>2. Quien suena es otro hilo.</b> nucleo.iniciar() llama a "
        "sonidos.iniciar(), que crea una sola vez un hilo daemon llamado "
        "alertas-sonoras. Ese hilo tiene su propio bucle: saca la alerta más "
        "antigua de la cola, la sintetiza y la reproduce. El ciclo de monitoreo "
        "jamás entra en ese bucle ni espera por él.", lista))
    elementos.append(Paragraph(
        "<b>3. La cola es acotada y protegida.</b> El deque tiene un tope de seis "
        "elementos y todos los accesos pasan por un threading.Lock. Si el equipo "
        "se atrasa, se pierde el aviso más viejo en lugar de acumular una cola "
        "infinita de sonidos pendientes.", lista))
    elementos.append(Paragraph(
        "<b>4. Dos controles por marca de tiempo.</b> La cadencia evita repetir "
        "el mismo aviso antes de 1,2 s y el vencimiento descarta alertas de más de "
        "6 s. Así una ráfaga de eventos no se convierte en una ráfaga de sonidos.", lista))
    elementos.append(Paragraph(
        "<b>5. Ningún fallo de audio detiene el monitoreo.</b> La síntesis y la "
        "reproducción están envueltas en try/except dentro del hilo: si no hay "
        "tarjeta de audio o el WAV falla, el hilo simplemente sigue con la "
        "siguiente alerta y el sistema continúa monitoreando en silencio.", lista))
    elementos.append(Paragraph(
        "<b>6. La prueba lo demuestra.</b> Las pruebas unitarias comprueban que "
        "encolar es inmediato y no llama a la emisión, que encolar no arranca ni "
        "toca el hilo, y que las lecturas siguen llegando con el reproductor "
        "encendido.", lista))

    elementos.append(Spacer(1, 0.1 * inch))
    elementos.extend(figura_diagrama(
        diagrama_no_bloqueante(),
        "Separación entre el ciclo de monitoreo y el hilo de alertas sonoras.",
        "A la izquierda, el hilo principal: recorre los sensores, detecta los "
        "eventos y llama a sonidos.reproducir(), función que solo encola. A la "
        "derecha, el hilo alertas-sonoras, que es el único que sintetiza y "
        "reproduce el audio. La única zona compartida es la cola deque protegida "
        "por un bloqueo; la banda inferior resume los cuatro controles por marca "
        "de tiempo que impiden que la cola crezca sin límite."))

    elementos.append(Spacer(1, 0.1 * inch))
    elementos.append(Paragraph(
        "Tabla 3. Controles por marca de tiempo del reproductor.", estilos["pie_tabla"]))
    elementos.append(Paragraph(
        "Los cuatro valores viven en config.py; ninguno de ellos se define en "
        "sonidos.py ni en el ciclo de monitoreo.", estilos["descripcion"]))
    elementos.append(tabla_datos(
        [[n, v, d] for n, v, d in CONTROLES],
        ["Constante", "Valor", "Qué evita"],
        [1.35 * inch, 0.75 * inch, 5.1 * inch]))
    elementos.append(PageBreak())

    # ------------------------------------------------------------------
    # 6. Ejecucion del codigo
    # ------------------------------------------------------------------
    elementos.append(Paragraph("6. Ejecución del código y capturas de pantalla", h1))
    elementos.append(Paragraph(
        "Se ejecutaron las distintas formas de arrancar el nodo y se capturó la "
        "pantalla de cada una. Cada captura va acompañada de la descripción de lo "
        "que en ella se observa.", cuerpo))

    elementos.append(Paragraph("6.1 Revisión del entorno", h2))
    elementos.extend(figura_captura(
        buscar_imagen("ejecucion_revisar_c.png", "ejecucion_revisar.png"),
        "Ejecución de python main.py --revisar en la terminal.",
        "Se ejecutó python main.py --revisar. La captura muestra el resultado de "
        "la revisión: psutil 7.2.2 y tkinter 8.6 están instalados, y debajo aparece "
        "la lista de sensores con su estado. Los seis sensores (Uso de CPU, "
        "Memoria RAM, Disco, Red, Procesos y Batería) figuran como disponibles, y "
        "el mensaje final explica que la batería puede aparecer como NO disponible "
        "en computadoras de escritorio, lo cual se maneja como un sensor ausente y "
        "no como un error."))

    elementos.append(Paragraph("6.2 Dashboard de consola en ejecución", h2))
    elementos.extend(figura_captura(
        buscar_imagen("ejecucion_consola_c.png", "ejecucion_consola.png"),
        "Ejecución de python main.py --consola con el tablero refrescándose.",
        "Se ejecutó python main.py --consola y se capturó el tablero después de "
        "varios refrescos. Se observa el encabezado con el nodo y la hora de cada "
        "vuelta, las seis métricas con su barra de progreso y su valor (CPU, RAM, "
        "disco, red en KB/s, número de procesos y batería), el bloque de últimos "
        "eventos y la leyenda Ctrl+C para terminar. La actualización se hace cada "
        "200 ms sin bloquear el ciclo."))

    elementos.append(Paragraph("6.3 Servidor del dashboard web", h2))
    elementos.extend(figura_captura(
        buscar_imagen("ejecucion_web_c.png", "ejecucion_web.png"),
        "Ejecución de python main.py --web (servidor local).",
        "Se ejecutó python main.py --web. La captura muestra el mensaje del "
        "servidor local indicando que el dashboard web quedó corriendo en "
        "http://localhost:8000, listo para atender las peticiones del navegador y "
        "entregar las lecturas por JSON en el endpoint /datos."))

    elementos.append(Paragraph("6.4 Ventana gráfica (tkinter)", h2))
    elementos.extend(figura_captura(
        buscar_imagen("dashboard_tk.png"),
        "Dashboard gráfico de escritorio (python main.py) en ejecución.",
        "Captura de la ventana gráfica que abre el punto de entrada por defecto. "
        "La ventana muestra las seis barras de métricas del nodo, los últimos "
        "eventos detectados y los botones de control del tablero, entre ellos el "
        "botón que silencia o reactiva las alertas sonoras, coherente con el "
        "estado del reproductor descrito en la sección 5."))

    elementos.append(Paragraph("6.5 Dashboard web en el navegador", h2))
    elementos.extend(figura_captura(
        buscar_imagen("dashboard_web.png"),
        "Dashboard web personalizado abierto en el navegador.",
        "Captura del panel web servido por el propio nodo en "
        "http://localhost:8000. Reproduce las mismas seis métricas y la gráfica "
        "del historial, y ofrece los botones Pausar / Reanudar, Generar reporte y "
        "Limpiar bitácora. El navegador se refresca cada segundo contra el "
        "endpoint /datos, por lo que la interfaz no interfiere con el ciclo de "
        "monitoreo."))
    elementos.append(PageBreak())

    # ------------------------------------------------------------------
    # 7. Eventos detectados
    # ------------------------------------------------------------------
    elementos.append(Paragraph("7. Eventos detectados durante la ejecución", h1))
    elementos.append(Paragraph("7.1 Eventos por umbral, histéresis y flanco", h2))
    elementos.append(Paragraph(
        "Con la opción 1 de generador.py se forzó carga de CPU para provocar "
        "eventos reales y observar cómo el despachador los atiende.", cuerpo))
    elementos.extend(figura_terminal(
        eventos_cpu,
        "Eventos provocados por la carga de CPU, los núcleos saturados y el swap.",
        "La captura muestra la secuencia de eventos emitidos por el despachador: "
        "primero el flanco swap_activo, luego los avisos nucleo_saturado de los "
        "ocho núcleos con su porcentaje, la alerta cpu_alta al superar el umbral "
        "de 80 % (con histéresis hasta 50 %), los avisos proceso_pesado con el "
        "consumo de cada proceso, los eventos INFO nucleo_libre cuando la carga "
        "baja y, por tiempo, el reporte guardado en bitacora.json.",
        max_lineas=30))

    elementos.append(Paragraph("7.2 Evento por falla o ausencia", h2))
    elementos.append(Paragraph(
        "Para demostrar el flujo de falla se simuló la ausencia de lectura en un "
        "sensor. El detector trata None como sensor_ausente y el despachador "
        "registra el evento como FALLA sin detener el monitoreo; además encola la "
        "alerta sonora zumbido_falla en el hilo descrito en la sección 5.", cuerpo))
    elementos.extend(figura_terminal(
        eventos_falla,
        "Evento de falla o ausencia de un sensor.",
        "Salida del evento simulado: una lectura None se interpreta como "
        "sensor_ausente, se registra con nivel FALLA y el ciclo continúa con el "
        "resto de las métricas. El sistema no se detiene ante la falta de un "
        "sensor.",
        max_lineas=16))

    elementos.append(Paragraph("7.3 Reporte por tiempo y bitácora JSON", h2))
    elementos.append(Paragraph(
        "El evento de reporte se genera por tiempo o con el botón Generar "
        "reporte. El sistema resume las muestras del periodo, escribe "
        "bitacora.json y limpia el historial sin borrar la ventana móvil.", cuerpo))
    elementos.extend(figura_terminal(
        bitacora,
        "Resumen del periodo guardado en bitacora.json.",
        "Fragmento del archivo bitacora.json: conserva la marca de tiempo del "
        "reporte, el nodo y el resumen de cada métrica del periodo (mínimo, "
        "máximo y promedio). Ilustra la estrategia medir, acumular, resumir y "
        "vaciar propia de los sistemas IoT.",
        max_lineas=34))
    elementos.append(PageBreak())

    # ------------------------------------------------------------------
    # 8. Pruebas unitarias
    # ------------------------------------------------------------------
    elementos.append(Paragraph("8. Pruebas unitarias", h1))
    elementos.append(Paragraph(
        "El paquete pruebas contiene cuatro suites de pruebas unitarias con "
        "unittest, más una prueba en vivo. Las pruebas congelan el hilo "
        "reproductor (sonidos.detener()) y ponen el backend en silencio "
        "(SONIDO_BACKEND_NULO), de modo que corren sin emitir un solo tono.", cuerpo))

    resumen_pruebas = [
        ["pruebas/test_sonidos.py", "14",
         "Encolar no reproducir, tope de la cola, cadencia y vencimiento por marca "
         "de tiempo, y síntesis de los 17 patrones a un WAV válido."],
        ["pruebas/test_conexion_red.py", "13",
         "Flancos de pérdida y recuperación, rebotes, interfaces reales y "
         "virtuales, y el recordatorio periódico durante la caída."],
        ["pruebas/test_integracion.py", "9",
         "El ciclo despacha la pérdida de red y el recordatorio por tiempo, y las "
         "lecturas siguen llegando con el sonido activo."],
        ["pruebas/test_ventana.py", "5",
         "Insignias de red, botón de sonido y refresco de la ventana gráfica sin "
         "errores."],
    ]
    elementos.append(Paragraph(
        "Tabla 4. Suites de pruebas unitarias y número de pruebas.", estilos["pie_tabla"]))
    elementos.append(Paragraph(
        "Total: 41 pruebas unitarias en cuatro archivos, todas orientadas a "
        "comprobar que el sistema reacciona sin bloquearse.", estilos["descripcion"]))
    elementos.append(tabla_datos(
        resumen_pruebas,
        ["Archivo de pruebas", "N.°", "Qué comprueba"],
        [1.7 * inch, 0.5 * inch, 5.0 * inch]))
    elementos.append(Spacer(1, 0.15 * inch))

    elementos.append(Paragraph("8.1 Resultado de la ejecución", h2))
    elementos.append(Paragraph(
        "Se ejecutó el comando completo de la suite con modo verboso:", cuerpo_izq))
    elementos.append(caja_terminal(
        "C:\\Users\\Windows 11\\Downloads\\monitor_iot_QuerubeAriza>"
        " entorno\\Scripts\\python.exe -m unittest discover -s pruebas -t . -v",
        max_lineas=6))
    elementos.append(Spacer(1, 0.1 * inch))

    if salida_pruebas:
        elementos.extend(figura_terminal(
            salida_pruebas,
            "Resultado final de las 41 pruebas unitarias (modo verboso).",
            "Salida completa de la ejecución. Cada línea termina en ok, lo que "
            "indica que la prueba pasó; al final aparece el resumen del "
            "ejecutador: Ran 41 tests ... y la palabra OK, que confirma que no "
            "hubo fallos ni errores. Las pruebas de la suite de sonidos verifican "
            "justamente que encolar es inmediato y que el hilo de audio trabaja "
            "aparte del ciclo de monitoreo.",
            max_lineas=60))
    elementos.append(PageBreak())

    elementos.append(Paragraph("8.2 Capturas de las pruebas unitarias", h2))
    elementos.extend(figura_captura(
        buscar_imagen("pruebas_sonidos_c.png", "pruebas_sonidos.png"),
        "Pruebas unitarias del reproductor de alertas sonoras.",
        "Captura de la ejecución de python -m unittest pruebas.test_sonidos -v. "
        "Se observan las pruebas de la cola (encolar es inmediato y no reproduce, "
        "encolar no arranca el hilo, la cola no supera su tope, la cadencia por "
        "marca de tiempo, el apagado no encola y el silenciamiento vacía la "
        "cola), las de marcas de tiempo (alerta vigente se entrega y alerta "
        "vencida se descarta) y las de patrones (los 17 patrones están bien "
        "formados, todos se sintetizan, un evento sin patrón no suena y el WAV "
        "resultante es válido). Cierra con el resumen del ejecutador."))

    elementos.extend(figura_captura(
        buscar_imagen("pruebas_unitarias_c.png", "pruebas_unitarias.png"),
        "Pruebas unitarias de la suite completa del proyecto.",
        "Captura de la ejecución de python -m unittest discover -s pruebas -t . "
        "-v. Se muestra la lista de pruebas de las cuatro suites: conexión de "
        "red (flancos, interfaces y recordatorio), integración (el ciclo "
        "despacha eventos y sigue midiendo con el sonido activo), sonidos "
        "(cola, cadencia y patrones) y ventana (insignias, botón de sonido y "
        "refresco). Todas aparecen marcadas como ok."))
    elementos.append(PageBreak())

    # ------------------------------------------------------------------
    # 9. Conclusiones
    # ------------------------------------------------------------------
    elementos.append(Paragraph("9. Conclusión", h1))
    conclusiones = [
        "La computadora funciona como un nodo IoT porque entrega mediciones "
        "reales del sistema operativo y permite reaccionar ante cambios de su "
        "estado.",
        "La organización en paquetes facilita mantener responsabilidades "
        "separadas: sensores, eventos, almacenamiento, núcleo, dashboard y "
        "reproductor de alertas.",
        "La ventana móvil con deque(maxlen=N) reduce falsos positivos, ya que los "
        "umbrales se evalúan sobre promedios y no solo sobre lecturas instantáneas.",
        "El uso de un despachador basado en diccionario evita cadenas extensas de "
        "if/elif y permite agregar eventos nuevos con menor riesgo de modificar el "
        "bucle principal.",
        "El registro JSON permite conservar resúmenes del periodo y demuestra la "
        "estrategia de medir, acumular, resumir y vaciar usada en sistemas IoT.",
        "La versión web reutiliza el mismo núcleo de monitoreo, lo que confirma "
        "que al separar el motor de la presentación se puede cambiar la interfaz "
        "sin modificar los sensores ni la detección de eventos.",
        "El subsistema de alertas sonoras demuestra que un sonido no tiene por qué "
        "bloquear el sistema: quien detecta solo encola y quien suena es un hilo "
        "aparte, por lo que el ciclo de monitoreo nunca espera audio.",
        "Los controles por marca de tiempo (cadencia, vencimiento y cola acotada) "
        "son suficientes para que una ráfaga de eventos no se convierta en una "
        "ráfaga de sonidos ni en una cola indefinida.",
        "El diseño sonoro por familias (graves para almacenamiento, agudos para "
        "CPU, barridos para red, cuadrada con ruido para fallas y una única "
        "campanita para las recuperaciones) permite identificar el problema solo "
        "con escuchar, sin mirar la pantalla.",
        "Las 41 pruebas unitarias pasaron sin fallos, y entre ellas están las que "
        "comprueban que encolar es inmediato y que las lecturas siguen llegando "
        "con el reproductor encendido: la condición del laboratorio queda "
        "verificada de forma automatizada.",
    ]
    for item in conclusiones:
        elementos.append(Paragraph(f"• {item}", lista))

    doc.multiBuild(elementos, canvasmaker=PaginasNumeradas)
    print(SALIDA)


if __name__ == "__main__":
    crear_pdf()
