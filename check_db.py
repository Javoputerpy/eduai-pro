from app import app, db
from models import Subject, Question

with app.app_context():
    subjects = Subject.query.all()
    for s in subjects:
        print(f"Subject: '{s.name}', Code: '{s.code}'")
