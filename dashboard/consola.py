"""dashboard/consola.py

Version de texto del dashboard, por si tkinter no esta disponible o si
se prefiere trabajar sin interfaz grafica.

Usa el mismo nucleo y los mismos sensores que la ventana: lo unico que
cambia es como se presenta la informacion. Esa es la ventaja de haber
separado el motor de la presentacion.
"""

import os
import time

import config
import eventos                                    # LABORATORIO
import nucleo
import sensores
import sonidos                                    # LABORATORIO
import almacenamiento as registro

ANCHO = 46


def _barra(porcentaje, ancho=28):
    """Barra de progreso hecha con caracteres."""
    llenos = int(max(0.0, min(100.0, porcentaje)) / 100.0 * ancho)
    return "[" + "#" * llenos + " -" * (ancho - llenos) + "]"


def _limpiar_pantalla():
    os.system("cls" if os.name == "nt" else "clear")


def _pintar(lecturas):
    _limpiar_pantalla()
    print("=" * 74)
    print(f" NODO {config.NODO} | {config.UBICACION} | "
          f"{time.strftime('%H:%M:%S')}")
    print("=" * 74)

    for clave in sensores.LECTORES:
        etiqueta = sensores.etiqueta(clave)
        lectura = lecturas.get(clave)

        if lectura is None:
            print(f" {etiqueta:<14} {'no disponible':<40}")
            continue

        print(f" {etiqueta:<14} {_barra(lectura['porcentaje'])} "
              f"{lectura['valor']:>7g} {lectura['unidad']}")
        print(f" {'':<14} {lectura['detalle']}")

    print("-" * 74)
    # LABORATORIO: bloque nuevo - enlace de red y alertas sonoras
    conexion = eventos.estado_conexion()

    if conexion["conectado"] is None:
        enlace = "sin datos"
    elif conexion["conectado"]:
        enlace = "conectada"
        if conexion["interfaces"]:
            enlace += " (" + ", ".join(conexion["interfaces"]) + ")"
    else:
        enlace = "SIN CONEXION"
        if conexion["caida"] is not None:
            enlace += f" desde hace {conexion['caida']:g} s"

    if sonidos.activo():
        alertas = (f"sonido activo | cola {sonidos.pendiente()} | "
                   f"ultimo: {sonidos.ultimo() or 'ninguno'}")
    else:
        alertas = "sonido silenciado"

    print(f" {'Red (enlace)':<14} {enlace:<40}")
    print(f" {'Alertas':<14} {alertas:<40}")
    print("-" * 74)

    print(" Ultimos eventos:")

    for e in registro.eventos()[-8:]:
        print(f"   {e['hora']}  [{e['nivel']:<6}] {e['mensaje'][:52]}")

    print("-" * 74)
    print(" Ctrl+C para terminar")


def iniciar():
    """Bucle de monitoreo en modo texto. No bloquea entre lecturas."""
    nucleo.iniciar()
    ultimo_pintado = 0.0

    try:
        while True:
            resultado = nucleo.ciclo()
            ahora = time.time()

            if ahora - ultimo_pintado >= config.PANTALLA_CONSOLA:  # LABORATORIO
                _pintar(resultado["lecturas"])
                ultimo_pintado = ahora

            # LABORATORIO: la espera tambien sale de config.py
            time.sleep(config.REFRESCO_MS / config.MILISEGUNDOS_POR_SEGUNDO)

    except KeyboardInterrupt:
        print("\n Monitoreo detenido por el usuario.")
        nucleo.generar_reporte()
        print(f" Reporte final guardado en {config.ARCHIVO_BITACORA}")