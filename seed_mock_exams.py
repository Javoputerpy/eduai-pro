"""
Mock Exam Seed Script
SAT, IELTS va MS imtihonlari uchun 2 tadan mock test
Haqiqiy imtihon formati va savollari asosida
"""
from models import db, Exam, ExamSection, ExamQuestion

def clear_existing():
    """Avvalgi mock imtihonlarni tozalash (ixtiyoriy)"""
    pass  # Eski ma'lumotlarni saqlab qolish uchun

def add_question(section_id, text, a, b, c, d, correct, pts=10):
    q = ExamQuestion(
        section_id=section_id,
        question_text=text,
        question_type='multi',
        option_a=a, option_b=b, option_c=c, option_d=d,
        correct_option=correct,
        points=pts
    )
    db.session.add(q)
    return q


def seed_sat():
    """SAT Mock Test 1 & 2 - Haqiqiy Digital SAT formati"""

    # ── SAT Mock Test #1 ──────────────────────────────────────────────
    if not Exam.query.filter_by(title="SAT Mock Test #1").first():
        exam = Exam(title="SAT Mock Test #1", exam_type="SAT",
                    description="Digital SAT simulyatsiyasi. Reading & Writing va Math bo'limlari.",
                    duration_minutes=134)
        db.session.add(exam); db.session.flush()

        # --- Section 1: Reading & Writing Module 1 (27 savol, 32 daqiqa) ---
        rw1 = ExamSection(exam_id=exam.id, title="Reading & Writing – Module 1", order=1, duration_minutes=32)
        db.session.add(rw1); db.session.flush()

        add_question(rw1.id,
            "The following text is adapted from Jane Austen's *Pride and Prejudice* (1813).\n\n\"It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.\"\n\nWhich choice best states the main purpose of this sentence?",
            "To argue that wealthy men are obligated to marry quickly",
            "To introduce an ironic social expectation about marriage and wealth",
            "To celebrate the institution of marriage in Regency England",
            "To describe a law requiring wealthy men to marry", "B")

        add_question(rw1.id,
            "A graduate student studying urban heat islands found that cities with more green spaces had lower average temperatures. She concluded that increasing park areas could reduce urban heat. Which finding, if true, would most directly support her conclusion?",
            "Cities with fewer residents tend to have lower temperatures.",
            "Green spaces in rural areas also reduce temperatures compared to barren land.",
            "Cities that added parks over a 10-year period showed measurable temperature drops.",
            "Trees require significant water resources that cities may lack.", "C")

        add_question(rw1.id,
            "The word 'ephemeral' most nearly means:",
            "Lasting forever",
            "Short-lived or transitory",
            "Extremely colorful",
            "Related to insects", "B")

        add_question(rw1.id,
            "Researchers studying the Amazon rainforest discovered that deforestation rates _____ significantly after new satellite monitoring systems were introduced, as illegal logging became easier to detect.",
            "accelerated",
            "remained constant",
            "declined",
            "fluctuated unpredictably", "C")

        add_question(rw1.id,
            "Which transition word best completes the sentence?\n\n\"The experiment produced unexpected results; _____, the team decided to repeat the process under controlled conditions.\"",
            "furthermore",
            "consequently",
            "meanwhile",
            "although", "B")

        # --- Section 2: Reading & Writing Module 2 (27 savol, 32 daqiqa) ---
        rw2 = ExamSection(exam_id=exam.id, title="Reading & Writing – Module 2", order=2, duration_minutes=32)
        db.session.add(rw2); db.session.flush()

        add_question(rw2.id,
            "Text: \"Despite its reputation as a solitary creature, the giant panda has been observed engaging in brief social interactions during the spring mating season.\" \n\nWhich choice best describes the function of 'despite' in this sentence?",
            "It introduces a cause-and-effect relationship.",
            "It signals a contrast between common perception and observed behavior.",
            "It provides evidence for a scientific claim.",
            "It introduces an example of social behavior.", "B")

        add_question(rw2.id,
            "A researcher claims that sleep deprivation impairs cognitive function. Which data would most strongly support this claim?",
            "A survey showing that 60% of students sleep fewer than 7 hours.",
            "A study where participants who slept 5 hours scored 30% lower on memory tests than those who slept 8 hours.",
            "A report stating that many professionals work night shifts.",
            "An article about the history of sleep research.", "B")

        add_question(rw2.id,
            "Choose the grammatically correct version:\n\nThe committee, along with its advisors, _____ recommended a new policy.",
            "have",
            "has",
            "were",
            "are", "B")

        # --- Section 3: Math Module 1 (22 savol, 35 daqiqa) ---
        m1 = ExamSection(exam_id=exam.id, title="Math – Module 1", order=3, duration_minutes=35)
        db.session.add(m1); db.session.flush()

        add_question(m1.id,
            "If 3x + 9 = 27, what is the value of x?",
            "3", "6", "9", "18", "B")

        add_question(m1.id,
            "A line passes through the points (2, 5) and (4, 11). What is the slope of the line?",
            "2", "3", "4", "6", "B")

        add_question(m1.id,
            "The price of a jacket was reduced by 20% to $64. What was the original price?",
            "$75", "$76", "$80", "$84", "C")

        add_question(m1.id,
            "If f(x) = 2x² – 3x + 1, what is f(3)?",
            "8", "10", "12", "16", "B")

        add_question(m1.id,
            "A circle has a radius of 5. What is its area? (Use π ≈ 3.14)",
            "15.7", "31.4", "78.5", "157", "C")

        add_question(m1.id,
            "Solve: |2x – 4| = 10",
            "x = 7 or x = –3",
            "x = 3 or x = –7",
            "x = 5 or x = –1",
            "x = 7 only", "A")

        # --- Section 4: Math Module 2 (22 savol, 35 daqiqa) ---
        m2 = ExamSection(exam_id=exam.id, title="Math – Module 2", order=4, duration_minutes=35)
        db.session.add(m2); db.session.flush()

        add_question(m2.id,
            "A data set has values: 4, 7, 7, 9, 13. What is the mean?",
            "7", "8", "9", "10", "B")

        add_question(m2.id,
            "If x² – 5x + 6 = 0, what are the solutions?",
            "x = 1, x = 6",
            "x = 2, x = 3",
            "x = –2, x = –3",
            "x = –1, x = 6", "B")

        add_question(m2.id,
            "A store sells apples for $0.75 each and oranges for $1.25 each. Maria buys a total of 10 fruits and pays $9.50. How many apples did she buy?",
            "3", "4", "5", "6", "C")

        add_question(m2.id,
            "What is the value of sin(30°)?",
            "√3/2", "1/2", "√2/2", "1", "B")

        db.session.commit()
        print("✅ SAT Mock Test #1 seeded!")

    # ── SAT Mock Test #2 ──────────────────────────────────────────────
    if not Exam.query.filter_by(title="SAT Mock Test #2").first():
        exam2 = Exam(title="SAT Mock Test #2", exam_type="SAT",
                     description="Digital SAT – 2-sonli amaliyot testi. Murakkablik darajasi yuqoriroq.",
                     duration_minutes=134)
        db.session.add(exam2); db.session.flush()

        rw = ExamSection(exam_id=exam2.id, title="Reading & Writing – Module 1", order=1, duration_minutes=32)
        db.session.add(rw); db.session.flush()

        add_question(rw.id,
            "Passage: Climate scientists have noted that Arctic ice melt is accelerating faster than models predicted. Some researchers argue this is due to feedback loops — as ice melts, darker ocean water absorbs more heat, causing further melting.\n\nThe passage suggests that Arctic ice loss is:",
            "Slowing down due to improved models",
            "Self-reinforcing once it reaches a certain threshold",
            "Primarily caused by ocean currents",
            "Less significant than previously thought", "B")

        add_question(rw.id,
            "Which sentence uses a semicolon correctly?",
            "She wanted to go to the store; but she had no money.",
            "He studied all night; as a result, he passed the exam.",
            "They ran quickly; to catch the bus.",
            "She likes apples; and oranges.", "B")

        add_question(rw.id,
            "Choose the word that most precisely completes the sentence:\n\nThe scientist's findings were so _____ that they challenged decades of established research.",
            "mundane", "provocative", "redundant", "ambiguous", "B")

        math = ExamSection(exam_id=exam2.id, title="Math – Module 1", order=2, duration_minutes=35)
        db.session.add(math); db.session.flush()

        add_question(math.id,
            "A train travels at 60 mph for 2.5 hours. How far does it travel?",
            "120 miles", "140 miles", "150 miles", "160 miles", "C")

        add_question(math.id,
            "What is 15% of 240?",
            "24", "30", "36", "42", "C")

        add_question(math.id,
            "Simplify: (3x²)(4x³)",
            "7x⁵", "12x⁵", "12x⁶", "7x⁶", "B")

        add_question(math.id,
            "A right triangle has legs of length 6 and 8. What is the length of the hypotenuse?",
            "10", "12", "14", "√100", "A")

        add_question(math.id,
            "If 5(x – 2) = 3x + 4, then x =",
            "5", "6", "7", "8", "C")

        db.session.commit()
        print("✅ SAT Mock Test #2 seeded!")


