from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import random
from ai_model import ai_assistant
import time
import os

import io
from PyPDF2 import PdfReader
from docx import Document

app = Flask(__name__)
app.config['SECRET_KEY'] = 'eduai-pro-super-secret-key-2024'

# Database Configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Fix for Render's postgres:// usage (SQLAlchemy requires postgresql://)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eduai.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db, User, Purchase, Message, Subject, Quiz, Announcement, UserProgress, TestResult, Question, Group, GroupMember, StudentRequest, Assignment, Literature
from models import calculate_user_rank, create_user_progress, get_ai_recommendation, get_last_lesson, get_next_recommendation, get_user_context

# Initialize Login manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Iltimos, tizimga kiring'

# Role based decorators


# OAuth Setup
from authlib.integrations.flask_client import OAuth

app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID', 'your-google-client-id')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET', 'your-google-client-secret')

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openid to fetch user info
    client_kwargs={'scope': 'openid email profile'},
)

@app.route('/login/google')
def login_google():
    google_client = oauth.create_client('google')  # Create client
    redirect_uri = url_for('google_auth', _external=True)
    return google_client.authorize_redirect(redirect_uri)

@app.route('/login/google/callback')
def google_auth():
    google_client = oauth.create_client('google')  # Create client
    token = google_client.authorize_access_token()
    resp = google_client.get('userinfo')
    user_info = resp.json()
    
    # Check if user exists
    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        # Create new user
        # Generate a random password or handle passwordless
        base_username = user_info['email'].split('@')[0]
        cleaned_username = ''.join(e for e in base_username if e.isalnum())
        
        # Ensure unique username
        username = cleaned_username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{cleaned_username}{counter}"
            counter += 1
            
        user = User(
            username=username,
            email=user_info['email'],
            password=generate_password_hash(os.urandom(16).hex()), # Random password
            role='student', # Default role
            rank='Yangi a\'zo'
        )
        db.session.add(user)
        db.session.commit()
    
    login_user(user)
    flash('Muvaffaqiyatli tizimga kirdingiz!', 'success')
    return redirect(url_for('dashboard'))

from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Bu sahifaga kirish uchun admin huquqi talab qilinadi!', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            flash('Bu sahifaga kirish uchun o\'qituvchi huquqi talab qilinadi!', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Blueprint Registration
from admin_file import admin_bp
app.register_blueprint(admin_bp)

# Models and logic moved to models.py

