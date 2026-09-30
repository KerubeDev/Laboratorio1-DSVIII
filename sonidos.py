"""sonidos.py

LABORATORIO: reproductor de alertas sonoras que NO bloquea el ciclo.

La condicion del laboratorio es que, mientras suena una alerta, el
dashboard siga refrescando y el ciclo siga detectando eventos. Para eso
se separan dos responsabilidades:

    quien detecta  ... solo ENCOLA  (cola deque + marca de tiempo)
    quien suena    ... un HILO aparte que ya esta creado

El hilo saca alertas de la cola y las emite; el ciclo de monitoreo jamas
espera un sonido, porque nunca llama a nada que reproduzca audio.

Tres controles por marca de tiempo:

    cadencia ..... no repite el mismo aviso antes de SONIDO_COOLDOWN
    vencimiento .. una alerta mas vieja que SONIDO_VENCIDO se descarta
    cola acotada . SONIDO_MAX_COLA evita que una racha inunde la cola

Las notas se sintetizan en un WAV en memoria (seno, cuadrada,
triangular, barrido y ruido) y se reproducen con winsound en modo
asincrono respecto al ciclo. Todos los sonidos y todos los tiempos
estan en config.py: este archivo no define ningun numero de esos.
"""

import io
import math
import random
import sys
import threading
import time
import wave
from array import array
from collections import deque

import config

# LABORATORIO: cola de pendientes y su proteccion
_cola = deque(maxlen=config.SONIDO_MAX_COLA)
_bloqueo = threading.Lock()          # protege cola, cadencias y ultimo
_arranque = threading.Lock()         # protege la creacion del hilo
_hilo = None
_iniciado = False
_activo = bool(config.SONIDO_ACTIVO)
_backend = None
_ultimo = {}                         # evento -> ultima marca de tiempo emitida
_ultimo_sonido = None                # (evento, marca) del ultimo encolado


# --------------------------------------------------------------------------
# LABORATORIO: estado y control (lo usan los dashboards)
# --------------------------------------------------------------------------
def activo():
    """True si en este momento las alertas suenan."""
    return _activo


def pendiente():
    """Alertas esperando en la cola (deque)."""
    with _bloqueo:
        return len(_cola)


def ultimo():
    """Ultimo evento encolado, o None."""
    with _bloqueo:
        return _ultimo_sonido[0] if _ultimo_sonido else None


def backend():
    """Salida de audio que se esta usando."""
    return _detectar_backend()


def estado():
    """Resumen completo para el dashboard."""
    with _bloqueo:
        cola = len(_cola)
        reciente = _ultimo_sonido[0] if _ultimo_sonido else None

    return {"activo": _activo, "cola": cola, "ultimo": reciente,
            "backend": _detectar_backend()}


def activar(valor):
    """Silencia (False) o reactiva (True) el reproductor."""
    global _activo

    _activo = bool(valor)

    if not _activo:
        with _bloqueo:
            _cola.clear()
    elif _iniciado:
        _arrancar()

    return _activo


def alternar():
    """Cambia el estado y devuelve el nuevo."""
    return activar(not _activo)


def reiniciar():
    """Vacia la cola y las cadencias. Lo usan las pruebas."""
    global _cola, _ultimo_sonido

    with _bloqueo:
        _cola = deque(maxlen=config.SONIDO_MAX_COLA)
        _ultimo.clear()
        _ultimo_sonido = None


def detener():
    """Congela el hilo: no vuelve a sacar nada de la cola.

    No destruye el hilo (es demonio y se apaga solo con el proceso),
    solo lo pone a dormir. Lo usan las pruebas para que ninguna cola
    de prueba sea consumida en medio de un assert.
    """
    global _iniciado

    _iniciado = False


def iniciar():
    """Crea el hilo reproductor una sola vez. Devuelve si quedo activo."""
    global _iniciado

    _iniciado = True

    if _activo:
        _arrancar()

    return _activo


# --------------------------------------------------------------------------
# LABORATORIO: encolado (esta es la parte que llama el despachador)
# --------------------------------------------------------------------------
def reproducir(clave, ahora=None):
    """Encola la alerta de un evento. Nunca reproduce ni espera aqui.

    Devuelve True si la alerta quedo en la cola y False si se descarto
    (sonido apagado, evento sin patrón, o todavia no toca repetirse).
    """
    global _ultimo_sonido

    if not _activo:
        return False

    nombre = config.SONIDO_EVENTOS.get(clave)

    if nombre is None:
        return False

    if ahora is None:
        ahora = time.time()

    with _bloqueo:
        emitida = _ultimo.get(clave)

        # Marca de tiempo de cadencia: un mismo aviso no se repite
        # antes de SONIDO_COOLDOWN, por mas veces que se dispare.
        if emitida is not None and ahora - emitida < config.SONIDO_COOLDOWN:
            return False

        _cola.append((ahora, nombre))     # deque acotada: aviso lo mas viejo
        _ultimo[clave] = ahora
        _ultimo_sonido = (clave, ahora)

    return True


# --------------------------------------------------------------------------
# LABORATORIO: hilo reproductor
# --------------------------------------------------------------------------
def _arrancar():
    """Arranca el hilo si no esta corriendo."""
    global _hilo

    with _arranque:
        if _hilo is not None and _hilo.is_alive():
            return

        _hilo = threading.Thread(target=_bucle, daemon=True,
                                 name="alertas-sonoras")
        _hilo.start()


