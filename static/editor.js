const svg = document.getElementById("editor");

let currentMode = "create";
let selectedObject = null;
let selectedElement = null;
let polygonPoints = [];
let objects = [];
let compatPairs = [];

function setMode(mode) {
  currentMode = mode;
  selectedObject = null;
  clearSelection();
}

function drawGrid() {
  for (let x = 0; x <= MAP_WIDTH_M; x++) {
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", x * SCALE);
    line.setAttribute("y1", 0);
    line.setAttribute("x2", x * SCALE);
    line.setAttribute("y2", MAP_HEIGHT_M * SCALE);
    line.setAttribute("stroke", "#eee");
    svg.appendChild(line);
  }

  for (let y = 0; y <= MAP_HEIGHT_M; y++) {
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", 0);
    line.setAttribute("y1", y * SCALE);
    line.setAttribute("x2", MAP_WIDTH_M * SCALE);
    line.setAttribute("y2", y * SCALE);
    line.setAttribute("stroke", "#eee");
    svg.appendChild(line);
  }
}

function loadCompat() {
  return fetch("/api/compat")
    .then(r => r.json())
    .then(data => {
      compatPairs = data;
    });
}

function loadObjects() {
  return fetch(`/api/maps/${MAP_ID}/objects`)
    .then(r => r.json())
    .then(data => {
      objects = data;
      data.forEach(drawObject);
      renderConflicts();
    });
}

function drawObject(obj) {
  if (obj.shape === "circle") {
    const circle = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "circle"
    );

    circle.setAttribute("cx", obj.x * SCALE);
    circle.setAttribute("cy", obj.y * SCALE);
    circle.setAttribute("r", obj.size * SCALE);
    circle.setAttribute("fill", obj.color || "#4caf50");
    circle.dataset.id = obj.id;

    circle.addEventListener("click", (e) => {
      e.stopPropagation();
      handleObjectClick(obj, circle);
    });

    svg.appendChild(circle);
  }

  if (obj.shape === "rect") {
    const rect = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "rect"
    );

    rect.setAttribute("x", obj.x * SCALE);
    rect.setAttribute("y", obj.y * SCALE);
    rect.setAttribute("width", obj.width * SCALE);
    rect.setAttribute("height", obj.height * SCALE);
    rect.setAttribute("fill", obj.color || "#9e9e9e");
    rect.setAttribute("opacity", 0.8);

    rect.addEventListener("click", (e) => {
      e.stopPropagation();
      handleObjectClick(obj, rect);
    });

    svg.appendChild(rect);
  }

  if (obj.shape === "polygon") {
    const poly = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "polygon"
    );

    const points = (obj.points || [])
      .map(p => `${p[0] * SCALE},${p[1] * SCALE}`)
      .join(" ");

    poly.setAttribute("points", points);
    poly.setAttribute("fill", obj.color || "#ffcc00");
    poly.setAttribute("opacity", 0.4);

    poly.addEventListener("click", (e) => {
      e.stopPropagation();
      handleObjectClick(obj, poly);
    });

    svg.appendChild(poly);
  }
}

svg.addEventListener("click", (e) => {
  if (currentMode !== "create") return;

  const rect = svg.getBoundingClientRect();
  const x = ((e.clientX - rect.left) / SCALE).toFixed(2);
  const y = ((e.clientY - rect.top) / SCALE).toFixed(2);

  const shape = document.getElementById("obj-shape").value;

  if (shape === "polygon") {
    polygonPoints.push([parseFloat(x), parseFloat(y)]);
    drawTempPoint(x, y);
    return;
  }

  const obj = getCurrentObjectData(parseFloat(x), parseFloat(y));
  createObject(obj);
});

