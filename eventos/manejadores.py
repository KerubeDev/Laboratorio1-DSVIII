"""eventos/manejadores.py

Que hacer cuando ocurre cada evento.

Un manejador es una funcion normal. Lo especial es que nadie la llama
directamente: se registra en el diccionario MANEJADORES y el despachador
la invoca cuando corresponde. Por eso se le llama callback.

Regla del curso: el manejador debe ser breve. Si tarda demasiado, el
bucle de monitoreo no alcanza a detectar los eventos siguientes.

Cada manejador devuelve una tupla (nivel, mensaje). Los niveles son
INFO, AVISO, ALERTA y FALLA, y el dashboard los pinta de distinto color.
"""

import config


# --------------------------------------------------------------------------
# CPU
# --------------------------------------------------------------------------
def cpu_alta(dato):
    return ("ALERTA", f"Carga alta sostenida: {dato['valor']}% "
                      f"(umbral {dato['umbral']}%)")


def cpu_normal(dato):
    return ("INFO", f"Carga normalizada: {dato['valor']}%")


def nucleo_saturado(dato):
    return ("AVISO", f"Nucleo {dato['nucleo']} saturado ({dato['valor']}%)")


def nucleo_libre(dato):
    return ("INFO", f"Nucleo {dato['nucleo']} liberado")


# --------------------------------------------------------------------------
# Memoria
# --------------------------------------------------------------------------
def ram_alta(dato):
    return ("ALERTA", f"Memoria RAM al {dato['valor']}%")


def ram_normal(dato):
    return ("INFO", f"Memoria normalizada: {dato['valor']}%")


def swap_activo(dato):
    return ("AVISO", "El sistema empezo a usar memoria de intercambio")


def swap_inactivo(dato):
    return ("INFO", "El sistema dejo de usar memoria de intercambio")


# --------------------------------------------------------------------------
# Disco
# --------------------------------------------------------------------------
def disco_lleno(dato):
    return ("ALERTA", f"Disco al {dato['valor']}% de su capacidad")


def disco_aliviado(dato):
    return ("INFO", f"Espacio en disco recuperado: {dato['valor']}% usado")


# --------------------------------------------------------------------------
# Red
# --------------------------------------------------------------------------
def red_pico(dato):
    return ("AVISO", f"Pico de trafico: {dato['valor']} KB/s")


def red_calma(dato):
    return ("INFO", f"Trafico normalizado: {dato['valor']} KB/s")


# --------------------------------------------------------------------------
# Procesos
# --------------------------------------------------------------------------
def proceso_nuevo(dato):
    return ("INFO", f"Proceso iniciado: {dato['nombre']}")


def proceso_cerrado(dato):
    return ("INFO", f"Proceso terminado: {dato['nombre']}")


def proceso_pesado(dato):
    return ("AVISO", f"{dato['nombre']} consume {dato['cpu']}% de CPU")


# --------------------------------------------------------------------------
# Bateria
# --------------------------------------------------------------------------
def bateria_baja(dato):
    return ("ALERTA", f"Bateria baja: {dato['valor']}%")


def bateria_recuperada(dato):
    return ("INFO", f"Bateria recuperada: {dato['valor']}%")


def cargador_conectado(dato):
    return ("INFO", f"Cargador conectado ({dato['valor']}%)")


def cargador_desconectado(dato):
    return ("AVISO", f"Cargador desconectado ({dato['valor']}%)")


# --------------------------------------------------------------------------
# LABORATORIO: Conexion de red (evento por flanco y por tiempo)
# --------------------------------------------------------------------------
def conexion_perdida(dato):
    return ("ALERTA", f"Se perdio la conexion de red: "
                      f"{dato['interfaces']:g} interfaces verificadas, "
                      f"{dato['activas']:g} activas")


def conexion_recuperada(dato):
    return ("INFO", f"Conexion de red restaurada tras {dato['caida']:g} s "
                    f"({dato['interfaces']:g} interfaces activas)")


def conexion_recordatorio(dato):
    return ("AVISO", f"Recordatorio: la red sigue caida desde hace "
                     f"{dato['caida']:g} s")


# --------------------------------------------------------------------------
# Fallas y anomalias
# --------------------------------------------------------------------------
def sensor_ausente(dato):
    return ("FALLA", f"Sin respuesta del sensor: {dato['metrica']}")


def lectura_invalida(dato):
    return ("FALLA", f"Lectura fuera de rango en {dato['metrica']}: "
                     f"{dato['valor']}")


def salto_anomalo(dato):
    return ("AVISO", f"Variacion brusca en {dato['metrica']}: "
                     f"de {dato['de']} a {dato['a']}")


def reporte(dato):
    return ("INFO", f"Reporte guardado en {config.ARCHIVO_BITACORA} "
                    f"({dato['metricas']} metricas)")


# --------------------------------------------------------------------------
# El diccionario que conecta cada evento con su manejador.
# Se escribe el nombre de la funcion SIN parentesis: con parentesis se
# guardaria el resultado de ejecutarla, no la funcion.
# Agregar un evento nuevo es agregar una linea aqui.
# --------------------------------------------------------------------------
MANEJADORES = {
    "cpu_alta": cpu_alta,
    "cpu_normal": cpu_normal,
    "nucleo_saturado": nucleo_saturado,
    "nucleo_libre": nucleo_libre,
    "ram_alta": ram_alta,
    "ram_normal": ram_normal,
    "swap_activo": swap_activo,
    "swap_inactivo": swap_inactivo,
    "disco_lleno": disco_lleno,
    "disco_aliviado": disco_aliviado,
    "red_pico": red_pico,
    "red_calma": red_calma,
    "proceso_nuevo": proceso_nuevo,
    "proceso_cerrado": proceso_cerrado,
    "proceso_pesado": proceso_pesado,
    "bateria_baja": bateria_baja,
    "bateria_recuperada": bateria_recuperada,
    "cargador_conectado": cargador_conectado,
    "cargador_desconectado": cargador_desconectado,
    "sensor_ausente": sensor_ausente,
    "lectura_invalida": lectura_invalida,
    "salto_anomalo": salto_anomalo,
    "reporte": reporte,
    # LABORATORIO: reaccion ante la perdida y la recuperacion de la red
    "conexion_perdida": conexion_perdida,
    "conexion_recuperada": conexion_recuperada,
    "conexion_recordatorio": conexion_recordatorio,
}