def seed_ielts():
    """IELTS Mock Test 1 & 2 - Academic format"""

    # ── IELTS Mock Test #1 ───────────────────────────────────────────
    if not Exam.query.filter_by(title="IELTS Academic Mock Test #1").first():
        exam = Exam(title="IELTS Academic Mock Test #1", exam_type="IELTS",
                    description="IELTS Academic – Reading, Listening va Language savollari. Band 6.0–7.5 darajasi.",
                    duration_minutes=170)
        db.session.add(exam); db.session.flush()

        # --- Reading (60 min) ---
        reading = ExamSection(exam_id=exam.id, title="Reading – Passage 1", order=1, duration_minutes=60)
        db.session.add(reading); db.session.flush()

        add_question(reading.id,
            "Passage: \"Coral reefs, often called the 'rainforests of the sea', support approximately 25% of all marine species. However, rising ocean temperatures caused by climate change have led to widespread coral bleaching events, threatening these ecosystems.\"\n\nAccording to the passage, what percentage of marine species depend on coral reefs?",
            "10%", "15%", "25%", "40%", "C")

        add_question(reading.id,
            "The phrase 'coral bleaching' in the passage most likely refers to:",
            "The natural color change of corals in winter",
            "A process where corals lose their color and symbiotic algae due to stress",
            "A method used by scientists to study corals",
            "The brightening of corals due to sunlight", "B")

        add_question(reading.id,
            "The author's tone in the passage can best be described as:",
            "Optimistic", "Informative and concerned", "Dismissive", "Humorous", "B")

        add_question(reading.id,
            "Passage: \"The Industrial Revolution, which began in Britain in the late 18th century, fundamentally transformed manufacturing, transportation, and society. Steam power replaced manual labor in many industries, enabling mass production.\"\n\nWhat was the PRIMARY driver of transformation mentioned?",
            "Electricity", "Steam power", "Child labor", "International trade", "B")

        add_question(reading.id,
            "Which statement is TRUE according to the Industrial Revolution passage?",
            "The Industrial Revolution began in France.",
            "It had no effect on transportation.",
            "Steam power enabled mass production.",
            "Mining was the only industry affected.", "C")

        # --- Listening (30 min) ---
        listening = ExamSection(exam_id=exam.id, title="Listening – Section 1 & 2", order=2, duration_minutes=30)
        db.session.add(listening); db.session.flush()

        add_question(listening.id,
            "A student is calling a university to register for a course. The receptionist says the course starts on the 15th of March. \n\nWhen does the course start?",
            "March 5th", "March 15th", "March 25th", "March 30th", "B")

        add_question(listening.id,
            "In the conversation, the student's reference number is B3472. Which of the following is the student's reference number?",
            "B3742", "B3472", "D3472", "B4372", "B")

        # --- Grammar & Vocabulary ---
        grammar = ExamSection(exam_id=exam.id, title="Language Use – Grammar & Vocabulary", order=3, duration_minutes=30)
        db.session.add(grammar); db.session.flush()

        add_question(grammar.id,
            "Choose the correct form:\nBy the time she arrives, we _____ dinner.",
            "will finish",
            "will have finished",
            "are finishing",
            "finished", "B")

        add_question(grammar.id,
            "Select the word closest in meaning to 'mitigate':",
            "Aggravate", "Reduce or lessen", "Celebrate", "Investigate", "B")

        add_question(grammar.id,
            "Identify the grammatically correct sentence:",
            "Neither the students nor the teacher were present.",
            "Neither the students nor the teacher was present.",
            "Neither the students nor the teacher have been present.",
            "Neither the students nor the teacher are present.", "B")

        add_question(grammar.id,
            "Choose the correct preposition:\nShe has been working _____ this company since 2018.",
            "in", "at", "for", "with", "C")

        add_question(grammar.id,
            "Which sentence uses the passive voice correctly?",
            "The book was read by the student.",
            "The student reads the book.",
            "The book reading by student.",
            "The student was reading the book has been.", "A")

        # --- Writing Task (50 min) ---
        writing = ExamSection(exam_id=exam.id, title="Writing – Task 1 & 2 (Concepts)", order=4, duration_minutes=50)
        db.session.add(writing); db.session.flush()

        add_question(writing.id,
            "IELTS Writing Task 1: The bar chart shows electricity consumption in three countries (USA, UK, Japan) from 2000–2020. Which country had the highest consumption in 2010?",
            "UK", "Japan", "USA", "All were equal", "C")

        add_question(writing.id,
            "IELTS Writing Task 2: 'Technology has made people more isolated'. What is the most effective essay structure for an opinion essay?",
            "Problem → Solution → Conclusion",
            "Introduction → Arguments for → Arguments against → Conclusion",
            "Narration → Description → Reflection",
            "Definition → Comparison → Summary", "B")

        db.session.commit()
        print("✅ IELTS Mock Test #1 seeded!")

    # ── IELTS Mock Test #2 ───────────────────────────────────────────
    if not Exam.query.filter_by(title="IELTS Academic Mock Test #2").first():
        exam2 = Exam(title="IELTS Academic Mock Test #2", exam_type="IELTS",
                     description="IELTS Academic – 2-sonli amaliyot testi. Band 7.0+ ga qaratilgan.",
                     duration_minutes=170)
        db.session.add(exam2); db.session.flush()

        reading2 = ExamSection(exam_id=exam2.id, title="Reading – Passage 1 & 2", order=1, duration_minutes=60)
        db.session.add(reading2); db.session.flush()

        add_question(reading2.id,
            "Passage: \"Urbanization is expected to accommodate 68% of the world's population by 2050. This shift from rural to urban living has profound implications for infrastructure, resource consumption, and social dynamics.\"\n\nWhich finding, if true, would WEAKEN the passage's implication that urbanization strains resources?",
            "Urban areas consume far more energy per capita than rural areas.",
            "Dense cities have been shown to use fewer resources per person than sprawling suburbs.",
            "Migration to cities is driven primarily by economic opportunity.",
            "Many cities struggle to provide adequate housing.", "B")

        add_question(reading2.id,
            "The word 'implications' in the passage is closest in meaning to:",
            "Accusations", "Consequences", "Arguments", "Solutions", "B")

        add_question(reading2.id,
            "Choose the correct article:\n_____ Eiffel Tower is located in Paris.",
            "A", "An", "The", "No article needed", "C")

        grammar2 = ExamSection(exam_id=exam2.id, title="Language Use – Collocations & Conditionals", order=2, duration_minutes=30)
        db.session.add(grammar2); db.session.flush()

        add_question(grammar2.id,
            "Which is the correct third conditional?",
            "If I study, I will pass.",
            "If I had studied, I would have passed.",
            "If I studied, I would pass.",
            "If I study, I would pass.", "B")

        add_question(grammar2.id,
            "Choose the correct collocation:\nShe _____ a decision after thinking carefully.",
            "did", "made", "took", "had", "B")

        add_question(grammar2.id,
            "Which word is an antonym of 'reluctant'?",
            "Hesitant", "Willing", "Doubtful", "Stubborn", "B")

        add_question(grammar2.id,
            "Choose the correctly punctuated sentence:",
            "However she didn't agree with the findings.",
            "However, she didn't agree with the findings.",
            "However she, didn't agree with the findings.",
            "However she didn't, agree with the findings.", "B")

        db.session.commit()
        print("✅ IELTS Mock Test #2 seeded!")


