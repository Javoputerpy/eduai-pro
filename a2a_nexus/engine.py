from core import NexusAgent
import time
from typing import List, Dict

class NegotiationHub:
    def __init__(self, agent_a: NexusAgent, agent_b: NexusAgent):
        self.agent_a = agent_a
        self.agent_b = agent_b
        self.history: List[Dict] = []
        self.is_finished = False

    def run_negotiation(self, initial_context: str, max_rounds: int = 5):
        current_context = initial_context
        print(f"[*] Muzokara boshlandi: {self.agent_a.name} vs {self.agent_b.name}")

        
        for round_num in range(1, max_rounds + 1):
            if self.is_finished:
                break
                
            print(f"\n--- Raund {round_num} ---")
            
            # Agent A turn
            thought_a = self.agent_a.think(current_context)
            message_a = self.agent_a.speak(current_context, thought_a)
            self.history.append({"agent": self.agent_a.name, "message": message_a, "thought": thought_a})
            print(f"🤖 {self.agent_a.name}: {message_a}")
            
            # Update context for Agent B
            current_context += f"\n{self.agent_a.name} dedi: {message_a}"
            
            # Agent B turn
            thought_b = self.agent_b.think(current_context)
            message_b = self.agent_b.speak(current_context, thought_b)
            self.history.append({"agent": self.agent_b.name, "message": message_b, "thought": thought_b})
            print(f"🤖 {self.agent_b.name}: {message_b}")
            
            # Update context for Agent A for next round
            current_context += f"\n{self.agent_b.name} dedi: {message_b}"
            
            # Simple consensus check (to be improved)
            if "kelishdik" in message_a.lower() or "kelishdik" in message_b.lower() or \
               "agree" in message_a.lower() or "agree" in message_b.lower():
                print("\n[+] Konsensusga erishildi!")

                self.is_finished = True
                
        if not self.is_finished:
            print("\n[!] Maksimal raundlar tugadi, lekin aniq to'xtamga kelinmadi.")

            
        return self.history
