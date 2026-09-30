import psutil
import config

ETIQUETA = "Disco"
UNIDAD = "%"
GB = 1024 ** 3


def disponible():
    try:
        psutil.disk_usage(config.UNIDAD_DISCO)
        return True
    except Exception:
        return False


def leer():
    try:
        uso = psutil.disk_usage(config.UNIDAD_DISCO)
    except Exception:
        return None

    libre = uso.free / GB
    total = uso.total / GB

    return {
        "valor": round(uso.percent, 1),
        "unidad": UNIDAD,
        "porcentaje": uso.percent,
        "detalle": f"{libre:.1f} GB libres de {total:.1f} GB",
        "extra": {
            "unidad_disco": config.UNIDAD_DISCO,
            "libre_gb": round(libre, 2),
            "total_gb": round(total, 2),
        },
    }