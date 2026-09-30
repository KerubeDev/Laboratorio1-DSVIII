"""eventos/conexion_red.py

LABORATORIO: deteccion de la perdida y la recuperacion de la red.

El sensor `sensores/red.py` mide el trafico en KB/s, pero 0 KB/s no
quiere decir "sin conexion": se puede tener enlace y no haber trafico.
Este modulo mira otro dato (las interfaces de red del sistema) y lo
convierte en eventos, SIN tocar el sensor ni los detectores:

    conexion_perdida ...... flanco de alto a bajo   (ALERTA)
    conexion_recuperada ... flanco de bajo a alto   (INFO)
    conexion_recordatorio . por TIEMPO, mientras siga caida (AVISO)

Los dos patrones del curso, aplicados al enlace:

    por flanco  ... solo se avanza si el estado CAMBIO respecto al
                    anterior, confirmado con N muestras seguidas
                    (antirrebote: un cable que baila no genera ruido)
    por tiempo  ... si la condicion persiste, el reloj vuelve a avisar
                    cada RED_CONEXION_RECORDATORIO segundos, igual que
                    un cronometro, hasta que la red vuelva.

Cada muestra es rapida y no bloquea: psutil solo consulta la tabla de
interfaces del sistema, sin abrir conexiones ni hacer ping.
"""

import socket
import time

import psutil

import config

# LABORATORIO: estado del enlace y marcas de tiempo de los eventos
_estado = {
    "conectado": None,      # situacion CONFIRMADA: True, False o None
    "candidato": None,      # situacion observada en curso (antirrebote)
    "racha": 0,             # muestras seguidas del candidato
    "cambio": None,         # marca de tiempo del ultimo flanco
    "recordatorio": None,   # marca de tiempo del ultimo recordatorio
    "interfaces": (),       # interfaces activas de la ultima muestra
}


# --------------------------------------------------------------------------
# LABORATORIO: muestreo del enlace
# --------------------------------------------------------------------------
def reiniciar():
    """Limpia el estado. Lo usan las pruebas para arrancar de cero."""
    _estado.update({"conectado": None, "candidato": None, "racha": 0,
                    "cambio": None, "recordatorio": None, "interfaces": ()})


def _ignorar(nombre):
    """True para loopback y adaptadores virtuales: no son la red real."""
    bajo = nombre.lower()
    return any(bajo.startswith(prefijo)
               for prefijo in config.RED_CONEXION_IGNORAR)


def _con_direccion(direcciones, nombre):
    """True si la interfaz tiene una direccion IP (no solo esta 'up')."""
    for dato in direcciones.get(nombre, ()):
        if dato.family in (socket.AF_INET, socket.AF_INET6) and dato.address:
            return True

    return False


def _situacion():
    """(estado, interfaces_activas, interfaces_verificadas).

    estado True  -> hay enlace
    estado False -> no hay enlace
    estado None  -> no se pudo determinar (no se arriesga un flanco)
    """
    try:
        estados = psutil.net_if_stats()
        direcciones = psutil.net_if_addrs()
    except Exception:
        return None, [], []

    verificadas = [n for n in estados if not _ignorar(n)]

    if not verificadas:
        return None, [], []

    activas = [n for n in verificadas
               if estados[n].isup and _con_direccion(direcciones, n)]

    return bool(activas), activas, verificadas


def _flanco(estado, activas, verificadas, ahora):
    """Cierra un flanco y devuelve el evento que corresponde."""
    inicio = _estado["cambio"] or ahora

    _estado["conectado"] = estado
    _estado["candidato"] = estado
    _estado["racha"] = 0
    _estado["cambio"] = ahora
    _estado["recordatorio"] = ahora
    _estado["interfaces"] = activas

    if estado:
        return ("conexion_recuperada",
                {"caida": round(ahora - inicio, config.RED_CONEXION_DECIMALES),
                 "interfaces": len(activas)})

    return ("conexion_perdida",
            {"interfaces": len(verificadas), "activas": len(activas)})


def muestrear(ahora=None):
    """Una muestra del enlace. Devuelve [(evento, dato)], sin bloquear.

    `ahora` se recibe como parametro para que las pruebas puedan mover
    el reloj y comprobar el recordatorio por tiempo sin esperar.
    """
    if ahora is None:
        ahora = time.time()

    estado, activas, verificadas = _situacion()
    eventos = []

    if estado is None:
        return eventos

    _estado["interfaces"] = activas

    # Primera muestra: solo fija la linea base. No hay flanco todavia,
    # igual que en los demas detectores del proyecto.
    if _estado["conectado"] is None:
        _estado["conectado"] = estado
        _estado["candidato"] = estado
        _estado["racha"] = 0
        _estado["recordatorio"] = ahora
        return eventos

    if estado == _estado["conectado"]:
        _estado["candidato"] = estado
        _estado["racha"] = 0
    else:
        # Antirrebote: el cambio se confirma recien cuando se repite.
        if estado != _estado["candidato"]:
            _estado["candidato"] = estado
            _estado["racha"] = 1
        else:
            _estado["racha"] += 1

        if _estado["racha"] >= config.RED_CONEXION_MUESTRAS:
            eventos.append(_flanco(estado, activas, verificadas, ahora))

    # Evento por tiempo: mientras el enlace siga caido, el reloj vuelve
    # a avisar cada RED_CONEXION_RECORDATORIO segundos.
    if _estado["conectado"] is False:
        ultimo = _estado["recordatorio"] or ahora

        if ahora - ultimo >= config.RED_CONEXION_RECORDATORIO:
            _estado["recordatorio"] = ahora
            caida = ahora - (_estado["cambio"] or ahora)
            eventos.append(("conexion_recordatorio",
                            {"caida": round(caida,
                                            config.RED_CONEXION_DECIMALES)}))

    return eventos


# --------------------------------------------------------------------------
# LABORATORIO: consulta para los dashboards
# --------------------------------------------------------------------------
def estado():
    """Resumen del enlace para pintar en pantalla."""
    conectado = _estado["conectado"]
    caida = None

    if conectado is False and _estado["cambio"]:
        caida = round(time.time() - _estado["cambio"],
                      config.RED_CONEXION_DECIMALES)

    return {"conectado": conectado,
            "interfaces": list(_estado["interfaces"]),
            "caida": caida}
