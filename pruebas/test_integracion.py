"""Pruebas unitarias de integracion del laboratorio.

LABORATORIO: verifican el cableado entre piezas que nadie modifica:
el despachador reacciona con sonido, los eventos de conexion tienen
manejador, y el ciclo de monitoreo los despacha sin depender del
periodo de ninguna metrica.
"""

import time
import unittest
from unittest import mock

import config
import eventos
import nucleo
import sonidos
from eventos import conexion_red


class TestDespachador(unittest.TestCase):
    def test_atender_encola_el_sonido_del_evento(self):
        with mock.patch.object(sonidos, "reproducir") as encolado:
            eventos.atender("cpu_alta",
                            {"valor": config.CPU_ALTO,
                             "umbral": config.CPU_ALTO})

        encolado.assert_called_with("cpu_alta")

    def test_sin_manejador_no_suena(self):
        with mock.patch.object(sonidos, "reproducir") as encolado:
            eventos.atender("evento_que_no_existe", {})

        encolado.assert_not_called()

    def test_todos_los_eventos_con_sonido_tienen_manejador(self):
        conocidos = eventos.eventos_conocidos()

        for nombre in config.SONIDO_EVENTOS:
            self.assertIn(nombre, conocidos)

    def test_los_eventos_de_conexion_tienen_manejador(self):
        for nombre in ("conexion_perdida", "conexion_recuperada",
                       "conexion_recordatorio"):
            self.assertIn(nombre, eventos.eventos_conocidos())


class TestManejadoresDeConexion(unittest.TestCase):
    def test_niveles_esperados(self):
        perdida = eventos.atender(
            "conexion_perdida",
            {"interfaces": len(config.RED_CONEXION_IGNORAR), "activas": 0})
        recuperada = eventos.atender(
            "conexion_recuperada",
            {"caida": config.PRUEBA_CAIDA_S,
             "interfaces": len(config.RED_CONEXION_IGNORAR)})
        recordatorio = eventos.atender(
            "conexion_recordatorio", {"caida": config.PRUEBA_CAIDA_S})

        self.assertEqual(perdida["nivel"], "ALERTA")
        self.assertEqual(recuperada["nivel"], "INFO")
        self.assertEqual(recordatorio["nivel"], "AVISO")


class TestCiclo(unittest.TestCase):
    """El ciclo completo, con el enlace fingido y el sonido sin ruido."""

    def setUp(self):
        self._situacion_real = conexion_red._situacion
        self._sonido = sonidos.activo()
        self._recordatorio = config.RED_CONEXION_RECORDATORIO
        sonidos.detener()
        sonidos.poner_backend(config.SONIDO_BACKEND_NULO)
        sonidos.activar(False)          # las pruebas no deben hacer ruido
        conexion_red.reiniciar()

    def tearDown(self):
        config.RED_CONEXION_RECORDATORIO = self._recordatorio
        conexion_red._situacion = self._situacion_real
        conexion_red.reiniciar()
        sonidos.detener()
        sonidos.poner_backend(None)
        sonidos.activar(self._sonido)

    def fijar(self, estado, activas=(), verificadas=()):
        def situacion(est=estado, act=list(activas), ver=list(verificadas)):
            return est, act, ver

        conexion_red._situacion = situacion

    def test_el_ciclo_despacha_la_perdida_de_red(self):
        self.fijar(True, ["Wi-Fi"], ["Wi-Fi"])
        nucleo.iniciar()

        self.fijar(False, [], ["Wi-Fi"])
        nombres = []

        for _ in range(config.RED_CONEXION_MUESTRAS + config.PRUEBA_MUESTRAS):
            for evento in nucleo.ciclo()["eventos"]:
                nombres.append(evento["origen"])

        self.assertIn("conexion_perdida", nombres)

    def test_el_ciclo_dispara_el_recordatorio_por_tiempo(self):
        """El aviso no lo dispara un sensor: lo dispara el reloj."""
        config.RED_CONEXION_RECORDATORIO = config.PRUEBA_RECORDATORIO_S
        self.fijar(True, ["Wi-Fi"], ["Wi-Fi"])
        nucleo.iniciar()

        self.fijar(False, [], ["Wi-Fi"])

        for _ in range(config.RED_CONEXION_MUESTRAS + config.PRUEBA_MUESTRAS):
            nucleo.ciclo()

        limite = time.time() + config.RED_CONEXION_RECORDATORIO \
            + config.PRUEBA_TOLERANCIA_S
        nombres = []

        while time.time() < limite and "conexion_recordatorio" not in nombres:
            for evento in nucleo.ciclo()["eventos"]:
                nombres.append(evento["origen"])
            time.sleep(config.SONIDO_PAUSA)

        self.assertIn("conexion_recordatorio", nombres)

    def test_al_recuperar_el_ciclo_lo_anuncia(self):
        self.fijar(True, ["Wi-Fi"], ["Wi-Fi"])
        nucleo.iniciar()

        self.fijar(False, [], ["Wi-Fi"])

        for _ in range(config.RED_CONEXION_MUESTRAS + config.PRUEBA_MUESTRAS):
            nucleo.ciclo()

        self.fijar(True, ["Wi-Fi"], ["Wi-Fi"])
        nombres = []

        for _ in range(config.RED_CONEXION_MUESTRAS + config.PRUEBA_MUESTRAS):
            for evento in nucleo.ciclo()["eventos"]:
                nombres.append(evento["origen"])

        self.assertIn("conexion_recuperada", nombres)

    def test_las_lecturas_siguen_llegando_con_el_sonido_activo(self):
        """Encender el reproductor no cambia la forma del ciclo."""
        self.fijar(True, ["Wi-Fi"], ["Wi-Fi"])
        sonidos.activar(True)
        nucleo.iniciar()

        with mock.patch.object(sonidos, "_emitir"):
            resultado = None

            for _ in range(config.PRUEBA_MUESTRAS):
                resultado = nucleo.ciclo()

        self.assertTrue(resultado["lecturas"])
        self.assertTrue(sonidos.activo())


if __name__ == "__main__":
    unittest.main()
