"""dashboard/ventana.py

Interfaz grafica del nodo, escrita con tkinter (viene con Python).

Es programacion orientada a eventos en estado puro:

  - after(ms, funcion) es el temporizador que dispara el refresco;
    cumple el mismo papel que las marcas de tiempo del nucleo, pero
    dentro del bucle de la interfaz.
  - command=funcion registra el manejador de cada boton. Se escribe
    sin parentesis: se pasa la funcion, no su resultado.
  - protocol('WM_DELETE_WINDOW', ...) es el manejador del evento de
    cerrar la ventana.

La ventana nunca bloquea: cada refresco llama a nucleo.ciclo(), que
devuelve enseguida, y vuelve a programarse.
"""

import tkinter as tk

import config
import eventos                                    # LABORATORIO
import nucleo
import sensores
import sonidos                                    # LABORATORIO
import almacenamiento as registro

# --------------------------------------------------------------------------
# Paleta
# --------------------------------------------------------------------------
FONDO = "#11161d"
TARJETA = "#1b232e"
BORDE = "#2b3643"
TEXTO = "#e6edf3"
TENUE = "#8b98a8"

VERDE = "#3fb950"
AMBAR = "#d29922"
ROJO = "#f85149"
MAGENTA = "#bc8cff"
AZUL = "#58a6ff"

COLOR_NIVEL = {"INFO": TENUE, "AVISO": AMBAR,
               "ALERTA": ROJO, "FALLA": MAGENTA}

ANCHO_BARRA = 300
ALTO_BARRA = 14

_tarjetas = {}
_pausado = False
_ventana = None
_lista_eventos = None
_lista_procesos = None
_estado_texto = None
_conexion_texto = None                          # LABORATORIO
_sonido_texto = None                            # LABORATORIO
_reloj = None
_ultimo_evento = 0


def _color_barra(clave, lectura):
    """El color de la barra depende de si la metrica esta en alarma."""
    if lectura is None:
        return BORDE

    p = lectura["porcentaje"]

    if clave == "bateria":
        if lectura["valor"] <= config.BATERIA_BAJA:
            return ROJO
        return VERDE if lectura["extra"]["conectado"] else AZUL

    if p >= config.UMBRAL_COLOR_ALTO:          # LABORATORIO
        return ROJO
    if p >= config.UMBRAL_COLOR_MEDIO:         # LABORATORIO
        return AMBAR

    return VERDE


def _crear_tarjeta(padre, clave, fila, columna):
    """Construye una tarjeta de metrica y devuelve sus widgets."""
    marco = tk.Frame(padre, bg=TARJETA, highlightbackground=BORDE,
                     highlightthickness=1)
    marco.grid(row=fila, column=columna, padx=8, pady=8, sticky="nsew")

    titulo = tk.Label(marco, text=sensores.etiqueta(clave), bg=TARJETA,
                      fg=TENUE, font=("Segoe UI", 10, "bold"), anchor="w")
    titulo.pack(fill="x", padx=14, pady=(12, 0))

    valor = tk.Label(marco, text=" --", bg=TARJETA, fg=TEXTO,
                     font=("Segoe UI", 26, "bold"), anchor="w")
    valor.pack(fill="x", padx=14)

    barra = tk.Canvas(marco, width=ANCHO_BARRA, height=ALTO_BARRA,
                      bg=FONDO, highlightthickness=0)
    barra.pack(fill="x", padx=14, pady=(2, 6))

    detalle = tk.Label(marco, text="sin datos", bg=TARJETA, fg=TENUE,
                       font=("Segoe UI", 9), anchor="w", justify="left")
    detalle.pack(fill="x", padx=14, pady=(0, 12))

    return {"marco": marco, "valor": valor, "barra": barra,
            "detalle": detalle}


