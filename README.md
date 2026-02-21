# EDUAI - O'quv Platformasi

EDUAI - bu o'quvchilarga Matematika, Fizika va boshqa fanlarni o'rganishda yordam beruvchi AI asosidagi platforma.

## Xususiyatlar
- AI Assistant (Groq orqali)
- Testlar va bilimni tekshirish
- Progress analytics
- O'qituvchi va o'quvchi panellari

## Render Deployment

Loyiha Render platformasiga deploy qilish uchun tayyorlangan.

### 1. Environment Variables
Render dashboard'ida quyidagi o'zgaruvchilarni o'rnating:
- `SECRET_KEY`: Tasodifiy matn (session xavfsizligi uchun)
- `GROQ_API_KEY`: Groq Cloud API kaliti
- `DATABASE_URL`: Render Postgres ulanish manzili (avtomatik o'rnatiladi)

### 2. Konfiguratsiya
- **Environment**: Python
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

## Mahalliy ishga tushirish

1. Virtual muhit yarating:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
2. Kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```
3. Appni ishga tushiring:
   ```bash
   python app.py
   ```

## Muallif
Loyiha EDUAI jamoasi tomonidan ishlab chiqilgan.
