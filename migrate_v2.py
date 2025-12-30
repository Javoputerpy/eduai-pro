import sqlite3
import os
from app import app, db

def migrate():
    print("Migratsiya boshlanmoqda...")
    
    # Message jadvalini yaratish (SQLAlchemy orqali)
    with app.app_context():
        db.create_all()
        print("Jadvallar tekshirildi/yaratildi.")

    # User jadvaliga is_active ustunini qo'shish (SQLite orqali)
    try:
        db_path = os.path.join(app.instance_path, 'eduai.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ustun borligini tekshirish
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_active' not in columns:
            print("'is_active' ustuni qo'shilmoqda...")
            cursor.execute("ALTER TABLE user ADD COLUMN is_active BOOLEAN DEFAULT 1")
            conn.commit()
            print("'is_active' ustuni muvaffaqiyatli qo'shildi.")
        else:
            print("'is_active' ustuni allaqachon mavjud.")
            
        conn.close()
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")

if __name__ == "__main__":
    migrate()
