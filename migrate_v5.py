import sqlite3
import os

def migrate_v5():
    """
    Database migration V5:
    - Fix NOT NULL constraints on option_a, option_b, option_c, option_d, correct_option
    - SQLite requires creating a new table and copying data to change constraints.
    """
    db_path = 'instance/eduai.db'
    
    if not os.path.exists(db_path):
        print(f"Database fayli topilmadi: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Migratsiya V5 (Constraint Fix) boshlanmoqda...")
        
        # 1. Rename existing table
        print("Eski jadvalni o'zgartirish...")
        cursor.execute("ALTER TABLE question RENAME TO question_old")
        
        # 2. Create new table with CORRECT schema (nullable options)
        print("Yangi jadval yaratish...")
        cursor.execute("""
            CREATE TABLE question (
                id INTEGER PRIMARY KEY,
                question_text TEXT NOT NULL,
                question_type VARCHAR(20) DEFAULT 'multi',
                option_a VARCHAR(200), -- Nullable
                option_b VARCHAR(200), -- Nullable
                option_c VARCHAR(200), -- Nullable
                option_d VARCHAR(200), -- Nullable
                correct_option VARCHAR(1), -- Nullable
                correct_text TEXT,
                code_language VARCHAR(20),
                subject_id INTEGER,
                quiz_id INTEGER,
                points INTEGER DEFAULT 10,
                FOREIGN KEY(subject_id) REFERENCES subject(id),
                FOREIGN KEY(quiz_id) REFERENCES quiz(id)
            )
        """)
        
        # 3. Copy data
        # We need to list columns explicitly to avoid mismatch if schema changed slightly
        # Old table columns: id, question_text, option_a, option_b, option_c, option_d, correct_option, subject_id, quiz_id, points, question_type, correct_text, code_language
        # Note: question_type, correct_text, code_language were added in v4.
        
        # We need to check which columns exist in question_old to be safe
        cursor.execute("PRAGMA table_info(question_old)")
        columns_info = cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        
        print(f"Mavjud ustunlar: {column_names}")
        
        # Construct dynamic insert
        cols_str = ", ".join(column_names)
        
        print("Ma'lumotlarni ko'chirish...")
        cursor.execute(f"""
            INSERT INTO question ({cols_str})
            SELECT {cols_str} FROM question_old
        """)
        
        # 4. Drop old table
        print("Eski jadvalni o'chirish...")
        cursor.execute("DROP TABLE question_old")
        
        conn.commit()
        print("Migratsiya V5 muvaffaqiyatli yakunlandi! Checklarni olib tashlandi.")

    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        if 'question_old' in str(e): # Recovery attempt if it failed partiall
             print("Qayta tiklashga urinish...")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_v5()