def _dibujar_barra(canvas, porcentaje, color):
    canvas.delete("all")
    ancho = max(canvas.winfo_width(), ANCHO_BARRA)
    canvas.create_rectangle(0, 0, ancho, ALTO_BARRA, fill=BORDE, width=0)
    largo = max(0, min(100.0, porcentaje)) / 100.0 * ancho
    if largo > 0:
        canvas.create_rectangle(0, 0, largo, ALTO_BARRA, fill=color,
                                width=0)


def _actualizar_tarjetas(lecturas):
    for clave, widgets in _tarjetas.items():
        lectura = lecturas.get(clave)

        if lectura is None:
            widgets["valor"].config(text=" --", fg=TENUE)
            widgets["detalle"].config(text="sensor no disponible")
            _dibujar_barra(widgets["barra"], 0, BORDE)
            continue

        widgets["valor"].config(
            text=f"{lectura['valor']:g} {lectura['unidad']}", fg=TEXTO)
        widgets["detalle"].config(text=lectura["detalle"])
        _dibujar_barra(widgets["barra"], lectura["porcentaje"],
                       _color_barra(clave, lectura))


def _actualizar_procesos(lecturas):
    lectura = lecturas.get("procesos")

    _lista_procesos.delete(0, tk.END)

    if lectura is None:
        _lista_procesos.insert(tk.END, "  sensor no disponible")
        return

    _lista_procesos.insert(tk.END, f"  {'PID':>7}  {'PROCESO':<24}"
                                   f"{'CPU':>7}{'RAM':>7}")

    for p in lectura["extra"]["top"]:
        _lista_procesos.insert(
            tk.END, f"  {p['pid']:>7}  {p['nombre']:<24}"
                    f"{p['cpu']:>6.1f}%{p['ram']:>6.1f}%")


def _actualizar_eventos():
    """Agrega a la lista solo los eventos que aun no se han mostrado."""
    global _ultimo_evento

    todos = registro.eventos()

    if len(todos) < _ultimo_evento:       # la bitacora fue limpiada
        _ultimo_evento = 0
        _lista_eventos.delete(0, tk.END)

    for e in todos[_ultimo_evento:]:
        linea = f" {e['hora']}  [{e['nivel']:<6}] {e['mensaje']}"
        _lista_eventos.insert(tk.END, linea)
        _lista_eventos.itemconfig(tk.END,
                                  fg=COLOR_NIVEL.get(e["nivel"], TEXTO))

    if len(todos) > _ultimo_evento:
        _lista_eventos.see(tk.END)

    _ultimo_evento = len(todos)


# --------------------------------------------------------------------------
# LABORATORIO: bloque nuevo - estado del enlace y de las alertas sonoras
# --------------------------------------------------------------------------
def _pintar_estado_red():
    """Encabezado: enlace de red (flanco) y cola de sonidos (deque)."""
    conexion = eventos.estado_conexion()

    if conexion["conectado"] is None:
        _conexion_texto.config(text="● RED SIN DATOS", fg=TENUE)
    elif conexion["conectado"]:
        texto = "● RED CONECTADA"

        if conexion["interfaces"]:
            texto += f" · {', '.join(conexion['interfaces'])}"

        _conexion_texto.config(text=texto, fg=VERDE)
    else:
        texto = "○ RED SIN CONEXION"

        if conexion["caida"] is not None:
            texto += f" · caida {conexion['caida']:g} s"

        _conexion_texto.config(text=texto, fg=ROJO)

    if sonidos.activo():
        _sonido_texto.config(
            text=f"♪ SONIDO ACTIVO · cola {sonidos.pendiente()} · "
                 f"ultimo: {sonidos.ultimo() or 'ninguno'}",
            fg=AZUL)
    else:
        _sonido_texto.config(text="♪ SILENCIO", fg=TENUE)


# --------------------------------------------------------------------------
# Manejadores de los botones
# --------------------------------------------------------------------------
def _alternar_pausa():
    global _pausado

    _pausado = not _pausado
    registro.registrar_evento(
        "INFO", "usuario", "Monitoreo en pausa" if _pausado
        else "Monitoreo reanudado")