function getCurrentObjectData(x, y) {
  const shape = document.getElementById("obj-shape").value;
  const type = document.getElementById("obj-type").value;

  const obj = {
    type: type,
    shape: shape,
    name: document.getElementById("obj-name").value || "Object",
    x: x,
    y: y,
    color: document.getElementById("obj-color").value
  };

  if (type === "plant") {
    const plantId = document.getElementById("plant-id").value;
    obj.plant_id = plantId ? parseInt(plantId, 10) : null;
    obj.planted_at = document.getElementById("planted-at").value || null;
    obj.bed_type = document.getElementById("bed-type").value;
  }

  if (shape === "circle") {
    obj.size = parseFloat(document.getElementById("obj-size").value);
  }

  if (shape === "rect") {
    obj.width = parseFloat(document.getElementById("obj-width").value);
    obj.height = parseFloat(document.getElementById("obj-height").value);
  }

  return obj;
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

  element.setAttribute("stroke", "#111");
  element.setAttribute("stroke-width", "2");

  const info = document.getElementById("object-info");
  const plantBlock = obj.plant_name
    ? `Plant: <strong>${obj.plant_name}</strong><br>
       Bed: ${obj.bed_type || "-"}<br>
       Planted: ${obj.planted_at || "-"}<br>
       Water: ${obj.water_need || "-"} / Sun: ${obj.sun_need || "-"}<br>
       Avg yield: ${obj.avg_yield || "-"} ${obj.yield_unit || ""}<br>`
    : "";

  info.innerHTML = `
    <strong>${obj.name || "Object"}</strong><br>
    Type: ${obj.type}<br>
    Shape: ${obj.shape}<br>
    X: ${obj.x} m, Y: ${obj.y} m<br>
    ${plantBlock}
  `;
}

function clearSelection() {
  const all = svg.querySelectorAll("[stroke]");
  all.forEach(el => el.removeAttribute("stroke"));
}

function finishPolygon() {
  if (polygonPoints.length < 3) {
    alert("Polygon needs at least 3 points");
    return;
  }

  createObject({
    type: "zone",
    shape: "polygon",
    points: polygonPoints,
    color: "#ffcc00",
    name: "Zone"
  });

  polygonPoints = [];
}

function createObject(obj) {
  fetch(`/api/maps/${MAP_ID}/objects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(obj)
  }).then(() => location.reload());
}

function removeObject(id, element) {
  fetch(`/api/objects/${id}`, {
    method: "DELETE"
  }).then(() => element.remove());
}

function drawTempPoint(x, y) {
  const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  c.setAttribute("cx", x * SCALE);
  c.setAttribute("cy", y * SCALE);
  c.setAttribute("r", 3);
  c.setAttribute("fill", "red");
  svg.appendChild(c);
}

function logWatering() {
  fetch("/api/logs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      map_id: MAP_ID,
      action_type: "watering",
      plant_object_id: selectedObject ? selectedObject.id : null
    })
  }).then(() => loadLogs());
}

function openHarvest() {
  const form = document.getElementById("harvest-form");
  form.style.display = form.style.display === "none" ? "block" : "none";
}

function submitHarvest() {
  if (!selectedObject) {
    alert("Select a plant first");
    return;
  }

  const amount = parseFloat(document.getElementById("harvest-amount").value);
  const unit = document.getElementById("harvest-unit").value;

  fetch("/api/harvest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      map_id: MAP_ID,
      plant_object_id: selectedObject.id,
      amount: amount,
      unit: unit
    })
  })
    .then(r => r.json())
    .then(data => {
      document.getElementById("harvest-result").innerText =
        data.efficiency
          ? `Efficiency: ${data.efficiency}% (avg ${data.avg_yield} ${data.yield_unit})`
          : "Harvest saved";
      loadLogs();
    });
}

function loadLogs() {
  fetch(`/api/logs?map_id=${MAP_ID}`)
    .then(r => r.json())
    .then(data => {
      const list = document.getElementById("log-list");
      list.innerHTML = "";
      data.forEach(item => {
        const div = document.createElement("div");
        div.className = "log-item";
        const date = item.created_at.slice(0, 10);
        div.innerText = `${date} - ${item.action_type}`;
        list.appendChild(div);
      });
    });
}

function getCenter(obj) {
  if (obj.shape === "circle") {
    return { x: obj.x, y: obj.y };
  }
  if (obj.shape === "rect") {
    return { x: obj.x + (obj.width / 2), y: obj.y + (obj.height / 2) };
  }
  return null;
}

function renderConflicts() {
  const list = document.getElementById("conflict-list");
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
      if (dist > 0.8) continue;

      const pair = compatPairs.find(p =>
        (p.plant_a === a.plant_name && p.plant_b === b.plant_name) ||
        (p.plant_a === b.plant_name && p.plant_b === a.plant_name)
      );

      if (pair && pair.level !== "good") {
        const item = document.createElement("li");
        item.className = "conflict-item";
        item.innerText = `${a.plant_name} + ${b.plant_name}: ${pair.note}`;
        list.appendChild(item);
      }
    }
  }

  if (list.children.length === 0) {
    const item = document.createElement("li");
    item.className = "conflict-item";
    item.innerText = "No risky combinations nearby.";
    list.appendChild(item);
  }
}

function boot() {
  drawGrid();
  Promise.all([loadCompat(), loadObjects()]).then(() => {
    loadLogs();
  });
}

boot();
