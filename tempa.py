"""
================================================================================
TEMPORARY DATABASE OPERATIONS FILE
================================================================================

This file is intended for temporary database operations, such as:
- Adding new plants to the plant_catalog table
- Adding new plant compatibility data to the plant_compat table
- Performing database migrations
- Testing database operations before adding them to db.py

IMPORTANT FOR DEPLOYERS:
------------------------
When adding your own values to the database, follow these examples:

1. ADDING PLANTS TO CATALOG:
   Use the same format as in db.py _seed_catalog function:
   
   import sqlite3
   conn = sqlite3.connect("growmap.db")
   c = conn.cursor()
   
   plants = [
       ("PlantName", "bed_type", "water_need", "sun_need", frost_sensitive, heat_sensitive, avg_yield, "yield_unit"),
       # bed_type: "bed" or "pot"
       # water_need: "low", "medium", "high"
       # sun_need: "low", "medium", "high"
       # frost_sensitive: 0 or 1 (boolean)
       # heat_sensitive: 0 or 1 (boolean)
       # Example:
       ("Lettuce", "bed", "high", "medium", 0, 0, 2.5, "kg"),
   ]
   
   c.executemany(
       '''INSERT INTO plant_catalog
       (name, bed_type, water_need, sun_need, frost_sensitive, heat_sensitive, avg_yield, yield_unit)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
       plants
   )
   conn.commit()
   conn.close()

2. ADDING PLANT COMPATIBILITY DATA:
   Use the same format as in db.py _seed_compat function:
   
   import sqlite3
   conn = sqlite3.connect("growmap.db")
   c = conn.cursor()
   
   compat_data = [
       ("plant_a", "plant_b", "level", "note"),
       # level: "good", "neutral", "bad"
       # Example:
       ("Tomato", "Basil", "good", "Basil repels pests"),
       ("Tomato", "Potato", "bad", "Both attract same pests"),
   ]
   
   c.executemany(
       '''INSERT INTO plant_compat (plant_a, plant_b, level, note)
       VALUES (?, ?, ?, ?)''',
       compat_data
   )
   conn.commit()
   conn.close()

3. AFTER RUNNING YOUR OPERATIONS:
   - Test that your changes work correctly
   - Comment out or delete the code you just ran
   - Consider adding permanent changes to db.py instead
   
WARNING: This file should NOT be deployed to production with active code!
After testing, either delete this file or keep only comments.
================================================================================
"""

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
