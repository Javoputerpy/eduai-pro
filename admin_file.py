from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from models import db, User, Subject, TestResult, UserProgress, Question, Quiz, Group, Message, GroupMember, Assignment

# Admin Blueprint yaratish
admin_bp = Blueprint('admin', __name__, url_prefix='/admin', 
                    template_folder='templates/admin')

# Admin tekshiruvi uchun decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Sizga admin paneliga kirish uchun ruxsat yo\'q', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# === DASHBOARD ===
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # Asosiy statistikalar
    stats = {
        'total_users': User.query.count(),
        'total_subjects': Subject.query.count(),
        'total_questions': Question.query.count(),
        'total_tests': TestResult.query.count(),
        'today_tests': TestResult.query.filter(
            db.func.date(TestResult.completed_at) == datetime.now().date()
        ).count(),
        'new_users_today': User.query.filter(
            db.func.date(User.created_at) == datetime.now().date()
        ).count()
    }
    
    # So'nggi foydalanuvchilar
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # So'nggi test natijalari
    recent_tests = TestResult.query.order_by(TestResult.completed_at.desc()).limit(10).all()
    
    # Eng faol foydalanuvchilar
    active_users = db.session.query(
        User.username,
        db.func.count(TestResult.id).label('test_count')
    ).join(TestResult).group_by(User.id).order_by(db.desc('test_count')).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_users=recent_users,
                         recent_tests=recent_tests,
                         active_users=active_users)

