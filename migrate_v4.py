import sqlite3

def migrate_v4():
    """
    Database migration V4:
    - Add question_type column to Question table
    - Add correct_text column to Question table (for open answers)
    - Add code_language column to Question table (for code questions)
    """
    db_path = 'instance/eduai.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Migratsiya V4 boshlanmoqda...")
        
        # 1. Add question_type
        try:
            print("question_type ustuni qo'shilmoqda...")
            cursor.execute("ALTER TABLE question ADD COLUMN question_type VARCHAR(20) DEFAULT 'multi'")
        except sqlite3.OperationalError:
            print("question_type allaqachon mavjud.")
            
        # 2. Add correct_text
        try:
            print("correct_text ustuni qo'shilmoqda...")
            cursor.execute("ALTER TABLE question ADD COLUMN correct_text TEXT")
        except sqlite3.OperationalError:
            print("correct_text allaqachon mavjud.")
            
        # 3. Add code_language
        try:
            print("code_language ustuni qo'shilmoqda...")
            cursor.execute("ALTER TABLE question ADD COLUMN code_language VARCHAR(20)")
        except sqlite3.OperationalError:
            print("code_language allaqachon mavjud.")

        conn.commit()
        print("Migratsiya V4 muvaffaqiyatli yakunlandi!")

    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_v4()
