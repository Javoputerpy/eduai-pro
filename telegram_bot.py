import telebot
from threading import Thread
import os
from flask import json
from models import db, User, TestResult, Subject, UserProgress
from datetime import datetime
import time
from telebot.apihelper import ApiTelegramException


# Initialize bot with token from environment
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN) if TOKEN else None

def bot_required(func):
    def wrapper(*args, **kwargs):
        if bot:
            return func(*args, **kwargs)
        return None
    return wrapper

def get_student_stats(user):

    """Generate a summary of student statistics for the parent."""
    stats = []
    stats.append(f"👤 O'quvchi: {user.full_name or user.username}")
    stats.append(f"🏆 Daraja: {user.rank}")
    stats.append(f"📊 Umumiy progress: {user.get_overall_progress()}%")
    stats.append(f"📝 Topshirilgan testlar: {user.get_tests_taken()} ta")
    stats.append(f"🎯 O'rtacha ball: {user.get_avg_test_score()}%")
    
    # Recent activity
    recent = TestResult.query.filter_by(user_id=user.id).order_by(TestResult.completed_at.desc()).limit(3).all()
    if recent:
        stats.append("\n🕒 So'nggi natijalar:")
        for r in recent:
            subject = Subject.query.get(r.subject_id)
            subj_name = subject.name if subject else "Test"
            stats.append(f"- {subj_name}: {r.score}% ({r.completed_at.strftime('%d.%m %H:%M')})")
            
    return "\n".join(stats)

if bot:
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        telegram_user = message.from_user.username
        if not telegram_user:
            bot.reply_to(message, "⚠️ Xatolik: Sizning Telegram profilizda 'username' o'rnatilmagan. "
                                 "Iltimos, Telegram sozlamalaridan username o'rnating va qayta urinib ko'ring.")
            return

        from app import app
        with app.app_context():
            # Find students who listed this telegram username as their parent
            students = User.query.filter_by(parent_telegram_username=telegram_user).all()
            
            if students:
                for student in students:
                    student.parent_telegram_chat_id = str(message.chat.id)
                db.session.commit()
                
                names = ", ".join([s.full_name or s.username for s in students])
                bot.reply_to(message, f"✅ Muvaffaqiyatli bog'landi!\n\n"
                                     f"Siz endi quyidagi o'quvchilarning natijalarini kuzatib borasiz: {names}.\n"
                                     f"Yangi natijalar avtomatik ravishda shu yerga yuboriladi.")
            else:
                bot.reply_to(message, "Xush kelibsiz! EDUAI Pro Monitoring botiga.\n\n"
                                     "Farzandingiz o'z profilida sizning Telegram usernamingizni kiritishi kerak.\n"
                                     f"Sizning usernamingiz: @{telegram_user}")

    @bot.message_handler(commands=['monitor'])
    def monitor_student(message):
        telegram_user = message.from_user.username
        from app import app
        with app.app_context():
            user = User.query.filter_by(parent_telegram_username=telegram_user).first()
            if not user or not user.parent_telegram_chat_id:
                bot.reply_to(message, "❌ Siz hali birorta o'quvchiga bog'lanmagansiz.")
                return
                
            stats_text = get_student_stats(user)
            bot.reply_to(message, stats_text)

def notify_parent(user, message_text):
    """Send an automatic notification to the parent if linked."""
    if bot and user.parent_telegram_chat_id:
        try:
            bot.send_message(user.parent_telegram_chat_id, message_text)
            print(f"[*] Notification sent to parent of {user.username}")
        except Exception as e:
            print(f"[!] Failed to send notification: {e}")




def run_bot():
    if bot:
        print("[*] Telegram Bot ishga tushmoqda...")
        try:
            bot.infinity_polling(skip_pending=True)
        except ApiTelegramException as e:
            if "Conflict" in str(e):
                print("[!] Bot confliti (Conflict: 409). Ehtimol boshqa bot versiyasi hali yopilmagan. 5 soniyadan keyin qayta urunib ko'ramiz...")
                time.sleep(5)
                run_bot()
            else:
                print(f"[!] Telegram Bot API Xatosi: {e}")
    else:
        print("[!] TELEGRAM_BOT_TOKEN topilmadi, bot ishga tushmadi.")


def start_bot_thread():
    bot_thread = Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
