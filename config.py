import os

# Identificacion del nodo
NODO = "laptop-QuerubeAriza"
UBICACION = "Querube Ariza - Laboratorio 3 FISC"

# Periodos de muestreo
PERIODO_RAPIDO = 1.0
PERIODO_LENTO = 5.0
PERIODO_REPORTE = 30.0
REFRESCO_MS = 200

# Dashboard web
WEB_PUERTO = 8000

# Umbrales
CPU_ALTO = 80.0
CPU_BAJO = 50.0
CPU_NUCLEO_SATURADO = 90.0

RAM_ALTA = 85.0
RAM_BAJA = 75.0

DISCO_LLENO = 90.0
DISCO_ALIVIADO = 85.0

RED_PICO_KBS = 500.0
RED_CALMA_KBS = 200.0

BATERIA_BAJA = 20.0
BATERIA_RECUPERADA = 30.0

PROCESO_PESADO = 50.0
SALTO_ANOMALO = 40.0

# Ventana movil y almacenamiento
VENTANA = 10
MAX_EVENTOS_LOG = 200
ARCHIVO_BITACORA = "bitacora.json"

# Unidad de disco
UNIDAD_DISCO = "C:\\" if os.name == "nt" else "/"

# Procesos
TOP_PROCESOS = 8

PROCESOS_IGNORADOS = (
    "kworker",
    "kthread",
    "ksoftirqd",
    "migration",
    "rcu_",
    "irq/",
    "svchost"
)

# ==========================================================================
# LABORATORIO: en este bloque vive TODO sonido, tiempo y umbral nuevo.
# Ningun otro archivo del proyecto define numeros de sonidos ni de tiempos.
# ==========================================================================

# --- LABORATORIO: conexion de red (perdida, recuperacion, recordatorio) ---
# El sensor red.py mide KB/s; estas constantes describen el ENLACE.
RED_CONEXION_MUESTRAS = 2              # muestras seguidas que confirman el flanco
RED_CONEXION_RECORDATORIO = 45.0       # segundos entre recordatorios de caida
RED_CONEXION_DECIMALES = 1             # decimales al informar la duracion de la caida
RED_CONEXION_IGNORAR = (               # interfaces que no son la red real
    "lo", "loopback", "veth", "docker", "br-", "virbr",
    "tun", "tap", "wg", "isatap", "teredo", "vmnet", "vboxnet",
)

# --- LABORATORIO: reproductor de alertas sonoras (sonidos.py) ---
SONIDO_ACTIVO = True                   # arranque con o sin sonido
SONIDO_BACKEND = "auto"                # auto | winsound | campana | nulo
SONIDO_BACKEND_NULO = "nulo"           # sin salida de audio (pruebas)
SONIDO_MUESTREO = 22050                # muestras por segundo del WAV generado
SONIDO_CANALES = 1                     # mono
SONIDO_BYTES_MUESTRA = 2               # 16 bits con signo por muestra
SONIDO_AMPLITUD = 32767                # amplitud maxima de 16 bits con signo
SONIDO_VOLUMEN = 0.30                  # volumen maestro (0.0 a 1.0)
SONIDO_VOLUMEN_MAX = 1.0               # tope de volumen por nota
SONIDO_RAMPA = 0.008                   # segundos de fundido anti-clic
SONIDO_ENVOLVENTE = 1.0                # multiplicador cuando no hay fundido
SONIDO_TRIANGULAR = 0.63662            # 2/pi para dibujar la onda triangular
SONIDO_SIGNO = 1.0                     # amplitud normalizada de la onda cuadrada
SONIDO_FASE_INICIAL = 0.0              # fase de arranque del acumulador
SONIDO_RUIDO_TOPE = 1.0                # rango del ruido blanco
SONIDO_HZ_MIN = 85.0                   # limite inferior audible y seguro
SONIDO_HZ_MAX = 4000.0                 # limite superior audible y seguro
SONIDO_SEG_MIN = 0.01                  # nota mas corta que esto no se oye
SONIDO_VOLUMEN_MIN = 0.05              # nota mas baja que esto no se oye
SONIDO_COOLDOWN = 1.2                  # cadencia minima del mismo aviso (s)
SONIDO_VENCIDO = 6.0                   # alerta mas vieja que esto ya no suena (s)
SONIDO_PAUSA = 0.05                    # espera del hilo con la cola vacia (s)
SONIDO_MAX_COLA = 6                    # longitud maxima de la cola (deque)
SONIDO_TIPOS = (                       # formas de onda admitidas en los patrones
    "seno", "cuadrada", "triangular", "barrido", "ruido", "silencio",
)
SONIDO_NAVEGADOR_RETRASO = 0.02        # arranque de la onda en el navegador (s)

