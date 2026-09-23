const ETIQUETAS = {
  analitico: "Analítico",
  social: "Social",
  creativo: "Creativo",
  ciencias_vida: "Ciencias de la vida",
  seguridad_laboral: "Seguridad laboral",
};

const mensajes = document.getElementById("mensajes");
const form = document.getElementById("formulario");
const entrada = document.getElementById("entrada");
const enviar = document.getElementById("enviar");
const estadoPerfil = document.getElementById("estado-perfil");
const barras = document.getElementById("barras");
const carreras = document.getElementById("carreras");
const reglas = document.getElementById("reglas");
const hechosNodo = document.getElementById("hechos");
const progreso = document.getElementById("progreso");
const sheetEl = document.getElementById("dictamen");
const abrirDictamen = document.getElementById("abrir-dictamen");
const cerrarDictamen = document.getElementById("cerrar-dictamen");
const handle = document.getElementById("sheet-handle");

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
let sesionId = null;

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
      if (Math.abs(current - target) < 0.4 && Math.abs(velocity) < 8) {
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
  abierta: false,
  arrastre: null,
  raf: 0,
  historia: [],
};

function distanciaCerrada() {
  return Math.max(sheetEl.getBoundingClientRect().height, window.innerHeight * 0.92) + 24;
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
    sheet.abierta = target === 0;
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

function abrirSheet() {
  sheet.abierta = true;
  springSheet(0, sheet.v);
}

function cerrarSheet() {
  sheet.abierta = false;
  springSheet(distanciaCerrada(), sheet.v);
}

function iniciarSheet() {
  const colocar = () => {
    if (escritorio()) {
      aplicarY(0);
      sheet.abierta = true;
      return;
    }
    aplicarY(distanciaCerrada());
    sheet.abierta = false;
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
  const abiertoTop = window.innerHeight * 0.08;
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
  const v = velocidadRelease();
  sheet.v = v;
  const proyectado = sheet.y + project(v);
  const medio = distanciaCerrada() / 2;
  const cerrar = v > 650 || proyectado > medio;
  sheet.abierta = !cerrar;
  springSheet(cerrar ? distanciaCerrada() : 0, v);
}

handle.addEventListener("pointerdown", onPointerDown);
handle.addEventListener("pointermove", onPointerMove);
handle.addEventListener("pointerup", onPointerUp);
handle.addEventListener("pointercancel", onPointerUp);
abrirDictamen.addEventListener("click", abrirSheet);
cerrarDictamen.addEventListener("click", cerrarSheet);
window.addEventListener("resize", () => {
  if (escritorio()) aplicarY(0);
});

function pressable(boton) {
  const down = () => boton.classList.add("pressed");
  const up = () => boton.classList.remove("pressed");
  boton.addEventListener("pointerdown", down);
  boton.addEventListener("pointerup", up);
  boton.addEventListener("pointercancel", up);
  boton.addEventListener("pointerleave", up);
}

[enviar, abrirDictamen, cerrarDictamen].forEach(pressable);

entrada.addEventListener("input", () => {
  enviar.disabled = entrada.value.trim() === "";
});

function agregar(texto, quien) {
  const item = document.createElement("li");
  item.className = quien;
  item.textContent = texto;
  item.style.opacity = "0";
  item.style.transform = "translate3d(0, 10px, 0)";
  mensajes.appendChild(item);
  let y = 10;
  let o = 0;
  animateSpring(() => y, (val) => {
    y = val;
    item.style.transform = `translate3d(0, ${val}px, 0)`;
  }, 0, { response: 0.32, damping: 1 });
  animateSpring(() => o, (val) => {
    o = val;
    item.style.opacity = String(val);
  }, 1, { response: 0.3, damping: 1 });
  item.scrollIntoView({ block: "end", behavior: reduceMotion.matches ? "auto" : "smooth" });
}

function pintarHechos(hechos) {
  const claves = Object.keys(ETIQUETAS);
  const listos = Object.keys(hechos || {}).length;
  progreso.textContent = `${listos} de ${claves.length} hechos`;
  hechosNodo.innerHTML = "";
  claves.forEach((clave) => {
    const chip = document.createElement("span");
    const tiene = hechos && clave in hechos;
    chip.className = tiene ? "chip on" : "chip";
    chip.textContent = tiene
      ? `${ETIQUETAS[clave]} ${Number(hechos[clave]).toFixed(0)}`
      : ETIQUETAS[clave];
    hechosNodo.appendChild(chip);
  });
}

function pintarDictamen(dictamen, hechos) {
  pintarHechos(hechos);
  if (!dictamen) {
    estadoPerfil.textContent = "El SED corre cuando el perfil está completo.";
    barras.innerHTML = "";
    carreras.textContent = "";
    reglas.innerHTML = '<li class="vacio">Todavía no hay inferencia.</li>';
    return;
  }

  estadoPerfil.textContent = dictamen.resumen;
  barras.innerHTML = "";
  dictamen.afinidades.forEach((item) => {
    const fila = document.createElement("div");
    const principal = item.area === dictamen.area_principal.area;
    fila.className = principal ? "barra principal" : "barra";
    const objetivo = Math.max(0.04, Math.min(1, item.valor / 10));
    fila.innerHTML = `
      <span>${item.etiqueta}</span>
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
    }, objetivo, { response: 0.45, damping: 1 });
  });
  carreras.textContent = `Carreras ilustrativas: ${dictamen.area_principal.carreras.join(", ")}.`;
  reglas.innerHTML = "";
  dictamen.reglas_disparadas.forEach((regla) => {
    const item = document.createElement("li");
    item.innerHTML = `<span class="id">${regla.id}</span>${regla.enunciado}
      <div class="grado">grado ${regla.grado.toFixed(2)}</div>`;
    reglas.appendChild(item);
  });
  if (!escritorio()) abrirSheet();
}

async function llamar(url, cuerpo) {
  const respuesta = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo || {}),
  });
  if (!respuesta.ok) throw new Error("backend");
  return respuesta.json();
}

async function abrir() {
  const turno = await llamar("/api/sesion", {});
  sesionId = turno.sesion_id;
  agregar(turno.respuesta, "bot");
  pintarDictamen(turno.dictamen, turno.hechos);
}

form.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const texto = entrada.value.trim();
  if (!texto) return;
  entrada.value = "";
  enviar.disabled = true;
  agregar(texto, "user");
  try {
    const turno = await llamar("/api/chat", { sesion_id: sesionId, mensaje: texto });
    sesionId = turno.sesion_id;
    agregar(turno.respuesta, "bot");
    pintarDictamen(turno.dictamen, turno.hechos);
  } catch (error) {
    agregar("No pude hablar con el backend. ¿Está levantado el compose?", "bot");
  }
});

iniciarSheet();
pintarHechos({});
abrir().catch(() => {
  agregar("No pude iniciar la sesión. Levantá el backend y recargá.", "bot");
});
