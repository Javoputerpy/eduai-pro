from app import app
from models import db, User, Exam, ExamSection, ExamQuestion, Subject
import json

def seed_exams():
    with app.app_context():
        # Create a sample SAT Exam if none exist
        if not Exam.query.filter_by(exam_type='SAT').first():
            print("Seeding sample SAT exam...")
            exam = Exam(
                title="SAT Practice Test #1 (Demo)",
                exam_type="SAT",
                description="Haqiqiy SAT imtihoniga tayyorgarlik uchun simulyatsiya.",
                duration_minutes=180
            )
            db.session.add(exam)
            db.session.flush()

            section = ExamSection(
                exam_id=exam.id,
                title="Reading & Writing Module 1",
                order=1,
                duration_minutes=32
            )
            db.session.add(section)
            db.session.flush()

            # Add some sample questions
            q1 = ExamQuestion(
                section_id=section.id,
                question_text="While many people believe that the first motorized vehicle was created in 1885, Nicolas-Joseph Cugnot had already _____ an experimental steam-powered artillery tractor in 1769.",
                option_a="envisioned",
                option_b="constructed",
                option_c="repudiated",
                option_d="obscured",
                correct_option="B",
                points=10
            )
            
            q2 = ExamQuestion(
                section_id=section.id,
                question_text="Find the value of x in the equation: 2x + 7 = 15",
                option_a="3",
                option_b="4",
                option_c="5",
                option_d="8",
                correct_option="B",
                points=10
            )
            
            db.session.add_all([q1, q2])
            db.session.commit()
            print("SAT seed complete!")

if __name__ == "__main__":
    seed_exams()