# LABORATORIO: patrones sonoros. Cada nota = {tipo, seg[, hz, vol, hz_ini, hz_fin]}.
# El oido distingue cada problema: sirenas caen, recuperaciones suben,
# fallas zumban, picos barriden hacia arriba y las caidas laten.
SONIDO_PATRONES = {
    "sirena_caida": [                  # rojo: la red se esta cayendo
        {"tipo": "barrido", "hz_ini": 880.0, "hz_fin": 160.0, "seg": 0.9},
        {"tipo": "silencio", "seg": 0.12},
        {"tipo": "barrido", "hz_ini": 660.0, "hz_fin": 120.0, "seg": 0.7},
    ],
    "arreglo_ascendente": [            # verde: do-mi-sol-do, todo vuelve
        {"tipo": "seno", "hz": 523.25, "seg": 0.13},
        {"tipo": "seno", "hz": 659.25, "seg": 0.13},
        {"tipo": "seno", "hz": 783.99, "seg": 0.13},
        {"tipo": "seno", "hz": 1046.5, "seg": 0.22, "vol": 0.9},
    ],
    "latido_caida": [                  # recordatorio: latido grave repetido
        {"tipo": "cuadrada", "hz": 220.0, "seg": 0.14, "vol": 0.8},
        {"tipo": "silencio", "seg": 0.14},
        {"tipo": "cuadrada", "hz": 220.0, "seg": 0.14, "vol": 0.8},
        {"tipo": "silencio", "seg": 0.14},
        {"tipo": "cuadrada", "hz": 146.83, "seg": 0.3, "vol": 0.9},
    ],
    "doble_tic": [                     # cpu: dos tics agudos, tipo semaforo
        {"tipo": "seno", "hz": 1567.98, "seg": 0.07, "vol": 0.7},
        {"tipo": "silencio", "seg": 0.07},
        {"tipo": "seno", "hz": 1567.98, "seg": 0.07, "vol": 0.7},
    ],
    "chime_corto": [                   # alivio: campanita corta
        {"tipo": "seno", "hz": 1046.5, "seg": 0.1, "vol": 0.6},
        {"tipo": "seno", "hz": 1318.51, "seg": 0.14, "vol": 0.6},
    ],
    "acorde_memoria": [                # ram: tres notas y se queda tensa
        {"tipo": "seno", "hz": 440.0, "seg": 0.09},
        {"tipo": "seno", "hz": 587.33, "seg": 0.09},
        {"tipo": "seno", "hz": 739.99, "seg": 0.09},
        {"tipo": "silencio", "seg": 0.05},
        {"tipo": "seno", "hz": 739.99, "seg": 0.18, "vol": 0.8},
    ],
    "golpe_grave": [                   # disco: golpe seco y grave
        {"tipo": "cuadrada", "hz": 110.0, "seg": 0.28, "vol": 0.9},
        {"tipo": "seno", "hz": 98.0, "seg": 0.3, "vol": 0.7},
    ],
    "swoosh_subida": [                 # trafico: barrido hacia arriba
        {"tipo": "barrido", "hz_ini": 320.0, "hz_fin": 1760.0, "seg": 0.4, "vol": 0.6},
    ],
    "pip_bateria": [                   # bateria: tres pitidos lentos
        {"tipo": "seno", "hz": 440.0, "seg": 0.22, "vol": 0.7},
        {"tipo": "silencio", "seg": 0.3},
        {"tipo": "seno", "hz": 440.0, "seg": 0.22, "vol": 0.7},
        {"tipo": "silencio", "seg": 0.3},
        {"tipo": "seno", "hz": 440.0, "seg": 0.22, "vol": 0.7},
    ],
    "plano_descarga": [                # cargador fuera: el tono se va al piso
        {"tipo": "barrido", "hz_ini": 700.0, "hz_fin": 300.0, "seg": 0.25, "vol": 0.7},
        {"tipo": "silencio", "seg": 0.08},
        {"tipo": "cuadrada", "hz": 300.0, "seg": 0.2, "vol": 0.7},
    ],
    "zumbido_falla": [                 # sensor mudo: zumbido feo
        {"tipo": "cuadrada", "hz": 130.0, "seg": 0.35, "vol": 0.9},
        {"tipo": "ruido", "seg": 0.12, "vol": 0.5},
        {"tipo": "cuadrada", "hz": 130.0, "seg": 0.35, "vol": 0.9},
    ],
    "tictac_invalido": [               # lectura rara: tres tics nerviosos
        {"tipo": "seno", "hz": 1174.66, "seg": 0.06, "vol": 0.6},
        {"tipo": "silencio", "seg": 0.06},
        {"tipo": "seno", "hz": 1174.66, "seg": 0.06, "vol": 0.6},
        {"tipo": "silencio", "seg": 0.06},
        {"tipo": "seno", "hz": 1174.66, "seg": 0.06, "vol": 0.6},
    ],
    "zigzag_salto": [                  # salto anomalo: ida y vuelta brusca
        {"tipo": "barrido", "hz_ini": 1400.0, "hz_fin": 300.0, "seg": 0.14, "vol": 0.7},
        {"tipo": "barrido", "hz_ini": 300.0, "hz_fin": 1400.0, "seg": 0.14, "vol": 0.7},
    ],
    "grunido_proceso": [               # proceso pesado: grunido quadrado
        {"tipo": "triangular", "hz": 196.0, "seg": 0.2, "vol": 0.8},
        {"tipo": "cuadrada", "hz": 196.0, "seg": 0.12, "vol": 0.6},
    ],
    "tic_nucleo": [                    # nucleo saturado: doble tic medio
        {"tipo": "seno", "hz": 987.77, "seg": 0.06, "vol": 0.6},
        {"tipo": "seno", "hz": 1318.51, "seg": 0.06, "vol": 0.6},
    ],
    "pulso_swap": [                    # swap: pulso binario, dos tiempos
        {"tipo": "cuadrada", "hz": 261.63, "seg": 0.1, "vol": 0.7},
        {"tipo": "silencio", "seg": 0.1},
        {"tipo": "cuadrada", "hz": 261.63, "seg": 0.1, "vol": 0.7},
    ],
}

