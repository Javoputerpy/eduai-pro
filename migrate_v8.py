import sqlite3
import os

db_path = 'instance/eduai.db'
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Add new columns
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN parent_telegram_username VARCHAR(32);")
        except: pass
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN parent_telegram_chat_id VARCHAR(20);")
        except: pass
        
        # Cleanup old column if possible (SQLite doesn't support DROP COLUMN in older versions, 
        # but we can just leave it or rename if needed. Best to just leave it for safety or try/catch)
        conn.commit()
        conn.close()
        print("Successfully updated database schema for automatic notifications.")
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Database not found at {db_path}")
