"""dashboard/web.py

Dashboard para el navegador, con la misma paleta y la misma logica
que la ventana de tkinter. Agrega una tercera presentacion al paquete
sin tocar ni el nucleo ni los sensores:

    python main.py --web

Usa solo la biblioteca estandar (http.server), como el generador.
Un hilo en segundo plano llama a nucleo.ciclo() cada REFRESCO_MS y el
navegador pide lecturas y eventos con fetch cada segundo.
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import config
import eventos                                    # LABORATORIO
import nucleo
import sensores
import sonidos                                    # LABORATORIO
import almacenamiento as registro

_pausado = False
_servidor = None


def _color_barra(clave, lectura):
    """Mismo criterio de color que dashboard/ventana.py."""
    if lectura is None:
        return "BORDE"

    p = lectura["porcentaje"]

    if clave == "bateria":
        if lectura["valor"] <= config.BATERIA_BAJA:
            return "ROJO"
        return "VERDE" if lectura["extra"]["conectado"] else "AZUL"

    if p >= config.UMBRAL_COLOR_ALTO:          # LABORATORIO
        return "ROJO"
    if p >= config.UMBRAL_COLOR_MEDIO:         # LABORATORIO
        return "AMBAR"

    return "VERDE"


def _pintar_lecturas(lecturas):
    """Deja las lecturas listas para JSON: los conjuntos no serializan."""
    salida = {}

    for clave, lectura in lecturas.items():
        if lectura is None:
            salida[clave] = None
            continue

        limpia = {
            "valor": lectura["valor"],
            "unidad": lectura["unidad"],
            "porcentaje": lectura["porcentaje"],
            "detalle": lectura["detalle"],
        }

        if clave == "procesos":
            limpia["top"] = lectura["extra"]["top"]

        salida[clave] = limpia

    return salida


def _datos():
    """Diccionario completo que consume la pagina."""
    return {
        "nodo": config.NODO,
        "ubicacion": config.UBICACION,
        "hora": time.strftime("%H:%M:%S"),
        "pausado": _pausado,
        "lecturas": _pintar_lecturas(nucleo.lecturas()),
        "etiquetas": {clave: sensores.etiqueta(clave)
                      for clave in sensores.LECTORES},
        "eventos": registro.eventos(),
        "conteo_eventos": _conteo_eventos(),
        "resumen": registro.resumen(),
        # LABORATORIO: bloque nuevo - enlace, sonidos y tiempos del navegador
        "conexion": eventos.estado_conexion(),
        "sonidos": _datos_sonidos(),
        "web": {
            "historial": config.WEB_HISTORIAL_PUNTOS,
            "offline": config.WEB_OFFLINE_MS,
            "refresco": config.WEB_REFRESCO_MS,
            "colorAlto": config.UMBRAL_COLOR_ALTO,
            "colorMedio": config.UMBRAL_COLOR_MEDIO,
        },
        "umbrales": {
            "CPU": config.CPU_ALTO,
            "RAM": config.RAM_ALTA,
            "disco": config.DISCO_LLENO,
            "red": config.RED_PICO_KBS,
            "bateria": config.BATERIA_BAJA,
        },
        "configuracion": _configuracion(),
    }


# LABORATORIO: bloque nuevo - todo lo que el navegador necesita para
# pintar el estado de la red y (si se desea) sintetizar sus propios tonos
def _datos_sonidos():
    estado = sonidos.estado()

    return {"activo": estado["activo"],
            "cola": estado["cola"],
            "ultimo": estado["ultimo"],
            "backend": estado["backend"],
            "eventos": config.SONIDO_EVENTOS,
            "patrones": config.SONIDO_PATRONES,
            "volumen": config.SONIDO_VOLUMEN,
            "retraso": config.SONIDO_NAVEGADOR_RETRASO,
            "navegador": config.WEB_SONIDO_NAVEGADOR}


def _conteo_eventos():
    conteo = {"INFO": 0, "AVISO": 0, "ALERTA": 0, "FALLA": 0}
    for evento in registro.eventos():
        nivel = evento.get("nivel", "INFO")
        conteo[nivel] = conteo.get(nivel, 0) + 1
    return conteo


def _configuracion():
    return {
        "CPU_ALTO": config.CPU_ALTO,
        "CPU_BAJO": config.CPU_BAJO,
        "RAM_ALTA": config.RAM_ALTA,
        "RAM_BAJA": config.RAM_BAJA,
        "DISCO_LLENO": config.DISCO_LLENO,
        "DISCO_ALIVIADO": config.DISCO_ALIVIADO,
        "RED_PICO_KBS": config.RED_PICO_KBS,
        "RED_CALMA_KBS": config.RED_CALMA_KBS,
        "BATERIA_BAJA": config.BATERIA_BAJA,
        "BATERIA_RECUPERADA": config.BATERIA_RECUPERADA,
        "PERIODO_REPORTE": config.PERIODO_REPORTE,
        # LABORATORIO: umbrales del enlace y del reproductor de sonido
        "RED_CONEXION_MUESTRAS": config.RED_CONEXION_MUESTRAS,
        "RED_CONEXION_RECORDATORIO": config.RED_CONEXION_RECORDATORIO,
        "SONIDO_VOLUMEN": config.SONIDO_VOLUMEN,
        "SONIDO_COOLDOWN": config.SONIDO_COOLDOWN,
        "SONIDO_VENCIDO": config.SONIDO_VENCIDO,
    }


def _actualizar_configuracion(datos):
    permitidos = _configuracion().keys()
    cambios = []
    for clave, valor in datos.items():
        if clave not in permitidos:
            continue
        try:
            nuevo = float(valor)
        except (TypeError, ValueError):
            continue
        setattr(config, clave, nuevo)
        cambios.append(f"{clave}={nuevo:g}")
    if cambios:
        registro.registrar_evento(
            "INFO", "config", "Umbrales actualizados: " + ", ".join(cambios))


def _csv_eventos():
    lineas = ["hora,nivel,origen,mensaje"]
    for evento in registro.eventos():
        mensaje = str(evento["mensaje"]).replace('"', '""')
        lineas.append(
            f'{evento["hora"]},{evento["nivel"]},{evento["origen"]},"{mensaje}"')
    return "\n".join(lineas) + "\n"


def _bucle_muestreo():
    """Muestrea aunque nadie mire la pagina: es el nucleo del nodo."""
    while True:
        if not _pausado:
            nucleo.ciclo()
        time.sleep(config.REFRESCO_MS / config.MILISEGUNDOS_POR_SEGUNDO)  # LABORATORIO


class _Manejador(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _responder_json(self, datos):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _responder_html(self, pagina):
        cuerpo = pagina.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _responder_archivo(self, nombre, tipo, cuerpo):
        if isinstance(cuerpo, str):
            cuerpo = cuerpo.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Disposition", f'attachment; filename="{nombre}"')
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _leer_json(self):
        tamano = int(self.headers.get("Content-Length", "0") or 0)
        if tamano <= 0:
            return {}
        cuerpo = self.rfile.read(tamano).decode("utf-8")
        try:
            return json.loads(cuerpo)
        except json.JSONDecodeError:
            return {}

    def do_GET(self):
        ruta = urlparse(self.path).path
        if ruta in ("/", "/index.html"):
            self._responder_html(_HTML)
        elif ruta == "/datos":
            self._responder_json(_datos())
        elif ruta == "/exportar.csv":
            self._responder_archivo("eventos.csv", "text/csv; charset=utf-8", _csv_eventos())
        elif ruta == "/bitacora.json":
            cuerpo = json.dumps(registro.eventos(), indent=2, ensure_ascii=False)
            self._responder_archivo("bitacora_eventos.json", "application/json; charset=utf-8", cuerpo)
        else:
            self.send_error(404)

    def do_POST(self):
        global _pausado

        ruta = urlparse(self.path).path

        if ruta == "/pausa":
            _pausado = not _pausado
            registro.registrar_evento(
                "INFO", "usuario",
                "Monitoreo en pausa" if _pausado
                else "Monitoreo reanudado")

        elif ruta == "/reporte":
            nucleo.generar_reporte()

        elif ruta == "/limpiar":
            registro.limpiar_eventos()

        # LABORATORIO: silenciar o reactivar el reproductor desde la web
        elif ruta == "/sonidos":
            datos = self._leer_json()

            if "activo" in datos:
                encendido = bool(datos["activo"])
            else:
                encendido = not sonidos.activo()

            sonidos.activar(encendido)
            registro.registrar_evento(
                "INFO", "usuario",
                "Alertas sonoras activadas" if encendido
                else "Alertas sonoras silenciadas")

        elif ruta == "/config":
            _actualizar_configuracion(self._leer_json())

        self._responder_json(_datos())


def iniciar(host="", puerto=config.WEB_PUERTO):
    """Arranca el hilo de muestreo y el servidor HTTP."""
    global _servidor

    nucleo.iniciar()
    threading.Thread(target=_bucle_muestreo, daemon=True).start()

    _servidor = ThreadingHTTPServer((host, puerto), _Manejador)
    url = f"http://localhost:{puerto}"

    registro.registrar_evento(
        "INFO", "sistema",
        f"Dashboard web iniciado | {url}")

    print(f"Dashboard web corriendo en {url}  (Ctrl+C para detener)")

    try:
        _servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo dashboard web.")
    finally:
        _servidor.server_close()
        nucleo.generar_reporte()
        print(f"Reporte final guardado en {config.ARCHIVO_BITACORA}")


_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nodo de telemetria - Dashboard web</title>
<style>
    :root {
        --fondo: #11161d; --tarjeta: #1b232e; --borde: #2b3643;
        --texto: #e6edf3; --tenue: #8b98a8;
        --verde: #3fb950; --ambar: #d29922; --rojo: #f85149;
        --magenta: #bc8cff; --azul: #58a6ff;
    }
    body.claro {
        --fondo: #f3f6fa; --tarjeta: #ffffff; --borde: #c9d6e2;
        --texto: #17212b; --tenue: #5d6975;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: var(--fondo); color: var(--texto); font-family: "Segoe UI", Arial, sans-serif; padding: 14px; }
    header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
    header h1 { font-size: 20px; font-weight: 700; }
    .ubicacion, .reloj, .umbrales, .detalle, .mini { color: var(--tenue); }
    .derecha { margin-left: auto; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .reloj { font-family: Consolas, monospace; }
    .estado { font-weight: 700; font-size: 13px; }
    .online { font-size: 12px; border: 1px solid var(--borde); border-radius: 999px; padding: 4px 8px; }
    .grilla { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 8px; }
    .paneles { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px; }
    .paneles3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 8px; }
    @media (max-width: 900px) { .grilla, .paneles, .paneles3 { grid-template-columns: 1fr; } }
    .tarjeta, .panel { background: var(--tarjeta); border: 1px solid var(--borde); border-radius: 6px; padding: 10px 12px; }
    .tarjeta.alerta { animation: pulso 0.7s alternate infinite; }
    @keyframes pulso { from { box-shadow: 0 0 0 transparent; } to { box-shadow: 0 0 18px var(--rojo); } }
    .tarjeta h2, .panel h3 { color: var(--tenue); font-size: 12px; font-weight: 700; margin-bottom: 6px; }
    .valor { font-size: 26px; font-weight: 700; }
    .barra { height: 10px; background: var(--borde); border-radius: 5px; overflow: hidden; margin: 6px 0; }
    .barra > div { height: 100%; border-radius: 5px; }
    .detalle { font-size: 12px; }
    table { width: 100%; border-collapse: collapse; font-family: Consolas, monospace; font-size: 12px; }
    th { color: var(--tenue); text-align: left; font-weight: 400; }
    td { padding: 2px 0; border-top: 1px solid var(--borde); }
    #bitacora { list-style: none; font-family: Consolas, monospace; font-size: 12px; max-height: 260px; overflow-y: auto; }
    #bitacora li { padding: 2px 0; border-top: 1px solid var(--borde); }
    .pie, .filtros, .config { display: flex; align-items: center; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
    button, a.boton { background: var(--borde); color: var(--texto); border: 0; padding: 8px 12px; border-radius: 4px; font-weight: 700; cursor: pointer; text-decoration: none; font-size: 13px; }
    button:hover, a.boton:hover { background: var(--azul); color: var(--fondo); }
    select, input { background: var(--fondo); color: var(--texto); border: 1px solid var(--borde); border-radius: 4px; padding: 6px; }
    input { width: 86px; }
    canvas { width: 100%; height: 160px; background: var(--fondo); border: 1px solid var(--borde); border-radius: 6px; }
    .contador { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
    .contador div { border: 1px solid var(--borde); border-radius: 5px; padding: 8px; text-align: center; }
    .contador strong { display: block; font-size: 22px; }
</style>
</head>
<body>
<header>
    <h1 id="nodo">Nodo</h1><span class="ubicacion" id="ubicacion"></span>
    <div class="derecha"><!-- LABORATORIO: insignias de red y sonido --><span class="online" id="conexionRed">red sin datos</span><span class="online" id="sonidoEstado">♪ ...</span><span class="online" id="online">online</span><span class="reloj" id="reloj"></span><span class="estado" id="estado">MONITOREANDO</span></div>
</header>

<main class="grilla" id="tarjetas"></main>

<section class="paneles3">
    <div class="panel"><h3>Graficas en tiempo real</h3><canvas id="grafica" width="700" height="220"></canvas><div class="mini">CPU, RAM, red y bateria. Ventana local del navegador.</div></div>
    <div class="panel"><h3>Estadisticas del periodo</h3><table><thead><tr><th>Metrica</th><th>n</th><th>min</th><th>max</th><th>prom</th></tr></thead><tbody id="estadisticas"></tbody></table></div>
    <div class="panel"><h3>Eventos por nivel</h3><div class="contador" id="contador"></div></div>
</section>

<section class="paneles">
    <div class="panel"><h3>Procesos con mayor consumo</h3><table><thead><tr><th>PID</th><th>PROCESO</th><th>CPU</th><th>RAM</th></tr></thead><tbody id="procesos"></tbody></table></div>
    <div class="panel"><h3>Bitacora de eventos</h3><div class="filtros"><label>Nivel <select id="filtroNivel"><option value="TODOS">TODOS</option><option>INFO</option><option>AVISO</option><option>ALERTA</option><option>FALLA</option></select></label><label>Buscar <input id="buscarEvento" placeholder="cpu, red..."></label></div><ul id="bitacora"></ul></div>
</section>

<section class="panel">
    <h3>Configuracion desde la web</h3>
    <div class="config">
        <label>CPU alto <input data-config="CPU_ALTO" type="number" step="1"></label>
        <label>CPU bajo <input data-config="CPU_BAJO" type="number" step="1"></label>
        <label>RAM alta <input data-config="RAM_ALTA" type="number" step="1"></label>
        <label>Disco lleno <input data-config="DISCO_LLENO" type="number" step="1"></label>
        <label>Red pico <input data-config="RED_PICO_KBS" type="number" step="10"></label>
        <label>Bateria baja <input data-config="BATERIA_BAJA" type="number" step="1"></label>
        <!-- LABORATORIO: umbrales del enlace y del reproductor de sonido -->
        <label>Recordatorio red <input data-config="RED_CONEXION_RECORDATORIO" type="number"></label>
        <label>Muestras flanco <input data-config="RED_CONEXION_MUESTRAS" type="number"></label>
        <label>Volumen <input data-config="SONIDO_VOLUMEN" type="number"></label>
        <label>Cadencia sonido <input data-config="SONIDO_COOLDOWN" type="number"></label>
        <label>Vencimiento sonido <input data-config="SONIDO_VENCIDO" type="number"></label>
        <button id="btnConfig">Guardar umbrales</button>
    </div>
</section>

<div class="pie">
    <button id="btnPausa">Pausar / Reanudar</button><button id="btnReporte">Generar reporte</button><button id="btnLimpiar">Limpiar bitacora</button><!-- LABORATORIO --><button id="btnSilencio">Silenciar / Activar sonido</button><button id="btnSonidoWeb">Sonido web: OFF</button><button id="btnTema">Modo claro/oscuro</button><button id="btnNotif">Activar notificaciones</button>
    <a class="boton" href="/exportar.csv">Exportar CSV</a><a class="boton" href="/bitacora.json">Descargar JSON</a><span class="umbrales" id="umbrales"></span>
</div>

<script>
const COLOR_NIVEL = {INFO:"TENUE", AVISO:"AMBAR", ALERTA:"ROJO", FALLA:"MAGENTA"};
const COLORES = {BORDE:"#2b3643", TEXTO:"#e6edf3", TENUE:"#8b98a8", VERDE:"#3fb950", AMBAR:"#d29922", ROJO:"#f85149", MAGENTA:"#bc8cff", AZUL:"#58a6ff"};
/* LABORATORIO: todo numero del navegador llega desde config.py */
const FORMAS = {seno:"sine", cuadrada:"square", triangular:"triangle"};
let UMBRALES = {};
let WEB = {};
let SONIDOS = {};
let historial = {cpu:[], memoria:[], red:[], bateria:[]};
let ultimoDato = Date.now();
let audioCtx = null;
let ultimoEventoVisto = "";
let sonidoWeb = false;
let arrancado = false;

if (localStorage.getItem("tema") === "claro") document.body.classList.add("claro");

async function post(ruta, datos=null) { const r = await fetch(ruta, {method:"POST", body: datos ? JSON.stringify(datos) : null, headers: datos ? {"Content-Type":"application/json"} : {}}); return r.json(); }
function colorBarra(clave, lectura) { if (!lectura) return "BORDE"; const p = lectura.porcentaje; if (clave === "bateria") return lectura.valor <= UMBRALES.bateria ? "ROJO" : "VERDE"; if (p >= WEB.colorAlto) return "ROJO"; if (p >= WEB.colorMedio) return "AMBAR"; return "VERDE"; } // LABORATORIO
function fmt(v) { return typeof v === "number" ? v.toFixed(1) : v; }

function dibujarTarjetas(d) {
    const cont = document.getElementById("tarjetas"); cont.innerHTML = "";
    for (const clave of Object.keys(d.etiquetas)) {
        const lectura = d.lecturas[clave]; const color = colorBarra(clave, lectura);
        const tarjeta = document.createElement("div"); tarjeta.className = "tarjeta" + ((color === "ROJO") ? " alerta" : "");
        tarjeta.innerHTML = `<h2>${d.etiquetas[clave]}</h2><div class="valor">${lectura ? lectura.valor + " " + lectura.unidad : " --"}</div><div class="barra"><div style="width:${lectura ? Math.max(0, Math.min(100, lectura.porcentaje)) : 0}%;background:${COLORES[color]}"></div></div><div class="detalle">${lectura ? lectura.detalle : "sensor no disponible"}</div>`;
        cont.appendChild(tarjeta);
    }
}
function dibujarProcesos(d) { const tbody = document.getElementById("procesos"); tbody.innerHTML = ""; const lectura = d.lecturas.procesos; if (!lectura || !lectura.top) return; for (const p of lectura.top) tbody.innerHTML += `<tr><td>${p.pid}</td><td>${p.nombre}</td><td>${p.cpu.toFixed(1)}%</td><td>${p.ram.toFixed(1)}%</td></tr>`; }
function dibujarEventos(d) { const lista = document.getElementById("bitacora"); const nivel = document.getElementById("filtroNivel").value; const busca = document.getElementById("buscarEvento").value.toLowerCase(); lista.innerHTML = ""; for (const e of d.eventos) { if (nivel !== "TODOS" && e.nivel !== nivel) continue; const linea = `${e.hora}  [${e.nivel.padEnd(6)}] ${e.mensaje}`; if (busca && !linea.toLowerCase().includes(busca)) continue; const li = document.createElement("li"); li.textContent = linea; li.style.color = COLORES[COLOR_NIVEL[e.nivel] || "TEXTO"]; lista.appendChild(li); } lista.scrollTop = lista.scrollHeight; }
function dibujarEstadisticas(d) { const tbody = document.getElementById("estadisticas"); tbody.innerHTML = ""; const metricas = d.resumen.metricas || {}; for (const k of Object.keys(metricas)) { const m = metricas[k]; tbody.innerHTML += `<tr><td>${k}</td><td>${m.n}</td><td>${m.min}</td><td>${m.max}</td><td>${m.prom}</td></tr>`; } }
function dibujarConteo(d) { const cont = document.getElementById("contador"); cont.innerHTML = ""; for (const n of ["INFO","AVISO","ALERTA","FALLA"]) cont.innerHTML += `<div><strong>${d.conteo_eventos[n] || 0}</strong>${n}</div>`; }
function alimentarHistorial(d) { for (const k of Object.keys(historial)) { const lectura = d.lecturas[k]; if (lectura) { historial[k].push(Number(lectura.valor)); if (historial[k].length > WEB.historial) historial[k].shift(); } } } // LABORATORIO
function dibujarGrafica() { const c = document.getElementById("grafica"), ctx = c.getContext("2d"), w = c.width, h = c.height; ctx.clearRect(0,0,w,h); ctx.strokeStyle = COLORES.BORDE; for (let y=0; y<=100; y+=25) { const py = h - y/100*h; ctx.beginPath(); ctx.moveTo(0, py); ctx.lineTo(w, py); ctx.stroke(); } const series = {cpu:COLORES.ROJO, memoria:COLORES.AMBAR, red:COLORES.AZUL, bateria:COLORES.VERDE}; for (const k of Object.keys(series)) { const vals = historial[k]; if (vals.length < 2) continue; ctx.strokeStyle = series[k]; ctx.beginPath(); vals.forEach((v,i) => { const x = i * (w / (WEB.historial - 1)); const y = h - Math.max(0, Math.min(100, v))/100*h; if (i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y); }); ctx.stroke(); } } // LABORATORIO
function cargarConfig(d) { for (const inp of document.querySelectorAll("[data-config]")) if (!inp.dataset.cargado) { inp.value = d.configuracion[inp.dataset.config]; inp.dataset.cargado = "1"; } }
/* LABORATORIO: bloque nuevo - sintesis de alertas con los patrones de config.py */
function contextoAudio() { try { if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)(); return audioCtx; } catch(e) { return null; } }
function pintarBotonSonido() { const b = document.getElementById("btnSonidoWeb"); if (b) b.textContent = sonidoWeb ? "Sonido web: ON" : "Sonido web: OFF"; }
function tocarPatron(nombre) {
    const patron = SONIDOS.patrones[nombre];
    const ctx = contextoAudio();
    if (!patron || !ctx) return;
    let t = ctx.currentTime + (SONIDOS.retraso || 0);
    for (const nota of patron) {
        const dur = nota.seg;
        const vol = (nota.vol === undefined ? SONIDOS.volumen : nota.vol * SONIDOS.volumen);
        if (nota.tipo === "silencio") { t += dur; continue; }
        const g = ctx.createGain(); g.gain.value = vol; g.connect(ctx.destination);
        if (nota.tipo === "ruido") {
            const largo = Math.floor(dur * ctx.sampleRate);
            if (!largo) { t += dur; continue; }
            const buffer = ctx.createBuffer(1, largo, ctx.sampleRate);
            const crudo = buffer.getChannelData(0);
            for (let i = 0; i < largo; i++) crudo[i] = Math.random() * 2 - 1;
            const fuente = ctx.createBufferSource(); fuente.buffer = buffer; fuente.connect(g); fuente.start(t);
        } else {
            const osc = ctx.createOscillator();
            osc.type = FORMAS[nota.tipo] || "square";
            if (nota.tipo === "barrido") { osc.frequency.setValueAtTime(nota.hz_ini, t); osc.frequency.exponentialRampToValueAtTime(nota.hz_fin, t + dur); }
            else osc.frequency.setValueAtTime(nota.hz, t);
            osc.connect(g); osc.start(t); osc.stop(t + dur);
        }
        t += dur;
    }
}
function notificar(e) { if (Notification.permission === "granted") new Notification("Alerta del nodo", {body: e.mensaje}); }
function revisarAlertas(d) {
    if (!d.eventos.length) return;
    const e = d.eventos[d.eventos.length - 1];
    const clave = e.hora + "|" + e.nivel + "|" + e.origen + "|" + e.mensaje;
    const primera = ultimoEventoVisto === "";
    ultimoEventoVisto = clave;
    if (primera) return;
    if (sonidoWeb && SONIDOS.eventos[e.origen]) tocarPatron(SONIDOS.eventos[e.origen]);
    if (["ALERTA", "FALLA"].includes(e.nivel)) notificar(e);
}
function actualizarOnline(ok=true) { const e = document.getElementById("online"); e.textContent = ok ? "online" : "sin conexion"; e.style.color = ok ? COLORES.VERDE : COLORES.ROJO; }
function actualizar(d) { /* LABORATORIO: primero la configuracion que viene de config.py */
    WEB = d.web; SONIDOS = d.sonidos;
    if (!arrancado) { arrancado = true; sonidoWeb = SONIDOS.navegador; pintarBotonSonido(); setInterval(refrescar, WEB.refresco); setInterval(function(){ if (Date.now() - ultimoDato > WEB.offline) actualizarOnline(false); }, WEB.refresco); }
    ultimoDato = Date.now(); actualizarOnline(true); document.getElementById("nodo").textContent = d.nodo; document.getElementById("ubicacion").textContent = "  ·  " + d.ubicacion; document.getElementById("reloj").textContent = d.hora; const estado = document.getElementById("estado"); estado.textContent = d.pausado ? "PAUSADO" : "MONITOREANDO"; estado.style.color = d.pausado ? COLORES.AMBAR : COLORES.VERDE; UMBRALES.bateria = d.umbrales.bateria; document.getElementById("umbrales").textContent = `umbrales: CPU ${d.umbrales.CPU}% · RAM ${d.umbrales.RAM}% · disco ${d.umbrales.disco}% · red ${d.umbrales.red} KB/s`; cargarConfig(d); dibujarTarjetas(d); dibujarProcesos(d); dibujarEventos(d); dibujarEstadisticas(d); dibujarConteo(d); alimentarHistorial(d); dibujarGrafica(); revisarAlertas(d);
    /* LABORATORIO: insignia del enlace (flanco) y estado del reproductor */
    const rojo = document.getElementById("conexionRed");
    if (d.conexion.conectado === null) { rojo.textContent = "red sin datos"; rojo.style.color = COLORES.TENUE; }
    else if (d.conexion.conectado) { rojo.textContent = "red conectada" + (d.conexion.interfaces.length ? " · " + d.conexion.interfaces.join(", ") : ""); rojo.style.color = COLORES.VERDE; }
    else { rojo.textContent = "red SIN CONEXION" + (d.conexion.caida !== null ? " · " + d.conexion.caida + " s" : ""); rojo.style.color = COLORES.ROJO; }
    const nota = document.getElementById("sonidoEstado");
    nota.textContent = SONIDOS.activo ? ("♪ sonido · cola " + SONIDOS.cola + " · " + (SONIDOS.ultimo || "nada")) : "♪ silencio";
    nota.style.color = SONIDOS.activo ? COLORES.AZUL : COLORES.TENUE;
}
document.getElementById("btnPausa").onclick = () => post("/pausa").then(actualizar);
document.getElementById("btnReporte").onclick = () => post("/reporte").then(actualizar);
document.getElementById("btnLimpiar").onclick = () => post("/limpiar").then(actualizar);
document.getElementById("btnTema").onclick = () => { document.body.classList.toggle("claro"); localStorage.setItem("tema", document.body.classList.contains("claro") ? "claro" : "oscuro"); };
document.getElementById("btnNotif").onclick = () => Notification.requestPermission();
/* LABORATORIO: control del reproductor local (gana el servidor) y sonido web */
document.getElementById("btnSilencio").onclick = () => post("/sonidos").then(actualizar);
document.getElementById("btnSonidoWeb").onclick = () => { sonidoWeb = !sonidoWeb; pintarBotonSonido(); };
document.getElementById("btnConfig").onclick = () => { const datos = {}; for (const i of document.querySelectorAll("[data-config]")) datos[i.dataset.config] = i.value; post("/config", datos).then(actualizar); };
document.getElementById("filtroNivel").onchange = () => refrescar(); document.getElementById("buscarEvento").oninput = () => refrescar();
async function refrescar() { try { const r = await fetch("/datos"); actualizar(await r.json()); } catch(e) { actualizarOnline(false); } }
/* LABORATORIO: los intervalos se crean recien al llegar la configuracion */
refrescar();
</script>
</body>
</html>
"""
