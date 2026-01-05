from app import app, db, User, Subject, TestResult, create_user_progress
from datetime import datetime, timedelta
import random

def create_test_data():
    with app.app_context():
        # Get or create admin user
        user = User.query.filter_by(username='admin').first()
        if not user:
            print("Admin user not found!")
            return

        # Clear existing results for clean test
        TestResult.query.filter_by(user_id=user.id).delete()
        
        subjects = Subject.query.all()
        
        # Generate data for last 30 days
        print("Generating test results...")
        for i in range(20):
            days_ago = random.randint(0, 28)
            date = datetime.now() - timedelta(days=days_ago)
            subject = random.choice(subjects)
            score = random.randint(40, 100)
            
            total_questions = 10
            correct_answers = int(total_questions * (score / 100.0))
            
            result = TestResult(
                user_id=user.id,
                subject_id=subject.id,
                score=score,
                total_questions=total_questions,
                correct_answers=correct_answers,
                completed_at=date
            )
            db.session.add(result)
            
            # Update user progress
            # (In a real app this logic is in the route, but here we just add results)
        
        db.session.commit()
        print(f"Added 20 test results for user {user.username}")

if __name__ == "__main__":
    create_test_data()
