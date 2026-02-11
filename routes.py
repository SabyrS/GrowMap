import json
import requests
from datetime import datetime, timedelta
from urllib.request import urlopen

from flask import jsonify, request, session, redirect, render_template

from app import app
from db import get_db


DEFAULT_LAT = 51.1801
DEFAULT_LON = 71.446


def _require_login():
    if "user_id" not in session:
        return False
    return True


def _get_map_or_404(map_id):
    conn = get_db()
    map_data = conn.execute(
        "SELECT * FROM maps WHERE id=? AND user_id=?",
        (map_id, session["user_id"])
    ).fetchone()
    conn.close()
    return map_data

def _get_location_by_ip():
    try:
        r = requests.get("http://ip-api.com/json/", timeout=3)
        data = r.json()
        if data.get("status") == "success":
            return {
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "city": data.get("city"),
                "country": data.get("country")
            }
    except Exception:
        pass
    return None

def _get_weather(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
        "&current_weather=true&timezone=auto"
    )
    with urlopen(url) as response:
        data = json.loads(response.read().decode("utf-8"))

    daily = data.get("daily", {})
    days = daily.get("time", [])
    tmax = daily.get("temperature_2m_max", [])
    tmin = daily.get("temperature_2m_min", [])
    rain = daily.get("precipitation_sum", [])

    forecast = []
    for i, day in enumerate(days):
        forecast.append({
            "date": day,
            "tmax": tmax[i],
            "tmin": tmin[i],
            "rain": rain[i]
        })

    current = data.get("current_weather", {})
    return current, forecast


def _make_weather_recommendation(forecast):
    if not forecast:
        return "No forecast data", []

    today = forecast[0]
    warnings = []
    if today["tmin"] <= 2:
        warnings.append("Frost risk tonight")
    if today["tmax"] >= 30:
        warnings.append("Heat stress risk")

    if today["rain"] >= 5:
        rec = "No watering today"
    elif today["tmax"] >= 28 and today["rain"] < 1:
        rec = "Watering recommended"
    else:
        rec = "Light watering if soil is dry"

    return rec, warnings


