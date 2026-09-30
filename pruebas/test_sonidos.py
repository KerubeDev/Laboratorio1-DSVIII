"""Pruebas unitarias del reproductor de alertas sonoras.

LABORATORIO: comprueban que encolar NO reproducir (el ciclo nunca se
congela), que la cola (deque) respeta su tope y sus marcas de tiempo,
y que todos los patrones de config.py son sintetizables.

Las pruebas congelan el hilo (sonidos.detener) y ponen el backend en
silencio (SONIDO_BACKEND_NULO): corren sin emitir un solo tono.
"""

import io
import time
import unittest
import wave
from unittest import mock

import config
import sonidos


class Base(unittest.TestCase):
    def setUp(self):
        self._activo = sonidos.activo()
        sonidos.detener()                              # el hilo no toca la cola
        sonidos.poner_backend(config.SONIDO_BACKEND_NULO)
        sonidos.reiniciar()
        sonidos.activar(True)

    def tearDown(self):
        sonidos.reiniciar()
        sonidos.poner_backend(None)                    # vuelve a deteccion auto
        sonidos.detener()
        sonidos.activar(self._activo)


class TestCola(Base):
    def test_encolar_es_inmediato_y_no_reproduce(self):
        with mock.patch.object(sonidos, "_emitir") as emision:
            self.assertTrue(sonidos.reproducir("cpu_alta"))
            emision.assert_not_called()

        self.assertTrue(sonidos.pendiente())
        self.assertEqual(sonidos.ultimo(), "cpu_alta")

    def test_encolar_no_arranca_el_hilo(self):
        hilo_antes = sonidos._hilo
        sonidos.reproducir("cpu_alta")
        self.assertIs(sonidos._hilo, hilo_antes,
                      "encolar no debe crear ni tocar el hilo")

    def test_la_cola_no_supera_su_tope(self):
        for nombre in config.SONIDO_EVENTOS:
            sonidos.reproducir(nombre)

        self.assertEqual(sonidos.pendiente(), config.SONIDO_MAX_COLA)

    def test_cadencia_por_marca_de_tiempo(self):
        instante = time.time()

        self.assertTrue(sonidos.reproducir("cpu_alta", ahora=instante))

        temprano = instante + (config.SONIDO_COOLDOWN * config.PRUEBA_MARGEN)
        self.assertFalse(sonidos.reproducir("cpu_alta", ahora=temprano),
                         "no debe repetirse antes de SONIDO_COOLDOWN")

        tarde = instante + config.SONIDO_COOLDOWN + config.SONIDO_PAUSA
        self.assertTrue(sonidos.reproducir("cpu_alta", ahora=tarde))

    def test_evento_sin_patron_no_suena(self):
        self.assertFalse(sonidos.reproducir("evento_inexistente"))
        self.assertFalse(sonidos.pendiente())

    def test_apagado_no_encola(self):
        sonidos.activar(False)
        self.assertFalse(sonidos.reproducir("cpu_alta"))
        self.assertFalse(sonidos.pendiente())

    def test_al_silenciar_se_vacia_la_cola(self):
        sonidos.reproducir("cpu_alta")
        self.assertTrue(sonidos.pendiente())
        sonidos.activar(False)
        self.assertFalse(sonidos.pendiente())
        self.assertFalse(sonidos.activo())


class TestMarcasDeTiempo(Base):
    def test_alerta_vencida_se_descarta(self):
        vieja = time.time() - config.SONIDO_VENCIDO - config.SONIDO_PAUSA

        self.assertTrue(sonidos.reproducir("cpu_alta", ahora=vieja))
        self.assertIsNone(sonidos._tomar_pendiente())
        self.assertFalse(sonidos.pendiente())

    def test_alerta_vigente_se_entrega(self):
        self.assertTrue(sonidos.reproducir("cpu_alta"))

        pendiente = sonidos._tomar_pendiente()

        self.assertIsNotNone(pendiente)
        self.assertEqual(pendiente[1], config.SONIDO_EVENTOS["cpu_alta"])
        self.assertFalse(sonidos.pendiente())


class TestPatrones(unittest.TestCase):
    """La configuracion misma tambien se prueba."""

    def test_cada_evento_apunta_a_un_patron_existente(self):
        for evento, patron in config.SONIDO_EVENTOS.items():
            self.assertIn(patron, config.SONIDO_PATRONES, evento)

    def test_los_patrones_estan_bien_formados(self):
        for nombre, patron in config.SONIDO_PATRONES.items():
            self.assertTrue(patron, nombre)

            for nota in patron:
                self.assertIn(nota["tipo"], config.SONIDO_TIPOS, nombre)
                self.assertGreaterEqual(nota["seg"], config.SONIDO_SEG_MIN,
                                        nombre)

                vol = nota.get("vol", config.SONIDO_VOLUMEN)
                self.assertGreaterEqual(vol, config.SONIDO_VOLUMEN_MIN, nombre)
                self.assertLessEqual(vol, config.SONIDO_VOLUMEN_MAX, nombre)

                frecuencias = []
                if "hz" in nota:
                    frecuencias.append(nota["hz"])
                if "hz_ini" in nota:
                    frecuencias.append(nota["hz_ini"])
                if "hz_fin" in nota:
                    frecuencias.append(nota["hz_fin"])

                for hz in frecuencias:
                    self.assertGreaterEqual(hz, config.SONIDO_HZ_MIN, nombre)
                    self.assertLessEqual(hz, config.SONIDO_HZ_MAX, nombre)

    def test_sintetiza_un_wav_valido(self):
        patron = config.SONIDO_PATRONES["sirena_caida"]
        datos = sonidos._sintetizar(patron)

        self.assertTrue(datos.startswith(b"RIFF"))
        self.assertGreater(len(datos), config.SONIDO_MUESTREO)

        with wave.open(io.BytesIO(datos)) as archivo:
            self.assertEqual(archivo.getnchannels(), config.SONIDO_CANALES)
            self.assertEqual(archivo.getsampwidth(),
                             config.SONIDO_BYTES_MUESTRA)
            self.assertEqual(archivo.getframerate(), config.SONIDO_MUESTREO)

    def test_todos_los_patrones_sintetizan(self):
        for nombre, patron in config.SONIDO_PATRONES.items():
            self.assertTrue(sonidos._sintetizar(patron), nombre)

    def test_backend_en_silencio_no_lanza_error(self):
        sonidos.poner_backend(config.SONIDO_BACKEND_NULO)
        sonidos._emitir(config.SONIDO_EVENTOS["conexion_perdida"])


if __name__ == "__main__":
    unittest.main()