def _forzar_reporte():
    nucleo.generar_reporte()


def _alternar_sonido():
    """LABORATORIO: silencia o reactiva el reproductor de alertas."""
    encendido = sonidos.alternar()

    registro.registrar_evento(
        "INFO", "usuario",
        "Alertas sonoras activadas" if encendido
        else "Alertas sonoras silenciadas")


def _limpiar():
    registro.limpiar_eventos()
    _lista_eventos.delete(0, tk.END)


def _salir():
    _ventana.destroy()


# --------------------------------------------------------------------------
# Bucle de refresco
# --------------------------------------------------------------------------
def _refrescar():
    """Se ejecuta cada REFRESCO_MS. Es el manejador del temporizador."""
    if not _pausado:
        resultado = nucleo.ciclo()
        _actualizar_tarjetas(resultado["lecturas"])
        _actualizar_procesos(resultado["lecturas"])
        _actualizar_eventos()

    _estado_texto.config(
        text="PAUSADO" if _pausado else "MONITOREANDO",
        fg=AMBAR if _pausado else VERDE)

    _pintar_estado_red()                       # LABORATORIO: encabezado vivo

    _reloj.config(text=__import__("time").strftime("%H:%M:%S"))

    # Se vuelve a programar a si misma: este es el temporizador.
    _ventana.after(config.REFRESCO_MS, _refrescar)


