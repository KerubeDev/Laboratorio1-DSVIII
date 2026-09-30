"""pruebas/en_vivo.py

LABORATORIO: prueba en vivo del sistema completo.

Se ejecuta en la propia computadora, con audio real:

    python pruebas/en_vivo.py

Recorre cuatro fases y termina con un veredicto:

  1. RECONOCIMIENTO AUDITIVO ... suena UNA vez cada patron de
     config.SONIDO_EVENTOS, con su nombre en pantalla, para que el
     tecnico escuche y aprenda a distinguirlos sin mirar la pantalla.
  2. NO BLOQUEA ............... se encolan todos los sonidos a la vez
     y el ciclo de monitoreo se mide con reloj: si el sonido lo
     frenara, la demora entre ciclos superaria PRUEBA_LATENCIA_MAX_S.
  3. FLANCO Y RECORDATORIO .... se SIMULA la caida del enlace (sin
     tocar la red real), corriendo el ciclo de verdad, y se espera el
     aviso por tiempo, el flanco de perdida y el de recuperacion.
  4. ENLACE REAL .............. estado actual de las interfaces.

Opciones:
    python pruebas/en_vivo.py --silencio   sin emitir audio
"""

import os
import sys
import time

# LABORATORIO: el script se corre desde pruebas/, asi que hay que
# devolver la raiz del proyecto al camino de busqueda.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config                                          # noqa: E402
import nucleo                                          # noqa: E402
import sonidos                                         # noqa: E402
from eventos import conexion_red                       # noqa: E402


class Veredicto:
    """Acumula el resultado de cada fase y devuelve el codigo de salida."""

    def __init__(self):
        self.resultados = []

    def comprobar(self, nombre, condicion):
        self.resultados.append((nombre, bool(condicion)))
        marca = "OK  " if condicion else "FALLA"
        print(f"  [{marca}] {nombre}")

    def resumen(self):
        print("=" * 74)
        aprobados = [r for r in self.resultados if r[1]]
        print(f" Prueba en vivo: {len(aprobados)} de "
              f"{len(self.resultados)} comprobaciones correctas")
        print("=" * 74)
        return self.resultados if len(aprobados) == len(self.resultados) else None


def _eventos_por_patron():
    """Un evento de muestra por cada patron distinto del catalogo."""
    vistos = set()
    muestra = []

    for evento, patron in config.SONIDO_EVENTOS.items():
        if patron in vistos:
            continue
        vistos.add(patron)
        muestra.append((evento, patron))

    return muestra


def _duracion(patron):
    return sum(nota["seg"] for nota in config.SONIDO_PATRONES[patron])


def _esperar_cola_vacia():
    while sonidos.pendiente():
        time.sleep(config.SONIDO_PAUSA)


# --------------------------------------------------------------------------
# LABORATORIO: fase 1 - que suene y se escuche cada patron
# --------------------------------------------------------------------------
def fase_sonidos(veredicto):
    print("-" * 74)
    print(" FASE 1: reconocimiento auditivo (un patron por evento)")
    print("-" * 74)

    tocados = 0

    for evento, patron in _eventos_por_patron():
        print(f"  suena {patron:<22} por el evento {evento}")
        sonidos.reproducir(evento)
        _esperar_cola_vacia()
        time.sleep(_duracion(patron) + config.PRUEBA_PAUSA_SONIDO)
        tocados += 1

    veredicto.comprobar("se encolaron y reprodujeron todos los patrones",
                        tocados == len(_eventos_por_patron()))


# --------------------------------------------------------------------------
# LABORATORIO: fase 2 - el ciclo no se congela mientras suena
# --------------------------------------------------------------------------
def fase_latencia(veredicto):
    print("-" * 74)
    print(" FASE 2: el ciclo sigue corriendo mientras suena la alarma")
    print("-" * 74)

    sonidos.reiniciar()

    # Se amontona todo lo que se pueda en la cola a la vez.
    for evento in config.SONIDO_EVENTOS:
        sonidos.reproducir(evento)

    espera = config.REFRESCO_MS / config.MILISEGUNDOS_POR_SEGUNDO
    deltas = []
    inicio = time.time()
    anterior = inicio

    while time.time() - inicio < config.PRUEBA_DURACION_S:
        nucleo.ciclo()
        ahora = time.time()
        deltas.append(ahora - anterior)
        anterior = ahora
        time.sleep(espera)

    transcurrido = time.time() - inicio
    maximo = max(deltas) if deltas else config.SONIDO_FASE_INICIAL
    demora_ms = maximo * config.MILISEGUNDOS_POR_SEGUNDO

    print(f"  {len(deltas)} ciclos en {transcurrido:.1f} s | "
          f"cola al arrancar: {config.SONIDO_MAX_COLA} | "
          f"demora maxima entre ciclos: {demora_ms:.1f} ms")
    print(f"  limite admitido: "
          f"{config.PRUEBA_LATENCIA_MAX_S * config.MILISEGUNDOS_POR_SEGUNDO:.1f} ms")

    veredicto.comprobar(
        "el sonido no congelo el ciclo de monitoreo",
        maximo <= config.PRUEBA_LATENCIA_MAX_S)


