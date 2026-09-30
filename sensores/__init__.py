from . import cpu, memoria, disco, red, procesos, bateria


LECTORES = {
    "cpu": cpu,
    "memoria": memoria,
    "disco": disco,
    "red": red,
    "procesos": procesos,
    "bateria": bateria,
}


def disponibles():
    """Devuelve la lista de claves de los sensores presentes en el equipo."""
    return [
        clave
        for clave, modulo in LECTORES.items()
        if modulo.disponible()
    ]


def leer(clave):
    """Lee un sensor por su clave. Devuelve None si no esta disponible."""
    modulo = LECTORES.get(clave)

    if modulo is None or not modulo.disponible():
        return None

    return modulo.leer()


def etiqueta(clave):
    """Nombre legible de un sensor, para mostrarlo en pantalla."""
    modulo = LECTORES.get(clave)

    return modulo.ETIQUETA if modulo else clave