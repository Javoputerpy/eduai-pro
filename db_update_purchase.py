from app import app, db, init_db

with app.app_context():
    print("Updating database schema...")
    db.create_all()
    print("Database updated!")