def _log_action(conn, map_id, action_type, plant_object_id=None, amount=None, note=None):
    conn.execute(
        """
        INSERT INTO logs (user_id, map_id, action_type, plant_object_id, amount, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session["user_id"],
            map_id,
            action_type,
            plant_object_id,
            amount,
            note,
            datetime.utcnow().isoformat()
        )
    )


@app.route("/")
def home():
    if not _require_login():
        return redirect("/login")
    return render_template("home.html")


@app.route("/maps")
def maps_page():
    if not _require_login():
        return redirect("/login")

    conn = get_db()
    maps = conn.execute(
        "SELECT * FROM maps WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    return render_template("maps.html", maps=maps)


@app.route("/maps/create", methods=["GET", "POST"])
def create_map():
    if not _require_login():
        return redirect("/login")

    if request.method == "POST":
        name = request.form["name"]
        width = float(request.form["width"])
        height = float(request.form["height"])

        conn = get_db()
        conn.execute(
            """
            INSERT INTO maps (user_id, name, width_m, height_m)
            VALUES (?, ?, ?, ?)
            """,
            (session["user_id"], name, width, height)
        )
        conn.commit()
        conn.close()

        return redirect("/maps")

    return render_template("create_map.html")


@app.route("/api/maps/<int:map_id>", methods=["DELETE"])
def delete_map(map_id):
    if not _require_login():
        return jsonify({"error": "Not logged in"}), 401

    map_data = _get_map_or_404(map_id)
    if not map_data:
        return jsonify({"error": "Map not found"}), 404

    conn = get_db()
    # Delete all objects in the map first
    conn.execute("DELETE FROM map_objects WHERE map_id=?", (map_id,))
    # Delete all logs for this map
    conn.execute("DELETE FROM logs WHERE map_id=?", (map_id,))
    # Delete all harvests for objects in this map
    conn.execute("""
        DELETE FROM harvests 
        WHERE plant_object_id IN (SELECT id FROM map_objects WHERE map_id=?)
    """, (map_id,))
    # Delete the map
    conn.execute("DELETE FROM maps WHERE id=?", (map_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/editor/<int:map_id>")
def editor(map_id):
    if not _require_login():
        return redirect("/login")

    map_data = _get_map_or_404(map_id)
    if not map_data:
        return "Map not found", 404

    conn = get_db()
    plants = conn.execute(
        "SELECT * FROM plant_catalog ORDER BY name"
    ).fetchall()
    conn.close()

    return render_template("editor.html", map=map_data, plants=plants)


@app.route("/api/catalog")
def catalog():
    conn = get_db()
    rows = conn.execute("SELECT * FROM plant_catalog ORDER BY name").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/compat")
def compat():
    conn = get_db()
    rows = conn.execute("SELECT * FROM plant_compat").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/maps/<int:map_id>/objects")
def get_objects(map_id):
    if not _require_login():
        return jsonify({"error": "unauthorized"}), 401

    if not _get_map_or_404(map_id):
        return jsonify({"error": "not_found"}), 404

    conn = get_db()
    rows = conn.execute(
        """
        SELECT mo.*, pc.name AS plant_name, pc.avg_yield, pc.yield_unit,
               pc.water_need, pc.sun_need, pc.frost_sensitive, pc.heat_sensitive
        FROM map_objects mo
        LEFT JOIN plant_catalog pc ON pc.id = mo.plant_id
        WHERE mo.map_id=?
        """,
        (map_id,)
    ).fetchall()
    conn.close()

    objects = []
    for r in rows:
        obj = dict(r)
        if obj.get("points"):
            obj["points"] = json.loads(obj["points"])
        objects.append(obj)

    return jsonify(objects)


@app.route("/api/maps/<int:map_id>/objects", methods=["POST"])
def add_object(map_id):
    if not _require_login():
        return jsonify({"error": "unauthorized"}), 401

    if not _get_map_or_404(map_id):
        return jsonify({"error": "not_found"}), 404

    data = request.json
    conn = get_db()

    plant_id = data.get("plant_id")
    bed_type = data.get("bed_type")
    planted_at = data.get("planted_at")

    new_id = None
    if data["shape"] == "polygon":
        cur = conn.execute(
            """
            INSERT INTO map_objects
            (map_id, type, shape, points, color, name, plant_id, planted_at, bed_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                map_id,
                data["type"],
                data["shape"],
                json.dumps(data["points"]),
                data.get("color", "#ffcc00"),
                data.get("name"),
                plant_id,
                planted_at,
                bed_type
            )
        )
        new_id = cur.lastrowid
    else:
        cur = conn.execute(
            """
            INSERT INTO map_objects
            (map_id, type, shape, x, y, size, width, height, color, name, plant_id, planted_at, bed_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                map_id,
                data["type"],
                data["shape"],
                data.get("x"),
                data.get("y"),
                data.get("size"),
                data.get("width"),
                data.get("height"),
                data.get("color"),
                data.get("name"),
                plant_id,
                planted_at,
                bed_type
            )
        )
        new_id = cur.lastrowid

    if data.get("type") == "plant":
        plant_row = conn.execute(
            "SELECT name FROM plant_catalog WHERE id=?",
            (plant_id,)
        ).fetchone()
        plant_name = plant_row["name"] if plant_row else "Plant"
        _log_action(conn, map_id, "planting", new_id, None, plant_name)

    conn.commit()
    
    # Return the created object with full data
    created_obj = conn.execute(
        """
        SELECT mo.*, pc.name AS plant_name, pc.avg_yield, pc.yield_unit,
               pc.water_need, pc.sun_need, pc.frost_sensitive, pc.heat_sensitive
        FROM map_objects mo
        LEFT JOIN plant_catalog pc ON pc.id = mo.plant_id
        WHERE mo.id=?
        """,
        (new_id,)
    ).fetchone()
    
    conn.close()
    
    if created_obj:
        obj = dict(created_obj)
        if obj.get("points"):
            obj["points"] = json.loads(obj["points"])
        return jsonify(obj)
    
    return jsonify({"status": "ok"})


@app.route("/api/objects/<int:obj_id>", methods=["DELETE"])
def delete_object(obj_id):
    if not _require_login():
        return jsonify({"error": "unauthorized"}), 401

    conn = get_db()
    row = conn.execute(
        """
        SELECT mo.id
        FROM map_objects mo
        JOIN maps m ON m.id = mo.map_id
        WHERE mo.id=? AND m.user_id=?
        """,
        (obj_id, session["user_id"])
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "not_found"}), 404

    conn.execute("DELETE FROM map_objects WHERE id=?", (obj_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})


@app.route("/api/logs", methods=["GET", "POST"])
def logs():
    if not _require_login():
        return jsonify({"error": "unauthorized"}), 401

    if request.method == "POST":
        data = request.json
        if not _get_map_or_404(data["map_id"]):
            return jsonify({"error": "not_found"}), 404
        
        conn = get_db()
        
        # Check if action is watering or harvest and object is a building
        if data["action_type"] in ["watering", "harvest"] and data.get("plant_object_id"):
            obj_row = conn.execute(
                "SELECT type FROM map_objects WHERE id=?",
                (data["plant_object_id"],)
            ).fetchone()
            if obj_row and obj_row["type"] == "building":
                conn.close()
                return jsonify({"error": "Cannot log watering or harvest for buildings"}), 400
        
        _log_action(
            conn,
            data["map_id"],
            data["action_type"],
            data.get("plant_object_id"),
            data.get("amount"),
            data.get("note")
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})

    map_id = request.args.get("map_id")
    conn = get_db()
    if map_id:
        if not _get_map_or_404(map_id):
            conn.close()
            return jsonify({"error": "not_found"}), 404
        rows = conn.execute(
            """
            SELECT * FROM logs
            WHERE user_id=? AND map_id=?
            ORDER BY created_at DESC
            LIMIT 50
            """,
            (session["user_id"], map_id)
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT * FROM logs
            WHERE user_id=?
            ORDER BY created_at DESC
            LIMIT 50
            """,
            (session["user_id"],)
        ).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


