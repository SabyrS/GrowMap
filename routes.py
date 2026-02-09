from flask import jsonify, request, session, redirect, render_template
from app import app
from db import get_db

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("home.html")

@app.route("/map")
def map_page():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("map.html")


@app.route("/api/map")
def get_map():
    if "user_id" not in session:
        return jsonify([])

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM map_objects WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


@app.route("/api/map/add", methods=["POST"])
def add_object():
    data = request.json
    conn = get_db()

    conn.execute("""
        INSERT INTO map_objects
        (user_id, name, type, shape, x, y, width, height, color)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        data["name"],
        data["type"],
        data["shape"],
        data["x"],
        data["y"],
        data.get("width"),
        data.get("height"),
        data["color"]
    ))

    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route("/api/map/delete/<int:obj_id>", methods=["DELETE"])
def delete_object(obj_id):
    if "user_id" not in session:
        return jsonify({"error": "unauthorized"}), 401

    conn = get_db()
    conn.execute(
        "DELETE FROM map_objects WHERE id=? AND user_id=?",
        (obj_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})


@app.route("/weather")
def weather_page():
    if "user_id" not in session:
        return redirect("/login")

    # temporary
    weather = {
        "temp": 23,
        "condition": "Sunny",
        "recommendation": "No watering today"
    }

    return render_template("weather.html", weather=weather)

@app.route("/analytics")
def analytics_page():
    if "user_id" not in session:
        return redirect("/login")

    analytics = {
        "plants_count": 5,
        "waterings": 12,
        "summary": "Too much water for plants"
    }

    return render_template("analytics.html", analytics=analytics)
