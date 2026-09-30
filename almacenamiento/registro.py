"""almacenamiento/registro.py

Ventana movil, historial del periodo y bitacora de eventos.

Por que una ventana movil y no la lectura instantanea: la CPU salta del
5 % al 90 % con solo abrir una pestana del navegador. Evaluar el umbral
sobre la media de las ultimas N muestras evita decenas de alarmas falsas.
Esa es la misma razon por la que en un sensor de temperatura se promedia
antes de decidir.
"""

import json
import os
import time
from collections import deque

import config

# Ventana movil por metrica: solo conserva las ultimas VENTANA muestras.
_ventanas = {}

# Ultimo valor crudo de cada metrica, para calcular saltos bruscos.
_ultimos = {}

# Historial del periodo actual: se vacia despues de cada reporte.
_historial = {}

# Bitacora de eventos que se muestra en pantalla.
_eventos = deque(maxlen=config.MAX_EVENTOS_LOG)


def agregar(clave, valor):
    """Guarda una lectura nueva en la ventana movil y en el historial."""
    if clave not in _ventanas:
        _ventanas[clave] = deque(maxlen=config.VENTANA)
        _historial[clave] = []

    _ventanas[clave].append(valor)
    _historial[clave].append(valor)
    _ultimos[clave] = valor


def media(clave):
    """Promedio de la ventana movil. None si aun no hay datos."""
    v = _ventanas.get(clave)

    if not v:
        return None

    return sum(v) / len(v)


def ultimo(clave):
    """Ultimo valor registrado de una metrica, o None."""
    return _ultimos.get(clave)


def registrar_evento(nivel, origen, mensaje):
    """Anota un evento en la bitacora y devuelve el registro creado."""
    registro = {
        "hora": time.strftime("%H:%M:%S"),
        "nivel": nivel,             # INFO, AVISO, ALERTA, FALLA
        "origen": origen,
        "mensaje": mensaje,
    }

    _eventos.append(registro)

    return registro


def eventos():
    """Lista de eventos registrados, del mas antiguo al mas reciente."""
    return list(_eventos)


def resumen():
    """Minimo, maximo, promedio y cantidad de muestras del periodo."""
    datos = {}

    for clave, valores in _historial.items():
        if not valores:
            continue

        datos[clave] = {
            "n": len(valores),
            "min": round(min(valores), 2),
            "max": round(max(valores), 2),
            "prom": round(sum(valores) / len(valores), 2),
        }

    return {
        "nodo": config.NODO,
        "ubicacion": config.UBICACION,
        "hora": time.strftime("%Y-%m-%d %H:%M:%S"),
        "metricas": datos,
    }


def guardar_bitacora(datos):
    """Agrega un resumen al archivo de bitacora en formato JSON.

    Se lee lo que habia, se agrega el nuevo resumen y se reescribe.
    Es la version sencilla de 'publicar' hacia un servidor.
    """
    ruta = config.ARCHIVO_BITACORA
    historial = []

    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                historial = json.load(f)
        except (json.JSONDecodeError, OSError):
            historial = []           # archivo danado: se empieza de nuevo

    historial.append(datos)

    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=2, ensure_ascii=False)

        return True
    except OSError:
        return False


def limpiar_periodo():
    """Vacia el historial despues de enviar el resumen. La ventana movil
    NO se toca: se necesita para seguir evaluando los umbrales."""
    for clave in _historial:
        _historial[clave].clear()


def limpiar_eventos():
    _eventos.clear()