def iniciar():
    """Arma la ventana y entra en el bucle de eventos de tkinter."""
    global _ventana, _lista_eventos, _lista_procesos, _estado_texto, _reloj
    global _conexion_texto, _sonido_texto       # LABORATORIO

    nucleo.iniciar()

    _ventana = tk.Tk()
    _ventana.title(f"Nodo de telemetria - {config.NODO}")
    _ventana.configure(bg=FONDO)
    _ventana.geometry("1120x740")
    _ventana.minsize(900, 640)

    # ---- encabezado ----
    cabecera = tk.Frame(_ventana, bg=FONDO)
    cabecera.pack(fill="x", padx=14, pady=(12, 0))

    tk.Label(cabecera, text=f"{config.NODO}", bg=FONDO, fg=TEXTO,
             font=("Segoe UI", 15, "bold")).pack(side="left")
    tk.Label(cabecera, text=f"  ·  {config.UBICACION}", bg=FONDO,
             fg=TENUE, font=("Segoe UI", 10)).pack(side="left")

    _reloj = tk.Label(cabecera, text="", bg=FONDO, fg=TENUE,
                      font=("Consolas", 11))
    _reloj.pack(side="right", padx=(10, 0))

    _estado_texto = tk.Label(cabecera, text="MONITOREANDO", bg=FONDO,
                             fg=VERDE, font=("Segoe UI", 10, "bold"))
    _estado_texto.pack(side="right")

    # LABORATORIO: bloque nuevo - insignia de red y estado del sonido
    _conexion_texto = tk.Label(cabecera, text="● RED ...", bg=FONDO,
                               fg=TENUE, font=("Segoe UI", 10, "bold"))
    _conexion_texto.pack(side="left", padx=(14, 0))

    _sonido_texto = tk.Label(cabecera, text="♪ ...", bg=FONDO, fg=TENUE,
                             font=("Segoe UI", 10))
    _sonido_texto.pack(side="left", padx=(14, 0))

    # ---- tarjetas de metricas ----
    grilla = tk.Frame(_ventana, bg=FONDO)
    grilla.pack(fill="x", padx=6, pady=6)

    for c in range(3):
        grilla.columnconfigure(c, weight=1, uniform="col")

    for i, clave in enumerate(sensores.LECTORES):
        _tarjetas[clave] = _crear_tarjeta(grilla, clave, i // 3, i % 3)

    # ---- paneles inferiores ----
    inferior = tk.Frame(_ventana, bg=FONDO)
    inferior.pack(fill="both", expand=True, padx=6, pady=(0, 6))
    inferior.columnconfigure(0, weight=1)
    inferior.columnconfigure(1, weight=1)
    inferior.rowconfigure(0, weight=1)

    izq = tk.Frame(inferior, bg=TARJETA, highlightbackground=BORDE,
                   highlightthickness=1)
    izq.grid(row=0, column=0, sticky="nsew", padx=8, pady=4)
    tk.Label(izq, text="Procesos con mayor consumo", bg=TARJETA,
             fg=TENUE, font=("Segoe UI", 10, "bold"), anchor="w").pack(
        fill="x", padx=12, pady=(10, 4))

    _lista_procesos = tk.Listbox(izq, bg=TARJETA, fg=TEXTO, bd=0,
                                 font=("Consolas", 9),
                                 highlightthickness=0,
                                 selectbackground=BORDE,
                                 activestyle="none")
    _lista_procesos.pack(fill="both", expand=True, padx=6, pady=(0, 10))

    der = tk.Frame(inferior, bg=TARJETA, highlightbackground=BORDE,
                   highlightthickness=1)
    der.grid(row=0, column=1, sticky="nsew", padx=8, pady=4)
    tk.Label(der, text="Bitacora de eventos", bg=TARJETA, fg=TENUE,
             font=("Segoe UI", 10, "bold"), anchor="w").pack(
        fill="x", padx=12, pady=(10, 4))

    contenedor = tk.Frame(der, bg=TARJETA)
    contenedor.pack(fill="both", expand=True, padx=6, pady=(0, 10))

    scroll_y = tk.Scrollbar(contenedor, orient="vertical")
    scroll_y.pack(side="right", fill="y")

    scroll_x = tk.Scrollbar(contenedor, orient="horizontal")
    scroll_x.pack(side="bottom", fill="x")

    _lista_eventos = tk.Listbox(contenedor, bg=TARJETA, fg=TEXTO, bd=0,
                                font=("Consolas", 9),
                                highlightthickness=0,
                                selectbackground=BORDE,
                                activestyle="none",
                                yscrollcommand=scroll_y.set,
                                xscrollcommand=scroll_x.set)
    _lista_eventos.pack(side="left", fill="both", expand=True)

    scroll_y.config(command=_lista_eventos.yview)
    scroll_x.config(command=_lista_eventos.xview)

    # ---- botones ----
    pie = tk.Frame(_ventana, bg=FONDO)
    pie.pack(fill="x", padx=14, pady=(0, 12))

    def boton(texto, comando, color=BORDE):
        # command recibe la FUNCION, sin parentesis: es un callback.
        b = tk.Button(pie, text=texto, command=comando, bg=color, fg=TEXTO,
                      bd=0, padx=16, pady=7,
                      font=("Segoe UI", 9, "bold"),
                      activebackground=AZUL, activeforeground=FONDO,
                      cursor="hand2")
        b.pack(side="left", padx=(0, 8))
        return b

    boton("Pausar / Reanudar", _alternar_pausa)
    boton("Generar reporte", _forzar_reporte)
    boton("Limpiar bitacora", _limpiar)
    boton("Silenciar / Activar sonido", _alternar_sonido)   # LABORATORIO
    boton("Salir", _salir)

    tk.Label(pie, text=f"umbrales: CPU {config.CPU_ALTO:g}%  ·  "
                       f"RAM {config.RAM_ALTA:g}%  ·  "
                       f"disco {config.DISCO_LLENO:g}%  ·  "
                       f"red {config.RED_PICO_KBS:g} KB/s",
             bg=FONDO, fg=TENUE, font=("Segoe UI", 8)).pack(side="right")

    _ventana.protocol("WM_DELETE_WINDOW", _salir)    # manejador del cierre
    _ventana.after(config.REFRESCO_MS, _refrescar)   # arranca el temporizador
    _ventana.mainloop()                              # bucle de eventos