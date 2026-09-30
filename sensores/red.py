import time
import psutil

ETIQUETA = "Red"
UNIDAD = "KB/s"

KB = 1024.0
MB = 1024.0 ** 2

_anterior = {
    "enviados": 0,
    "recibidos": 0,
    "marca": 0.0
}

_iniciado = False


def disponible():
    try:
        return psutil.net_io_counters() is not None
    except Exception:
        return False


def _iniciar():
    global _iniciado

    c = psutil.net_io_counters()

    _anterior.update({
        "enviados": c.bytes_sent,
        "recibidos": c.bytes_recv,
        "marca": time.time()
    })

    _iniciado = True


def leer():
    global _iniciado

    if not _iniciado:
        _iniciar()
        return None

    try:
        c = psutil.net_io_counters()
    except Exception:
        return None

    ahora = time.time()
    transcurrido = ahora - _anterior["marca"]

    if transcurrido <= 0:
        return None

    subida = (
        c.bytes_sent - _anterior["enviados"]
    ) / KB / transcurrido

    bajada = (
        c.bytes_recv - _anterior["recibidos"]
    ) / KB / transcurrido

    _anterior.update({
        "enviados": c.bytes_sent,
        "recibidos": c.bytes_recv,
        "marca": ahora
    })

    total = subida + bajada

    import config
    tope = max(config.RED_PICO_KBS * 2, 1.0)

    return {
        "valor": round(total, 1),
        "unidad": UNIDAD,
        "porcentaje": min(
            100.0,
            total / tope * 100.0
        ),
        "detalle": (
            f"sube {subida:.1f} | "
            f"baja {bajada:.1f} KB/s | "
            f"total {(c.bytes_sent + c.bytes_recv) / MB:.0f} MB"
        ),
        "extra": {
            "subida_kbs": round(subida, 1),
            "bajada_kbs": round(bajada, 1)
        },
    }