from app import app, db
import sqlite3

def migrate():
    with app.app_context():
        # Create table manually using SQL because Flask-Migrate is not set up
        # This is a safe way to add a new table in SQLite
        conn = sqlite3.connect('eduai.db')
        cursor = conn.cursor()
        
        try:
            print("Creating 'announcement' table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS announcement (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(200) NOT NULL,
                    content TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME
                )
            ''')
            print("Table 'announcement' created successfully!")
            conn.commit()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            conn.close()

if __name__ == '__main__':
    migrate()
