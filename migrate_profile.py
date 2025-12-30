import sqlite3

def migrate_db():
    conn = sqlite3.connect('eduai.db')
    cursor = conn.cursor()
    
    # Check and add 'rank' column
    try:
        cursor.execute("ALTER TABLE user ADD COLUMN rank TEXT DEFAULT 'Yangi a''zo'")
        print("Added 'rank' column")
    except sqlite3.OperationalError:
        print("'rank' column already exists")

    # Check and add 'bio' column
    try:
        cursor.execute("ALTER TABLE user ADD COLUMN bio TEXT")
        print("Added 'bio' column")
    except sqlite3.OperationalError:
        print("'bio' column already exists")

    # Check and add 'phone' column
    try:
        cursor.execute("ALTER TABLE user ADD COLUMN phone TEXT")
        print("Added 'phone' column")
    except sqlite3.OperationalError:
        print("'phone' column already exists")

    conn.commit()
    conn.close()
    print("Migration finished.")

if __name__ == "__main__":
    migrate_db()
