const ETIQUETAS = {
  analitico: "Analítico",
  social: "Social",
  creativo: "Creativo",
  ciencias_vida: "Ciencias de la vida",
  seguridad_laboral: "Seguridad laboral",
};

const PREGUNTAS_ESCALA = {
  analitico: "¿Cuánto te interesan los números y resolver problemas?",
  social: "¿Cuánto te gusta trabajar con otras personas?",
  creativo: "¿Cuánto te gusta crear o diseñar?",
  ciencias_vida: "¿Cuánto te interesan la biología y la salud?",
  seguridad_laboral: "¿Cuánto valorás la estabilidad laboral?",
};

const mensajes = document.getElementById("mensajes");
const form = document.getElementById("formulario");
const entrada = document.getElementById("entrada");
const enviar = document.getElementById("enviar");
const estadoPerfil = document.getElementById("estado-perfil");
const barras = document.getElementById("barras");
const carreras = document.getElementById("carreras");
const carrerasCard = document.getElementById("carreras-card");
const carrerasArea = document.getElementById("carreras-area");
const reglas = document.getElementById("reglas");
const detalleReglas = document.getElementById("detalle-reglas");
const hechosNodo = document.getElementById("hechos");
const progreso = document.getElementById("progreso");
const sheetEl = document.getElementById("dictamen");
const abrirDictamen = document.getElementById("abrir-dictamen");
const cerrarDictamen = document.getElementById("cerrar-dictamen");
const handle = document.getElementById("sheet-handle");
const scrim = document.getElementById("sheet-scrim");

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
// Pausa mínima antes de mostrar la respuesta: parece que Rumbo piensa.
const MINIMO_PENSANDO_MS = 1000;
let sesionId = null;
let esperando = false;

function vibrar(patron) {
  if (navigator.vibrate) navigator.vibrate(patron);
}

const temaToggle = document.getElementById("tema-toggle");
const mqOscuro = window.matchMedia("(prefers-color-scheme: dark)");

function aplicarTema(oscuro, animar) {
  const raiz = document.documentElement;
  if (animar) {
    // Cross-fade de colores: no es movimiento vestibular, aplica siempre
    // (es justo lo que Apple pide para cambios de tema con reduced-motion).
    raiz.classList.add("transicion-tema");
    void raiz.offsetHeight; // reflow: la transición queda activa antes del cambio
    setTimeout(() => raiz.classList.remove("transicion-tema"), 380);
  }
  raiz.classList.toggle("tema-oscuro", oscuro);
  temaToggle.setAttribute("aria-pressed", String(oscuro));
  temaToggle.setAttribute("aria-label", oscuro ? "Cambiar a modo claro" : "Cambiar a modo oscuro");
  document.querySelector('meta[name="theme-color"]').setAttribute("content", oscuro ? "#000000" : "#f5f5f7");
}

temaToggle.addEventListener("click", () => {
  const oscuro = !document.documentElement.classList.contains("tema-oscuro");
  try { localStorage.setItem("tema", oscuro ? "oscuro" : "claro"); } catch (e) { /* sin persistencia */ }
  vibrar(6);
  aplicarTema(oscuro, true);
});

mqOscuro.addEventListener("change", (evento) => {
  let guardado = null;
  try { guardado = localStorage.getItem("tema"); } catch (e) { /* sin persistencia */ }
  if (!guardado) aplicarTema(evento.matches, true);
});

aplicarTema(document.documentElement.classList.contains("tema-oscuro"), false);
let escalaActiva = null;

function escritorio() {
  return window.matchMedia("(min-width: 900px)").matches;
}

function rubberband(overshoot, dimension, constant = 0.55) {
  return (overshoot * dimension * constant) / (dimension + constant * Math.abs(overshoot));
}

function project(velocity, decelerationRate = 0.998) {
  return (velocity / 1000) * decelerationRate / (1 - decelerationRate);
}

