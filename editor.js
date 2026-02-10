const svg = document.getElementById("editor");


let currentMode = "create";
let selectedObject = null;

let polygonPoints = [];
let tempLines = [];

function snapValue(v) {
  const enabled = document.getElementById("snap-enabled").checked;
  if (!enabled) return v;

  const step = parseFloat(document.getElementById("snap-step").value);
  return Math.round(v / step) * step;
}


function setMode(mode) {
  currentMode = mode;
  selectedObject = null;
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
let start = {};

svg.addEventListener("mousedown", (e) => {
  if (currentMode !== "select") return;
  isPanning = true;
  start = { x: e.clientX, y: e.clientY };
});

svg.addEventListener("mousemove", (e) => {
  if (!isPanning) return;

  const dx = (start.x - e.clientX);
  const dy = (start.y - e.clientY);

  viewBox.x += dx;
  viewBox.y += dy;

  start = { x: e.clientX, y: e.clientY };
  updateViewBox();
});

svg.addEventListener("mouseup", () => isPanning = false);
svg.addEventListener("mouseleave", () => isPanning = false);


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


function loadObjects() {
  fetch(`/api/maps/${MAP_ID}/objects`)
    .then(r => r.json())
    .then(data => data.forEach(drawObject));
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
    circle.setAttribute("fill", obj.color);
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
  rect.setAttribute("fill", obj.color);
  rect.setAttribute("opacity", 0.7);

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

  const points = obj.points
    .map(p => `${p[0] * SCALE},${p[1] * SCALE}`)
    .join(" ");

  poly.setAttribute("points", points);
  poly.setAttribute("fill", obj.color);
  poly.setAttribute("opacity", 0.4);

  poly.addEventListener("click", (e) => {
    e.stopPropagation();
    handleObjectClick(obj, poly);
  });

  svg.appendChild(poly);
  }
}


// svg.addEventListener("click", (e) => {
//   const rect = svg.getBoundingClientRect();
//   const x = ((e.clientX - rect.left) / SCALE).toFixed(2);
//   const y = ((e.clientY - rect.top) / SCALE).toFixed(2);

//   const obj = getCurrentObjectData(parseFloat(x), parseFloat(y));
//   createObject(obj);
// });

svg.addEventListener("click", (e) => {
  if (currentMode !== "create") return;

  const rect = svg.getBoundingClientRect();
  let x = (e.clientX - rect.left) / SCALE;
  let y = (e.clientY - rect.top) / SCALE;

  x = snapValue(x);
  y = snapValue(y);

  x = x.toFixed(2);
  y = y.toFixed(2);

  const shape = document.getElementById("obj-shape").value;

  
  if (shape === "polygon") {
  const px = parseFloat(x);
  const py = parseFloat(y);

  if (polygonPoints.length > 0) {
    const last = polygonPoints[polygonPoints.length - 1];
    drawTempLine(last[0], last[1], px, py);
  }

  polygonPoints.push([px, py]);
  drawTempPoint(px, py);
  return;
  }


  const obj = getCurrentObjectData(parseFloat(x), parseFloat(y));
  createObject(obj);
});



function getCurrentObjectData(x, y) {
  const shape = document.getElementById("obj-shape").value;

  const obj = {
    type: document.getElementById("obj-type").value,
    shape: shape,
    name: document.getElementById("obj-name").value || "Object",
    x: x,
    y: y,
    color: document.getElementById("obj-color").value
  };

  if (shape === "circle") {
    obj.size = parseFloat(document.getElementById("obj-size").value);
  }

  if (shape === "rect") {
    obj.width = parseFloat(document.getElementById("obj-width").value);
    obj.height = parseFloat(document.getElementById("obj-height").value);
  }

  // if (currentMode === "create" && currentShape === "polygon") {
  // polygonPoints.push([x, y]);
  // drawTempPoint(x, y);
  // }

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
  selectedObject = element;

  element.setAttribute("stroke", "black");
  element.setAttribute("stroke-width", "2");

  let info = `
    <b>${obj.name}</b><br>
    Тип: ${obj.type}<br>
    Форма: ${obj.shape}<br>
  `;

  if (obj.shape !== "polygon") {
    info += `
      X: ${obj.x} м<br>
      Y: ${obj.y} м<br>
    `;
  } else {
    info += `
      Точек: ${obj.points.length}<br>
    `;
  }

  document.getElementById("object-info").innerHTML = info;
}


function clearSelection() {
  const all = svg.querySelectorAll("[stroke]");
  all.forEach(el => el.removeAttribute("stroke"));
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




// function getCurrentObjectData(x, y) {
//   return {
//     type: document.getElementById("obj-type").value,
//     shape: document.getElementById("obj-shape").value,
//     name: document.getElementById("obj-name").value || "Object",
//     x: x,
//     y: y,
//     size: parseFloat(document.getElementById("obj-size").value),
//     color: document.getElementById("obj-color").value
//   };
// }

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


loadObjects();
