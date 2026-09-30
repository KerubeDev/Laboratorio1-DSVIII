"""pruebas/test_ventana.py

LABORATORIO: prueba de la ventana de tkinter.

La ventana abre de verdad, pero queda OCULTA (withdraw) y con el bucle
de eventos parchado, asi que las pruebas no se cuelgan ni tapan la
pantalla.  Comprueba que el encabezado nuevo (enlace de red y estado
del reproductor) se pinta sin errores.
"""

import unittest

try:                                        # LABORATORIO: sin tkinter no hay ventana
    import tkinter as tk
    _ventana_de_prueba = tk.Tk()
    _ventana_de_prueba.withdraw()
    _ventana_de_prueba.destroy()
except Exception as exc:                    # pragma: no cover
    raise unittest.SkipTest(f"este equipo no tiene tkinter: {exc}")

import config                                # noqa: E402
import eventos                               # noqa: E402
import sonidos                               # noqa: E402
from dashboard import ventana                # noqa: E402
from eventos import conexion_red             # noqa: E402


class TestVentana(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._mainloop_real = tk.Tk.mainloop
        cls._sonido = sonidos.activo()
        tk.Tk.mainloop = lambda self, *args, **kwargs: None   # sin bloqueo
        sonidos.detener()
        sonidos.poner_backend(config.SONIDO_BACKEND_NULO)     # sin ruido
        ventana.iniciar()
        ventana._ventana.withdraw()

    @classmethod
    def tearDownClass(cls):
        try:
            ventana._ventana.destroy()
        except Exception:                   # pragma: no cover
            pass
        tk.Tk.mainloop = cls._mainloop_real
        sonidos.poner_backend(None)
        sonidos.activar(cls._sonido)

    def setUp(self):
        self._situacion_real = conexion_red._situacion
        conexion_red.reiniciar()

    def tearDown(self):
        conexion_red._situacion = self._situacion_real
        conexion_red.reiniciar()

    def fijar(self, estado, activas=("Wi-Fi",), verificadas=("Wi-Fi",)):
        def situacion(est=estado, act=list(activas), ver=list(verificadas)):
            return est, act, list(ver)

        conexion_red._situacion = situacion

    def muestrear(self, veces=config.RED_CONEXION_MUESTRAS):
        for _ in range(veces):
            eventos.muestrear_conexion()

    def test_insignia_de_red_conectada(self):
        self.fijar(True)
        self.muestrear()
        ventana._pintar_estado_red()

        texto = ventana._conexion_texto.cget("text")

        self.assertIn("RED CONECTADA", texto)
        self.assertIn("Wi-Fi", texto)

    def test_insignia_de_red_caida(self):
        self.fijar(True)
        self.muestrear()
        self.fijar(False, activas=[], verificadas=["Wi-Fi"])
        self.muestrear()
        ventana._pintar_estado_red()

        texto = ventana._conexion_texto.cget("text")

        self.assertIn("RED SIN CONEXION", texto)
        self.assertIn("caida", texto)

    def test_insignia_de_sonido_sigue_al_reproductor(self):
        sonidos.activar(False)
        ventana._pintar_estado_red()
        self.assertEqual(ventana._sonido_texto.cget("text"), "♪ SILENCIO")

        sonidos.activar(True)
        ventana._pintar_estado_red()
        self.assertIn("SONIDO ACTIVO", ventana._sonido_texto.cget("text"))

    def test_el_boton_de_sonido_altera_el_reproductor(self):
        antes = sonidos.activo()
        ventana._alternar_sonido()
        self.assertNotEqual(sonidos.activo(), antes)
        ventana._alternar_sonido()
        self.assertEqual(sonidos.activo(), antes)

    def test_refrescar_pinta_sin_errores(self):
        self.fijar(True)
        self.muestrear()
        ventana._refrescar()                # incluye un ciclo de verdad

        self.assertTrue(ventana._reloj.cget("text"))


if __name__ == "__main__":
    unittest.main()
