# ai_model.py
import requests
import json
import random
import os

class GroqAIAssistant:
    def __init__(self):
        # Env var is required for deployment
        self.api_key = os.environ.get("GROQ_API_KEY", "")

        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.is_loaded = True
        self.available_models = [
            "llama-3.1-8b-instant",      # Eng yangi va tez
            "llama-3.2-3b-preview",      # Yangi kichik model
            "llama-3.2-1b-preview",      # Eng tez
            "llama-3.1-70b-versatile",   # Kuchliroq
            "mixtral-8x7b-32768",        # Fransuz modeli
            "gemma2-9b-it"               # Google modeli
        ]
        self.current_model = self.available_models[0]
        print("Groq AI Assistant ishga tayyor!")
        print(f"Model: {self.current_model}")
    
    def generate_response(self, user_message, user_context=""):
        """Groq API orqali javob olish"""
        print(f"Foydalanuvchi xabari: {user_message}")
        
        # Avval barcha modellarni urinib ko'ramiz
        for model in self.available_models:
            response = self._try_model(model, user_message, user_context)
            if response and response != "FALLBACK":
                return response
        
        # Agar hech biri ishlamasa, fallback
        return self._get_fallback_response(user_message)
    
    def _try_model(self, model, user_message, user_context):
        """Ma'lum model bilan urinib ko'rish"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = self._create_prompt(user_message, user_context)
            
            data = {
                "messages": [
                    {
                        "role": "system", 
                        "content": prompt
                    },
                    {
                        "role": "user", 
                        "content": user_message
                    }
                ],
                "model": model,
                "temperature": 0.7,
                "max_tokens": 500,
                "top_p": 0.8
            }
            
            print(f"{model} ga so'rov yuborilmoqda...")
            response = requests.post(self.url, headers=headers, json=data, timeout=20)
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                ai_response = result['choices'][0]['message']['content'].strip()
                print(f"{model} javobi: {ai_response}")
                self.current_model = model  # Ishlayotgan modelni saqlaymiz
                return ai_response
            elif 'error' in result:
                print(f"{model} xatosi: {result['error']['message']}")
                return "FALLBACK"
            else:
                return "FALLBACK"
                
        except Exception as e:
            print(f"{model} xatosi: {e}")
            return "FALLBACK"
    
    def _create_prompt(self, user_message, user_context):
        """Prompt yaratish"""
        return f"""Siz EDUAI o'quv platformasining yordamchi AI'siz. 
Foydalanuvchiga O'ZBEKCHA javob bering.

Foydalanuvchi ma'lumotlari:
{user_context}

Javob qisqa, aniq va o'quvga yo'naltirilgan bo'lsin.

