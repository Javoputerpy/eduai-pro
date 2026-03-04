import sqlite3
import os

db_path = 'instance/eduai.db'
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Add points column
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN points INTEGER DEFAULT 0;")
        except: pass
        
        conn.commit()
        conn.close()
        print("Successfully added points column to User table.")
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Database not found at {db_path}")
