const canvas = document.getElementById("map");
const ctx = canvas.getContext("2d");

let objects = [];

// загрузка карты
async function loadMap() {
  const res = await fetch("/api/map");
  objects = await res.json();
  draw();
}

// отрисовка
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // участок
  ctx.fillStyle = "#c8e6c9";
  ctx.fillRect(20, 20, 560, 360);

  objects.forEach(obj => {
    ctx.fillStyle = obj.color;

    if (obj.shape === "circle") {
      ctx.beginPath();
      ctx.arc(obj.x, obj.y, 10, 0, Math.PI * 2);
      ctx.fill();
    }

    if (obj.shape === "rect") {
      ctx.fillRect(obj.x, obj.y, obj.width, obj.height);
    }
  });
}

// добавление растения
async function addPlant() {
  const plant = {
    name: "Tomato",
    type: "plant",
    shape: "circle",
    x: Math.random() * 400 + 50,
    y: Math.random() * 300 + 50,
    color: "red"
  };

  await fetch("/api/map/add", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(plant)
  });

  loadMap();
}

async function addPlantAt(x, y) {
  const plant = {
    name: "Tomato",
    type: "plant",
    shape: "circle",
    x: Math.round(x),
    y: Math.round(y),
    color: "red"
  };

  await fetch("/api/map/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(plant)
  });

  loadMap();
}

function getObjectAt(x, y) {
  for (let obj of objects) {
    if (obj.shape === "circle") {
      const dist = Math.hypot(obj.x - x, obj.y - y);
      if (dist < 12) return obj;
    }

    if (obj.shape === "rect") {
      if (
        x >= obj.x &&
        x <= obj.x + obj.width &&
        y >= obj.y &&
        y <= obj.y + obj.height
      ) {
        return obj;
      }
    }
  }
  return null;
}

async function handleDelete(obj) {
  const ok = confirm(`Удалить объект "${obj.name}"?`);
  if (!ok) return;

  await fetch(`/api/map/delete/${obj.id}`, {
    method: "DELETE"
  });

  loadMap();
}


canvas.addEventListener("click", async (e) => {
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  // проверяем: кликнули по объекту или по пустому месту
  const clickedObject = getObjectAt(x, y);

  if (clickedObject) {
    handleDelete(clickedObject);
  } else {
    addPlantAt(x, y);
  }
});


loadMap();
