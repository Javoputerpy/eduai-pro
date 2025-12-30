import sqlite3
import os

def migrate_v3():
    db_path = 'instance/eduai.db'
    if not os.path.exists(db_path):
        print(f"Database topilmadi: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Create Quiz table
        print("Quiz jadvali yaratilmoqda...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz (
                id INTEGER PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                teacher_id INTEGER NOT NULL,
                subject_id INTEGER,
                created_at DATETIME,
                FOREIGN KEY(teacher_id) REFERENCES user(id),
                FOREIGN KEY(subject_id) REFERENCES subject(id)
            )
        """)

        # 2. Add quiz_id to question table
        print("Question jadvaliga quiz_id qo'shilmoqda...")
        try:
            cursor.execute("ALTER TABLE question ADD COLUMN quiz_id INTEGER REFERENCES quiz(id)")
        except sqlite3.OperationalError:
            print("quiz_id allaqachon question jadvalida mavjud.")

        # 3. Add quiz_id to test_result table
        print("TestResult jadvaliga quiz_id qo'shilmoqda...")
        try:
            cursor.execute("ALTER TABLE test_result ADD COLUMN quiz_id INTEGER REFERENCES quiz(id)")
        except sqlite3.OperationalError:
            print("quiz_id allaqachon test_result jadvalida mavjud.")

        conn.commit()
        print("Migratsiya v3 muvaffaqiyatli yakunlandi!")

    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_v3()
