import sqlite3
import os

db_path = 'instance/eduai.db'
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE user ADD COLUMN parent_monitoring_code VARCHAR(20);")
        conn.commit()
        conn.close()
        print("Successfully added parent_monitoring_code column.")
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Database not found at {db_path}")