@app.route("/api/harvest", methods=["POST"])
def add_harvest():
    if not _require_login():
        return jsonify({"error": "unauthorized"}), 401

    data = request.json
    if not _get_map_or_404(data["map_id"]):
        return jsonify({"error": "not_found"}), 404
    conn = get_db()

    row = conn.execute(
        """
        SELECT mo.id, mo.type
        FROM map_objects mo
        JOIN maps m ON m.id = mo.map_id
        WHERE mo.id=? AND m.user_id=?
        """,
        (data["plant_object_id"], session["user_id"])
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "not_found"}), 404
    
    # Check if object is a building
    if row["type"] == "building":
        conn.close()
        return jsonify({"error": "Cannot add harvest for buildings"}), 400

    conn.execute(
        """
        INSERT INTO harvests (user_id, map_id, plant_object_id, amount, unit, harvested_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            session["user_id"],
            data["map_id"],
            data["plant_object_id"],
            data["amount"],
            data["unit"],
            data.get("harvested_at", datetime.utcnow().date().isoformat())
        )
    )

    _log_action(
        conn,
        data["map_id"],
        "harvest",
        data["plant_object_id"],
        data["amount"],
        data.get("note")
    )

    avg_row = conn.execute(
        """
        SELECT pc.avg_yield, pc.yield_unit
        FROM map_objects mo
        LEFT JOIN plant_catalog pc ON pc.id = mo.plant_id
        WHERE mo.id=?
        """,
        (data["plant_object_id"],)
    ).fetchone()

    conn.commit()
    conn.close()

    efficiency = None
    if avg_row and avg_row["avg_yield"]:
        efficiency = round((data["amount"] / avg_row["avg_yield"]) * 100, 1)

    return jsonify({
        "status": "ok",
        "avg_yield": avg_row["avg_yield"] if avg_row else None,
        "yield_unit": avg_row["yield_unit"] if avg_row else None,
        "efficiency": efficiency
    })


@app.route("/api/harvests", methods=["GET"])
def get_harvests():
    if not _require_login():
        return jsonify({"error": "unauthorized"}), 401

    plant_object_id = request.args.get("plant_object_id")
    conn = get_db()
    
    if plant_object_id:
        rows = conn.execute(
            """
            SELECT h.*, mo.name as object_name
            FROM harvests h
            JOIN map_objects mo ON mo.id = h.plant_object_id
            WHERE h.user_id=? AND h.plant_object_id=?
            ORDER BY h.harvested_at DESC
            """,
            (session["user_id"], plant_object_id)
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT h.*, mo.name as object_name
            FROM harvests h
            JOIN map_objects mo ON mo.id = h.plant_object_id
            WHERE h.user_id=?
            ORDER BY h.harvested_at DESC
            """,
            (session["user_id"],)
        ).fetchall()
    
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/harvests/<int:harvest_id>", methods=["DELETE"])
def delete_harvest(harvest_id):
    if not _require_login():
        return jsonify({"error": "unauthorized"}), 401

    conn = get_db()
    row = conn.execute(
        "SELECT id FROM harvests WHERE id=? AND user_id=?",
        (harvest_id, session["user_id"])
    ).fetchone()
    
    if not row:
        conn.close()
        return jsonify({"error": "not_found"}), 404
    
    conn.execute("DELETE FROM harvests WHERE id=?", (harvest_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "ok"})


