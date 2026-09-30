"""generador.py

Genera carga controlada en el equipo para provocar los eventos del
laboratorio "Monitor de salud del equipo".

Se ejecuta en una SEGUNDA ventana, mientras el monitor corre en la primera:

    python generador.py

No requiere bibliotecas externas: solo usa la biblioteca estandar.
Toda la carga se libera al terminar cada prueba.

Unidad 2 - Programacion en Python para sistemas IoT
Facultad de Ingenieria de Sistemas Computacionales - UTP
"""

import multiprocessing
import os
import tempfile
import time

# Limites de seguridad. No los suba sin necesidad.
MAX_SEGUNDOS = 60
MAX_MB_MEMORIA = 800
MAX_MB_DISCO = 500


def _quemar(fin):
    """Ocupa un nucleo del procesador hasta el instante `fin`."""
    while time.time() < fin:
        pass


def cargar_cpu(segundos=15, nucleos=None):
    """Sube el uso de CPU cerca del 100 % durante `segundos`.

    Lanza un proceso por nucleo. Al terminar, la carga desaparece sola.
    """
    segundos = min(segundos, MAX_SEGUNDOS)
    nucleos = nucleos or os.cpu_count() or 1
    fin = time.time() + segundos

    print(f"Cargando {nucleos} nucleo(s) durante {segundos} s...")

    procesos = [multiprocessing.Process(target=_quemar, args=(fin,))
                for _ in range(nucleos)]

    for p in procesos:
        p.start()

    for p in procesos:
        p.join()

    print("CPU liberada. \n")


def cargar_memoria(megabytes=400, segundos=15):
    """Reserva `megabytes` de RAM y los mantiene ocupados."""
    megabytes = min(megabytes, MAX_MB_MEMORIA)
    segundos = min(segundos, MAX_SEGUNDOS)

    print(f"Reservando {megabytes} MB durante {segundos} s...")

    bloques = []

    try:
        for _ in range(megabytes):
            bloques.append(bytearray(1024 * 1024))    # 1 MB cada uno

        time.sleep(segundos)

    except MemoryError:
        print("El sistema no pudo reservar toda la memoria pedida.")

    finally:
        bloques.clear()           # se libera aqui
        print("Memoria liberada. \n")


def cargar_disco(megabytes=200, segundos=10):
    """Crea un archivo temporal grande y lo borra al terminar."""
    megabytes = min(megabytes, MAX_MB_DISCO)
    segundos = min(segundos, MAX_SEGUNDOS)

    ruta = os.path.join(tempfile.gettempdir(), "lab_iot_relleno.tmp")
    print(f"Escribiendo {megabytes} MB en {ruta} ...")

    try:
        with open(ruta, "wb") as f:
            for _ in range(megabytes):
                f.write(b" \0" * 1024 * 1024)

        time.sleep(segundos)

    finally:
        if os.path.exists(ruta):
            os.remove(ruta)

        print("Archivo temporal eliminado. \n")


def abrir_procesos(cantidad=3, segundos=10):
    """Lanza procesos hijos que no hacen nada, para que el monitor
    detecte su aparicion y su cierre."""
    segundos = min(segundos, MAX_SEGUNDOS)

    print(f"Abriendo {cantidad} procesos durante {segundos} s...")

    fin = time.time() + segundos

    procesos = [multiprocessing.Process(target=time.sleep,
                                        args=(max(0, fin - time.time()),))
                for _ in range(cantidad)]

    for p in procesos:
        p.start()

    for p in procesos:
        p.join()

    print("Procesos cerrados. \n")


MENU = """
=== Generador  de eventos ===
 1. Cargar CPU            (evento por umbral)
 2. Ocupar memoria        (evento por umbral)
 3. Llenar disco temporal (evento por umbral)
 4. Abrir y cerrar procesos (evento por aparicion/desaparicion)
 5. Secuencia completa
 0. Salir

Recuerde: el cargador de la laptop se conecta y desconecta a mano;
ese es el evento de flanco y no necesita este programa.
"""


def secuencia():
    cargar_cpu(12)
    time.sleep(5)           # deja que el monitor vea la bajada
    cargar_memoria(400, 12)
    time.sleep(5)
    abrir_procesos(3, 8)


def main():
    while True:
        print(MENU)
        opcion = input("Opcion: ").strip()

        if opcion == "1":
            cargar_cpu(15)

        elif opcion == "2":
            cargar_memoria(400, 15)

        elif opcion == "3":
            cargar_disco(200, 10)

        elif opcion == "4":
            abrir_procesos(3, 10)

        elif opcion == "5":
            secuencia()

        elif opcion == "0":
            print("Fin.")
            break

        else:
            print("Opcion no valida. \n")


if __name__ == "__main__":
    multiprocessing.freeze_support()    # necesario en Windows
    main()