function springStep(current, target, velocity, dt, damping, response) {
  const omega = (2 * Math.PI) / response;
  const acc = -(omega * omega) * (current - target) - 2 * damping * omega * velocity;
  const v = velocity + acc * dt;
  return { current: current + v * dt, velocity: v };
}

function animateSpring(read, write, target, opts = {}) {
  const damping = opts.damping ?? 1;
  const response = opts.response ?? 0.35;
  const umbral = opts.umbral ?? 0.4;
  let velocity = opts.velocity ?? 0;
  return new Promise((resolve) => {
    if (reduceMotion.matches) {
      write(target);
      resolve();
      return;
    }
    let current = read();
    let last = performance.now();
    const tick = (now) => {
      const dt = Math.min(0.032, (now - last) / 1000);
      last = now;
      const next = springStep(current, target, velocity, dt, damping, response);
      current = next.current;
      velocity = next.velocity;
      write(current);
      if (Math.abs(current - target) < umbral && Math.abs(velocity) < umbral * 20) {
        write(target);
        resolve();
        return;
      }
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });
}

const sheet = {
  y: 0,
  v: 0,
  detente: "cerrada",
  arrastre: null,
  raf: 0,
  historia: [],
};

function alturaSheet() {
  return Math.max(sheetEl.getBoundingClientRect().height, window.innerHeight * 0.92);
}

function distanciaCerrada() {
  return alturaSheet() + 24;
}

function distanciaMedia() {
  return Math.round(alturaSheet() * 0.52);
}

function yDeDetente(detente) {
  if (detente === "abierta") return 0;
  if (detente === "media") return distanciaMedia();
  return distanciaCerrada();
}

function inicioSheet() {
  return parseFloat(window.getComputedStyle(sheetEl).top);
}

function aplicarY(y) {
  sheet.y = y;
  sheetEl.style.transform = `translate3d(0, ${y}px, 0)`;
}

function detenerSpring() {
  if (sheet.raf) cancelAnimationFrame(sheet.raf);
  sheet.raf = 0;
}

function springSheet(target, velocity) {
  detenerSpring();
  if (escritorio() || reduceMotion.matches) {
    aplicarY(0);
    return;
  }
  let current = sheet.y;
  let v = velocity ?? sheet.v;
  const damping = Math.abs(velocity || 0) > 700 ? 0.82 : 1;
  const response = 0.32;
  let last = performance.now();
  const tick = (now) => {
    const dt = Math.min(0.032, (now - last) / 1000);
    last = now;
    const next = springStep(current, target, v, dt, damping, response);
    current = next.current;
    v = next.velocity;
    sheet.v = v;
    aplicarY(current);
    if (Math.abs(current - target) < 0.5 && Math.abs(v) < 10) {
      aplicarY(target);
      sheet.v = 0;
      sheet.raf = 0;
      return;
    }
    sheet.raf = requestAnimationFrame(tick);
  };
  sheet.raf = requestAnimationFrame(tick);
}

function estadoSheet(detente) {
  const visible = escritorio() || detente !== "cerrada";
  sheetEl.inert = !visible;
  sheetEl.setAttribute("aria-hidden", String(!visible));
  sheetEl.classList.toggle("is-closed", !visible);
  abrirDictamen.setAttribute("aria-expanded", String(detente !== "cerrada"));
  scrim.classList.toggle("visible", detente === "abierta" && !escritorio());
}

function irADetente(detente, velocity) {
  sheet.detente = detente;
  estadoSheet(detente);
  springSheet(yDeDetente(detente), velocity);
}

function abrirSheet(enfocar) {
  irADetente("media", sheet.v);
  if (enfocar && !escritorio()) sheetEl.focus();
}

function cerrarSheet() {
  irADetente("cerrada", sheet.v);
  if (!escritorio()) abrirDictamen.focus();
}

function iniciarSheet() {
  const colocar = () => {
    if (escritorio()) {
      aplicarY(0);
      sheet.detente = "abierta";
      estadoSheet("abierta");
      return;
    }
    aplicarY(yDeDetente(sheet.detente));
    estadoSheet(sheet.detente);
  };
  colocar();
  requestAnimationFrame(colocar);
}

function onPointerDown(evento) {
  if (escritorio()) return;
  detenerSpring();
  handle.setPointerCapture(evento.pointerId);
  const top = sheetEl.getBoundingClientRect().top;
  sheet.arrastre = {
    offset: evento.clientY - top,
  };
  sheet.historia = [{ y: evento.clientY, t: evento.timeStamp }];
}

function onPointerMove(evento) {
  if (!sheet.arrastre) return;
  const abiertoTop = inicioSheet();
  let top = evento.clientY - sheet.arrastre.offset;
  const cerradoTop = abiertoTop + distanciaCerrada();
  if (top < abiertoTop) {
    top = abiertoTop - rubberband(abiertoTop - top, window.innerHeight);
  } else if (top > cerradoTop) {
    top = cerradoTop + rubberband(top - cerradoTop, window.innerHeight);
  }
  aplicarY(top - abiertoTop);
  const hist = sheet.historia;
  hist.push({ y: evento.clientY, t: evento.timeStamp });
  if (hist.length > 5) hist.shift();
}

function velocidadRelease() {
  const hist = sheet.historia;
  if (hist.length < 2) return 0;
  const a = hist[0];
  const b = hist[hist.length - 1];
  const dt = Math.max(1, b.t - a.t);
  return ((b.y - a.y) / dt) * 1000;
}

function onPointerUp() {
  if (!sheet.arrastre) return;
  sheet.arrastre = null;
  const hist = sheet.historia;
  const primero = hist[0];
  const ultimo = hist[hist.length - 1];
  const v = velocidadRelease();
  sheet.v = v;

  // Tap en el grabber: cicla entre detent medio y completo
  if (Math.abs(ultimo.y - primero.y) < 8 && ultimo.t - primero.t < 350) {
    vibrar(6);
    irADetente(sheet.detente === "abierta" ? "media" : "abierta", 0);
    return;
  }

  const proyectado = sheet.y + project(v);
  const puntos = [
    { detente: "abierta", y: 0 },
    { detente: "media", y: distanciaMedia() },
    { detente: "cerrada", y: distanciaCerrada() },
  ];
  let destino;
  if (Math.abs(v) > 650) {
    // Con momentum manda la dirección del gesto: un detent hacia arriba o abajo
    const actual = puntos.findIndex((p) => p.detente === sheet.detente);
    const paso = v < 0 ? -1 : 1;
    destino = puntos[Math.min(puntos.length - 1, Math.max(0, actual + paso))];
  } else {
    destino = puntos.reduce((mejor, p) =>
      Math.abs(p.y - proyectado) < Math.abs(mejor.y - proyectado) ? p : mejor
    );
  }
  vibrar(8);
  irADetente(destino.detente, v);
  if (destino.detente === "cerrada") abrirDictamen.focus();
}

handle.addEventListener("pointerdown", onPointerDown);
handle.addEventListener("pointermove", onPointerMove);
handle.addEventListener("pointerup", onPointerUp);
handle.addEventListener("pointercancel", onPointerUp);
abrirDictamen.addEventListener("click", () => abrirSheet(true));
cerrarDictamen.addEventListener("click", cerrarSheet);
scrim.addEventListener("click", cerrarSheet);
document.addEventListener("keydown", (evento) => {
  if (evento.key === "Escape" && sheet.detente !== "cerrada" && !escritorio()) cerrarSheet();
  if (evento.key === "Tab" && sheet.detente === "abierta" && !escritorio()) {
    const focables = [...sheetEl.querySelectorAll("button, input, a[href], [tabindex]:not([tabindex='-1'])")]
      .filter((elemento) => !elemento.disabled && elemento.getClientRects().length);
    if (!focables.length) return;
    const primero = focables[0];
    const ultimo = focables[focables.length - 1];
    if (evento.shiftKey && (document.activeElement === primero || !sheetEl.contains(document.activeElement))) {
      evento.preventDefault();
      ultimo.focus();
    } else if (!evento.shiftKey && (document.activeElement === ultimo || !sheetEl.contains(document.activeElement))) {
      evento.preventDefault();
      primero.focus();
    }
  }
});
window.addEventListener("resize", () => {
  detenerSpring();
  if (escritorio()) {
    aplicarY(0);
    sheet.detente = "abierta";
  } else {
    aplicarY(yDeDetente(sheet.detente));
  }
  estadoSheet(sheet.detente);
});

function pressable(boton) {
  const down = () => boton.classList.add("pressed");
  const up = () => boton.classList.remove("pressed");
  boton.addEventListener("pointerdown", down);
  boton.addEventListener("pointerup", up);
  boton.addEventListener("pointercancel", up);
  boton.addEventListener("pointerleave", up);
}

[enviar, abrirDictamen, cerrarDictamen, temaToggle].forEach(pressable);

entrada.addEventListener("input", () => {
  enviar.disabled = esperando || !sesionId || entrada.value.trim() === "";
});

function inflar(item, desde, damping) {
  let s = desde;
  item.style.transform = `scale(${s})`;
  return animateSpring(() => s, (val) => {
    s = val;
    item.style.transform = `scale(${val})`;
  }, 1, { response: 0.42, damping, umbral: 0.002 });
}

function viajar(item, origen) {
  const inicial = item.getBoundingClientRect();
  const desde = origen.getBoundingClientRect();
  const centroX = origen === entrada
    ? desde.left + Math.min(inicial.width, desde.width) / 2
    : desde.left + desde.width / 2;
  const centroY = desde.top + desde.height / 2;
  let x = centroX + inicial.width / 2 - inicial.right;
  let y = centroY + inicial.height / 2 - inicial.bottom;

  const globo = document.createElement("div");
  globo.className = "globo-viajero";
  globo.textContent = item.textContent;
  globo.style.width = `${inicial.width}px`;
  const pintar = () => {
    const r = item.getBoundingClientRect();
    globo.style.left = `${r.left}px`;
    globo.style.top = `${r.top}px`;
    globo.style.transform = `translate3d(${x}px, ${y}px, 0)`;
  };
  pintar();
  document.body.appendChild(globo);

  return Promise.all([
    animateSpring(() => x, (val) => { x = val; pintar(); }, 0, { response: 0.4, damping: 1 }),
    animateSpring(() => y, (val) => { y = val; pintar(); }, 0, { response: 0.32, damping: 1 }),
  ]).then(() => {
    globo.remove();
    item.style.opacity = "1";
  });
}

function agregar(texto, quien, origen) {
  const item = document.createElement("li");
  item.className = quien;
  item.textContent = texto;
  mensajes.appendChild(item);
  mensajes.scrollTop = mensajes.scrollHeight;
  if (reduceMotion.matches) {
    item.llegada = Promise.resolve();
    return item;
  }
  if (origen) {
    item.style.opacity = "0";
    item.llegada = viajar(item, origen);
    return item;
  }
  let o = 0;
  item.style.opacity = "0";
  animateSpring(() => o, (val) => {
    o = val;
    item.style.opacity = String(val);
  }, 1, { response: 0.2, damping: 1, umbral: 0.01 });
  item.llegada = inflar(item, 0.3, 0.55);
  return item;
}

function mostrarEscala(clave) {
  if (escalaActiva) {
    if (!escalaActiva.dataset.seleccionado) escalaActiva.remove();
    escalaActiva = null;
  }
  entrada.placeholder = clave
    ? "Elegí un número arriba o escribilo acá…"
    : "Contame qué te gusta o preguntame algo…";
  if (!clave || !PREGUNTAS_ESCALA[clave]) return;

  const item = agregar("", "bot escala-card");
  const titulo = document.createElement("p");
  titulo.className = "escala-titulo";
  titulo.textContent = PREGUNTAS_ESCALA[clave];
  item.appendChild(titulo);

  const opciones = document.createElement("div");
  opciones.className = "escala-opciones";
  opciones.setAttribute("role", "group");
  opciones.setAttribute("aria-label", `Elegí del 1 al 10: ${ETIQUETAS[clave]}`);
  for (let valor = 1; valor <= 10; valor += 1) {
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = "escala-opcion";
    boton.textContent = String(valor);
    boton.setAttribute("aria-label", `${valor} de 10 para ${ETIQUETAS[clave]}`);
    boton.setAttribute("aria-pressed", "false");
    boton.addEventListener("click", () => enviarValor(valor, item));
    opciones.appendChild(boton);
  }
  item.appendChild(opciones);

  const extremos = document.createElement("div");
  extremos.className = "escala-extremos";
  extremos.innerHTML = "<span>Poco</span><span>Mucho</span>";
  item.appendChild(extremos);
  escalaActiva = item;
  mensajes.scrollTop = mensajes.scrollHeight;
}

function agregarEscribiendo() {
  const item = agregar("", "bot typing");
  item.innerHTML = `
    <svg class="spinner" viewBox="0 0 24 24" role="status" aria-label="Rumbo está escribiendo">
      <circle cx="12" cy="12" r="9" fill="none" />
    </svg>`;
  return item;
}

function llenarCarreras(lista, nombres) {
  lista.replaceChildren(...nombres.map((nombre) => {
    const fila = document.createElement("li");
    fila.textContent = nombre;
    return fila;
  }));
}

function popCarreras() {
  let o = 0;
  carrerasCard.style.opacity = "0";
  animateSpring(() => o, (val) => {
    o = val;
    carrerasCard.style.opacity = String(val);
  }, 1, { response: 0.25, damping: 1, umbral: 0.01 });
  inflar(carrerasCard, 0.6, 0.5);
}

function pintarHechos(hechos) {
  const claves = Object.keys(ETIQUETAS);
  const listos = Object.keys(hechos || {}).length;
  progreso.textContent = listos
    ? `Ya charlamos sobre ${listos} de ${claves.length} temas`
    : "Vamos a ir armando este mapa juntos";
  hechosNodo.innerHTML = "";
  claves.forEach((clave) => {
    if (!hechos || !(clave in hechos)) return;
    const chip = document.createElement("span");
    chip.className = "chip on";
    chip.textContent = `${ETIQUETAS[clave]} ${Number(hechos[clave]).toFixed(0)}`;
    hechosNodo.appendChild(chip);
  });
}

function pintarDictamen(dictamen, hechos) {
  pintarHechos(hechos);
  detalleReglas.hidden = !dictamen;
  const carrerasNuevas = Boolean(dictamen) && carrerasCard.hidden;
  carrerasCard.hidden = !dictamen;
  if (!dictamen) {
    estadoPerfil.textContent = "Cuando terminemos de charlar, vas a ver algunas opciones para explorar acá.";
    barras.innerHTML = "";
    carreras.replaceChildren();
    reglas.innerHTML = '<li class="vacio">Todavía no hay resultado.</li>';
    return;
  }

  estadoPerfil.textContent = `${dictamen.area_principal.etiqueta} aparece como la afinidad más alta. Tomalo como una pista para investigar, no como una decisión cerrada.`;
  barras.innerHTML = "";
  dictamen.afinidades.forEach((item) => {
    const fila = document.createElement("div");
    const principal = item.area === dictamen.area_principal.area;
    fila.className = principal ? "barra principal" : "barra";
    const objetivo = Math.max(0.04, Math.min(1, item.valor / 10));
    fila.innerHTML = `
      <span>${item.etiqueta}<small>${item.descripcion || ""}</small></span>
      <span class="pista"><span class="fill"></span></span>
      <span>${item.valor.toFixed(1)}</span>
    `;
    barras.appendChild(fila);
    const fill = fila.querySelector(".fill");
    let escala = 0;
    fill.style.transform = "scaleX(0)";
    animateSpring(() => escala, (val) => {
      escala = val;
      fill.style.transform = `scaleX(${val})`;
    }, objetivo, { response: 0.45, damping: 1, umbral: 0.002 });
  });
  carrerasArea.textContent = dictamen.area_principal.etiqueta;
  llenarCarreras(carreras, dictamen.area_principal.carreras);
  if (carrerasNuevas) popCarreras();
  reglas.innerHTML = "";
  dictamen.reglas_disparadas.forEach((regla) => {
    const item = document.createElement("li");
    item.innerHTML = `<span class="id">${regla.id}</span>${regla.enunciado}
      <div class="grado">grado ${regla.grado.toFixed(2)}</div>`;
    reglas.appendChild(item);
  });
  if (!escritorio()) abrirSheet();
}

async function llamar(url, cuerpo, timeoutMs = 110000) {
  const control = new AbortController();
  const temporizador = setTimeout(() => control.abort(), timeoutMs);
  try {
    const respuesta = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cuerpo || {}),
      signal: control.signal,
    });
    if (!respuesta.ok) throw new Error("backend");
    return respuesta.json();
  } finally {
    clearTimeout(temporizador);
  }
}

