import sqlite3
import os

def migrate_v6():
    """
    Database migration V6:
    - Add quiz_id column to Assignment table linking to quiz.id
    """
    db_path = 'instance/eduai.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Migratsiya V6 (Assignment -> Quiz) boshlanmoqda...")
        
        try:
            print("assignment jadvaliga quiz_id qo'shilmoqda...")
            cursor.execute("ALTER TABLE assignment ADD COLUMN quiz_id INTEGER REFERENCES quiz(id)")
            print("OK.")
        except sqlite3.OperationalError:
            print("quiz_id allaqachon mavjud.")

        conn.commit()
        print("Migratsiya V6 muvaffaqiyatli yakunlandi!")

    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_v6()
