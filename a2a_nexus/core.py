import os
import json
import requests
from typing import List, Dict

class NexusAgent:
    def __init__(self, name: str, role: str, goal: str, constraints: List[str] = None):
        self.name = name
        self.role = role
        self.goal = goal
        self.constraints = constraints or []
        self.memory: List[Dict] = []
        self.api_key = os.getenv("GROQ_API_KEY")
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def think(self, context: str) -> str:
        """Agent processes the situation and decides its next move (inner monologue)"""
        prompt = f"""
        Sizning ismingiz: {self.name}
        Rolingiz: {self.role}
        Maqsadingiz: {self.goal}
        Cheklovlar: {', '.join(self.constraints)}

        Vaziyat (Context): {context}

        DIQQAT: Siz hozircha faqat *o'zingiz uchun* fikrlayapsiz (Inner Monologue). 
        Qaror qabul qiling va keyingi xabaringizni qanday bo'lishini rejalashtiring.
        Faqat fikrlaringizni qaytaring.
        """
        return self._call_llm(prompt)

    def speak(self, context: str, thought: str) -> str:
        """Agent generates a message to the other agent based on its thoughts"""
        prompt = f"""
        Sizning fikrlaringiz: {thought}
        Sizning rolingiz va maqsadingizga mos ravishda boshqa agentga xabar yuboring.
        Xabar qisqa, aniq va maqsadga yo'naltirilgan bo'lsin.
        """
        message = self._call_llm(prompt)
        self.memory.append({"role": "assistant", "content": message})
        return message

    def _call_llm(self, prompt: str) -> str:
        if not self.api_key:
            return "Error: No API Key provided."
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        try:
            response = requests.post(self.url, headers=headers, json=data)
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Error connecting to AI: {str(e)}"
