"""Pruebas unitarias de la deteccion de la conexion de red.

LABORATORIO: verifican los dos patrones que exige el encargo:

  * flanco .......... perdida y recuperacion, con antirrebote
  * tiempo .......... el recordatorio mientras dure la caida

Ademas se prueba el filtro de interfaces. El reloj NO se espera: se le
pasa a muestrear() como argumento, por eso las pruebas corren en
milisegundos y todos los tiempos salen de config.py.
"""

import socket
import time
import unittest
from types import SimpleNamespace
from unittest import mock

import config
from eventos import conexion_red


class Base(unittest.TestCase):
    """Deja la conexion limpia y permite fingir el estado del enlace."""

    def setUp(self):
        self._situacion_real = conexion_red._situacion
        conexion_red.reiniciar()

    def tearDown(self):
        conexion_red._situacion = self._situacion_real
        conexion_red.reiniciar()

    def fijar(self, estado, activas=(), verificadas=()):
        """Sustituye el muestreo real por un estado controlado.

        Los valores se atan como argumentos por defecto para que el
        lamba no arrastre cambios del bucle.
        """
        def situacion(est=estado, act=list(activas), ver=list(verificadas)):
            return est, act, ver

        conexion_red._situacion = situacion


class TestFlanco(Base):
    def test_primera_muestra_solo_fija_la_base(self):
        self.fijar(True, ["Wi-Fi"], ["Wi-Fi"])
        self.assertFalse(conexion_red.muestrear())
        self.assertFalse(conexion_red.muestrear())
        self.assertTrue(conexion_red.estado()["conectado"])

    def test_flanco_de_perdida(self):
        base = time.time()
        self.fijar(True, ["Wi-Fi"], ["Wi-Fi"])
        conexion_red.muestrear(ahora=base)

        self.fijar(False, [], ["Wi-Fi"])
        primera = conexion_red.muestrear(ahora=base)
        self.assertFalse(primera, "un solo cambio no confirma el flanco")

        nombres = []
        for i in range(config.RED_CONEXION_MUESTRAS + config.PRUEBA_MUESTRAS):
            for nombre, _dato in conexion_red.muestrear(ahora=base + i):
                nombres.append(nombre)

        self.assertIn("conexion_perdida", nombres)
        self.assertIs(conexion_red.estado()["conectado"], False)

    def test_flanco_de_recuperacion_informa_la_duracion(self):
        base = time.time()
        self.fijar(True, ["Wi-Fi"], ["Wi-Fi"])
        conexion_red.muestrear(ahora=base)

        self.fijar(False, [], ["Wi-Fi"])
        for i in range(config.RED_CONEXION_MUESTRAS + config.PRUEBA_MUESTRAS):
            conexion_red.muestrear(ahora=base + i)

        cambio = conexion_red._estado["cambio"]
        self.fijar(True, ["Wi-Fi"], ["Wi-Fi"])

        datos = None
        for i in range(config.RED_CONEXION_MUESTRAS + config.PRUEBA_MUESTRAS):
            ahora = cambio + config.PRUEBA_CAIDA_S + i
            for nombre, dato in conexion_red.muestrear(ahora=ahora):
                if nombre == "conexion_recuperada":
                    datos = dato

        self.assertIsNotNone(datos, "falto el flanco de recuperacion")
        self.assertGreaterEqual(datos["caida"], config.PRUEBA_CAIDA_S)
        self.assertTrue(conexion_red.estado()["conectado"])
        self.assertIsNone(conexion_red.estado()["caida"])

    def test_rebote_no_produce_flanco(self):
        base = time.time()
        self.fijar(True, ["Wi-Fi"], ["Wi-Fi"])
        conexion_red.muestrear(ahora=base)

        nombres = []
        actual = False

        for _ in range(config.PRUEBA_MUESTRAS):
            if actual:
                self.fijar(True, ["Wi-Fi"], ["Wi-Fi"])
            else:
                self.fijar(False, [], ["Wi-Fi"])

            for nombre, _dato in conexion_red.muestrear(ahora=base):
                nombres.append(nombre)

            actual = not actual

        self.assertFalse(nombres, "un enlace que baila no debe generar eventos")

    def test_estado_indeterminado_no_se_arriesga(self):
        self.fijar(None)
        self.assertFalse(conexion_red.muestrear())
        self.assertIsNone(conexion_red.estado()["conectado"])


