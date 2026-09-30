import psutil

ETIQUETA = "Uso de CPU"
UNIDAD = "%"

_iniciado = False


def disponible():
    """El procesador siempre esta presente."""
    return True


def _iniciar():
    """Descarta la primera lectura, que siempre es 0.0."""
    global _iniciado

    psutil.cpu_percent(interval=None)
    psutil.cpu_percent(interval=None, percpu=True)

    _iniciado = True


def leer():
    """Devuelve el uso de CPU con el detalle por nucleo."""
    global _iniciado

    if not _iniciado:
        _iniciar()

    try:
        global_pct = psutil.cpu_percent(interval=None)
        nucleos = psutil.cpu_percent(interval=None, percpu=True)
    except Exception:
        return None

    try:
        f = psutil.cpu_freq()
        frecuencia = round(f.current) if f else None
    except Exception:
        frecuencia = None

    detalle = f"{len(nucleos)} nucleos"

    if frecuencia:
        detalle += f" | {frecuencia} MHz"

    return {
        "valor": round(global_pct, 1),
        "unidad": UNIDAD,
        "porcentaje": global_pct,
        "detalle": detalle,
        "extra": {
            "nucleos": [round(n, 1) for n in nucleos]
        },
    }