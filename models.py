from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='student') # student, teacher, admin
    avatar = db.Column(db.Text)
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_active = db.Column(db.Boolean, default=True)
    rank = db.Column(db.String(50), default='Yangi a\'zo')

    # Relationships
    progress = db.relationship('UserProgress', backref='user', lazy=True)
    test_results = db.relationship('TestResult', backref='user', lazy=True)
    groups_taught = db.relationship('Group', backref='teacher', lazy=True)
    purchased_books = db.relationship('Purchase', backref='user', lazy=True)
    group_memberships = db.relationship('GroupMember', backref='student', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_overall_progress(self):
        progresses = UserProgress.query.filter_by(user_id=self.id).all()
        if not progresses:
            return 0
        total = sum([p.progress_percentage for p in progresses])
        return round(total / len(progresses))
    
    def get_tests_taken(self):
        return TestResult.query.filter_by(user_id=self.id).count()
    
    def get_avg_test_score(self):
        avg = db.session.query(db.func.avg(TestResult.score)).filter_by(user_id=self.id).scalar()
        return round(avg) if avg else 0
    
    def get_recent_activity(self, limit=3):
        results = TestResult.query.filter_by(user_id=self.id).order_by(TestResult.completed_at.desc()).limit(limit).all()
        activity = []
        for result in results:
            subject = db.session.get(Subject, result.subject_id) if result.subject_id else None
            if subject:
                activity.append({
                    'title': f'{subject.name} testi',
                    'time': result.completed_at.strftime('%H:%M'),
                    'score': f'{result.score}%',
                    'type_color': 'success' if result.score >= 70 else 'warning'
                })
        return activity
        
    def get_unread_messages_count(self):
        return Message.query.filter_by(recipient_id=self.id, is_read=False).count()

    @property
    def teacher_rank(self):
        if self.role != 'teacher':
            return None
        groups = Group.query.filter_by(teacher_id=self.id).all()
        total_students = 0
        for group in groups:
            total_students += len(group.members)
        if total_students < 10:
            return "Boshlovchi O'qituvchi"
        elif total_students < 50:
            return "Tajribali O'qituvchi"
        return "Ekspert O'qituvchi"

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('literature.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Null for broadcast
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_unique = db.Column(db.Boolean, default=False)
    generation_params = db.Column(db.Text) # JSON string
    
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade="all, delete-orphan")
    results = db.relationship('TestResult', backref='quiz', lazy=True)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    progress_percentage = db.Column(db.Integer, default=0)
    last_activity = db.Column(db.DateTime, default=datetime.now)

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=True)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    correct_answers = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.now)
    unique_questions_snapshot = db.Column(db.Text) # JSON string
    
    subject = db.relationship('Subject', backref='test_results')

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default='multi')
    option_a = db.Column(db.String(200), nullable=True)
    option_b = db.Column(db.String(200), nullable=True)
    option_c = db.Column(db.String(200), nullable=True)
    option_d = db.Column(db.String(200), nullable=True)
    correct_option = db.Column(db.String(1), nullable=True)
    correct_text = db.Column(db.Text, nullable=True)
    code_language = db.Column(db.String(20), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=True)
    points = db.Column(db.Integer, default=10)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.Text)
    code = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    members = db.relationship('GroupMember', backref='group', lazy=True)
    assignments = db.relationship('Assignment', backref='group', lazy=True)

class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.now)

class StudentRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    student = db.relationship('User', foreign_keys=[student_id], backref='sent_enrollment_requests')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='received_enrollment_requests')

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_completed = db.Column(db.Boolean, default=False)
    
    quiz = db.relationship('Quiz', backref='assignments')

class Literature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    author = db.Column(db.String(100))
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_path = db.Column(db.String(300), nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    price = db.Column(db.String(50), nullable=True)
    hashtags = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    uploader = db.relationship('User', backref='uploaded_books')

# Helper functions
def calculate_user_rank(user_id):
    user = db.session.get(User, user_id)
    if not user: return
    total_score = db.session.query(db.func.sum(TestResult.score)).filter_by(user_id=user_id).scalar() or 0
    new_rank = user.rank
    if total_score >= 3000: new_rank = "Ekspert"
    elif total_score >= 1500: new_rank = "Mutaxassis"
    elif total_score >= 500: new_rank = "Bilimdon"
    elif total_score >= 100: new_rank = "Havaskor"
    else: new_rank = "Yangi a'zo"
    if user.rank != new_rank:
        user.rank = new_rank
        db.session.commit()
    return new_rank

def create_user_progress(user_id):
    subjects = Subject.query.all()
    for subject in subjects:
        progress = UserProgress(user_id=user_id, subject_id=subject.id, progress_percentage=0)
        db.session.add(progress)
    db.session.commit()

def get_ai_recommendation(user_id):
    min_progress = UserProgress.query.filter_by(user_id=user_id).order_by(UserProgress.progress_percentage).first()
    if min_progress:
        subject = db.session.get(Subject, min_progress.subject_id)
        return f"{subject.name} bo'yicha 20 daqiqalik dars. Siz bu mavzuda {min_progress.progress_percentage}% bilimga egasiz."
    return "Darslarni boshlash uchun biror fanni tanlang."

def get_last_lesson(user_id):
    last_progress = UserProgress.query.filter_by(user_id=user_id).order_by(UserProgress.last_activity.desc()).first()
    if last_progress:
        subject = db.session.get(Subject, last_progress.subject_id)
        return f"{subject.name} - So'nggi dars"
    return "Hali dars boshlanmagan"

def get_next_recommendation(user_id):
    progresses = UserProgress.query.filter_by(user_id=user_id).all()
    if progresses:
        for progress in progresses:
            if 30 <= progress.progress_percentage < 70:
                subject = Subject.query.get(progress.subject_id)
                return {
                    'title': f'{subject.name} testi',
                    'description': f'Siz {subject.name}da {progress.progress_percentage}% bilimga egasiz. Keyingi bosqichga o\'tish uchun test topshiring.'
                }
    return {
        'title': 'Darslarni boshlash',
        'description': 'Biror fanni tanlab darslarni boshlang.'
    }

def get_user_context(user):
    context_parts = []
    try:
        context_parts.append(f"Foydalanuvchi: {user.username}")
        context_parts.append(f"Umumiy progress: {user.get_overall_progress()}%")
        context_parts.append(f"Testlar soni: {user.get_tests_taken()} ta")
        context_parts.append(f"O'rtacha ball: {user.get_avg_test_score()}%")
        user_progress = UserProgress.query.filter_by(user_id=user.id).all()
        if user_progress:
            context_parts.append("Fanlar progressi:")
            for progress in user_progress:
                subject = Subject.query.get(progress.subject_id)
                if subject:
                    status = "A'lo" if progress.progress_percentage >= 80 else "Yaxshi" if progress.progress_percentage >= 60 else "O'rta" if progress.progress_percentage >= 40 else "Zaif"
                    context_parts.append(f"- {subject.name}: {progress.progress_percentage}% ({status})")
        recent_tests = TestResult.query.filter_by(user_id=user.id).order_by(TestResult.completed_at.desc()).limit(3).all()
        if recent_tests:
            context_parts.append("So'nggi test natijalari:")
            for test in recent_tests:
                subject = Subject.query.get(test.subject_id)
                if subject: context_parts.append(f"- {subject.name}: {test.score}%")
    except Exception as e:
        context_parts.append("Statistika mavjud emas")
    return "\n".join(context_parts)