db.init_app(app)
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Case insensitive check
        if User.query.filter(db.func.lower(User.username) == db.func.lower(username)).first():
            flash('Bu username band!', 'error')
            return render_template('register.html')
            
        if User.query.filter_by(email=email).first():
            flash('Bu email band!', 'error')
            return render_template('register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Yangi foydalanuvchi uchun progress yaratish
        create_user_progress(user.id)
        
        login_user(user)
        flash('Muvaffaqiyatli ro\'yxatdan o\'tdingiz!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Sizning hisobingiz vaqtincha muzlatilgan!', 'error')
                return render_template('login.html')

            login_user(user)
            flash(f'Xush kelibsiz, {username}!', 'success')
            
            # Role based redirect
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('dashboard'))

        else:
            flash('Login yoki parol xato!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Siz tizimdan chiqdingiz', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard sahifasi - barcha ma'lumotlar DB dan"""
    
    # Calculate total score from test results
    test_results = TestResult.query.filter_by(user_id=current_user.id).all()
    total_score = sum([r.score for r in test_results]) if test_results else 0
    
    dashboard_data = {
        'overall_progress': current_user.get_overall_progress(),
        'daily_study_time': '45 daqiqa',
        'badges_earned': 0,
        'total_badges': 15,
        'tests_taken': current_user.get_tests_taken(),
        'avg_test_score': current_user.get_avg_test_score(),
'total_score': total_score,
        'avg_score': current_user.get_avg_test_score(),
        'ai_recommendation': get_ai_recommendation(current_user.id),
        'last_lesson': get_last_lesson(current_user.id),
        'gamification': {
            'streak_days': 7,
            'level': 3,
            'points': 450
        },
        'recent_activity': current_user.get_recent_activity(),
        'recent_badges': [],
        'next_recommendation': get_next_recommendation(current_user.id)
    }
    
    return render_template('dashboard.html', **dashboard_data)

@app.route('/learning_center')
@login_required
def learning_center():
    """O'quv markazi sahifasi - darslar va progress fokusida"""
    subjects = Subject.query.all()
    user_progress = UserProgress.query.filter_by(user_id=current_user.id).all()
    
    # Map progress to subject IDs
    subject_progress_dict = {p.subject_id: p.progress_percentage for p in user_progress}
    
    # Global stats
    total_progress = current_user.get_overall_progress()
    completed_subjects = len([p for p in subject_progress_dict.values() if p >= 80])
    in_progress_subjects = len([p for p in subject_progress_dict.values() if 0 < p < 80])
    not_started_subjects = len(subjects) - completed_subjects - in_progress_subjects
    
    return render_template('learning_center.html', 
                         subjects=subjects, 
                         subject_progress=subject_progress_dict,
                         total_progress=total_progress,
                         completed_subjects=completed_subjects,
                         in_progress_subjects=in_progress_subjects,
                         not_started_subjects=not_started_subjects)

@app.route('/test_center')
@login_required
def test_center():
    """Bilim markazi sahifasi - testlar fokusida"""
    subjects = Subject.query.all()
    user_progress = UserProgress.query.filter_by(user_id=current_user.id).all()
    subject_progress_dict = {p.subject_id: p.progress_percentage for p in user_progress}
    
    recent_results = TestResult.query.filter_by(user_id=current_user.id)\
        .order_by(TestResult.completed_at.desc())\
        .limit(5).all()
        
    return render_template('test_center.html', 
                         subjects=subjects, 
                         recent_results=recent_results,
                         subject_progress=subject_progress_dict,
                         total_progress=current_user.get_overall_progress(),
                         completed_subjects=len([p for p in subject_progress_dict.values() if p >= 80]))

@app.route('/start_learning/<subject_code>')
@login_required
def start_learning(subject_code):
    """Start learning wrapper"""
    sub = Subject.query.filter_by(code=subject_code).first()
    if not sub:
        # Fallback to name search
        sub = Subject.query.filter_by(name=subject_code).first()
        
    if sub:
        return redirect(url_for('subject_detail', subject=sub.name))
    
    flash('Fan topilmadi', 'error')
    return redirect(url_for('learning_center'))

@app.route('/achievements')
@login_required
def achievements():
    # 1. Barcha nishonlar ro'yxati (Static definition for now)
    all_badges = [
        {'id': 'first_step', 'name': 'Ilk Qadam', 'icon': 'fa-shoe-prints', 'color': 'primary', 'description': 'Birinchi testni topshirdingiz'},
        {'id': 'high_score', 'name': 'Mergan', 'icon': 'fa-bullseye', 'color': 'danger', 'description': '100% natija qayd etdingiz'},
        {'id': 'active_learner', 'name': 'Faol O\'quvchi', 'icon': 'fa-book-reader', 'color': 'success', 'description': '5 ta test topshirdingiz'},
        {'id': 'consistent', 'name': 'Barqaror', 'icon': 'fa-calendar-check', 'color': 'info', 'description': '3 kun ketma-ket kirdingiz (simulyatsiya)'},
        {'id': 'master', 'name': 'Master', 'icon': 'fa-crown', 'color': 'warning', 'description': 'Umumiy ballingiz 1000 dan oshdi'}
    ]

    # 2. Foydalanuvchi erishgan nishonlarni aniqlash
    user_badges = []
    tests_count = current_user.get_tests_taken()
    total_score = sum([r.score for r in current_user.test_results]) if current_user.test_results else 0
    has_perfect_score = any(r.score == 100 for r in current_user.test_results)

    if tests_count >= 1:
        user_badges.append('first_step')
    if has_perfect_score:
        user_badges.append('high_score')
    if tests_count >= 5:
        user_badges.append('active_learner')
    if total_score >= 1000:
        user_badges.append('master')
    # consistent logikasi murakkabroq, hozircha qo'shmaymiz

    # 3. Ballar tarixi (So'nggi 4 hafta)
    # Bu yerda biz hafta bo'yicha guruhlaymiz
    points_history_labels = []
    points_history_data = []
    
    today = datetime.now()
    for i in range(3, -1, -1):
        start_date = today - timedelta(days=i*7 + 6)
        end_date = today - timedelta(days=i*7)
        label = f"{i+1}-hafta" if i > 0 else "Bu hafta"
        
        # Shu oralıqdagi testlarni yig'amiz
        weekly_score = 0
        for result in current_user.test_results:
            if start_date.date() <= result.completed_at.date() <= end_date.date():
                weekly_score += result.score
        
        points_history_labels.append(label)
        points_history_data.append(weekly_score)

    gamification = {
        'points': total_score,
        'level': current_user.rank or 1 # Agar rank raqam bo'lsa. String bo'lsa o'zgartirish kerak.
    }
    # Agar rank string bo'lsa, levelni hisoblaymiz
    if isinstance(gamification['level'], str):
         gamification['level'] = (total_score // 100) + 1

    return render_template('achievements.html', 
                         all_badges=all_badges, 
                         user_badges=user_badges,
                         gamification=gamification,
                         points_history_labels=points_history_labels,
                         points_history_data=points_history_data,
                         tests_taken=tests_count,
                         perfect_score=1 if has_perfect_score else 0)


@app.route('/progress_analytics')
@login_required
def progress_analytics():
    """Progress tahlili sahifasi"""
    subjects = Subject.query.all()
    
    # Calculate trend data (simple mock for now based on recent results)
    import datetime
    dates = []
    scores = []
    today = datetime.datetime.now()
    for i in range(6, -1, -1):
        d = today - datetime.timedelta(days=i)
        dates.append(d.strftime("%Y-%m-%d"))
        # Mock logic: average score for that day or random if no data
        # improved: fetch actual daily averages
        # Improved date filtering for SQLite compatibility
        # We filter by day boundaries
        day_start = datetime.datetime.combine(d.date(), datetime.time.min)
        day_end = datetime.datetime.combine(d.date(), datetime.time.max)
        
        results = TestResult.query.filter(
            TestResult.completed_at >= day_start,
            TestResult.completed_at <= day_end,
            TestResult.user_id == current_user.id
        ).all()
        
        if results:
            daily_avg = sum([r.score for r in results]) / len(results)
        else:
            daily_avg = 0
            
        scores.append(round(daily_avg))

    # AI Insights (Mock)
    ai_insights = [
        "Sizning matematikadan o'zlashtirishingiz 15% ga oshdi.",
        "Fizika faniga ko'proq e'tibor qaratishingiz tavsiya etiladi."
    ]

    # Fetch recent test results for the template
    test_results = TestResult.query.filter_by(user_id=current_user.id).order_by(TestResult.completed_at.desc()).limit(10).all()

    return render_template('progress_analytics.html', 
                         subjects=subjects,
                         trend_labels=dates,
                         trend_data=scores,
                         ai_insights=ai_insights,
                         test_results=test_results)

@app.route('/api/user/mini-profile/<int:user_id>')
@login_required
def api_user_mini_profile(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Foydalanuvchi topilmadi'}), 404
        
    # Check if a request already exists
    existing_request = StudentRequest.query.filter_by(
        student_id=current_user.id,
        teacher_id=user_id
    ).first()
    
    data = {
        'id': user.id,
        'username': user.username,
        'full_name': user.full_name or user.username,
        'avatar': user.avatar,
        'bio': user.bio or "Ushbu foydalanuvchi haqida ma'lumot yo'q.",
        'role': user.role,
        'rank': user.rank,
        'joined_at': user.created_at.strftime('%Y-%m-%d'),
        'stats': {
            'tests': user.get_tests_taken(),
            'avg_score': user.get_avg_test_score(),
            'progress': user.get_overall_progress()
        },
        'request_status': existing_request.status if existing_request else None
    }
    
    if user.role == 'teacher':
        data['teacher_rank'] = user.teacher_rank
        data['students_count'] = sum(len(g.members) for g in user.groups_taught)
        
    return jsonify(data)

@app.route('/api/enroll/request', methods=['POST'])
@login_required
def api_request_enrollment():
    teacher_id = request.json.get('teacher_id')
    if not teacher_id:
        return jsonify({'error': 'O\'qituvchi ID ko\'rsatilmadi'}), 400
        
    if current_user.id == teacher_id:
        return jsonify({'error': 'O\'zingizga so\'rov yubora olmaysiz'}), 400
        
    existing = StudentRequest.query.filter_by(
        student_id=current_user.id,
        teacher_id=teacher_id
    ).first()
    
    if existing:
        return jsonify({'error': 'Siz allaqachon so\'rov yuborgansiz'}), 400
        
    req = StudentRequest(student_id=current_user.id, teacher_id=teacher_id)
    db.session.add(req)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'So\'rov muvaffaqiyatli yuborildi'})

@app.route('/api/enroll/handle', methods=['POST'])
@teacher_required
def api_handle_enrollment():
    request_id = request.json.get('request_id')
    action = request.json.get('action') # accept, reject
    
    req = StudentRequest.query.get_or_404(request_id)
    if req.teacher_id != current_user.id:
        return jsonify({'error': 'Ruxsat berilmagan'}), 403
        
    if action == 'accept':
        req.status = 'accepted'
        # Add to teacher's first group or create one
        group = Group.query.filter_by(teacher_id=current_user.id).first()
        if not group:
            # Create a default group
            group = Group(
                name="Sinfim",
                teacher_id=current_user.id,
                code=os.urandom(4).hex().upper()
            )
            db.session.add(group)
            db.session.flush()
            
        # Add student to group
        member = GroupMember(group_id=group.id, student_id=req.student_id)
        db.session.add(member)
        
    elif action == 'reject':
        req.status = 'rejected'
        
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/ai/chat', methods=['POST'])
@login_required
def ai_chat():
    """AI suhbat API"""
    try:
        data = request.get_json()
        print(f"📨 Kelgan data: {data}")
        
        user_message = data.get('message', '').strip()
        print(f"📝 Foydalanuvchi xabari: {user_message}")
        
        if not user_message:
            return jsonify({
                'success': False,
                'response': "Iltimos, xabar kiriting."
            })
        
        # Foydalanuvchi kontekstini olish
        user_context = get_user_context(current_user)
        print(f"👤 Foydalanuvchi konteksti: {user_context[:200]}...")
        
        # AI javobini olish
        print("🔄 AI ga so'rov yuborilmoqda...")
        ai_response = ai_assistant.generate_response(user_message, user_context)
        print(f"🤖 AI javobi: {ai_response}")
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        return jsonify({
            'success': False,
            'response': f"Xatolik yuz berdi: {str(e)}"
        })

@app.route('/api/ai/analyze_progress', methods=['POST'])
@login_required
def analyze_progress():
    """Progress tahlili API"""
    try:
        user_context = get_user_context(current_user)
        
        analysis_prompt = """
        Quyidagi o'quvchi statistikasini tahlil qiling va quyidagilarni tavsiya bering:
        1. Kuchli tomonlari
        2. Zaif tomonlari  
        3. Takomillashtirish uchun tavsiyalar
        4. Keyingi qadamlar
        
        Javob qisqa va amaliy bo'lsin.
        """
        
        ai_response = ai_assistant.generate_response(analysis_prompt, user_context)
        
        return jsonify({
            'success': True,
            'analysis': ai_response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'analysis': f"Tahlil qilishda xatolik: {str(e)}"
        })

@app.route('/api/ai/subject_help', methods=['POST'])
@login_required
def subject_help():
    """Fan bo'yicha yordam API"""
    try:
        data = request.get_json()
        subject_name = data.get('subject', '')
        topic = data.get('topic', '')
        
        user_context = get_user_context(current_user)
        
        help_prompt = f"""
        {subject_name} fanining {topic} mavzusini tushuntirib bering.
        Oddiy va tushunarli tilda, misollar bilan izohlang.
        """
        
        ai_response = ai_assistant.generate_response(help_prompt, user_context)
        
        return jsonify({
            'success': True,
            'explanation': ai_response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'explanation': f"Tushuntirishda xatolik: {str(e)}"
        })

@app.route('/api/ai/test_advice', methods=['POST'])
@login_required
def test_advice():
    """Testga tayyorgarlik bo'yicha maslahat"""
    try:
        data = request.get_json()
        subject_name = data.get('subject', '')
        
        user_context = get_user_context(current_user)
        
        advice_prompt = f"""
        {subject_name} fanidan testga qanday tayyorlanish kerak?
        Quyidagilarni tavsiya bering:
        1. Asosiy mavzular
        2. Tushuncha tekshirish usullari
        3. Vaqtni boshqarish
        4. Test strategiyalari
        
        Javob qisqa va amaliy bo'lsin.
        """
        
        ai_response = ai_assistant.generate_response(advice_prompt, user_context)
        
        return jsonify({
            'success': True,
            'advice': ai_response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'advice': f"Maslahat olishda xatolik: {str(e)}"
        })

@app.route('/study_plans')
@login_required
def study_plans():
    weekly_plan = [
        {'day': 'Dushanba', 'subject': 'Matematika', 'completed': True},
        {'day': 'Seshanba', 'subject': 'Fizika', 'completed': True},
        {'day': 'Chorshanba', 'subject': 'Ingliz tili', 'completed': False},
        {'day': 'Payshanba', 'subject': 'Informatika', 'completed': False},
        {'day': 'Juma', 'subject': 'Matematika', 'completed': False},
        {'day': 'Shanba', 'subject': 'Fizika', 'completed': False},
        {'day': 'Yakshanba', 'subject': 'Dam olish', 'completed': False},
    ]
    return render_template('study_plans.html', weekly_plan=weekly_plan)

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/leaderboard')
@login_required
def leaderboard():
    """Reyting sahifasi"""
    # 1. O'quvchilar reytingi (Faqat studentlar)
    student_scores = db.session.query(
        User,
        db.func.coalesce(db.func.sum(TestResult.score), 0).label('total_score'),
        db.func.count(TestResult.id).label('tests_taken')
    ).filter(User.role == 'student').outerjoin(TestResult, User.id == TestResult.user_id).group_by(User.id).order_by(db.desc('total_score')).all()
    
    student_leaders = []
    for i, (user, total_score, tests_taken) in enumerate(student_scores, 1):
        # Darajani hisoblash
        level = min(10, (total_score or 0) // 100 + 1) if total_score else 1
        
        student_leaders.append({
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'points': total_score or 0,
            'level': level,
            'rank': i,
            'tests_taken': tests_taken or 0,
            'avatar': user.avatar,
            'role': user.role
        })
    
    # 2. O'qituvchilar reytingi (O'quvchilar soniga qarab)
    teachers = User.query.filter_by(role='teacher').all()
    teacher_leaders = []
    
    for teacher in teachers:
        # O'quvchilar sonini hisoblash
        students_count = 0
        for group in teacher.groups_taught:
            students_count += len(group.members)
            
        teacher_leaders.append({
            'id': teacher.id,
            'username': teacher.username,
            'full_name': teacher.full_name,
            'students_count': students_count,
            'groups_count': len(teacher.groups_taught),
            'rank_title': teacher.teacher_rank or "O'qituvchi",
            'avatar': teacher.avatar
        })
    
    # Sort teachers by student count desc
    teacher_leaders.sort(key=lambda x: x['students_count'], reverse=True)
    
    # Add rank number
    for i, t in enumerate(teacher_leaders, 1):
        t['rank'] = i
    
    # Agar joriy foydalanuvchi student bo'lsa va ro'yxatda bo'lmasa (Pagination bo'lsa kerak edi, lekin hozircha hammasi chiqadi)
    # Hozircha hammasini chiqaramiz, shuning uchun "current_user_in_list" shart emas.
    return render_template('leaderboard.html', 
                         student_leaders=student_leaders,
                         teacher_leaders=teacher_leaders,
                         current_user=current_user)

@app.route('/profile')
@login_required
def profile():
    """Profil sahifasi"""
    subjects = Subject.query.all()
    
    # So'nggi test natijalari
    recent_results = TestResult.query.filter_by(user_id=current_user.id)\
        .order_by(TestResult.completed_at.desc())\
        .limit(5)\
        .all()
    
    return render_template('profile.html', 
                         user=current_user,
                         subjects=subjects,
                         recent_results=recent_results)

@app.route('/api/update_avatar', methods=['POST'])
@login_required
def api_update_avatar():
    """Avatar yangilash"""
    data = request.get_json()
    avatar = data.get('avatar')
    avatar_type = data.get('type', 'emoji')
    
    if not avatar:
        return jsonify({'success': False, 'error': 'Avatar talab qilinadi'})
    
    try:
        current_user.avatar = avatar
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update_profile', methods=['POST'])
@login_required
def api_update_profile():
    """Profil ma'lumotlarini yangilash"""
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    bio = data.get('bio', '').strip()
    
    # Validatsiya
    if not username or not email:
        return jsonify({'success': False, 'error': 'Username va email talab qilinadi'})
    
    try:
        # Username tekshirish
        if username != current_user.username:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                return jsonify({'success': False, 'error': 'Bu username band!'})
        
        # Email tekshirish
        if email != current_user.email:
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                return jsonify({'success': False, 'error': 'Bu email band!'})
        
        # Yangilash
        current_user.username = username
        current_user.email = email
        current_user.bio = bio
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Profil ma'lumotlarini yangilash (Form)"""
    try:
        current_user.full_name = request.form.get('full_name')
        current_user.bio = request.form.get('bio')
        current_user.avatar = request.form.get('avatar')
        
        new_password = request.form.get('new_password')
        if new_password:
            current_user.set_password(new_password)
            
        db.session.commit()
        flash('Profil muvaffaqiyatli yangilandi!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Xatolik: {str(e)}', 'error')
        
    return redirect(url_for('profile'))

@app.route('/api/start_test/<int:subject_id>')
@login_required
def api_start_test(subject_id):
    """Test boshlash API"""
    try:
        subject = Subject.query.get_or_404(subject_id)
        
        # Misol savollar - keyinchalik Question modelidan olish mumkin
        questions = generate_sample_questions(subject.name)
        
        return jsonify({
            'success': True,
            'subject': subject.name,
            'questions': questions
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_sample_questions(subject_name):
    """Misol test savollarini yaratish"""
    if 'matematika' in subject_name.lower():
        return [
            {
                'id': 1,
                'question_text': '2 + 2 nechaga teng?',
                'options': {'A': '3', 'B': '4', 'C': '5', 'D': '6'},
                'correct_option': 'B'
            },
            {
                'id': 2,
                'question_text': '5 × 3 nechaga teng?',
                'options': {'A': '8', 'B': '12', 'C': '15', 'D': '18'},
                'correct_option': 'C'
            },
            {
                'id': 3,
                'question_text': '10 - 4 nechaga teng?',
                'options': {'A': '4', 'B': '5', 'C': '6', 'D': '7'},
                'correct_option': 'C'
            },
            {
                'id': 4,
                'question_text': '8 ÷ 2 nechaga teng?',
                'options': {'A': '2', 'B': '3', 'C': '4', 'D': '5'},
                'correct_option': 'C'
            },
            {
                'id': 5,
                'question_text': '3² nechaga teng?',
                'options': {'A': '6', 'B': '9', 'C': '12', 'D': '15'},
                'correct_option': 'B'
            }
        ]
    elif 'fizika' in subject_name.lower():
        return [
            {
                'id': 1,
                'question_text': 'Yerning tortishish tezlanishi qancha?',
                'options': {'A': '5 m/s²', 'B': '9.8 m/s²', 'C': '12 m/s²', 'D': '15 m/s²'},
                'correct_option': 'B'
            },
            {
                'id': 2,
                'question_text': 'Tezlik formulasi qanday?',
                'options': {'A': 'v = s/t', 'B': 'v = t/s', 'C': 'v = s×t', 'D': 'v = s+t'},
                'correct_option': 'A'
            }
        ]
    else:
        return [
            {
                'id': 1,
                'question_text': f'{subject_name} fanining asosiy tushunchasi nima?',
                'options': {'A': 'Tushuncha A', 'B': 'Tushuncha B', 'C': 'Tushuncha C', 'D': 'Tushuncha D'},
                'correct_option': 'A'
            },
            {
                'id': 2,
                'question_text': f'{subject_name} fanida qanday usullar qo\'llaniladi?',
                'options': {'A': 'Usul 1', 'B': 'Usul 2', 'C': 'Usul 3', 'D': 'Usul 4'},
                'correct_option': 'B'
            }
        ]

@app.route('/api/submit_test', methods=['POST'])
@login_required
def api_submit_test():
    """Test natijalarini qabul qilish"""
    try:
        data = request.get_json()
        subject_id = data.get('subject_id')
        subject_name = data.get('subject_name')
        user_answers = data.get('answers', {})
        score = data.get('score', 0)
        correct_answers = data.get('correct_answers', 0)
        total_questions = data.get('total_questions', 0)
        
        # Subjectni topish
        subject = Subject.query.get(subject_id)
        if not subject:
            return jsonify({'error': 'Fan topilmadi'}), 404
        
        # Test natijasini saqlash
        test_result = TestResult(
            user_id=current_user.id,
            subject_id=subject.id,
            score=score,
            total_questions=total_questions,
            correct_answers=correct_answers
        )
        db.session.add(test_result)
        
        # Progress yangilash
        user_progress = UserProgress.query.filter_by(
            user_id=current_user.id, 
            subject_id=subject.id
        ).first()
        if user_progress:
            user_progress.progress_percentage = max(user_progress.progress_percentage, score)
            user_progress.last_activity = datetime.now()
        else:
            user_progress = UserProgress(
                user_id=current_user.id,
                subject_id=subject.id,
                progress_percentage=score
            )
            db.session.add(user_progress)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'score': score,
            'points': score * 10,  # Ballarni hisoblash
            'message': 'Test natijalari muvaffaqiyatli saqlandi!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice_query', methods=['POST'])
@login_required
def api_voice_query():
    data = request.get_json()
    responses = [
        "Bu juda yaxshi savol! Men sizga yordam berishdan xursandman.",
        "Keling, bu mavzuni batafsil o'rganamiz.",
        "Sizning savolingizni tushundim. Quyidagi misol orqali tushuntiraman.",
        "Ajoyib savol! Buni quyidagi usulda yechish mumkin."
    ]
    return jsonify({
        'success': True,
        'response': random.choice(responses)
    })

@app.route('/api/progress_data')
@login_required
def api_progress_data():
    # DB dan progress ma'lumotlarini olish
    user_progress = UserProgress.query.filter_by(user_id=current_user.id).all()
    
    labels = []
    data = []
    
    for progress in user_progress:
        subject = Subject.query.get(progress.subject_id)
        labels.append(subject.name)
        data.append(progress.progress_percentage)
    
    
    return jsonify({
        'labels': labels,
        'data': data
    })

# Admin Routes
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # Basic Stats
    stats = {
        'total_users': User.query.count(),
        'teachers': User.query.filter_by(role='teacher').count(),
        'students': User.query.filter_by(role='student').count(),
        'groups': Group.query.count(),
        'total_tests': TestResult.query.count(),
        'total_purchases': Purchase.query.count()
    }
    
    # Activity Feeds
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_tests = TestResult.query.order_by(TestResult.id.desc()).limit(5).all() # Assuming id implies time, or use completed_at if available
    recent_purchases = Purchase.query.order_by(Purchase.date.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_users=recent_users,
                         recent_tests=recent_tests,
                         recent_purchases=recent_purchases)

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/create_teacher', methods=['POST'])
@admin_required
def create_teacher():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if User.query.filter_by(username=username).first():
        flash('Bu username band!', 'error')
        return redirect(url_for('admin_users'))
        
    if User.query.filter_by(email=email).first():
        flash('Bu email band!', 'error')
        return redirect(url_for('admin_users'))
    
    user = User(username=username, email=email, role='teacher')
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    flash('O\'qituvchi muvaffaqiyatli yaratildi!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/teacher/dashboard')
@teacher_required
def teacher_dashboard():
    groups = Group.query.filter_by(teacher_id=current_user.id).all()
    assignments = Assignment.query.filter(Assignment.group_id.in_([g.id for g in groups])).order_by(Assignment.created_at.desc()).limit(5).all() if groups else []
    pending_requests = StudentRequest.query.filter_by(teacher_id=current_user.id, status='pending').all()
    return render_template('teacher/dashboard.html', groups=groups, assignments=assignments, pending_requests=pending_requests, now=datetime.now())

@app.route('/teacher/groups/create', methods=['POST'])
@teacher_required
def create_group():
    name = request.form.get('name')
    description = request.form.get('description')
    
    # Generate unique 6-digit code
    while True:
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        if not Group.query.filter_by(code=code).first():
            break
            
    group = Group(
        name=name,
        description=description,
        teacher_id=current_user.id,
        code=code
    )
    db.session.add(group)
    db.session.commit()
    
    flash('Guruh muvaffaqiyatli yaratildi! Kod: ' + code, 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/groups/<int:id>')
@teacher_required
def teacher_group_detail(id):
    group = Group.query.get_or_404(id)
    if group.teacher_id != current_user.id:
        flash('Huquq yo\'q!', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    # Guruh a'zolarini olish
    members = db.session.query(User).join(GroupMember).filter(GroupMember.group_id == group.id).all()
    
    # O'qituvchining testlari
    quizzes = Quiz.query.filter_by(teacher_id=current_user.id).all()
    
    return render_template('teacher/group_detail.html', group=group, members=members, quizzes=quizzes)

@app.route('/teacher/assignment/create', methods=['POST'])
@teacher_required
def create_assignment():
    """Yangi vazifa yaratish"""
    try:
        group_id = request.form.get('group_id')
        group = Group.query.get_or_404(group_id)
        
        if group.teacher_id != current_user.id:
            flash('Ruxsat yo\'q!', 'error')
            return redirect(url_for('teacher_dashboard'))
            
        title = request.form.get('title')
        description = request.form.get('description')
        due_date = request.form.get('due_date')
        quiz_id = request.form.get('quiz_id')
        
        assignment = Assignment(
            group_id=group.id,
            title=title,
            description=description,
            due_date=datetime.strptime(due_date, '%Y-%m-%dT%H:%M') if due_date else None,
            quiz_id=int(quiz_id) if quiz_id else None
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        flash('Vazifa muvaffaqiyatli qo\'shildi!', 'success')
        return redirect(url_for('teacher_group_detail', id=group.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Xatolik: {str(e)}', 'error')
        return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/api/add_student', methods=['POST'])
@teacher_required
def add_student_to_group():
    data = request.get_json()
    group_id = data.get('group_id')
    student_username = data.get('username') # Username or email
    
    group = Group.query.get(group_id)
    if not group or group.teacher_id != current_user.id:
        return jsonify({'success': False, 'error': 'Guruh topilmadi yoki ruxsat yo\'q'})
        
    student = User.query.filter((User.username==student_username) | (User.email==student_username)).first()
    if not student or student.role != 'student':
        return jsonify({'success': False, 'error': 'O\'quvchi topilmadi'})
        
    if GroupMember.query.filter_by(group_id=group.id, student_id=student.id).first():
        return jsonify({'success': False, 'error': 'O\'quvchi allaqachon guruhda'})
        
    member = GroupMember(group_id=group.id, student_id=student.id)
    db.session.add(member)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/teacher/student/<int:id>')
@teacher_required
def view_student_profile(id):
    """O'quvchi profilini ko'rish (O'qituvchi uchun)"""
    student = User.query.get_or_404(id)
    if student.role != 'student':
        flash('Faqat o\'quvchilar profilini ko\'rish mumkin', 'error')
        return redirect(url_for('teacher_dashboard'))
        
    subjects = Subject.query.all()
    recent_results = TestResult.query.filter_by(user_id=student.id).order_by(TestResult.completed_at.desc()).limit(5).all()
    
    return render_template('profile.html', user=student, subjects=subjects, recent_results=recent_results)

@app.route('/teacher/student/<int:id>/rank', methods=['POST'])
@teacher_required
def set_student_rank(id):
    """O'quvchiga daraja berish"""
    student = User.query.get_or_404(id)
    rank = request.form.get('rank')
    
    if rank:
        student.rank = rank
        db.session.commit()
        flash(f'{student.username} darajasi yangilandi!', 'success')
        
    return redirect(url_for('view_student_profile', id=id))



@app.route('/api/user_stats')
@login_required
def api_user_stats():
    """Foydalanuvchi statistikasi - DB dan"""
    stats = {
        'overall_progress': current_user.get_overall_progress(),
        'tests_taken': current_user.get_tests_taken(),
        'avg_score': current_user.get_avg_test_score(),
        'total_subjects': UserProgress.query.filter_by(user_id=current_user.id).count(),
        'completed_subjects': UserProgress.query.filter_by(user_id=current_user.id).filter(UserProgress.progress_percentage >= 70).count()
    }
    
    
    return jsonify(stats)

@app.route('/messages')
@login_required
def view_messages():
    messages = Message.query.filter_by(recipient_id=current_user.id).order_by(Message.created_at.desc()).all()
    # Mark as read
    for msg in messages:
        if not msg.is_read:
            msg.is_read = True
    db.session.commit()
    return render_template('messages.html', messages=messages)

@app.route('/admin/message/send', methods=['POST'])
@admin_required
def send_message():
    recipient_id = request.form.get('recipient_id')
    content = request.form.get('content')
    
    if recipient_id == 'all':
        users = User.query.filter(User.role != 'admin').all()
        for user in users:
            msg = Message(sender_id=current_user.id, recipient_id=user.id, content=content)
            db.session.add(msg)
        flash(f'{len(users)} ta foydalanuvchiga xabar yuborildi', 'success')
    else:
        msg = Message(sender_id=current_user.id, recipient_id=recipient_id, content=content)
        db.session.add(msg)
        flash('Xabar yuborildi', 'success')
        
    db.session.commit()
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:id>/delete', methods=['POST'])
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.role == 'admin':
        flash('Adminni o\'chirib bo\'lmaydi!', 'error')
        return redirect(url_for('admin_users'))
        
    # Manually delete related records
    try:
        TestResult.query.filter_by(user_id=user.id).delete()
        UserProgress.query.filter_by(user_id=user.id).delete()
        GroupMember.query.filter_by(student_id=user.id).delete()
        Message.query.filter((Message.sender_id==user.id) | (Message.recipient_id==user.id)).delete()
        
        # If teacher, also delete quizzes, groups, assignments
        if user.role == 'teacher':
            quizzes = Quiz.query.filter_by(teacher_id=user.id).all()
            for q in quizzes:
                # Question delete cascade is set in model, but results?
                # Results will be deleted via cascade if set, otherwise manual
                pass
            Quiz.query.filter_by(teacher_id=user.id).delete()
            
            groups = Group.query.filter_by(teacher_id=user.id).all()
            for g in groups:
                 Assignment.query.filter_by(group_id=g.id).delete()
                 GroupMember.query.filter_by(group_id=g.id).delete()
            Group.query.filter_by(teacher_id=user.id).delete()

        db.session.delete(user)
        db.session.commit()
        flash('Foydalanuvchi va barcha bog\'liq ma\'lumotlar o\'chirildi', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Xatolik yuz berdi: {str(e)}', 'error')
        
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:id>/edit', methods=['POST'])
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    
    existing_user = User.query.filter(User.username == username).first()
    if existing_user and existing_user.id != user.id:
        flash('Bu username band', 'error')
        return redirect(url_for('admin_users'))
        
    user.username = username
    user.email = email
    
    if password:
        user.set_password(password)
        
    db.session.commit()
    flash('Ma\'lumotlar yangilandi', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:id>/toggle_status', methods=['POST'])
@admin_required
def toggle_user_status(id):
    user = User.query.get_or_404(id)
    if user.role == 'admin':
        flash('Adminni muzlatib bo\'lmaydi!', 'error')
        return redirect(url_for('admin_users'))
        
    user.is_active = not user.is_active
    db.session.commit()
    
    status = "faollashtirildi" if user.is_active else "muzlatildi"
    flash(f'Foydalanuvchi {status}', 'success')
    return redirect(url_for('admin_users'))

@app.context_processor
def inject_messages():
    context = {}
    if current_user.is_authenticated:
        unread_count = current_user.get_unread_messages_count()
        context['unread_messages_count'] = unread_count
        
    # Global announcements (last 3 active)
    announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.created_at.desc()).limit(3).all()
    context['global_announcements'] = announcements
    
    return context

@app.route('/student/join_group', methods=['POST'])
@login_required
def join_group():
    code = request.form.get('code')
    group = Group.query.filter_by(code=code).first()
    
    if not group:
        flash('Guruh topilmadi!', 'error')
        return redirect(url_for('dashboard'))
        
    if GroupMember.query.filter_by(group_id=group.id, student_id=current_user.id).first():
        flash('Siz allaqachon bu guruhga a\'zosiz!', 'info')
        return redirect(url_for('dashboard'))
        
    member = GroupMember(group_id=group.id, student_id=current_user.id)
    db.session.add(member)
    db.session.commit()
    
    flash(f'{group.name} guruhiga muvaffaqiyatli qo\'shildingiz!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/start_learning/<subject>')
@login_required
def subject_detail(subject):
    """Fan detail sahifasi"""
    
    # DB dan fan ma'lumotlarini olish
    subject_obj = Subject.query.filter_by(name=subject).first()
    if not subject_obj:
        flash('Fan topilmadi!', 'error')
        return redirect(url_for('learning_center'))
    
    # Foydalanuvchining progressi
    user_progress = UserProgress.query.filter_by(
        user_id=current_user.id, 
        subject_id=subject_obj.id
    ).first()
    
    progress_value = user_progress.progress_percentage if user_progress else 0
    
    # Mock data for lessons (keyin DB ga qo'shamiz)
    subject_data = {
        'matematika': {
            'progress': progress_value,
            'lessons': {
                'basic': [
                    {'title': 'Chiziqli tenglamalar', 'duration': 15, 'difficulty': 'Beginner', 'difficulty_color': 'success', 'progress': 75},
                    {'title': 'Kvadrat tenglamalar', 'duration': 20, 'difficulty': 'Intermediate', 'difficulty_color': 'warning', 'progress': 40},
                    {'title': 'Funksiyalar asoslari', 'duration': 25, 'difficulty': 'Beginner', 'difficulty_color': 'success', 'progress': 60}
                ],
                'formulas': [
                    {'title': 'Algebraik formulalar', 'duration': 18, 'progress': 30},
                    {'title': 'Geometrik formulalar', 'duration': 22, 'progress': 20}
                ]
            },
            'hints': [
                {'title': 'Kvadrat tenglama', 'formula': 'ax² + bx + c = 0'},
                {'title': 'Chiziqli funksiya', 'formula': 'y = mx + b'},
                {'title': 'Pifagor teoremasi', 'formula': 'a² + b² = c²'}
            ]
        }
    }
    
    data = subject_data.get(subject, {
        'progress': progress_value,
        'lessons': {'basic': [], 'formulas': []},
        'hints': []
    })
    
    # Leaderboard
    subject_leaderboard = db.session.query(
        User.username,
        db.func.sum(TestResult.score).label('total_score')
    ).join(TestResult).filter(TestResult.subject_id == subject_obj.id).group_by(User.id).order_by(db.desc('total_score')).limit(5).all()
    
    leaderboard_data = []
    for i, (username, score) in enumerate(subject_leaderboard, 1):
        leaderboard_data.append({
            'name': username,
            'points': score or 0,
            'rank': i,
            'current': username == current_user.username
        })
    
    return render_template('subject_detail.html', 
                         progress=data['progress'],
                         lessons=data['lessons'],
                         hints=data['hints'],
                         leaderboard=leaderboard_data)

# === ADMIN EXPANSION ROUTES ===
@app.route('/admin/announcements')
@admin_required
def admin_announcements():
    """E'lonlar boshqaruvi"""
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('admin/announcements.html', announcements=announcements)

@app.route('/admin/announcement/create', methods=['POST'])
@admin_required
def create_announcement():
    title = request.form.get('title')
    content = request.form.get('content')
    
    if title and content:
        announcement = Announcement(title=title, content=content)
        db.session.add(announcement)
        db.session.commit()
        flash('E\'lon yaratildi!', 'success')
    else:
        flash('Barcha maydonlarni to\'ldiring', 'error')
        
    return redirect(url_for('admin_announcements'))

@app.route('/admin/announcement/<int:id>/delete', methods=['POST'])
@admin_required
def delete_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    db.session.delete(announcement)
    db.session.commit()
    flash('E\'lon o\'chirildi', 'success')
    return redirect(url_for('admin_announcements'))

@app.route('/admin/content')
@admin_required
def admin_content():
    """Kontent boshqaruvi (Fanlar va Kitoblar)"""
    subjects = Subject.query.all()
    books = Literature.query.all()
    return render_template('admin/content_manager.html', subjects=subjects, books=books)

@app.route('/admin/subject/<int:id>/delete', methods=['POST'])
@admin_required
def delete_subject(id):
    subject = Subject.query.get_or_404(id)
    # Check for related data
    if UserProgress.query.filter_by(subject_id=id).first():
        flash('Bu fanga bog\'liq ma\'lumotlar (progress) mavjud, o\'chirib bo\'lmaydi!', 'error')
    else:
        return redirect(url_for('subject_detail', id=sub.id))
    
    flash('Fan topilmadi', 'error')
    return redirect(url_for('learning_center'))

@app.route('/ai-tutor')
@login_required
def ai_tutor_page():
    return render_template('ai_tutor.html')

# === LITERATURE (LIBRARY) SECTION ===
@app.route('/library')
def library():
    """Kutubxona asosiy sahifasi"""
    query = request.args.get('q', '')
    filter_type = request.args.get('type', 'all')
    
    books_query = Literature.query
    
    if query:
        search_term = f"%{query}%"
        if filter_type == 'author':
            books_query = books_query.filter(Literature.author.ilike(search_term))
        elif filter_type == 'user':
            books_query = books_query.join(User).filter(User.username.ilike(search_term))
        elif filter_type == 'tag':
            books_query = books_query.filter(Literature.hashtags.ilike(search_term))
        else:
            # General search
            books_query = books_query.join(User).filter(
                db.or_(
                    Literature.title.ilike(search_term),
                    Literature.author.ilike(search_term),
                    Literature.hashtags.ilike(search_term),
                    User.username.ilike(search_term)
                )
            )
            
    books = books_query.order_by(Literature.created_at.desc()).all()
    return render_template('library.html', books=books, query=query)

from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'epub'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/library/upload', methods=['GET', 'POST'])
@login_required
def upload_book():
    """Kitob yuklash"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Fayl tanlanmadi', 'error')
            return redirect(request.url)
            
        file = request.files['file']
        title = request.form.get('title')
        description = request.form.get('description')
        author = request.form.get('author')
        is_paid = request.form.get('is_paid') == 'on'
        price = request.form.get('price')
        hashtags = request.form.get('hashtags')
        
        if file.filename == '':
            flash('Fayl tanlanmadi', 'error')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Create uploads dir if not exists
            upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'books')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Save file (prepend timestamp to avoid overwrite)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            final_filename = f"{timestamp}_{filename}"
            file.save(os.path.join(upload_folder, final_filename))
            
            # Create DB entry
            book = Literature(
                title=title,
                description=description,
                author=author,
                uploader_id=current_user.id,
                file_path=f"uploads/books/{final_filename}",
                is_paid=is_paid,
                price=price if is_paid else "Bepul",
                hashtags=hashtags
            )
            
            db.session.add(book)
            db.session.commit()
            
            flash('Kitob muvaffaqiyatli yuklandi!', 'success')
            return redirect(url_for('library'))
            
    return render_template('upload_book.html')

@app.route('/library/book/<int:id>')
def book_detail(id):
    """Kitob sahifasi"""
    book = Literature.query.get_or_404(id)
    return render_template('book_detail.html', book=book)

@app.route('/library/book/<int:id>/buy', methods=['POST'])
@login_required
def buy_book(id):
    """Kitob sotib olish (Simulyatsiya)"""
    book = Literature.query.get_or_404(id)
    
    # Check payment details (Basic check)
    promocode = request.form.get('promocode')
    card_number = request.form.get('card_number')
    
    if promocode == 'EDUAI2025' or (card_number and len(card_number) >= 16):
        # Grant access (Persistent)
        existing_purchase = Purchase.query.filter_by(user_id=current_user.id, book_id=id).first()
        if not existing_purchase:
            purchase = Purchase(user_id=current_user.id, book_id=id)
            db.session.add(purchase)
            db.session.commit()
            
        flash('Xarid muvaffaqiyatli amalga oshirildi! Yuklab olishingiz mumkin.', 'success')
    else:
        flash('To\'lov ma\'lumotlari xato!', 'error')
        
    return redirect(url_for('book_detail', id=id))

@app.route('/library/book/<int:id>/download')
@login_required
def download_book(id):
    """Kitobni yuklab olish"""
    book = Literature.query.get_or_404(id)
    
    # Check access
    if book.is_paid:
        # Check if user is owner or paid (DB check)
        has_purchased = Purchase.query.filter_by(user_id=current_user.id, book_id=id).first()
        if book.uploader_id != current_user.id and not has_purchased:
             flash('Bu kitob pullik. Avval sotib oling.', 'error')
             return redirect(url_for('book_detail', id=id))
             
    # Serve file
    return redirect(url_for('static', filename=book.file_path))

# Database initialization - MA'LUMOTLAR YANGILANMAYDI
def init_db():
    with app.app_context():
        # Faqat jadvallar mavjud bo'lmaganda yaratish
        db.create_all()
        
        # Fanlarni tekshirish, agar mavjud bo'lmasa yaratish
        existing_subjects = Subject.query.count()
        if existing_subjects == 0:
            print("📚 Fanlar ma'lumotlari yo'q, yaratilmoqda...")
            
            subjects_data = [
                {'name': 'Matematika', 'code': 'matematika', 'description': 'Matematika fanidan darslar'},
                {'name': 'Fizika', 'code': 'fizika', 'description': 'Fizika fanidan darslar'},
                {'name': 'Ingliz tili', 'code': 'ingliz_tili', 'description': 'Ingliz tili darslari'},
                {'name': 'Informatika', 'code': 'informatika', 'description': 'Informatika fanidan darslar'},
                {'name': 'Biologiya', 'code': 'biologiya', 'description': 'Biologiya fanidan darslar'},
                {'name': 'Kimyo', 'code': 'kimyo', 'description': 'Kimyo fanidan darslar'},
                {'name': 'Tarix', 'code': 'tarix', 'description': 'Tarix fanidan darslar'},
                {'name': 'Ona tili', 'code': 'ona_tili', 'description': 'Ona tili darslari'},
                {'name': 'Geografiya', 'code': 'geografiya', 'description': 'Geografiya fanidan darslar'},
                {'name': 'Adabiyot', 'code': 'adabiyot', 'description': 'Adabiyot fanidan darslar'},
            ]
            
            for subj_data in subjects_data:
                subject = Subject(**subj_data)
                db.session.add(subject)
            
            # Admin user ni tekshirish
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(username='admin', email='admin@eduai.uz', role='admin')
                admin.set_password('admin123')
                db.session.add(admin)
            
            # Demo user ni tekshirish
            demo = User.query.filter_by(username='demo').first()
            if not demo:
                demo = User(username='demo', email='demo@eduai.uz', role='student')
                demo.set_password('demo123')
                db.session.add(demo)
            
            db.session.commit()
            
            # User progress yaratish
            create_user_progress(admin.id)
            create_user_progress(demo.id)
            
            print("[+] Database initialized successfully!")
        else:
            print(f"[*] Database allaqachon mavjud: {existing_subjects} ta fan")

@app.route('/teacher/quiz/create', methods=['GET', 'POST'])
@teacher_required
def create_quiz():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Fayl tanlanmadi', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        title = request.form.get('title')
        subject_id = request.form.get('subject_id')
        
        if file.filename == '':
            flash('Fayl tanlanmadi', 'error')
            return redirect(request.url)
            
        if file:
            try:
                text = extract_text_from_file(file)
                if len(text) < 50:
                    flash('Fayl ichida yetarli matn topilmadi', 'error')
                    return redirect(request.url)
                
                # AI orqali test tuzish
                questions_data = ai_assistant.generate_quiz_from_text(text)
                
                if not questions_data:
                    flash('AI test tuza olmadi. Iltimos qaytadan urining.', 'error')
                    return redirect(request.url)
                
                return render_template('teacher/quiz_preview.html', 
                                     questions=questions_data, 
                                     title=title, 
                                     subject_id=subject_id)
            except Exception as e:
                flash(f'Xatolik: {str(e)}', 'error')
                return redirect(request.url)
    
    subjects = Subject.query.all()
    return render_template('teacher/create_quiz.html', subjects=subjects)

@app.route('/teacher/quiz/create/manual', methods=['GET'])
@teacher_required
def create_quiz_manual():
    subjects = Subject.query.all()
    return render_template('teacher/create_quiz_manual.html', subjects=subjects)

@app.route('/teacher/quiz/create/unique', methods=['GET', 'POST'])
@teacher_required
def create_quiz_unique():
    """AI orqali har bir o'quvchi uchun individual test yaratish"""
    if request.method == 'POST':
        title = request.form.get('title')
        subject_id = request.form.get('subject_id')
        topic = request.form.get('topic')
        grade = request.form.get('grade')
        count = request.form.get('count', 10)
        
        generation_params = json.dumps({
            'topic': topic,
            'grade': grade,
            'count': int(count)
        })
        
        quiz = Quiz(
            title=title,
            teacher_id=current_user.id,
            subject_id=int(subject_id) if subject_id else None,
            is_unique=True,
            generation_params=generation_params
        )
        
        db.session.add(quiz)
        db.session.commit()
        
        flash('Individual AI testi muvaffaqiyatli yaratildi!', 'success')
        return redirect(url_for('teacher_quizzes'))
        
    subjects = Subject.query.all()
    return render_template('teacher/create_quiz_unique.html', subjects=subjects)

@app.route('/teacher/quiz/save', methods=['POST'])
@teacher_required
def save_quiz():
    try:
        title = request.form.get('title')
        subject_id = request.form.get('subject_id')
        questions_json = request.form.get('questions_json')
        
        if not questions_json:
            flash('Test ma\'lumotlari yo\'qolgan', 'error')
            return redirect(url_for('create_quiz'))
            
        questions_data = json.loads(questions_json)
        
        # Create Quiz
        quiz = Quiz(
            title=title,
            teacher_id=current_user.id,
            subject_id=int(subject_id) if subject_id else None
        )
        db.session.add(quiz)
        db.session.commit()
        
        # Create Questions
        for q in questions_data:
            # Handle different types
            q_type = q.get('type', 'multi')
            
            question = Question(
                question_text=q['question'],
                question_type=q_type,
                subject_id=int(subject_id) if subject_id else 1,
                quiz_id=quiz.id,
                correct_text=q.get('correct_text'),
                code_language=q.get('code_language')
            )
            
            # Options logic
            if q_type == 'multi':
                question.option_a = q['options']['A']
                question.option_b = q['options']['B']
                question.option_c = q['options']['C']
                question.option_d = q['options']['D']
                question.correct_option = q['correct_answer']
            
            elif q_type == 'match':
                # For match, we stored pairs in correct_text as JSON
                # And displayed options in options A-D for right side
                question.option_a = q['options']['A']
                question.option_b = q['options']['B']
                question.option_c = q['options']['C']
                question.option_d = q['options']['D']
                # correct_text holds the JSON map
            
            db.session.add(question)
        
        db.session.commit()
        flash('Test muvaffaqiyatli saqlandi!', 'success')
        return redirect(url_for('teacher_dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Saqlashda xatolik: {str(e)}', 'error')
        print(f"DEBUG ERROR: {e}") # Debugging
        return redirect(url_for('create_quiz'))



@app.route('/teacher/assignment/<int:id>/edit', methods=['POST'])
@teacher_required
def edit_assignment(id):
    """Vazifani tahrirlash"""
    try:
        assignment = Assignment.query.get_or_404(id)
        group = Group.query.get_or_404(assignment.group_id)
        
        if group.teacher_id != current_user.id:
            flash('Ruxsat yo\'q!', 'error')
            return redirect(url_for('teacher_dashboard'))
        
        assignment.title = request.form.get('title')
        assignment.description = request.form.get('description')
        due_date = request.form.get('due_date')
        assignment.due_date = datetime.strptime(due_date, '%Y-%m-%dT%H:%M') if due_date else None
        
        quiz_id = request.form.get('quiz_id')
        assignment.quiz_id = int(quiz_id) if quiz_id else None
        
        db.session.commit()
        
        flash('Vazifa muvaffaqiyatli yangilandi!', 'success')
        return redirect(url_for('teacher_group_detail', id=group.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Xatolik: {str(e)}', 'error')
        return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/assignment/<int:id>/delete', methods=['POST'])
@teacher_required
def delete_assignment(id):
    """Vazifani o'chirish"""
    try:
        assignment = Assignment.query.get_or_404(id)
        group = Group.query.get_or_404(assignment.group_id)
        
        if group.teacher_id != current_user.id:
            flash('Ruxsat yo\'q!', 'error')
            return redirect(url_for('teacher_dashboard'))
        
        group_id = assignment.group_id
        db.session.delete(assignment)
        db.session.commit()
        
        flash('Vazifa o\'chirildi!', 'success')
        return redirect(url_for('teacher_group_detail', id=group_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Xatolik: {str(e)}', 'error')
        return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/api/assignment/<int:id>', methods=['GET'])
@teacher_required
def get_assignment(id):
    """Vazifa ma'lumotlarini olish (AJAX)"""
    try:
        assignment = Assignment.query.get_or_404(id)
        group = Group.query.get_or_404(assignment.group_id)
        
        if group.teacher_id != current_user.id:
            return jsonify({'success': False, 'error': 'Ruxsat yo\'q'}), 403
        
        return jsonify({
            'success': True,
            'assignment': {
                'id': assignment.id,
                'title': assignment.title,
                'description': assignment.description,
                'due_date': assignment.due_date.strftime('%Y-%m-%dT%H:%M') if assignment.due_date else '',
                'quiz_id': assignment.quiz_id or ''
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/teacher/quizzes')
@teacher_required
def teacher_quizzes():
    quizzes = Quiz.query.filter_by(teacher_id=current_user.id).order_by(Quiz.created_at.desc()).all()
    return render_template('teacher/quizzes.html', quizzes=quizzes)

@app.route('/teacher/quiz/<int:id>/view')
@teacher_required
def view_quiz(id):
    """Testni ko'rish"""
    quiz = Quiz.query.get_or_404(id)
    
    if quiz.teacher_id != current_user.id:
        flash('Bu testni ko\'rish huquqingiz yo\'q!', 'error')
        return redirect(url_for('teacher_quizzes'))
    
    return render_template('teacher/view_quiz.html', quiz=quiz)

@app.route('/teacher/quiz/<int:id>/delete', methods=['POST'])
@teacher_required
def delete_quiz(id):
    """Testni o'chirish"""
    try:
        quiz = Quiz.query.get_or_404(id)
        
        if quiz.teacher_id != current_user.id:
            flash('Bu testni o\'chirish huquqingiz yo\'q!', 'error')
            return redirect(url_for('teacher_quizzes'))
        
        # Check if quiz is assigned to any group
        assignments = Assignment.query.filter_by(quiz_id=quiz.id).all()
        if assignments:
            flash('Bu test guruhlarga biriktirilgan. Avval vazifalarni o\'chiring!', 'warning')
            return redirect(url_for('teacher_quizzes'))
        
        db.session.delete(quiz)
        db.session.commit()
        
        flash('Test muvaffaqiyatli o\'chirildi!', 'success')
        return redirect(url_for('teacher_quizzes'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Xatolik: {str(e)}', 'error')
        return redirect(url_for('teacher_quizzes'))



@app.route('/teacher/group/<int:id>/quiz_results/<int:quiz_id>')
@teacher_required
def group_quiz_results(id, quiz_id):
    group = Group.query.get_or_404(id)
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if group.teacher_id != current_user.id:
        return 'Unauthorized', 403
        
    # Get all students in group
    students = [m.student_id for m in group.members]
    
    # Get results for this quiz from these students
    results = TestResult.query.filter(
        TestResult.quiz_id == quiz_id,
        TestResult.user_id.in_(students)
    ).all()
    
    # Map results by user
    student_results = []
    for member in group.members:
        student = User.query.get(member.student_id)
        # Find best score for this student (if multiple attempts)
        attempts = [r for r in results if r.user_id == student.id]
        if attempts:
            best_attempt = max(attempts, key=lambda x: x.score)
            best_score = best_attempt.score
            best_result_id = best_attempt.id
        else:
            best_score = None
            best_result_id = None
            
        student_results.append({
            'student': student,
            'score': best_score,
            'result_id': best_result_id
        })
        
    return render_template('teacher/quiz_results.html', 
                         group=group, 
                         quiz=quiz, 
                         student_results=student_results)

@app.route('/teacher/group/<int:id>/analytics')
@teacher_required
def group_analytics(id):
    group = Group.query.get_or_404(id)
    if group.teacher_id != current_user.id:
        flash('Siz bu guruh egasi emassiz', 'error')
        return redirect(url_for('teacher_dashboard'))
        
    # Get all students in group
    students = [member.student for member in group.members]
    
    analytics_data = []
    for student in students:
        # Get all quiz results for this student
        results = TestResult.query.filter_by(user_id=student.id).filter(TestResult.quiz_id.isnot(None)).all()
        
        student_stat = {
            'student': student,
            'total_quizzes': len(results),
            'avg_score': round(sum([r.score for r in results]) / len(results)) if results else 0,
            'recent_results': results[-5:] # Last 5 results
        }
        analytics_data.append(student_stat)
    
    return render_template('teacher/group_analytics.html', group=group, analytics=analytics_data)

def extract_text_from_file(file):
    text = ""
    filename = file.filename
    
    if filename.endswith('.pdf'):
        pdf = PdfReader(file)
        for page in pdf.pages:
            text += page.extract_text() + "\n"
            
    elif filename.endswith('.docx'):
        doc = Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"
            
    return text

@app.route('/student/quizzes')
@login_required
def student_quizzes():
    quizzes = Quiz.query.order_by(Quiz.created_at.desc()).all()
    return render_template('student/quizzes.html', quizzes=quizzes)

@app.route('/student/quiz/<int:id>')
@login_required
def take_quiz(id):
    quiz = Quiz.query.get_or_404(id)
    
    if quiz.is_unique:
        params = json.loads(quiz.generation_params) if quiz.generation_params else {}
        topic = params.get('topic', 'General')
        grade = params.get('grade', '5')
        count = params.get('count', 10)
        
        # O'quvchi uchun maxsus savollar tuzish
        questions = ai_assistant.generate_unique_questions(topic, grade, count)
        
        # Savollarni sessiyada saqlash (grading uchun)
        session['unique_quiz_id'] = id
        session['unique_quiz_questions'] = questions
        
        return render_template('student/take_quiz_unique.html', quiz=quiz, questions=questions)
        
    return render_template('student/take_quiz.html', quiz=quiz)

@app.template_filter('from_json')
def from_json_filter(s):
    try:
        return json.loads(s) if s else {}
    except:
        return {}

@app.route('/student/quiz/<int:id>/submit', methods=['POST'])
@login_required
def submit_quiz(id):
    quiz = Quiz.query.get_or_404(id)
    
    # 1. Initialize variables for both types
    final_score = 0
    total_q_count = 0
    correct_val = 0 # Can be points or count
    snapshot = None
    
    if quiz.is_unique:
        questions = session.get('unique_quiz_questions', [])
        saved_quiz_id = session.get('unique_quiz_id')
        
        if not questions or saved_quiz_id != id:
            flash('Sessiya muddati tugagan yoki xatolik yuz berdi.', 'error')
            return redirect(url_for('student_quizzes'))
            
        total_q_count = len(questions)
        correct_count = 0
        detailed_snapshot = []
        
        for i, q in enumerate(questions):
            user_answer = request.form.get(f'question_{i}')
            is_correct = (user_answer == q['correct_answer'])
            if is_correct:
                correct_count += 1
            
            detailed_snapshot.append({
                'question': q['question'],
                'options': q['options'],
                'correct_answer': q['correct_answer'],
                'user_answer': user_answer,
                'is_correct': is_correct
            })
            
        final_score = int((correct_count / total_q_count) * 100) if total_q_count > 0 else 0
        correct_val = correct_count
        snapshot = json.dumps(detailed_snapshot)
        
        # Clear session
        session.pop('unique_quiz_questions', None)
        session.pop('unique_quiz_id', None)
        
    else:
        # 2. Standard Quiz Handling
        total_q_count = len(quiz.questions)
        total_max_points = sum([q.points for q in quiz.questions]) or (total_q_count * 10)
        student_score_points = 0
        
        for question in quiz.questions:
            q_id = str(question.id)
            if question.question_type == 'multi' or question.question_type == None:
                user_answer = request.form.get(f'question_{q_id}')
                if user_answer == question.correct_option:
                    student_score_points += question.points
                    
            # 2. Matching
            elif question.question_type == 'match':
                correct_pairs = json.loads(question.correct_text) if question.correct_text else {}
                pairs_count = len(correct_pairs)
                correct_matches = 0
                
                keys = list(correct_pairs.keys())
                for i, left_key in enumerate(keys):
                    idx = i + 1
                    user_val = request.form.get(f'question_{q_id}_{idx}')
                    correct_val_pair = correct_pairs[left_key]
                    if user_val == correct_val_pair:
                        correct_matches += 1
                
                if pairs_count > 0:
                    ratio = correct_matches / pairs_count
                    student_score_points += int(question.points * ratio)

            # 3. Text / Code / Math (AI Grading)
            elif question.question_type in ['text', 'code', 'math']:
                user_answer = request.form.get(f'question_{q_id}')
                correct_model = question.correct_text
                
                if question.question_type == 'code':
                    code_language = question.code_language or 'python'
                    if code_language.lower() == 'python' and user_answer:
                        try:
                            compile(user_answer, '<string>', 'exec')
                        except SyntaxError as e:
                            # give partial credit for attempt
                            earned_points = int(question.points * 0.2)
                            student_score_points += earned_points
                            continue
                    
                grade_result = ai_assistant.grade_answer(question.question_text, user_answer, correct_model)
                ai_percentage = grade_result.get('score', 0)
                earned_points = int(question.points * (ai_percentage / 100))
                student_score_points += earned_points

        if total_max_points > 0:
            final_score = int((student_score_points / total_max_points) * 100)
        correct_val = int(student_score_points)

    # 3. Save Unified Result
    result = TestResult(
        user_id=current_user.id,
        subject_id=quiz.subject_id,
        quiz_id=quiz.id,
        score=final_score,
        total_questions=total_q_count,
        correct_answers=correct_val,
        unique_questions_snapshot=snapshot
    )
    
    db.session.add(result)
    
    # Update Progress
    if quiz.subject_id:
        progress = UserProgress.query.filter_by(user_id=current_user.id, subject_id=quiz.subject_id).first()
        if progress:
            progress.progress_percentage = max(progress.progress_percentage, final_score)
            progress.last_activity = datetime.now()
            
    db.session.commit()
    
    # Update Rank Automatically
    calculate_user_rank(current_user.id)
    
    msg = f'Sizning natijangiz: {final_score}%.'
    if final_score >= 80:
        flash(msg + ' Ajoyib natija!', 'success')
    else:
        flash(msg, 'info')
    
    return redirect(url_for('student_quizzes'))


@app.route('/student/result/<int:id>')
@login_required
def student_result_detail(id):
    """O'quvchi uchun test natijasi tafsilotlari"""
    result = TestResult.query.get_or_404(id)
    if result.user_id != current_user.id:
        flash('Ruxsat yo\'q!', 'error')
        return redirect(url_for('dashboard'))
    
    quiz = Quiz.query.get(result.quiz_id) if result.quiz_id else None
    
    # Handle Unique AI Quiz Snapshot
    snapshot = None
    if result.unique_questions_snapshot:
        snapshot = json.loads(result.unique_questions_snapshot)
        
    return render_template('student/result_detail.html', 
                         result=result, 
                         quiz=quiz, 
                         snapshot=snapshot,
                         student=current_user)

@app.route('/teacher/result/<int:id>')
@teacher_required
def teacher_result_detail(id):
    """O'qituvchi uchun o'quvchi natijasi tafsilotlari"""
    result = TestResult.query.get_or_404(id)
    
    # Check if teacher owns the quiz or group
    quiz = Quiz.query.get(result.quiz_id) if result.quiz_id else None
    if quiz and quiz.teacher_id != current_user.id:
        flash('Ruxsat yo\'q!', 'error')
        return redirect(url_for('teacher_dashboard'))
        
    snapshot = None
    if result.unique_questions_snapshot:
        snapshot = json.loads(result.unique_questions_snapshot)
        
    return render_template('teacher/result_detail.html', 
                         result=result, 
                         quiz=quiz, 
                         snapshot=snapshot,
                         student=User.query.get(result.user_id))

# Initialize DB on startup (required for production like Gunicorn)
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"[*] EDUAI Pro ishga tushmoqda... Port: {port}")
    app.run(debug=False, host='0.0.0.0', port=port)

