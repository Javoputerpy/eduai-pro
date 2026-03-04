from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from datetime import datetime
from models import get_user_context
from ai_model import ai_assistant

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/ai/chat', methods=['POST'])
@login_required
def ai_chat():
    """AI suhbat API - Xotira bilan"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'success': False, 'response': "Iltimos, xabar kiriting."})
        
        # Xotirani yuklash (session-dan)
        if 'chat_history' not in session:
            session['chat_history'] = []
            
        # Kontekstni tayyorlash (User stats + Chat history)
        user_stats = get_user_context(current_user)
        history = "\n".join([f"User: {m['u']}\nAI: {m['a']}" for m in session['chat_history'][-5:]])
        full_context = f"{user_stats}\n\nOldingi suhbatlar:\n{history}"
        
        # AI javobini olish
        ai_response = ai_assistant.generate_response(user_message, full_context)
        
        # Xotirani yangilash
        session['chat_history'].append({'u': user_message, 'a': ai_response})
        if len(session['chat_history']) > 10:
            session['chat_history'].pop(0)
        session.modified = True
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'response': f"Xatolik: {str(e)}"})

@api_bp.route('/ai/analyze_progress', methods=['POST'])
@login_required
def analyze_progress():
    """Progress tahlili API"""
    try:
        user_context = get_user_context(current_user)
        analysis_prompt = "O'quvchi statistikasini tahlil qiling va takliflar bering."
        ai_response = ai_assistant.generate_response(analysis_prompt, user_context)
        return jsonify({'success': True, 'analysis': ai_response})
    except Exception as e:
        return jsonify({'success': False, 'analysis': str(e)})

@api_bp.route('/ai/subject_help', methods=['POST'])
@login_required
def subject_help():
    """Fan bo'yicha yordam API"""
    data = request.get_json()
    subject = data.get('subject', '')
    topic = data.get('topic', '')
    prompt = f"{subject} fanining {topic} mavzusini tushuntirib bering."
    ai_response = ai_assistant.generate_response(prompt, get_user_context(current_user))
    return jsonify({'success': True, 'explanation': ai_response})
