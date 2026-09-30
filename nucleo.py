"""nucleo.py

Motor de monitoreo. Aqui esta el bucle orientado a eventos.

Diseno clave: el ciclo NO usa time.sleep() para esperar. Cada metrica
guarda su propia marca de tiempo y se lee cuando le toca. Asi un solo
ciclo atiende tareas con periodos distintos sin bloquearse, que es el
patron recomendado de la Unidad 2.

La funcion ciclo() no bloquea: se puede llamar cada 200 ms desde un
dashboard grafico o desde un bucle de consola. Ella decide sola que
hay que leer en ese instante.
"""

import time

import config
import sensores
import eventos
import sonidos                                     # LABORATORIO
import almacenamiento as registro

# Que metricas se leen rapido y cuales despacio. Consultar los procesos
# es caro; consultar la CPU no lo es.
GRUPO_RAPIDO = ["cpu", "memoria", "red"]
GRUPO_LENTO = ["disco", "procesos", "bateria"]

# Marcas de tiempo: la ultima vez que se ejecuto cada tarea.
_marcas = {"rapido": 0.0, "lento": 0.0, "reporte": 0.0}

# Ultima lectura conocida de cada metrica, para que el dashboard siempre
# tenga algo que mostrar aunque en este instante no toque leer.
_ultimas = {}

_activos = []


def iniciar():
    """Detecta que sensores existen en este equipo y prepara el ciclo."""
    global _activos

    _activos = sensores.disponibles()
    ahora = time.time()

    # LABORATORIO: el reproductor de alertas arranca en su propio hilo,
    # de modo que nunca herede el ritmo del ciclo de monitoreo.
    sonidos.iniciar()

    for clave in _marcas:
        _marcas[clave] = ahora

    # Lectura de calentamiento: se descarta. La CPU siempre devuelve 0.0
    # la primera vez y la red necesita dos contadores para calcular una
    # velocidad. Sin este paso, la primera vuelta generaria eventos falsos.
    for clave in _activos:
        _ultimas[clave] = sensores.leer(clave)

    # LABORATORIO: la misma idea para el enlace de red: una lectura de
    # calentamiento fija la linea base y evita un flanco falso al arrancar.
    for nombre, dato in eventos.muestrear_conexion(ahora):      # LABORATORIO
        eventos.atender(nombre, dato)                           # LABORATORIO

    ausentes = [c for c in sensores.LECTORES if c not in _activos]

    for clave in ausentes:
        eventos.atender("sensor_ausente", {"metrica": clave})

    registro.registrar_evento(
        "INFO", "sistema",
        f"Nodo {config.NODO} iniciado | sensores activos: "
        f"{', '.join(_activos)}")

    return _activos


def _leer_grupo(claves):
    """Lee un grupo de metricas y despacha los eventos que provoquen."""
    nuevos = []

    for clave in claves:
        if clave not in _activos:
            continue

        lectura = sensores.leer(clave)
        _ultimas[clave] = lectura

        if lectura is not None:
            registro.agregar(clave, lectura["valor"])

        for nombre, dato in eventos.detectar(clave, lectura):
            nuevos.append(eventos.atender(nombre, dato))

    return nuevos


def ciclo():
    """Una vuelta del bucle de monitoreo. No bloquea.

    Devuelve un diccionario con las ultimas lecturas y con los eventos
    generados en esta vuelta.
    """
    ahora = time.time()
    nuevos = []

    if ahora - _marcas["rapido"] >= config.PERIODO_RAPIDO:
        nuevos += _leer_grupo(GRUPO_RAPIDO)
        _marcas["rapido"] = ahora

    if ahora - _marcas["lento"] >= config.PERIODO_LENTO:
        nuevos += _leer_grupo(GRUPO_LENTO)
        _marcas["lento"] = ahora

    # LABORATORIO: la red se muestrea en CADA vuelta (es barata y no
    # depende de ningun sensor). De aqui salen el flanco de perdida, el
    # flanco de recuperacion y el recordatorio por tiempo de caida.
    for nombre, dato in eventos.muestrear_conexion(ahora):      # LABORATORIO
        nuevos.append(eventos.atender(nombre, dato))            # LABORATORIO

    # Evento por tiempo: no lo dispara ningun sensor, lo dispara el reloj.
    if ahora - _marcas["reporte"] >= config.PERIODO_REPORTE:
        nuevos.append(generar_reporte())
        _marcas["reporte"] = ahora

    return {"lecturas": dict(_ultimas), "eventos": nuevos}


def generar_reporte():
    """Resume el periodo, lo guarda en la bitacora y vacia el historial."""
    datos = registro.resumen()
    registro.guardar_bitacora(datos)
    registro.limpiar_periodo()

    return eventos.atender("reporte",
                           {"metricas": len(datos["metricas"])})


def lecturas():
    """Ultimas lecturas conocidas, sin forzar una nueva medicion."""
    return dict(_ultimas)


def activos():
    return list(_activos)


if __name__ == "__main__":
    # Prueba del propio modulo: diez vueltas mostrando lo que ocurre.
    iniciar()

    # LABORATORIO: el ejemplo toma sus tiempos de config.py
    for _ in range(config.PRUEBA_DEMO_CICLOS):
        resultado = ciclo()

        for e in resultado["eventos"]:
            print(f"{e['hora']} [{e['nivel']}] {e['mensaje']}")

        time.sleep(config.PRUEBA_DEMO_PAUSA)