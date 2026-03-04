from models import db, User

def init_db():
    """Jadvallarni va boshlang'ich ma'lumotlarni yaratish"""
    # Jadvallarni yaratish
    db.create_all()
    
    # Admin tekshirish
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        print("Admin foydalanuvchi yaratilmoqda...")
        admin = User(username='admin', email='admin@eduai.uz', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin yaratildi: Login: admin, Parol: admin123")
    else:
        print("Admin allaqachon mavjud.")
    
    # Mock imtihonlarni seeding qilish
    from seed_mock_exams import run as seed_mocks
    seed_mocks()

if __name__ == "__main__":
    from app import app
    with app.app_context():
        init_db()