class TestRecordatorio(Base):
    def _caer(self, base):
        self.fijar(True, ["Wi-Fi"], ["Wi-Fi"])
        conexion_red.muestrear(ahora=base)
        self.fijar(False, [], ["Wi-Fi"])

        for i in range(config.RED_CONEXION_MUESTRAS + config.PRUEBA_MUESTRAS):
            conexion_red.muestrear(ahora=base + i)

        return conexion_red._estado["cambio"]

    def test_recordatorio_solo_despues_del_periodo(self):
        cambio = self._caer(time.time())

        antes = cambio + (config.RED_CONEXION_RECORDATORIO
                          * config.PRUEBA_MARGEN)
        self.assertFalse(conexion_red.muestrear(ahora=antes),
                         "aviso antes de tiempo")

        justo = cambio + config.RED_CONEXION_RECORDATORIO
        nombres = [n for n, _ in conexion_red.muestrear(ahora=justo)]
        self.assertIn("conexion_recordatorio", nombres)

        # se rearma con su propia marca de tiempo
        self.assertFalse(conexion_red.muestrear(ahora=justo))

    def test_el_recordatorio_se_repite_mientras_dure_la_caida(self):
        cambio = self._caer(time.time())
        disparos = []
        instante = cambio

        for _ in range(config.PRUEBA_MUESTRAS):
            instante += config.RED_CONEXION_RECORDATORIO
            for nombre, _dato in conexion_red.muestrear(ahora=instante):
                if nombre == "conexion_recordatorio":
                    disparos.append(nombre)

        self.assertTrue(disparos, "el recordatorio no se repitio")

    def test_al_recuperar_se_detiene_el_recordatorio(self):
        cambio = self._caer(time.time())
        instante = cambio + config.RED_CONEXION_RECORDATORIO
        nombres = [n for n, _ in conexion_red.muestrear(ahora=instante)]
        self.assertIn("conexion_recordatorio", nombres)

        self.fijar(True, ["Wi-Fi"], ["Wi-Fi"])
        recuperada = False

        for i in range(config.RED_CONEXION_MUESTRAS + config.PRUEBA_MUESTRAS):
            for nombre, _dato in conexion_red.muestrear(
                    ahora=instante + config.RED_CONEXION_RECORDATORIO + i):
                if nombre == "conexion_recuperada":
                    recuperada = True

        self.assertTrue(recuperada)

        nombres = []
        for i in range(config.PRUEBA_MUESTRAS):
            for nombre, _dato in conexion_red.muestrear(
                    ahora=instante + config.RED_CONEXION_RECORDATORIO
                    + config.RED_CONEXION_MUESTRAS + i):
                nombres.append(nombre)

        self.assertNotIn("conexion_recordatorio", nombres)


class TestInterfaces(unittest.TestCase):
    """El filtro de interfaces se prueba con psutil fingido."""

    @staticmethod
    def _interfaz(up):
        return SimpleNamespace(isup=up)

    @staticmethod
    def _dir(ip):
        return [SimpleNamespace(family=socket.AF_INET, address=ip)]

    @staticmethod
    def _probar(estados, direcciones):
        with mock.patch.object(conexion_red.psutil, "net_if_stats",
                               return_value=estados), \
             mock.patch.object(conexion_red.psutil, "net_if_addrs",
                               return_value=direcciones):
            return conexion_red._situacion()

    def test_ignora_loopback_y_adaptadores_virtuales(self):
        estados = {
            "lo": self._interfaz(True),
            "Loopback Pseudo-Interface 1": self._interfaz(True),
            "vEthernet (WSL)": self._interfaz(True),
            "Wi-Fi": self._interfaz(True),
            "Ethernet": self._interfaz(False),
        }
        direcciones = {nombre: self._dir("192.168.0.7") for nombre in estados}

        estado, activas, verificadas = self._probar(estados, direcciones)

        self.assertTrue(estado)
        self.assertEqual(activas, ["Wi-Fi"])
        self.assertNotIn("lo", verificadas)
        self.assertNotIn("vEthernet (WSL)", verificadas)
        self.assertNotIn("Ethernet", activas)

    def test_todas_las_interfaces_reales_caidas(self):
        estados = {"Wi-Fi": self._interfaz(False),
                   "Ethernet": self._interfaz(False)}
        direcciones = {nombre: self._dir("10.0.0.4") for nombre in estados}

        estado, activas, verificadas = self._probar(estados, direcciones)

        self.assertFalse(estado)
        self.assertFalse(activas)
        self.assertTrue(verificadas)

    def test_interfaz_activa_sin_direccion_no_cuenta(self):
        estados = {"Wi-Fi": self._interfaz(True)}
        estado, activas, _verificadas = self._probar(estados, {"Wi-Fi": []})

        self.assertFalse(estado)
        self.assertFalse(activas)

    def test_sin_interfaces_no_hay_dato(self):
        estado, _activas, _verificadas = self._probar({}, {})
        self.assertIsNone(estado)

    def test_si_psutil_falla_no_hay_dato(self):
        with mock.patch.object(conexion_red.psutil, "net_if_stats",
                               side_effect=OSError):
            estado, _activas, _verificadas = conexion_red._situacion()

        self.assertIsNone(estado)


if __name__ == "__main__":
    unittest.main()
