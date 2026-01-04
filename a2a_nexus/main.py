import os
from dotenv import load_dotenv
from core import NexusAgent
from engine import NegotiationHub

load_dotenv()

    print("--- Muzokara boshlanmoqda ---")
    buyer = NexusAgent(
        name="Haridor-Bot",
        role="Xizmat oluvchi",
        goal="iPhone 15 Pro Max telefonini imkon qadar arzonroq (maksimal $900) sotib olish.",
        constraints=["Maksimal budjet $900", "Holati ideal bo'lishi kerak"]
    )
    
    seller = NexusAgent(
        name="Sotuvchi-Bot",
        role="Xizmat ko'rsatuvchi",
        goal="iPhone 15 Pro Max-ni imkon qadar qimmatroq (minumum $1000) sotish.",
        constraints=["Eng past narx $950", "Yangi holatda"]
    )
    
    # 2. Muzokara xonasini yaratish
    hub = NegotiationHub(buyer, seller)
    
    # 3. Muzokarani boshlash
    initial_context = "Sotuvchi iPhone 15 Pro Max uchun $1100 narx so'ramoqda. Haridor muzokarani boshlaydi."
    hub.run_negotiation(initial_context, max_rounds=3)

if __name__ == "__main__":
    main()