async function abrir() {
  const turno = await llamar("/api/sesion", {});
  sesionId = turno.sesion_id;
  agregar(turno.respuesta, "bot");
  mostrarEscala(turno.escala_pendiente);
  pintarDictamen(turno.dictamen, turno.hechos);
  enviar.disabled = entrada.value.trim() === "";
  if (escritorio()) entrada.focus();
}

async function pedirTurnoClasico(cuerpo, timeoutMs) {
  return llamar("/api/chat", cuerpo, timeoutMs);
}

async function leerStreamTurno(cuerpo, alTurno, timeoutMs = 110000) {
  const control = new AbortController();
  const temporizador = setTimeout(() => control.abort(), timeoutMs);
  let eventos = 0;
  const consumir = (turno, esFinal) => {
    eventos += 1;
    alTurno(turno, esFinal);
  };
  try {
    let respuesta;
    try {
      respuesta = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify(cuerpo || {}),
        signal: control.signal,
      });
    } catch (error) {
      if (error && error.name === "AbortError") throw error;
      consumir(await pedirTurnoClasico(cuerpo, timeoutMs), true);
      return;
    }
    if (!respuesta.ok || !respuesta.body) {
      consumir(await pedirTurnoClasico(cuerpo, timeoutMs), true);
      return;
    }
    const lector = respuesta.body.getReader();
    const decodificador = new TextDecoder();
    let buffer = "";
    const procesar = (trozo) => {
      buffer += trozo;
      let fin;
      while ((fin = buffer.indexOf("\n\n")) !== -1) {
        const bloque = buffer.slice(0, fin);
        buffer = buffer.slice(fin + 2);
        for (const linea of bloque.split("\n")) {
          if (!linea.startsWith("data:")) continue;
          const evento = JSON.parse(linea.slice(5).trim());
          if (evento.tipo === "guia" || evento.tipo === "final") {
            consumir(evento.turno, evento.tipo === "final");
          } else if (evento.tipo === "error") {
            throw new Error("backend");
          }
        }
      }
    };
    for (;;) {
      const { done, value } = await lector.read();
      if (value) procesar(decodificador.decode(value, { stream: !done }));
      if (done) break;
    }
    if (!eventos) consumir(await pedirTurnoClasico(cuerpo, timeoutMs), true);
  } catch (error) {
    // Si la guía ya se mostró, queda como respuesta válida: no reintentamos
    // (reenviar duplicaría el turno en el servidor) y no mostramos error.
    if (eventos) return;
    throw error;
  } finally {
    clearTimeout(temporizador);
  }
}

