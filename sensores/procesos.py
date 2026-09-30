import psutil
import config

ETIQUETA = "Procesos"
UNIDAD = "procs"


def disponible():
    return True


def leer():
    try:
        lista = []

        for p in psutil.process_iter([
            "pid",
            "name",
            "cpu_percent",
            "memory_percent"
        ]):

            info = p.info

            lista.append({
                "pid": info["pid"],
                "nombre": (info["name"] or "?")[:24],
                "cpu": round(
                    info["cpu_percent"] or 0.0,
                    1
                ),
                "ram": round(
                    info["memory_percent"] or 0.0,
                    1
                ),
            })

    except Exception:
        return None

    lista.sort(
        key=lambda p: p["cpu"],
        reverse=True
    )

    top = lista[:config.TOP_PROCESOS]

    pesado = (
        top[0]
        if top and top[0]["cpu"] > 0
        else None
    )

    detalle = "sin proceso dominante"

    if pesado:
        detalle = (
            f"mayor: {pesado['nombre']} "
            f"({pesado['cpu']:.0f}%)"
        )

    return {
        "valor": len(lista),
        "unidad": UNIDAD,
        "porcentaje": min(
            100.0,
            len(lista) / 4.0
        ),
        "detalle": detalle,
        "extra": {
            "top": top,
            "pids": {
                p["pid"]
                for p in lista
            },
            "nombres": {
                p["nombre"]
                for p in lista
            },
        },
    }