def _tomar_pendiente():
    """Saca de la cola la alerta mas antigua que aun este vigente.

    Las vencidas (mas viejas que SONIDO_VENCIDO) se descartan aqui: si
    el equipo estuvo ocupado, lo peor que puede pasar es que la alerta
    ya no tenga sentido sonar.
    """
    with _bloqueo:
        while _cola:
            marca, nombre = _cola.popleft()

            if time.time() - marca <= config.SONIDO_VENCIDO:
                return marca, nombre

    return None


def _bucle():
    """El hilo: saca de la cola y emite. El ciclo jamas entra aqui."""
    while True:
        # LABORATORIO: si el reproductor esta congelado (pruebas) o
        # apagado, el hilo duerme y no toca la cola.
        if not _iniciado or not _activo:
            time.sleep(config.SONIDO_PAUSA)
            continue

        pendiente_hilo = _tomar_pendiente()

        if pendiente_hilo is None:
            time.sleep(config.SONIDO_PAUSA)
            continue

        try:
            _emitir(pendiente_hilo[1])
        except Exception:
            # Un sonido roto no debe tumbar el hilo ni el monitoreo.
            pass


def _detectar_backend():
    """Elige la salida de audio una sola vez."""
    global _backend

    if _backend is None:
        elegido = config.SONIDO_BACKEND

        if elegido == "auto":
            try:
                import winsound            # solo existe en Windows
                elegido = "winsound"
            except ImportError:
                elegido = "campana"

        _backend = elegido

    return _backend


def poner_backend(nombre):
    """Fuerza una salida de audio. Las pruebas usan SONIDO_BACKEND_NULO."""
    global _backend

    _backend = nombre


def _emitir(nombre):
    """Reproduce un patron completo. Solo lo llama el hilo."""
    patron = config.SONIDO_PATRONES.get(nombre)

    if not patron:
        return

    elegido = _detectar_backend()

    if elegido == config.SONIDO_BACKEND_NULO:
        return

    if elegido == "campana":
        # Respaldo sin winsound: campana de terminal, nota por nota.
        for nota in patron:
            sys.stdout.write("\a")
            sys.stdout.flush()
            time.sleep(nota["seg"])

        return

    try:
        import winsound
        # SND_SYNC no existe en todos los builds de Python: PlaySound ya
        # es sincrono salvo que se pida SND_ASYNC, asi que no hace falta.
        winsound.PlaySound(
            _sintetizar(patron),
            winsound.SND_MEMORY | winsound.SND_NODEFAULT,
        )
    except Exception:
        # Sin tarjeta de audio: se sigue monitoreando en silencio.
        pass


# --------------------------------------------------------------------------
# LABORATORIO: sintesis de las notas (todo parametrico desde config.py)
# --------------------------------------------------------------------------
def _muestra_nota(nota):
    """Dibuja una nota y devuelve enteros de 16 bits con signo."""
    muestreo = config.SONIDO_MUESTREO
    total = int(nota["seg"] * muestreo)

    if not total:
        return array("h")

    if nota["tipo"] == "silencio":
        silencio = array("h")
        silencio.frombytes(bytes(total * config.SONIDO_BYTES_MUESTRA))
        return silencio

    vol = nota.get("vol", config.SONIDO_VOLUMEN)
    amplitud = config.SONIDO_AMPLITUD * vol
    rampa = int(config.SONIDO_RAMPA * muestreo)
    salida = array("h")
    fase = config.SONIDO_FASE_INICIAL

    for i in range(total):
        if nota["tipo"] == "barrido":
            progreso = i / total
            hz = nota["hz_ini"] + (nota["hz_fin"] - nota["hz_ini"]) * progreso
            fase += math.tau * hz / muestreo
            onda = math.sin(fase)
        elif nota["tipo"] == "ruido":
            onda = random.uniform(-config.SONIDO_RUIDO_TOPE,
                                  config.SONIDO_RUIDO_TOPE)
        else:
            fase += math.tau * nota["hz"] / muestreo

            if nota["tipo"] == "cuadrada":
                onda = math.copysign(config.SONIDO_SIGNO, math.sin(fase))
            elif nota["tipo"] == "triangular":
                onda = math.asin(math.sin(fase)) * config.SONIDO_TRIANGULAR
            else:
                onda = math.sin(fase)

        # Fundido de entrada y salida: evita el clic al cambiar de tono.
        env = config.SONIDO_ENVOLVENTE
        if rampa and (i < rampa or i > total - rampa):
            env = min(i, total - i) / rampa

        salida.append(int(env * amplitud * onda))

    return salida


def _sintetizar(patron):
    """Convierte un patron completo en bytes de un WAV."""
    muestras = array("h")

    for nota in patron:
        muestras.extend(_muestra_nota(nota))

    if not muestras:
        return b""

    if sys.byteorder != "little":
        muestras.byteswap()               # el WAV siempre es little-endian

    memoria = io.BytesIO()

    with wave.open(memoria, "wb") as archivo:
        archivo.setnchannels(config.SONIDO_CANALES)
        archivo.setsampwidth(config.SONIDO_BYTES_MUESTRA)
        archivo.setframerate(config.SONIDO_MUESTREO)
        archivo.writeframes(muestras.tobytes())

    return memoria.getvalue()
