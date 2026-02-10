# import sqlite3
# conn = sqlite3.connect("growmap.db")
# cursor = conn.cursor()

# cursor.execute("""
# ALTER TABLE map_objects ADD COLUMN points TEXT
# """)

# conn.commit()
# conn.close()
# exit()
# import sqlite3
# conn = sqlite3.connect("growmap.db")
# c = conn.cursor()

# c.execute("DROP TABLE IF EXISTS map_objects")

# conn.commit()
# conn.close()
# exit()
import sqlite3
conn = sqlite3.connect("growmap.db")
c = conn.cursor()

c.execute("""
CREATE TABLE map_objects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    map_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    shape TEXT NOT NULL,

    x REAL,
    y REAL,
    size REAL,
    width REAL,
    height REAL,

    points TEXT,
    color TEXT
)
""")

conn.commit()
conn.close()
exit()