def seed_ms():
    """
    MS (O'zbekiston maktab bitiruvchilari imtihoni) Mock Test #1 & #2
    Matematika, Ona tili (Uzbekcha), Fizika / Kimyo
    """

    # ── MS Mock Test #1 ──────────────────────────────────────────────
    if not Exam.query.filter_by(title="MS Imtihoni – Mock Test #1").first():
        exam = Exam(title="MS Imtihoni – Mock Test #1", exam_type="MS",
                    description="Maktab bitiruvchilari imtihoni (MS) simulyatsiyasi. Matematika, Fizika va Ona tili.",
                    duration_minutes=180)
        db.session.add(exam); db.session.flush()

        # --- Matematika (60 min) ---
        math = ExamSection(exam_id=exam.id, title="Matematika", order=1, duration_minutes=60)
        db.session.add(math); db.session.flush()

        add_question(math.id,
            "Tenglamani yeching: 3x – 7 = 14",
            "5", "6", "7", "8", "C")

        add_question(math.id,
            "Ikki sonning EKUB = 12, EKUK = 60. Sonlardan biri 12 bo'lsa, ikkinchisi necha?",
            "48", "36", "60", "24", "C")

        add_question(math.id,
            "a = 5, b = 3 bo'lsa, a² + 2ab + b² = ?",
            "34", "49", "64", "74", "C")

        add_question(math.id,
            "Doiraning yuzasini toping (r = 7 sm, π ≈ 3,14):",
            "43,96 sm²", "87,92 sm²", "153,86 sm²", "196 sm²", "C")

        add_question(math.id,
            "Proportsiyani yeching: x/4 = 9/12",
            "2", "3", "4", "6", "B")

        add_question(math.id,
            "log₂(8) = ?",
            "2", "3", "4", "8", "B")

        add_question(math.id,
            "f(x) = x² – 4x + 4 funksiyasining minimumi qaysi nuqtada?",
            "x = 0", "x = 2", "x = 4", "x = –2", "B")

        add_question(math.id,
            "sin²α + cos²α = ?",
            "0", "2", "1", "α", "C")

        # --- Ona tili va Adabiyot (60 min) ---
        ona_tili = ExamSection(exam_id=exam.id, title="Ona tili va Adabiyot", order=2, duration_minutes=60)
        db.session.add(ona_tili); db.session.flush()

        add_question(ona_tili.id,
            "Quyidagi so'zlardan qaysi biri otdan yasalgan sifat?",
            "yugurik", "kitobiy", "sevimli", "chiroyli", "B")

        add_question(ona_tili.id,
            "\"O'tkan kunlar\" romanining muallifi kim?",
            "Hamza", "Abdulla Qodiriy", "Cho'lpon", "Oybek", "B")

        add_question(ona_tili.id,
            "Quyidagi gaplarda qaysi birida to'ldiruvchi bor?\n\"Bola kitob o'qiydi.\"",
            "Ega – bola", "Kesim – o'qiydi", "To'ldiruvchi – kitob", "Hol – to'ldiruvchi yo'q", "C")

        add_question(ona_tili.id,
            "\"Alvido\" so'zining sinonimi qaysi?",
            "Salom", "Xayr", "Rahmat", "Marhamat", "B")

        add_question(ona_tili.id,
            "Abdulla Oripovning mashhur sherlar to'plamlaridan biri:\n",
            "\"Yulduzlarga qarab\"", "\"Mehr yog'dusi\"", "\"Alvido Muhabbat\"", "\"O'tkan kunlar\"", "A")

        # --- Fizika (60 min) ---
        fizika = ExamSection(exam_id=exam.id, title="Fizika", order=3, duration_minutes=60)
        db.session.add(fizika); db.session.flush()

        add_question(fizika.id,
            "Nyutonning 2-qonuni: F = ma. Massa m = 5 kg, tezlanish a = 3 m/s² bo'lса kuch (N):",
            "8 N", "10 N", "15 N", "2 N", "C")

        add_question(fizika.id,
            "Elektrning zaryadi qancha? (C – kulon)",
            "–1,6 × 10⁻¹⁵ C",
            "–1,6 × 10⁻¹⁹ C",
            "1,6 × 10⁻¹⁹ C",
            "9 × 10⁹ C", "B")

        add_question(fizika.id,
            "Yorug'likning bo'shliqda tarqalish tezligi (m/s):",
            "3 × 10⁶", "3 × 10⁸", "3 × 10¹⁰", "3 × 10⁴", "B")

        add_question(fizika.id,
            "Ohm qonuni bo'yicha I = U / R. U = 12 V, R = 4 Ω bo'lsa I = ?",
            "2 A", "3 A", "48 A", "0.33 A", "B")

        add_question(fizika.id,
            "Issiqlik miqdori formulasi: Q = mc∆t. Bu erda 'm' nima?",
            "Temperatura farqi",
            "Moddaning massasi",
            "Solishtirma issiqlik sig'imi",
            "Bosim", "B")

        db.session.commit()
        print("✅ MS Mock Test #1 seeded!")

    # ── MS Mock Test #2 ──────────────────────────────────────────────
    if not Exam.query.filter_by(title="MS Imtihoni – Mock Test #2").first():
        exam2 = Exam(title="MS Imtihoni – Mock Test #2", exam_type="MS",
                     description="MS imtihoni – 2-sonli amaliyot. Matematika, Kimyo va Biologiya.",
                     duration_minutes=180)
        db.session.add(exam2); db.session.flush()

        # --- Matematika ---
        math2 = ExamSection(exam_id=exam2.id, title="Matematika", order=1, duration_minutes=60)
        db.session.add(math2); db.session.flush()

        add_question(math2.id,
            "Tengsizlikni yeching: 2x + 5 > 13",
            "x > 4", "x > 3", "x < 4", "x > 9", "A")

        add_question(math2.id,
            "Geometrik progressiya: a₁ = 3, q = 2. a₅ = ?",
            "24", "48", "96", "32", "B")

        add_question(math2.id,
            "Agar a + b = 10 va ab = 21 bo'lsa, a² + b² = ?",
            "48", "58", "64", "100", "B")

        add_question(math2.id,
            "cos(60°) = ?",
            "√3/2", "1/2", "√2/2", "1", "B")

        add_question(math2.id,
            "Ikki sonning farqi 6, yig'indisi 20. Katta son necha?",
            "7", "13", "10", "14", "B")

        # --- Kimyo ---
        kimyo = ExamSection(exam_id=exam2.id, title="Kimyo", order=2, duration_minutes=60)
        db.session.add(kimyo); db.session.flush()

        add_question(kimyo.id,
            "Suvning kimyoviy formulasi:",
            "CO₂", "H₂O", "NaCl", "H₂SO₄", "B")

        add_question(kimyo.id,
            "Davriy jadvalda 1-guruh elementlari qanday ataladi?",
            "Galogenlar", "Inert gazlar", "Ishqoriy metallar", "D-elementlar", "C")

        add_question(kimyo.id,
            "NaOH + HCl → ? (+H₂O)",
            "NaCl₂", "NaCl", "Na₂Cl", "NaH", "B")

        add_question(kimyo.id,
            "Elektrolitik dissotsiatsiya nima?",
            "Moddaning qattiq holatga o'tishi",
            "Moddaning eritma yoki suyuqlikda ionlarga parchalanishi",
            "Moddaning yonishi",
            "Moddaning bug'lanishi", "B")

        # --- Biologiya ---
        bio = ExamSection(exam_id=exam2.id, title="Biologiya", order=3, duration_minutes=60)
        db.session.add(bio); db.session.flush()

        add_question(bio.id,
            "Odam organizmining asosiy hujayrasi qaysi organellni tutadi va DNK saqlaydi?",
            "Mitoxondriya", "Yadro", "Ribosoma", "Lizosoma", "B")

        add_question(bio.id,
            "Fotosintez qayerda sodir bo'ladi?",
            "Mitoxondriya", "Vakuol", "Xloroplast", "Yadro", "C")

        add_question(bio.id,
            "Qonning qizil hujayralari (eritrositlar) qanday vazifani bajaradi?",
            "Immunitetni ta'minlash",
            "Kislorodni tashish",
            "Qon ivishini ta'minlash",
            "Moddalar almashinuvi", "B")

        add_question(bio.id,
            "Mendel qonunlarida F1 avlodda qanday belgi namoyon bo'ladi?",
            "Ikkala belgi aralashib ko'rinadi",
            "Retsessiv belgi",
            "Dominant belgi",
            "Hech qanday belgi ko'rinmaydi", "C")

        add_question(bio.id,
            "DNK dekodlash jarayoni qanday ataladi?",
            "Replikatsiya", "Transkriptsiya", "Translyatsiya", "Mutatsiya", "B")

        db.session.commit()
        print("✅ MS Mock Test #2 seeded!")


def run():
    from app import app
    with app.app_context():
        print("🌱 Mock imtihonlar yuklanmoqda...")
        seed_sat()
        seed_ielts()
        seed_ms()
        print("\n🎉 Barcha mock imtihonlar muvaffaqiyatli yuklandi!")
        print(f"   Jami: {Exam.query.count()} ta imtihon mavjud.")

if __name__ == "__main__":
    run()