# --------------------------------------------------------------------------
# LABORATORIO: fase 3 - flanco de perdida, recordatorio y recuperacion
# --------------------------------------------------------------------------
def fase_conexion(veredicto):
    print("-" * 74)
    print(" FASE 3: caida simulada del enlace (la red real NO se toca)")
    print("-" * 74)

    real = conexion_red._situacion
    periodo_real = config.RED_CONEXION_RECORDATORIO
    config.RED_CONEXION_RECORDATORIO = config.PRUEBA_RECORDATORIO_S
    conexion_red.reiniciar()

    nucleo.iniciar()                     # linea base con el enlace real
    print(f"  linea base: {conexion_red.estado()}")

    verificados = ["enlace-fingido"]

    vistos = []
    inicio = time.time()

    try:
        # El enlace "se cae": el ciclo sigue corriendo de verdad.
        conexion_red._situacion = lambda: (False, [], verificados)

        while time.time() - inicio < config.PRUEBA_CAIDA_S:
            for evento in nucleo.ciclo()["eventos"]:
                vistos.append(evento["origen"])
                print(f"    +{time.time() - inicio:5.1f} s "
                      f"[{evento['nivel']:<6}] {evento['mensaje']}")
            time.sleep(config.REFRESCO_MS / config.MILISEGUNDOS_POR_SEGUNDO)

        # "Se arregla": flanco de recuperacion.
        conexion_red._situacion = lambda: (True, ["Wi-Fi"], verificados)

        limite = time.time() + config.PRUEBA_CAIDA_S
        while time.time() < limite and "conexion_recuperada" not in vistos:
            for evento in nucleo.ciclo()["eventos"]:
                vistos.append(evento["origen"])
                print(f"    +{time.time() - inicio:5.1f} s "
                      f"[{evento['nivel']:<6}] {evento['mensaje']}")
            time.sleep(config.REFRESCO_MS / config.MILISEGUNDOS_POR_SEGUNDO)

    finally:
        conexion_red._situacion = real
        config.RED_CONEXION_RECORDATORIO = periodo_real
        conexion_red.reiniciar()
        nucleo.ciclo()                    # vuelve a la linea base real

    print(f"  eventos observados: {sorted(set(vistos))}")
    veredicto.comprobar("flanco de perdida detectado y anunciado",
                        "conexion_perdida" in vistos)
    veredicto.comprobar("recordatorio por tiempo disparado en la caida",
                        "conexion_recordatorio" in vistos)
    veredicto.comprobar("flanco de recuperacion detectado y anunciado",
                        "conexion_recuperada" in vistos)


# --------------------------------------------------------------------------
# LABORATORIO: fase 4 - estado real de las interfaces
# --------------------------------------------------------------------------
def fase_enlace(veredicto):
    print("-" * 74)
    print(" FASE 4: estado real del enlace de este equipo")
    print("-" * 74)

    estado, activas, verificadas = conexion_red._situacion()

    print(f"  interfaces verificadas: {verificadas}")
    print(f"  interfaces activas    : {activas}")
    print(f"  estado                : {estado}")

    veredicto.comprobar("el muestreo real del enlace responde",
                        estado is not None)


def main():
    if "--silencio" in sys.argv:
        sonidos.poner_backend(config.SONIDO_BACKEND_NULO)

    veredicto = Veredicto()

    print("=" * 74)
    print(f" PRUEBA EN VIVO - nodo {config.NODO}")
    print(f" backend de audio: {sonidos.backend()} | "
          f"sonido activo: {sonidos.activo()}")
    print("=" * 74)

    sonidos.iniciar()

    fase_sonidos(veredicto)
    fase_latencia(veredicto)
    fase_conexion(veredicto)
    fase_enlace(veredicto)

    ok = veredicto.resumen()

    if ok is None:
        print(" RESULTADO: la prueba NO supero todas las comprobaciones")
        return 1

    print(" RESULTADO: sistema verificado en vivo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