# === FOYDALANUVCHILAR BOSHQARUVI ===
@admin_bp.route('/users')
@login_required
@admin_required
def users_management():
    """Foydalanuvchilarni boshqarish"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Qidiruv va pagination
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search)

@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """Foydalanuvchi tafsilotlari"""
    user = User.query.get_or_404(user_id)
    
    # Foydalanuvchi statistikasi
    user_stats = {
        'total_tests': TestResult.query.filter_by(user_id=user_id).count(),
        'avg_score': db.session.query(
            db.func.avg(TestResult.score)
        ).filter_by(user_id=user_id).scalar() or 0,
        'total_progress': user.get_overall_progress(),
        'joined_days': (datetime.now() - user.created_at).days
    }
    
    # So'nggi test natijalari
    recent_tests = TestResult.query.filter_by(user_id=user_id)\
        .order_by(TestResult.completed_at.desc())\
        .limit(5)\
        .all()
    
    return render_template('admin/user_detail.html',
                         user=user,
                         user_stats=user_stats,
                         recent_tests=recent_tests)

@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    """Foydalanuvchi aktivligini o'zgartirish"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('O\'zingizni bloklab qo\'ya olmaysiz', 'error')
        return redirect(url_for('admin.users_management'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    action = "faollashtirildi" if user.is_active else "bloklandi"
    flash(f'Foydalanuvchi {user.username} {action}', 'success')
    return redirect(url_for('admin.users_management'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Foydalanuvchini o'chirish"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('O\'zingizni o\'chira olmaysiz', 'error')
        return redirect(url_for('admin.users_management'))
    
    # Foydalanuvchiga tegishli ma'lumotlarni o'chirish
    # 1. Test natijalari
    TestResult.query.filter_by(user_id=user_id).delete()
    # 2. Progress
    UserProgress.query.filter_by(user_id=user_id).delete()
    # 3. Guruh a'zoligi
    GroupMember.query.filter_by(student_id=user_id).delete()
    # 4. Xabarlar (yuborilgan va qabul qilingan)
    Message.query.filter(db.or_(Message.sender_id==user_id, Message.recipient_id==user_id)).delete()
    
    # Agar o'qituvchi bo'lsa, u yaratgan narsalarni ham o'chirish yoki boshqasiga o'tkazish kerak
    # Hozircha oddiy yondashuv: o'qituvchining guruhlari va testlarini o'chiramiz
    if user.role == 'teacher':
        quizzes = Quiz.query.filter_by(teacher_id=user_id).all()
        for quiz in quizzes:
            # Testga bog'liq savollar va natijalar
            Question.query.filter_by(quiz_id=quiz.id).delete()
            TestResult.query.filter_by(quiz_id=quiz.id).delete()
            Assignment.query.filter_by(quiz_id=quiz.id).delete()
            db.session.delete(quiz)
            
        groups = Group.query.filter_by(teacher_id=user_id).all()
        for group in groups:
            # Guruhga bog'liq a'zolik va vazifalar
            GroupMember.query.filter_by(group_id=group.id).delete()
            Assignment.query.filter_by(group_id=group.id).delete()
            db.session.delete(group)

    db.session.delete(user)
    db.session.commit()
    
    flash(f'Foydalanuvchi {user.username} o\'chirildi', 'success')
    return redirect(url_for('admin.users_management'))

# === FANLAR BOSHQARUVI ===
@admin_bp.route('/subjects')
@login_required
@admin_required
def subjects_management():
    """Fanlarni boshqarish"""
    subjects = Subject.query.all()
    return render_template('admin/subjects.html', subjects=subjects)

@admin_bp.route('/subjects/add', methods=['POST'])
@login_required
@admin_required
def add_subject():
    """Yangi fan qo'shish"""
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip()
    description = request.form.get('description', '').strip()
    
    if not name or not code:
        flash('Fan nomi va kodi talab qilinadi', 'error')
        return redirect(url_for('admin.subjects_management'))
    
    # Kod unikal ligini tekshirish
    if Subject.query.filter_by(code=code).first():
        flash('Bu kod bilan fan mavjud', 'error')
        return redirect(url_for('admin.subjects_management'))
    
    subject = Subject(
        name=name,
        code=code,
        description=description
    )
    
    db.session.add(subject)
    db.session.commit()
    
    # Barcha foydalanuvchilar uchun yangi fan progressi yaratish
    users = User.query.all()
    for user in users:
        progress = UserProgress(
            user_id=user.id,
            subject_id=subject.id,
            progress_percentage=0
        )
        db.session.add(progress)
    
    db.session.commit()
    
    flash(f'{name} fani muvaffaqiyatli qo\'shildi', 'success')
    return redirect(url_for('admin.subjects_management'))

@admin_bp.route('/subjects/<int:subject_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_subject(subject_id):
    """Fanni tahrirlash"""
    subject = Subject.query.get_or_404(subject_id)
    
    if request.method == 'POST':
        subject.name = request.form.get('name', '').strip()
        subject.description = request.form.get('description', '').strip()
        
        db.session.commit()
        flash('Fan muvaffaqiyatli yangilandi', 'success')
        return redirect(url_for('admin.subjects_management'))
    
    return render_template('admin/edit_subject.html', subject=subject)

@admin_bp.route('/subjects/<int:subject_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_subject(subject_id):
    """Fanni o'chirish"""
    subject = Subject.query.get_or_404(subject_id)
    
    # Fanga tegishli ma'lumotlarni o'chirish
    Question.query.filter_by(subject_id=subject_id).delete()
    TestResult.query.filter_by(subject_id=subject_id).delete()
    UserProgress.query.filter_by(subject_id=subject_id).delete()
    
    db.session.delete(subject)
    db.session.commit()
    
    flash(f'{subject.name} fani o\'chirildi', 'success')
    return redirect(url_for('admin.subjects_management'))

# === SAVOLLAR BOSHQARUVI ===
@admin_bp.route('/questions')
@login_required
@admin_required
def questions_management():
    """Savollarni boshqarish"""
    page = request.args.get('page', 1, type=int)
    subject_id = request.args.get('subject_id', '', type=int)
    search = request.args.get('search', '')
    
    # Filterlar
    query = Question.query
    
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    
    if search:
        query = query.filter(Question.question_text.ilike(f'%{search}%'))
    
    questions = query.order_by(Question.id.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    
    subjects = Subject.query.all()
    return render_template('admin/questions.html',
                         questions=questions,
                         subjects=subjects,
                         current_subject_id=subject_id,
                         search=search)

@admin_bp.route('/questions/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_question():
    """Yangi savol qo'shish"""
    subjects = Subject.query.all()
    
    if request.method == 'POST':
        try:
            question_data = {
                'question_text': request.form.get('question_text', '').strip(),
                'option_a': request.form.get('option_a', '').strip(),
                'option_b': request.form.get('option_b', '').strip(),
                'option_c': request.form.get('option_c', '').strip(),
                'option_d': request.form.get('option_d', '').strip(),
                'correct_option': request.form.get('correct_option', 'A').upper(),
                'subject_id': request.form.get('subject_id'),
                'points': request.form.get('points', 10, type=int),
                'explanation': request.form.get('explanation', '').strip(),
                'difficulty': request.form.get('difficulty', 'medium')
            }
            
            # Validatsiya
            if not question_data['question_text']:
                flash('Savol matni talab qilinadi', 'error')
                return render_template('admin/add_question.html', subjects=subjects)
            
            if not all([question_data['option_a'], question_data['option_b']]):
                flash('Kamida 2 ta variant talab qilinadi', 'error')
                return render_template('admin/add_question.html', subjects=subjects)
            
            if question_data['correct_option'] not in ['A', 'B', 'C', 'D']:
                flash('To\'g\'ri javob A, B, C yoki D bo\'lishi kerak', 'error')
                return render_template('admin/add_question.html', subjects=subjects)
            
            question = Question(**question_data)
            db.session.add(question)
            db.session.commit()
            
            flash('Savol muvaffaqiyatli qo\'shildi', 'success')
            return redirect(url_for('admin.questions_management'))
            
        except Exception as e:
            flash(f'Xatolik: {str(e)}', 'error')
    
    return render_template('admin/add_question.html', subjects=subjects)

@admin_bp.route('/questions/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_question(question_id):
    """Savolni tahrirlash"""
    question = Question.query.get_or_404(question_id)
    subjects = Subject.query.all()
    
    if request.method == 'POST':
        try:
            question.question_text = request.form.get('question_text', '').strip()
            question.option_a = request.form.get('option_a', '').strip()
            question.option_b = request.form.get('option_b', '').strip()
            question.option_c = request.form.get('option_c', '').strip()
            question.option_d = request.form.get('option_d', '').strip()
            question.correct_option = request.form.get('correct_option', 'A').upper()
            question.subject_id = request.form.get('subject_id')
            question.points = request.form.get('points', 10, type=int)
            question.explanation = request.form.get('explanation', '').strip()
            question.difficulty = request.form.get('difficulty', 'medium')
            
            db.session.commit()
            flash('Savol muvaffaqiyatli yangilandi', 'success')
            return redirect(url_for('admin.questions_management'))
            
        except Exception as e:
            flash(f'Xatolik: {str(e)}', 'error')
    
    return render_template('admin/edit_question.html',
                         question=question,
                         subjects=subjects)

@admin_bp.route('/questions/<int:question_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_question(question_id):
    """Savolni o'chirish"""
    question = Question.query.get_or_404(question_id)
    
    db.session.delete(question)
    db.session.commit()
    
    flash('Savol o\'chirildi', 'success')
    return redirect(url_for('admin.questions_management'))

@admin_bp.route('/questions/<int:question_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_question(question_id):
    """Savolni faolligini o'zgartirish"""
    question = Question.query.get_or_404(question_id)
    question.is_active = not getattr(question, 'is_active', True)
    
    db.session.commit()
    
    status = "faollashtirildi" if question.is_active else "nofaollashtirildi"
    flash(f'Savol {status}', 'success')
    return redirect(url_for('admin.questions_management'))

# === TEST NATIJALARI ===
@admin_bp.route('/test_results')
@login_required
@admin_required
def test_results():
    """Test natijalarini ko'rish"""
    page = request.args.get('page', 1, type=int)
    subject_id = request.args.get('subject_id', '', type=int)
    user_id = request.args.get('user_id', '', type=int)
    
    query = TestResult.query
    
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    results = query.order_by(TestResult.completed_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    subjects = Subject.query.all()
    users = User.query.all()
    
    return render_template('admin/test_results.html',
                         results=results,
                         subjects=subjects,
                         users=users,
                         current_subject_id=subject_id,
                         current_user_id=user_id)

# === ANALITIKA ===
@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Analitika sahifasi"""
    # Oylik foydalanuvchi qo'shilish statistikasi
    monthly_users = db.session.query(
        db.func.strftime('%Y-%m', User.created_at).label('month'),
        db.func.count(User.id).label('count')
    ).group_by('month').order_by('month').all()
    
    # Fanlar bo'yicha test natijalari
    subject_stats = db.session.query(
        Subject.name,
        db.func.avg(TestResult.score).label('avg_score'),
        db.func.count(TestResult.id).label('test_count')
    ).join(TestResult).group_by(Subject.id).all()
    
    # Eng yaxshi natijalar
    top_scores = db.session.query(
        User.username,
        Subject.name,
        TestResult.score,
        TestResult.completed_at
    ).join(TestResult).join(Subject)\
     .order_by(TestResult.score.desc())\
     .limit(10)\
     .all()
    
    return render_template('admin/analytics.html',
                         monthly_users=monthly_users,
                         subject_stats=subject_stats,
                         top_scores=top_scores)

# === API ENDPOINTS ===
@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """Admin statistikasi API"""
    stats = {
        'total_users': User.query.count(),
        'total_subjects': Subject.query.count(),
        'total_questions': Question.query.count(),
        'total_tests': TestResult.query.count(),
        'active_today': TestResult.query.filter(
            db.func.date(TestResult.completed_at) == datetime.now().date()
        ).count()
    }
    return jsonify(stats)

@admin_bp.route('/api/user_activity')
@login_required
@admin_required
def api_user_activity():
    """Foydalanuvchi faolligi API"""
    # So'nggi 7 kunlik faollik
    days = []
    activity_counts = []
    
    for i in range(7):
        day = datetime.now().date() - timedelta(days=i)
        count = TestResult.query.filter(
            db.func.date(TestResult.completed_at) == day
        ).count()
        days.append(day.strftime('%m-%d'))
        activity_counts.append(count)
    
    return jsonify({
        'days': list(reversed(days)),
        'activity': list(reversed(activity_counts))
    })

# === YANGI: O'QITUVCHI FUNKSIYALARI ===
@admin_bp.route('/teacher/groups')
@login_required
@admin_required
def teacher_groups():
    """O'qituvchi guruhlari (keyinroq to'ldiramiz)"""
    return render_template('admin/teacher_groups.html')

@admin_bp.route('/teacher/tests')
@login_required
@admin_required
def teacher_tests():
    """O'qituvchi testlari (keyinroq to'ldiramiz)"""
    return render_template('admin/teacher_tests.html')