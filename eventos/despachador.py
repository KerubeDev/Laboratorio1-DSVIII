"""eventos/despachador.py

Conecta cada evento con su manejador.

Este archivo tiene una sola funcion y no va a crecer nunca, por mas
eventos que se agreguen: en lugar de una cadena de if/elif, busca la
funcion en un diccionario. Ese es exactamente el mecanismo con el que
trabajan por dentro las bibliotecas de eventos y los clientes MQTT.
"""

import almacenamiento as registro
import sonidos                                    # LABORATORIO
from .manejadores import MANEJADORES


def atender(nombre, dato):
    """Ejecuta el manejador del evento y lo anota en la bitacora.

    Devuelve el registro creado, o None si el evento no tiene manejador.
    Se usa .get() para no provocar un KeyError con un evento desconocido.
    """
    manejador = MANEJADORES.get(nombre)

    if manejador is None:
        return registro.registrar_evento(
            "FALLA", nombre,
            f"Evento sin manejador registrado: {nombre}")

    try:
        nivel, mensaje = manejador(dato)
    except Exception as error:
        # Un manejador defectuoso no debe tumbar el bucle de monitoreo.
        return registro.registrar_evento(
            "FALLA", nombre, f"Error en el manejador: {error}")

    # LABORATORIO: reaccion sonora. Solo ENCOLA (deque + marca de tiempo)
    # y regresa enseguida: el sonido lo emite otro hilo, nunca este.
    sonidos.reproducir(nombre)

    return registro.registrar_evento(nivel, nombre, mensaje)


def eventos_conocidos():
    """Nombres de todos los eventos que el sistema sabe atender."""
    return sorted(MANEJADORES.keys())