async function enviarTurno(cuerpo, textoVisible, origen, alFallar) {
  if (esperando || !sesionId) return;
  esperando = true;
  enviar.disabled = true;
  if (escalaActiva) {
    escalaActiva.querySelectorAll("button").forEach((boton) => { boton.disabled = true; });
  }
  const burbuja = agregar(textoVisible, "user", origen);
  vibrar(10);
  const inicio = performance.now();
  let escribiendo = null;
  let burbujaRespuesta = null;
  let primerTurno = null;
  let pintado = null;
  const alTurno = (turno, esFinal) => {
    sesionId = turno.sesion_id;
    if (!primerTurno) {
      primerTurno = turno;
      const espera = MINIMO_PENSANDO_MS - (performance.now() - inicio);
      pintado = new Promise((resolver) => {
        setTimeout(() => {
          if (escribiendo) {
            escribiendo.remove();
            escribiendo = null;
          }
          burbujaRespuesta = agregar(primerTurno.respuesta, "bot");
          mostrarEscala(primerTurno.escala_pendiente);
          pintarDictamen(primerTurno.dictamen, primerTurno.hechos);
          resolver();
        }, Math.max(0, espera));
      });
    } else if (!burbujaRespuesta) {
      primerTurno = turno;
    } else if (esFinal && turno.respuesta !== burbujaRespuesta.textContent) {
      burbujaRespuesta.textContent = turno.respuesta;
      mensajes.scrollTop = mensajes.scrollHeight;
    }
  };
  const pedido = leerStreamTurno({ sesion_id: sesionId, ...cuerpo }, alTurno);
  pedido.catch(() => {});
  await burbuja.llegada;
  if (!burbujaRespuesta) escribiendo = agregarEscribiendo();
  try {
    await pedido;
    if (pintado) await pintado;
    if (!burbujaRespuesta) throw new Error("vacio");
  } catch (error) {
    if (escribiendo) escribiendo.remove();
    if (!burbujaRespuesta) {
      burbuja.remove();
      if (alFallar) alFallar();
      if (error && error.name === "AbortError") {
        agregar("Me está tomando más tiempo del esperado. Podés probar de nuevo.", "bot");
      } else {
        agregar("Se cortó la conexión. Podés probar de nuevo.", "bot");
      }
    }
  } finally {
    esperando = false;
    enviar.disabled = entrada.value.trim() === "";
    if (escalaActiva && !escalaActiva.dataset.seleccionado) {
      escalaActiva.querySelectorAll("button").forEach((boton) => { boton.disabled = false; });
    }
  }
}

async function enviarValor(valor, item) {
  if (esperando || escalaActiva !== item) return;
  item.dataset.seleccionado = "true";
  item.querySelectorAll("button").forEach((boton) => {
    boton.disabled = true;
    const seleccionado = Number(boton.textContent) === valor;
    boton.classList.toggle("selected", seleccionado);
    boton.setAttribute("aria-pressed", String(seleccionado));
  });
  await enviarTurno({ valor }, `${valor}/10`, item.querySelector(".escala-opcion.selected"), () => {
    delete item.dataset.seleccionado;
    item.querySelectorAll("button").forEach((boton) => {
      boton.disabled = false;
      boton.classList.remove("selected");
      boton.setAttribute("aria-pressed", "false");
    });
  });
}

form.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const texto = entrada.value.trim();
  if (!texto || esperando || !sesionId) return;
  entrada.value = "";
  await enviarTurno({ mensaje: texto }, texto, entrada, () => {
    if (!entrada.value.trim()) entrada.value = texto;
  });
});

iniciarSheet();
pintarHechos({});
abrir().catch(() => {
  agregar("No pude abrir la charla. Probá recargar la página en un momento.", "bot");
});
