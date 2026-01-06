import os
import sqlalchemy
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_db():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        database_url = 'sqlite:///instance/eduai.db'
    
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    logger.info(f"Connecting to database to check schema...")
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # 1. Check 'user' table
        logger.info("Checking 'user' table...")
        
        # Helper to check if column exists
        def column_exists(table, column):
            if "postgresql" in database_url:
                result = conn.execute(text(
                    f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}'"
                ))
            else: # SQLite
                result = conn.execute(text(f"PRAGMA table_info({table})"))
                return column in [row[1] for row in result]
            
            return result.first() is not None

        # Columns to check in 'user' table
        user_columns = {
            'full_name': 'VARCHAR(100)',
            'rank': 'VARCHAR(50)',
            'bio': 'TEXT',
            'avatar': 'TEXT',
            'is_active': 'BOOLEAN DEFAULT TRUE'
        }
        
        for col, col_type in user_columns.items():
            if not column_exists('user', col):
                logger.info(f"Adding column '{col}' to 'user' table...")
                try:
                    conn.execute(text(f"ALTER TABLE \"user\" ADD COLUMN {col} {col_type}"))
                    conn.commit()
                except Exception as e:
                    logger.error(f"Error adding {col}: {e}")

        # 2. Check 'test_result' table
        test_result_columns = {
            'quiz_id': 'INTEGER',
            'unique_questions_snapshot': 'TEXT',
            'correct_answers': 'INTEGER'
        }
        for col, col_type in test_result_columns.items():
            if not column_exists('test_result', col):
                logger.info(f"Adding column '{col}' to 'test_result' table...")
                try:
                    conn.execute(text(f"ALTER TABLE test_result ADD COLUMN {col} {col_type}"))
                    conn.commit()
                except Exception as e:
                    logger.error(f"Error: {e}")

        # 3. Check 'assignment' table
        if not column_exists('assignment', 'quiz_id'):
            logger.info("Adding 'quiz_id' to 'assignment'...")
            try:
                conn.execute(text("ALTER TABLE assignment ADD COLUMN quiz_id INTEGER"))
                conn.commit()
            except Exception as e:
                logger.error(f"Error: {e}")

        # 4. Check 'question' table
        question_columns = {
            'question_type': 'VARCHAR(20) DEFAULT \'multi\'',
            'correct_text': 'TEXT',
            'code_language': 'VARCHAR(20)',
            'quiz_id': 'INTEGER',
            'points': 'INTEGER DEFAULT 10'
        }
        for col, col_type in question_columns.items():
            if not column_exists('question', col):
                logger.info(f"Adding column '{col}' to 'question' table...")
                try:
                    conn.execute(text(f"ALTER TABLE question ADD COLUMN {col} {col_type}"))
                    conn.commit()
                except Exception as e:
                    logger.error(f"Error: {e}")
        
        # 4. Check for 'literature' table (if it's new)
        # literature table check might be more complex if it doesn't exist at all
        # But db.create_all() in init_db handles entire new tables usually.
        # This script focuses on ALTERing existing tables.
        
    logger.info("Database schema update check completed.")

if __name__ == "__main__":
    update_db()
