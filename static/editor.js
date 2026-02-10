const svg = document.getElementById("editor");

let currentMode = "create";
let selectedObject = null;
let selectedElement = null;

let objects = [];

let polygonPoints = [];
let tempLines = [];


function snapValue(v) {
  const enabled = document.getElementById("snap-enabled")?.checked;
  if (!enabled) return v;

  const step = parseFloat(document.getElementById("snap-step")?.value || 0.5);
  return Math.round(v / step) * step;
}


function setMode(mode) {
  currentMode = mode;
  selectedObject = null;
  selectedElement = null;
  clearSelection();
}


let viewBox = {
  x: 0,
  y: 0,
  w: MAP_WIDTH_M * SCALE,
  h: MAP_HEIGHT_M * SCALE
};

function updateViewBox() {
  svg.setAttribute(
    "viewBox",
    `${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`
  );
}
updateViewBox();

svg.addEventListener("wheel", (e) => {
  e.preventDefault();
  const zoom = e.deltaY > 0 ? 1.1 : 0.9;
  viewBox.w *= zoom;
  viewBox.h *= zoom;
  updateViewBox();
});

let isPanning = false;
let panStart = {};

svg.addEventListener("mousedown", (e) => {
  if (currentMode !== "select") return;
  isPanning = true;
  panStart = { x: e.clientX, y: e.clientY };
});

svg.addEventListener("mousemove", (e) => {
  if (!isPanning) return;

  const dx = panStart.x - e.clientX;
  const dy = panStart.y - e.clientY;

  viewBox.x += dx;
  viewBox.y += dy;

  panStart = { x: e.clientX, y: e.clientY };
  updateViewBox();
});

svg.addEventListener("mouseup", () => (isPanning = false));
svg.addEventListener("mouseleave", () => (isPanning = false));

function zoomIn() {
  viewBox.w *= 0.8;
  viewBox.h *= 0.8;
  updateViewBox();
}

function zoomOut() {
  viewBox.w *= 1.2;
  viewBox.h *= 1.2;
  updateViewBox();
}

function resetView() {
  viewBox = {
    x: 0,
    y: 0,
    w: MAP_WIDTH_M * SCALE,
    h: MAP_HEIGHT_M * SCALE
  };
  updateViewBox();
}


function drawGrid() {
  for (let x = 0; x <= MAP_WIDTH_M; x++) {
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", x * SCALE);
    line.setAttribute("y1", 0);
    line.setAttribute("x2", x * SCALE);
    line.setAttribute("y2", MAP_HEIGHT_M * SCALE);
    line.setAttribute("stroke", "#ddd");
    svg.appendChild(line);
  }

  for (let y = 0; y <= MAP_HEIGHT_M; y++) {
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", 0);
    line.setAttribute("y1", y * SCALE);
    line.setAttribute("x2", MAP_WIDTH_M * SCALE);
    line.setAttribute("y2", y * SCALE);
    line.setAttribute("stroke", "#ddd");
    svg.appendChild(line);
  }
}


function loadObjects() {
  fetch(`/api/maps/${MAP_ID}/objects`)
    .then(r => r.json())
    .then(data => {
      objects = data;
      data.forEach(drawObject);
    });
}


function drawObject(obj) {
  let el = null;

  if (obj.shape === "circle") {
    el = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    el.setAttribute("cx", obj.x * SCALE);
    el.setAttribute("cy", obj.y * SCALE);
    el.setAttribute("r", obj.size * SCALE);
  }

  if (obj.shape === "rect") {
    el = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    el.setAttribute("x", obj.x * SCALE);
    el.setAttribute("y", obj.y * SCALE);
    el.setAttribute("width", obj.width * SCALE);
    el.setAttribute("height", obj.height * SCALE);
  }

  if (obj.shape === "polygon") {
    el = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
    const points = (obj.points || [])
      .map(p => `${p[0] * SCALE},${p[1] * SCALE}`)
      .join(" ");
    el.setAttribute("points", points);
  }

  if (!el) return;

  el.setAttribute("fill", obj.color || "#4caf50");
  el.setAttribute("opacity", obj.shape === "polygon" ? 0.4 : 0.8);

  el.addEventListener("click", (e) => {
    e.stopPropagation();
    handleObjectClick(obj, el);
  });

  svg.appendChild(el);
}


svg.addEventListener("click", (e) => {
  if (currentMode !== "create") return;

  const rect = svg.getBoundingClientRect();
  let x = (e.clientX - rect.left) / SCALE;
  let y = (e.clientY - rect.top) / SCALE;

  x = snapValue(x);
  y = snapValue(y);

  x = parseFloat(x.toFixed(2));
  y = parseFloat(y.toFixed(2));

  const shape = document.getElementById("obj-shape").value;

  if (shape === "polygon") {
    if (polygonPoints.length > 0) {
      const last = polygonPoints[polygonPoints.length - 1];
      drawTempLine(last[0], last[1], x, y);
    }
    polygonPoints.push([x, y]);
    drawTempPoint(x, y);
    return;
  }

  createObject(getCurrentObjectData(x, y));
});

