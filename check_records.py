import sqlite3
import os

def check_db(db_path):
    print(f"\nChecking database: {db_path}")
    if not os.path.exists(db_path):
        print("File does not exist.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {[t[0] for t in tables]}")
        
        for table in ['exam', 'exam_section', 'exam_question']:
            if (table,) in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"Row count in '{table}': {count}")
                if count > 0 and table == 'exam':
                    cursor.execute(f"SELECT id, title, exam_type FROM {table}")
                    exams = cursor.fetchall()
                    for e in exams:
                        print(f"  - Exam: {e}")
            else:
                print(f"Table '{table}' does not exist.")
                
        conn.close()
    except Exception as e:
        print(f"Error checking {db_path}: {e}")

if __name__ == "__main__":
    check_db('eduai.db')
    check_db('instance/eduai.db')