# LABORATORIO: que patrón suena ante cada evento. Sin entrada aqui: silencio.
SONIDO_EVENTOS = {
    "conexion_perdida": "sirena_caida",
    "conexion_recuperada": "arreglo_ascendente",
    "conexion_recordatorio": "latido_caida",
    "cpu_alta": "doble_tic",
    "cpu_normal": "chime_corto",
    "ram_alta": "acorde_memoria",
    "ram_normal": "chime_corto",
    "disco_lleno": "golpe_grave",
    "disco_aliviado": "chime_corto",
    "red_pico": "swoosh_subida",
    "red_calma": "chime_corto",
    "bateria_baja": "pip_bateria",
    "bateria_recuperada": "arreglo_ascendente",
    "cargador_conectado": "chime_corto",
    "cargador_desconectado": "plano_descarga",
    "swap_activo": "pulso_swap",
    "sensor_ausente": "zumbido_falla",
    "lectura_invalida": "tictac_invalido",
    "salto_anomalo": "zigzag_salto",
    "proceso_pesado": "grunido_proceso",
    "nucleo_saturado": "tic_nucleo",
}

# --- LABORATORIO: presentacion del dashboard ---
UMBRAL_COLOR_ALTO = 85.0               # a partir de aqui la barra se pone roja
UMBRAL_COLOR_MEDIO = 60.0              # a partir de aqui la barra se pone ambar
PANTALLA_CONSOLA = 1.0                 # segundos entre repintados de consola
MILISEGUNDOS_POR_SEGUNDO = 1000.0      # factor de conversion de tiempos
WEB_HISTORIAL_PUNTOS = 60              # muestras que dibuja la grafica web
WEB_OFFLINE_MS = 3500.0                # ms sin datos para marcar "sin conexion"
WEB_REFRESCO_MS = 1000.0               # ms entre peticiones del navegador
WEB_SONIDO_NAVEGADOR = False           # sonido sintetizado en el navegador

# --- LABORATORIO: pruebas (unitarias y en vivo) ---
PRUEBA_DURACION_S = 10.0               # duracion de la fase de latencia
PRUEBA_LATENCIA_MAX_S = 0.5            # demora maxima admisible entre ciclos
PRUEBA_CAIDA_S = 12.0                  # duracion de la caida simulada
PRUEBA_RECORDATORIO_S = 3.0            # recordatorio acelerado durante la prueba
PRUEBA_MARGEN = 0.5                    # fraccion del periodo usada como "antes"
PRUEBA_TOLERANCIA_S = 0.5              # espera extra al comprobar un aviso
PRUEBA_MUESTRAS = 6                    # muestras de repeticion en las pruebas
PRUEBA_PAUSA_SONIDO = 0.4              # espera entre sonido y sonido
PRUEBA_DEMO_CICLOS = 10                # vueltas del ejemplo de nucleo.py
PRUEBA_DEMO_PAUSA = 0.5                # espera entre vueltas del ejemplo