function finishPolygon() {
  if (polygonPoints.length < 3) {
    alert("Минимум 3 точки");
    return;
  }

  createObject({
    type: "zone",
    shape: "polygon",
    points: polygonPoints,
    color: document.getElementById("obj-color").value
  });

  polygonPoints = [];
  tempLines.forEach(l => l.remove());
  tempLines = [];
}


function drawTempPoint(x, y) {
  const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  c.setAttribute("cx", x * SCALE);
  c.setAttribute("cy", y * SCALE);
  c.setAttribute("r", 3);
  c.setAttribute("fill", "red");
  svg.appendChild(c);
}

function drawTempLine(x1, y1, x2, y2) {
  const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
  line.setAttribute("x1", x1 * SCALE);
  line.setAttribute("y1", y1 * SCALE);
  line.setAttribute("x2", x2 * SCALE);
  line.setAttribute("y2", y2 * SCALE);
  line.setAttribute("stroke", "#888");
  line.setAttribute("stroke-dasharray", "4");
  svg.appendChild(line);
  tempLines.push(line);
}


function handleObjectClick(obj, element) {
  if (currentMode === "delete") {
    removeObject(obj.id, element);
    return;
  }
  if (currentMode === "select") {
    selectObject(obj, element);
  }
}

function selectObject(obj, element) {
  clearSelection();
  selectedObject = obj;
  selectedElement = element;

  element.setAttribute("stroke", "#000");
  element.setAttribute("stroke-width", "2");

  let info = `
    <b>${obj.name || "Object"}</b><br>
    Тип: ${obj.type}<br>
    Форма: ${obj.shape}<br>
  `;

  if (obj.shape === "polygon") {
    info += `Точек: ${obj.points.length}<br>`;
  } else {
    info += `X: ${obj.x} м<br>Y: ${obj.y} м<br>`;
  }

  if (obj.plant_name) {
    info += `
      Растение: ${obj.plant_name}<br>
      Посажено: ${obj.planted_at || "-"}<br>
      Тип грядки: ${obj.bed_type || "-"}<br>
    `;
  }

  document.getElementById("object-info").innerHTML = info;
}

function clearSelection() {
  svg.querySelectorAll("[stroke]").forEach(el => el.removeAttribute("stroke"));
}


function createObject(obj) {
  fetch(`/api/maps/${MAP_ID}/objects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(obj)
  }).then(() => location.reload());
}

function removeObject(id, element) {
  fetch(`/api/objects/${id}`, { method: "DELETE" })
    .then(() => element.remove());
}

function getCenter(obj) {
  if (obj.shape === "circle") {
    return { x: obj.x, y: obj.y };
  }
  if (obj.shape === "rect") {
    return {
      x: obj.x + obj.width / 2,
      y: obj.y + obj.height / 2
    };
  }
  return null;
}

function renderConflicts(compatPairs) {
  const list = document.getElementById("conflict-list");
  if (!list) return;

  list.innerHTML = "";

  const plants = objects.filter(o => o.type === "plant" && o.plant_name);

  for (let i = 0; i < plants.length; i++) {
    for (let j = i + 1; j < plants.length; j++) {
      const a = plants[i];
      const b = plants[j];

      const ca = getCenter(a);
      const cb = getCenter(b);
      if (!ca || !cb) continue;

      const dist = Math.hypot(ca.x - cb.x, ca.y - cb.y);
      if (dist > 1) continue;

      const pair = compatPairs.find(p =>
        (p.plant_a === a.plant_name && p.plant_b === b.plant_name) ||
        (p.plant_a === b.plant_name && p.plant_b === a.plant_name)
      );

      if (pair && pair.level !== "good") {
        const li = document.createElement("li");
        li.textContent = `${a.plant_name} + ${b.plant_name}: ${pair.note}`;
        list.appendChild(li);
      }
    }
  }

  if (!list.children.length) {
    list.innerHTML = "<li>Нет опасных сочетаний</li>";
  }
}

function logWatering() {
  if (!selectedObject) {
    alert("Выберите растение");
    return;
  }

  fetch("/api/logs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      map_id: MAP_ID,
      action_type: "watering",
      plant_object_id: selectedObject.id
    })
  });
}

function loadLogs() {
  fetch(`/api/logs?map_id=${MAP_ID}`)
    .then(r => r.json())
    .then(data => {
      const list = document.getElementById("log-list");
      if (!list) return;

      list.innerHTML = "";
      data.forEach(item => {
        const div = document.createElement("div");
        div.textContent =
          `${item.created_at.slice(0,10)} — ${item.action_type}`;
        list.appendChild(div);
      });
    });
}


drawGrid();
loadObjects();