@app.route("/weather", methods=["GET", "POST"])
def weather_page():
    if not _require_login():
        return redirect("/login")

    if request.method == "POST":
        lat_raw = request.form.get("lat", "").strip()
        lon_raw = request.form.get("lon", "").strip()
        if lat_raw and lon_raw:
            try:
                session["lat"] = float(lat_raw)
                session["lon"] = float(lon_raw)
            except ValueError:
                pass

    lat = session.get("lat")
    lon = session.get("lon")
    location_label = None

    # Если координат нет => пробуем IP
    use_ip = request.args.get("use_ip") == "1"
    if use_ip:
        ip_location = _get_location_by_ip()
        if ip_location and ip_location["lat"] is not None and ip_location["lon"] is not None:
            lat = ip_location["lat"]
            lon = ip_location["lon"]
            session["lat"] = lat
            session["lon"] = lon
            session["location_city"] = ip_location.get("city")
            session["location_country"] = ip_location.get("country")

    location_city = session.get("location_city")
    location_country = session.get("location_country")

    if lat is None or lon is None:
        ip_location = _get_location_by_ip()
        if ip_location and ip_location["lat"] is not None and ip_location["lon"] is not None:
            lat = ip_location["lat"]
            lon = ip_location["lon"]
            session["lat"] = lat
            session["lon"] = lon
            location_city = ip_location.get("city")
            location_country = ip_location.get("country")
            session["location_city"] = location_city
            session["location_country"] = location_country
        else:
            lat = DEFAULT_LAT
            lon = DEFAULT_LON

    if location_city:
        location_label = location_city
        if location_country:
            location_label = f"{location_city}, {location_country}"

    current, forecast = _get_weather(lat, lon)
    recommendation, warnings = _make_weather_recommendation(forecast)

    weather = {
        "temp": current.get("temperature"),
        "wind": current.get("windspeed"),
        "recommendation": recommendation,
        "warnings": warnings,
        "forecast": forecast
    }

    return render_template(
        "weather.html",
        weather=weather,
        lat=lat,
        lon=lon,
        location_label=location_label
    )


@app.route("/api/location/ip")
def location_by_ip_api():
    if not _require_login():
        return jsonify({"error": "unauthorized"}), 401

    ip_location = _get_location_by_ip()
    if not ip_location:
        return jsonify({"error": "ip_lookup_failed"}), 503

    if ip_location["lat"] is None or ip_location["lon"] is None:
        return jsonify({"error": "ip_lookup_incomplete"}), 503

    return jsonify(ip_location)



@app.route("/analytics")
def analytics_page():
    if not _require_login():
        return redirect("/login")

    lat = session.get("lat", DEFAULT_LAT)
    lon = session.get("lon", DEFAULT_LON)
    _, forecast = _get_weather(lat, lon)

    conn = get_db()
    rows = conn.execute(
        """
        SELECT action_type, created_at
        FROM logs
        WHERE user_id=?
        """,
        (session["user_id"],)
    ).fetchall()
    
    # Get harvest data grouped by plant
    harvest_data = conn.execute(
        """
        SELECT COALESCE(pc.name, mo.name, 'Unknown plant') as plant_name, 
               SUM(h.amount) as total_harvested,
               COALESCE(pc.avg_yield, 0) as avg_yield,
               h.unit as yield_unit,
               COUNT(DISTINCT mo.id) as plant_count
        FROM harvests h
        JOIN map_objects mo ON mo.id = h.plant_object_id
        LEFT JOIN plant_catalog pc ON pc.id = mo.plant_id
        WHERE h.user_id = ?
        GROUP BY COALESCE(pc.name, mo.name), COALESCE(pc.avg_yield, 0), h.unit
        """,
        (session["user_id"],)
    ).fetchall()
    
    conn.close()

    today = datetime.utcnow().date()
    days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    labels = [d.isoformat() for d in days]

    watering_counts = {d.isoformat(): 0 for d in days}
    for r in rows:
        if r["action_type"] != "watering":
            continue
        day = r["created_at"][:10]
        if day in watering_counts:
            watering_counts[day] += 1

    temp_series = [{
        "date": f["date"],
        "tmax": f["tmax"],
        "tmin": f["tmin"]
    } for f in forecast[:7]]

    # Prepare harvest analytics
    harvest_analytics = None
    if harvest_data:
        # Create labels with plant name and unit for each plant
        plant_labels = [f"{r['plant_name']} ({r['yield_unit']})" for r in harvest_data]
        harvest_analytics = {
            "plants": plant_labels,
            "harvested": [float(r["total_harvested"]) / r["plant_count"] if r["plant_count"] > 0 else 0 for r in harvest_data],
            "expected": [float(r["avg_yield"]) for r in harvest_data]
        }

    analytics = {
        "labels": labels,
        "watering": [watering_counts[d] for d in labels],
        "temp": temp_series
    }

    summary = "Watering is balanced this week."
    if sum(analytics["watering"]) >= 6:
        summary = "High watering frequency. Consider soil moisture."
    if sum(analytics["watering"]) == 0:
        summary = "No watering events recorded."

    return render_template("analytics.html", analytics=analytics, harvest_analytics=harvest_analytics, summary=summary)
