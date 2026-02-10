import sqlite3

DB_NAME = "growmap.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS maps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        width_m REAL NOT NULL,
        height_m REAL NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS map_objects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        map_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        shape TEXT NOT NULL,

        name TEXT,
        plant_id INTEGER,
        planted_at TEXT,
        bed_type TEXT,

        x REAL,
        y REAL,
        size REAL,
        width REAL,
        height REAL,

        points TEXT,
        color TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plant_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        bed_type TEXT NOT NULL,
        water_need TEXT NOT NULL,
        sun_need TEXT NOT NULL,
        frost_sensitive INTEGER NOT NULL,
        heat_sensitive INTEGER NOT NULL,
        avg_yield REAL NOT NULL,
        yield_unit TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plant_compat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plant_a TEXT NOT NULL,
        plant_b TEXT NOT NULL,
        level TEXT NOT NULL,
        note TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        map_id INTEGER NOT NULL,
        action_type TEXT NOT NULL,
        plant_object_id INTEGER,
        amount REAL,
        note TEXT,
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS harvests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        map_id INTEGER NOT NULL,
        plant_object_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        unit TEXT NOT NULL,
        harvested_at TEXT NOT NULL
    )
    """)

    _add_missing_columns(conn)
    _seed_catalog(conn)
    _seed_compat(conn)

    conn.commit()
    conn.close()


def _add_missing_columns(conn):
    existing = {r[1] for r in conn.execute("PRAGMA table_info(map_objects)").fetchall()}
    columns = [
        ("name", "TEXT"),
        ("plant_id", "INTEGER"),
        ("planted_at", "TEXT"),
        ("bed_type", "TEXT")
    ]
    for name, ctype in columns:
        if name not in existing:
            conn.execute(f"ALTER TABLE map_objects ADD COLUMN {name} {ctype}")


def _seed_catalog(conn):
    count = conn.execute("SELECT COUNT(*) FROM plant_catalog").fetchone()[0]
    if count > 0:
        return

    plants = [
        ("Tomato", "bed", "medium", "high", 1, 1, 3.5, "kg"),
        ("Potato", "bed", "medium", "high", 1, 0, 4.0, "kg"),
        ("Cucumber", "bed", "high", "medium", 1, 1, 2.8, "kg"),
        ("Pepper", "bed", "medium", "high", 1, 1, 1.6, "kg"),
        ("Strawberry", "bed", "medium", "high", 1, 1, 1.2, "kg"),
        ("Basil", "pot", "medium", "high", 0, 1, 0.3, "kg"),
        ("Rosemary", "pot", "low", "high", 0, 1, 0.2, "kg")
    ]
    conn.executemany(
        """
        INSERT INTO plant_catalog
        (name, bed_type, water_need, sun_need, frost_sensitive, heat_sensitive, avg_yield, yield_unit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        plants
    )


def _seed_compat(conn):
    count = conn.execute("SELECT COUNT(*) FROM plant_compat").fetchone()[0]
    if count > 0:
        return

    pairs = [
        ("Tomato", "Potato", "bad", "Tomato and potato are prone to shared diseases."),
        ("Cucumber", "Tomato", "warn", "Cucumber prefers more moisture than tomato."),
        ("Pepper", "Tomato", "good", "Pepper and tomato have similar care needs."),
        ("Strawberry", "Rosemary", "good", "Rosemary helps deter pests near strawberry.")
    ]
    conn.executemany(
        """
        INSERT INTO plant_compat (plant_a, plant_b, level, note)
        VALUES (?, ?, ?, ?)
        """,
        pairs
    )
