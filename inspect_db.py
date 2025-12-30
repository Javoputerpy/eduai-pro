import sqlite3
import os

def list_tables():
    try:
        conn = sqlite3.connect('instance/eduai.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Mavjud jadvallar:", tables)
        conn.close()
    except Exception as e:
        print(f"Xatolik: {e}")

if __name__ == "__main__":
    list_tables()
