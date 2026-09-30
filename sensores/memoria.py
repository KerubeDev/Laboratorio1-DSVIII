import psutil

ETIQUETA = "Memoria RAM"
UNIDAD = "%"
GB = 1024 ** 3


def disponible():
    return True


def leer():
    try:
        ram = psutil.virtual_memory()
        swap = psutil.swap_memory()
    except Exception:
        return None

    usada = ram.used / GB
    total = ram.total / GB

    return {
        "valor": round(ram.percent, 1),
        "unidad": UNIDAD,
        "porcentaje": ram.percent,
        "detalle": f"{usada:.1f} de {total:.1f} GB | swap {swap.percent:.0f}%",
        "extra": {
            "usada_gb": round(usada, 2),
            "total_gb": round(total, 2),
            "swap_pct": round(swap.percent, 1),
            "usa_swap": swap.percent > 0.0,
        },
    }