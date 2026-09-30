"""main.py

Punto de entrada del nodo de telemetria.

Fijese en lo que NO hay en este archivo: ni un umbral, ni un periodo,
ni una llamada a psutil, ni un if encadenado decidiendo que hacer con
cada evento. Todo eso vive en su modulo. main.py solo elige la
presentacion y arranca.

Uso:
    python main.py              dashboard grafico (tkinter)
    python main.py --consola    dashboard de texto
    python main.py --web        dashboard en el navegador
    python main.py --revisar    comprueba el entorno y sale
"""

import sys


def revisar_entorno():
    """Comprueba que todo lo necesario este instalado."""
    print("Revision del entorno")
    print("-" * 40)

    try:
        import psutil
        print(f"  psutil          OK  (version {psutil.__version__})")
    except ImportError:
        print("  psutil          FALTA -> pip install psutil")
        return False

    try:
        import tkinter
        print(f"  tkinter         OK  (Tk {tkinter.TkVersion})")
    except ImportError:
        print("  tkinter         FALTA -> use: python main.py --consola")

    import sensores

    activos = sensores.disponibles()
    print("-" * 40)

    for clave, modulo in sensores.LECTORES.items():
        estado = "disponible" if clave in activos else "NO disponible"
        print(f"  {modulo.ETIQUETA:<14} {estado}")

    print("-" * 40)
    print("La bateria aparece como NO disponible en computadoras de")
    print("escritorio. No es un error: es un sensor ausente y el")
    print("programa lo maneja como tal.")
    return True


def main():
    if "--revisar" in sys.argv:
        revisar_entorno()
        return

    if "--consola" in sys.argv:
        from dashboard import consola
        consola.iniciar()
        return

    if "--web" in sys.argv:
        from dashboard import web
        web.iniciar()
        return

    try:
        from dashboard import ventana
    except ImportError:
        print("tkinter no esta disponible en este equipo.")
        print("Se inicia el dashboard de consola.")
        from dashboard import consola
        consola.iniciar()
        return

    ventana.iniciar()


if __name__ == "__main__":
    main()