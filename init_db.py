from app import app
from models import db, User

def init_db():
    with app.app_context():
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

if __name__ == "__main__":
    init_db()