Muhim: Faqat O'ZBEKCHA javob bering!"""
    
    def _get_fallback_response(self, user_message):
        """Smart fallback"""
        print("Smart fallback ishlatilmoqda...")
        user_lower = user_message.lower()
        
        if any(word in user_lower for word in ['salom', 'hello', 'hi', 'assalom']):
            return "Assalomu alaykum! EDUAI o'quv platformasiga xush kelibsiz! Men sizga Matematika, Fizika, Ingliz tili va boshqa fanlar bo'yicha yordam bera olaman."
        
        elif any(word in user_lower for word in ['fizika', 'nyuton', 'mexanika']):
            responses = [
                "Nyutonning 1-qonuni: Tana tashqi kuch ta'sir etmaguncha tinch yoki tekis harakatda qoladi.",
                "Nyutonning 2-qonuni: F = m × a (Kuch = massa × tezlanish)",
                "Nyutonning 3-qonuni: Har bir harakatga teng va qarama-qarshi reaktsiya mavjud."
            ]
            return random.choice(responses)
        
        elif any(word in user_lower for word in ['matematika', 'algebra', 'tenglama']):
            responses = [
                "Algebra - sonlar va ular orasidagi munosabatlarni o'rganadi. Masalan: 2x + 5 = 15 => x = 5",
                "Kvadrat tenglama: ax² + bx + c = 0. Diskriminant: D = b² - 4ac",
                "Geometriya - shakllar va ularning xususiyatlarini o'rganadi. Uchburchak burchaklari: 180°"
            ]
            return random.choice(responses)
        
        elif any(word in user_lower for word in ['ingliz', 'english', 'present simple']):
            responses = [
                "Present Simple - doimiy harakatlar uchun: 'I work every day'",
                "Present Continuous - hozirgi harakatlar: 'I am studying now'",
                "Ingliz tilida so'z boyligi - har kuni yangi so'zlar o'rganing"
            ]
            return random.choice(responses)
        
        else:
            responses = [
                "Qaysi fandan savolingiz bor? Matematika, Fizika yoki Ingliz tili?",
                "Sizning savolingizni tushundim. Aniqroq savol bering.",
                "O'quv masalalarda yordam bera olaman. Qaysi fandan boshlaymiz?"
            ]
            return random.choice(responses)

    def _normalize_questions(self, questions):
        """AI tomonidan qaytarilgan JSON kalitlarini standartlashtirish (Uzbek -> English)"""
        if not isinstance(questions, list):
            return []
            
        normalized = []
        mapping = {
            'savol': 'question',
            'variantlar': 'options',
            'to\'g\'ri_javob': 'correct_answer',
            'togri_javob': 'correct_answer',
            'variants': 'options',
            'javob': 'correct_answer'
        }
        
        for q in questions:
            if not isinstance(q, dict): continue
            
            new_q = {}
            # Kalitlarni xarita asosida o'zgartirish
            for k, v in q.items():
                norm_k = mapping.get(k.lower(), k.lower())
                new_q[norm_k] = v
            
            # Majburiy maydonlar mavjudligini tekshirish
            if 'question' not in new_q: new_q['question'] = "Savol topilmadi"
            if 'options' not in new_q: new_q['options'] = {"A": "-", "B": "-", "C": "-", "D": "-"}
            if 'correct_answer' not in new_q: new_q['correct_answer'] = "A"
            
            normalized.append(new_q)
        return normalized

    def generate_quiz_from_text(self, text):
        """Matndan testlar tuzish"""
        prompt = """
        Quyidagi matndan 5 ta test savolini tuzib ber.
        
        MUHIM QOIDA: 
        1. Javobni FAQAT va FAQAT JSON formatida qaytar.
        2. Kalitlar (keys) FAQAT ingliz tilida bo'lishi shart: "question", "options", "correct_answer".
        3. Savol va variantlar matni o'zbek tilida bo'lsin.
        
        Format aniq shunday bo'lsin:
        [
            {
                "question": "Savol matni",
                "options": {
                    "A": "Variant A",
                    "B": "Variant B",
                    "C": "Variant C",
                    "D": "Variant D"
                },
                "correct_answer": "A"
            }
        ]
        
        Matn:
        """ + text[:2000]

        try:
            import re
            response = self.generate_response(prompt, "O'qituvchi test tuzmoqchi")
            
            if "```" in response:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0]
                else:
                    response = response.split("```")[1].split("```")[0]
            
            response = response.strip()
            
            # Try to extract array with Regex
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                response = match.group(0)
            
            questions = json.loads(response)
            return self._normalize_questions(questions)
                
        except Exception as e:
            print(f"Quiz Generation Error: {e}")
            return [
                {
                    "question": "AI test tuza olmadi (API Xatosi). Bu namuna savol.",
                    "options": {"A": "To'g'ri", "B": "Xato", "C": "Bilmayman", "D": "Balki"},
                    "correct_answer": "A"
                }
            ]

    def generate_unique_questions(self, topic, grade, count):
        """Mavzu va sinf bo'yicha alohida savollar tuzish"""
        prompt = f"""
        Siz professional o'qituvchisiz. TEST savollari tuzing.
        
        MAVZU: {topic}
        O'QUVCHI DARAJASI: {grade}-sinf o'quvchilari.
        SAVOLLAR SONI: {count} ta.
        
        MUHIM QOIDA:
        1. Kalitlar (keys) FAQAT ingliz tilida: "question", "options", "correct_answer".
        2. Javobni FAQAT va FAQAT JSON formatida qaytar. Hech qanday kirish so'zlari ishlatma.
        
        Format:
        [
            {{
                "question": "Savol matni",
                "options": {{
                    "A": "Variant A",
                    "B": "Variant B",
                    "C": "Variant C",
                    "D": "Variant D"
                }},
                "correct_answer": "A"
            }}
        ]
        """

        try:
            response = self.generate_response(prompt, "Unique test generation")
            import re
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                response = match.group(0)
            
            response = response.strip()
            questions = json.loads(response)
            return self._normalize_questions(questions)
        except Exception as e:
            print(f"Unique Quiz Generation Error: {e}")
            return self._normalize_questions([
                {
                    "question": f"{topic} mavzusi bo'yicha {grade}-sinf uchun savol (AI Xatosi)",
                    "options": {"A": "Namuna A", "B": "Namuna B", "C": "Namuna C", "D": "Namuna D"},
                    "correct_answer": "A"
                }
            ] * count)

    def grade_answer(self, question, user_answer, correct_answer=None):
        """Ochiq savol yoki kodni baholash"""
        if not user_answer or len(user_answer.strip()) < 1:
            return {"score": 0, "feedback": "Javob berilmadi"}
            
        prompt = f"""
        Sen o'qituvchisan. Talabaning javobini bahola.
        Savol: {question}
        To'g'ri javob namunasi: {correct_answer}
        Talaba javobi: {user_answer}
        
        Vazifa: Talabaning javobini 0-100 oralig'ida bahola.
        Javob FAQAT JSON formatida bo'lsin:
        {{
            "score": 85,
            "feedback": "Izoh"
        }}
        """
        
        try:
            response = self.generate_response(prompt, "Baholash")
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return {"score": 0, "feedback": "AI xatosi"}
        except Exception as e:
            print(f"Grading error: {e}")
            return {"score": 0, "feedback": "Tizim xatosi"}

# Global instance
ai_assistant = GroqAIAssistant()
