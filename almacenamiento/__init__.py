"""Paquete almacenamiento

Guarda lo que el nodo va midiendo: la ventana movil de cada metrica,
el historial del periodo y la bitacora de eventos.

Un dispositivo IoT no puede guardar todo lo que mide. La estrategia es
siempre la misma: medir, acumular, resumir, enviar y vaciar.
"""

from .registro import (agregar, media, ultimo, registrar_evento, eventos,
                       resumen, guardar_bitacora, limpiar_periodo,
                       limpiar_eventos)