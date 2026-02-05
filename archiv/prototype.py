import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Tara's Learning Journey",
    page_icon="📚",
    layout="wide"
)

# --- SESSION STATE INITIALISATION ---
if "xp" not in st.session_state:
    st.session_state.xp = 0
if "level" not in st.session_state:
    st.session_state.level = 1
if "math_quiz_done" not in st.session_state:
    st.session_state.math_quiz_done = False
if "heart_quiz_done" not in st.session_state:
    st.session_state.heart_quiz_done = False
if "rights_quiz_done" not in st.session_state:
    st.session_state.rights_quiz_done = False

XP_PER_LEVEL = 100

def add_xp(amount: int):
    """Simple XP system with auto-level-up."""
    st.session_state.xp += amount
    old_level = st.session_state.level
    st.session_state.level = max(1, st.session_state.xp // XP_PER_LEVEL + 1)
    if st.session_state.level > old_level:
        st.success(f"🎉 Level Up! You reached Level {st.session_state.level}!")
        st.balloons()

# --- LANGUAGE DICTIONARY ---
translations = {
    "English": {
        "title": "Tara’s Next Gen Digital Learning Space",
        "intro": (
            "🌍 Meet **Tara**, a 13-year-old girl from a rural village in India.\n\n"
            "She helps her family with work, but she also wants to learn – secretly dreaming of becoming a teacher. "
            "This digital learning space helps Tara learn step by step with **small story-based lessons**, "
            "**mini games**, and **rewards (XP, levels, badges)**."
        ),
        "choose_language": "Choose your language:",
        "choose_module": "Choose a learning module:",
        "modules": [
            "Math for Everyday Life",
            "Health & Body Awareness",
            "Empowerment & Rights",
            "English Basics",
            "Digital Literacy",
            "Sustainable Farming"
        ],
        "journey_title": "Tara’s Learning Journey",
        "journey_subtitle": "Learn with Tara through stories, choices and small challenges.",
        "xp_label": "Learning XP",
        "level_label": "Level",
        "badges_title": "Unlocked Badges",
        "no_badges": "No badges yet – complete more activities to unlock them! 🌟",
        "math_story": (
            "Tara helps her mother harvest vegetables. She fills **1/2 of a basket**, "
            "then later adds **1/4 of a basket** more. Fractions help her understand how much she really collected."
        ),
        "math_quiz_question": "What is 1/2 + 1/4 ?",
        "math_quiz_correct": "Correct! 🎉 Tara now knows she has 3/4 of a basket.",
        "math_quiz_wrong": "Not yet. Think of cutting a circle into 4 equal parts.",
        "math_task": "Tara wants to share 1 whole roti equally between 4 children. How much does each get?",
        "math_task_answer": "1/4",
        "math_task_hint": "If you cut one roti into 4 equal parts…",
        "math_task_label": "Write the fraction for each child:",
        "math_task_correct": "Exactly! Each child gets **1/4** of the roti. 🥙",
        "health_story": (
            "Sometimes Tara feels tired when she walks to school. In science class, she learns about the **heart** "
            "and why moving, eating well and resting are important for her body."
        ),
        "heart_quiz_question": "What is the main job of the heart?",
        "heart_quiz_options": [
            "To pump blood through the body",
            "To help you see in the dark",
            "To digest the food",
        ],
        "heart_quiz_feedback_correct": "Great! ❤️ The heart pumps blood and keeps Tara strong.",
        "heart_quiz_feedback_wrong": "Not quite. Think about what moves in your body when your heart beats.",
        "rights_story": (
            "Tara sometimes hears that school is ‘not necessary for girls’. But she learns that **every child** "
            "has the **right to education**, to feel safe and to dream about their own future."
        ),
        "rights_affirmation": "Say it aloud together with Tara:",
        "rights_affirmation_text": "_I am strong. I can learn. I have a future._",
        "rights_quiz_question": "Who has the right to go to school?",
        "rights_quiz_options": [
            "Only boys",
            "Only children in cities",
            "All children – girls and boys",
        ],
        "rights_quiz_correct": "Yes! 🎓 Every child has this right.",
        "rights_quiz_wrong": "Think about fairness: Who should be allowed to learn?",
        "english_vocab_title": "Basic Vocabulary – Daily Words",
        "english_vocab_text": "Learn simple words Tara hears in school:",
        "english_vocab_table": [
            ("Hello", "Hallo", "Namaste / Habari"),
            ("Thank you", "Danke", "Dhanyavaad / Asante"),
            ("School", "Schule", "School / Shule"),
            ("Book", "Buch", "Kitaab"),
        ],
        "digital_story": (
            "Tara doesn’t have a computer, but her family has an old smartphone. "
            "She learns how to use it safely to join a **WhatsApp study group**, "
            "watch learning videos and practise English."
        ),
        "digital_checklist_title": "Digital Skills Checklist",
        "digital_checklist_items": [
            "I can open an app on the phone.",
            "I know how to ask an adult before using mobile data.",
            "I can search YouTube or the web for school topics.",
            "I know I should never share my full name, address or phone number with strangers."
        ],
        "farming_story": (
            "Tara’s family grows vegetables on a small field. With better farming knowledge – "
            "like **composting, crop rotation and saving water** – they can grow more with less."
        ),
        "farming_activity_title": "Plan a Smart Field",
        "farming_activity_text": "Choose two crops Tara can rotate to keep the soil healthy:",
        "quiz_header": "Mini Quiz: Help Tara Solve a Problem",
        "footer": "💬 This space is for learners like Tara – balancing work, family, and dreams."
    },
    "Swahili": {
        "title": "Eneo la Kujifunza la Dijitali la Tara",
        "intro": (
            "🌍 Mkutane na **Tara**, msichana wa miaka 13 kutoka kijiji cha India.\n\n"
            "Anasaidia familia yake kufanya kazi, lakini pia anataka kujifunza. "
            "Eneo hili la kujifunza linamsaidia kujifunza hatua kwa hatua kwa kupitia **hadithi**, "
            "**michezo midogo** na **zawadi (XP, viwango, beji)**."
        ),
        "choose_language": "Chagua lugha:",
        "choose_module": "Chagua somo la kujifunza:",
        "modules": [
            "Hisabati ya Maisha ya Kila Siku",
            "Afya na Mwili",
            "Uwezeshaji na Haki",
            "Misingi ya Kiingereza",
            "Ujuzi wa Dijitali",
            "Kilimo Endelevu"
        ],
        "journey_title": "Safari ya Kujifunza ya Tara",
        "journey_subtitle": "Jifunze pamoja na Tara kwa hadithi na changamoto ndogo.",
        "xp_label": "Alama za Kujifunza (XP)",
        "level_label": "Kiwango",
        "badges_title": "Beji Ulizofungua",
        "no_badges": "Bado hakuna beji – maliza shughuli zaidi ili upate beji! 🌟",
        "math_story": (
            "Tara anamsaidia mama yake kuvuna mboga. Anajaza **nusu ya kapu (1/2)**, "
            "kisha anaongeza **robo moja (1/4)**. Sehemu (fractions) zinamsaidia kujua kiasi halisi."
        ),
        "math_quiz_question": "Nusu (1/2) + robo (1/4) ni sawa na nini?",
        "math_quiz_correct": "Sahihi! 🎉 Sasa Tara anajua ana 3/4 ya kapu.",
        "math_quiz_wrong": "Jaribu tena. Fikiria duara lililogawanywa kwa sehemu 4 sawa.",
        "math_task": "Tara anataka kugawa chapati 1 sawa kati ya watoto 4. Kila mmoja atapata kiasi gani?",
        "math_task_answer": "1/4",
        "math_task_hint": "Ukikata chapati moja katika sehemu 4 sawa…",
        "math_task_label": "Andika sehemu anayopata kila mtoto:",
        "math_task_correct": "Ndio! Kila mtoto anapata **1/4** ya chapati. 🥙",
        "health_story": (
            "Wakati mwingine Tara anachoka anapotembea kwenda shule. Katika somo la sayansi "
            "anajifunza kuhusu **moyo** na kwa nini kula vizuri, kusogea na kupumzika ni muhimu."
        ),
        "heart_quiz_question": "Kazi kuu ya moyo ni nini?",
        "heart_quiz_options": [
            "Kusukuma damu mwilini",
            "Kukusaidia kuona gizani",
            "Kumeng’enya chakula",
        ],
        "heart_quiz_feedback_correct": "Vizuri sana! ❤️ Moyo unasukuma damu na kumfanya Tara kuwa na nguvu.",
        "heart_quiz_feedback_wrong": "Si sahihi bado. Fikiria kinachotembea mwilini moyo unapopiga.",
        "rights_story": (
            "Wakati mwingine Tara anasikia watu wakisema shule ‘si muhimu kwa wasichana’. "
            "Lakini anajifunza kuwa **kila mtoto** ana **haki ya kupata elimu** na ndoto zake."
        ),
        "rights_affirmation": "Sema pamoja na Tara:",
        "rights_affirmation_text": "_Mimi ni mwenye nguvu. Naweza kujifunza. Nina maisha ya baadaye._",
        "rights_quiz_question": "Nani ana haki ya kwenda shule?",
        "rights_quiz_options": [
            "Vijana wa kiume tu",
            "Watoto wa mijini tu",
            "Watoto wote – wa kike na wa kiume",
        ],
        "rights_quiz_correct": "Ndiyo! 🎓 Kila mtoto ana haki hii.",
        "rights_quiz_wrong": "Fikiria kuhusu haki na usawa: Nani anapaswa kuruhusiwa kujifunza?",
        "english_vocab_title": "Maneno ya Msingi ya Kila Siku",
        "english_vocab_text": "Jifunze maneno rahisi ambayo Tara husikia shuleni:",
        "english_vocab_table": [
            ("Hello", "Hallo", "Habari"),
            ("Thank you", "Danke", "Asante"),
            ("School", "Schule", "Shule"),
            ("Book", "Buch", "Kitabu"),
        ],
        "digital_story": (
            "Tara hana kompyuta, lakini familia yake ina simu ya zamani. "
            "Anajifunza kuitumia vizuri kujiunga na **vikundi vya kusoma WhatsApp**, "
            "kuangalia video za elimu na kufanya mazoezi ya Kiingereza."
        ),
        "digital_checklist_title": "Orodha ya Ujuzi wa Dijitali",
        "digital_checklist_items": [
            "Naweza kufungua programu kwenye simu.",
            "Najua kuuliza mzazi kabla ya kutumia data.",
            "Naweza kutafuta mada za shule kwenye mtandao.",
            "Najua sitoi jina kamili, anwani au namba ya simu kwa watu nisowajua."
        ],
        "farming_story": (
            "Familia ya Tara inalima mboga kwenye shamba dogo. Kwa maarifa bora ya kilimo – "
            "kama **mbolea ya mboji, mzunguko wa mazao na kuokoa maji** – wanaweza kupata zaidi kwa kidogo."
        ),
        "farming_activity_title": "Panga Shamba Smart",
        "farming_activity_text": "Chagua mazao mawili ya kuyabadilishana ili ardhi ibaki na rutuba:",
        "quiz_header": "Jaribio Dogo: Msaidie Tara Kutatua Tatizo",
        "footer": "💬 Eneo hili ni kwa wanafunzi kama Tara – wakipambana na kazi, familia na ndoto."
    },
    "German": {
        "title": "TARAs Next-Gen Lernplattform",
        "intro": (
            "🌍 Lerne **Tara** kennen, ein 13-jähriges Mädchen aus einem indischen Dorf.\n\n"
            "Sie hilft ihrer Familie bei der Arbeit, möchte aber auch lernen – und träumt heimlich davon, Lehrerin zu werden. "
            "Diese digitale Lernumgebung unterstützt Tara mit **Geschichten**, **Mini-Spielen** und "
            "**Gamification-Elementen (XP, Level, Badges)**."
        ),
        "choose_language": "Wähle deine Sprache:",
        "choose_module": "Wähle ein Lernmodul:",
        "modules": [
            "Mathematik im Alltag",
            "Gesundheit & Körper",
            "Empowerment & Rechte",
            "Englisch-Grundlagen",
            "Digitale Kompetenz",
            "Nachhaltige Landwirtschaft"
        ],
        "journey_title": "TARAs Lernreise",
        "journey_subtitle": "Lerne mit Tara durch Geschichten, Entscheidungen und kleine Challenges.",
        "xp_label": "Lernpunkte (XP)",
        "level_label": "Level",
        "badges_title": "Freigeschaltete Badges",
        "no_badges": "Noch keine Badges – schließe mehr Aktivitäten ab, um welche zu verdienen! 🌟",
        "math_story": (
            "Tara hilft ihrer Mutter bei der Gemüseernte. Sie füllt **1/2 eines Korbes** "
            "und später kommen **1/4 Korb** dazu. Mit Brüchen versteht sie genau, wie viel sie gesammelt hat."
        ),
        "math_quiz_question": "Was ist 1/2 + 1/4 ?",
        "math_quiz_correct": "Richtig! 🎉 Tara weiß jetzt, dass sie 3/4 eines Korbes hat.",
        "math_quiz_wrong": "Noch nicht ganz. Denke an einen Kreis, der in 4 gleich große Stücke geteilt ist.",
        "math_task": "Tara möchte ein Fladenbrot gerecht auf 4 Kinder aufteilen. Wie viel erhält jedes Kind?",
        "math_task_answer": "1/4",
        "math_task_hint": "Wenn du ein Brot in 4 gleich große Teile schneidest…",
        "math_task_label": "Schreibe den Bruch für den Anteil je Kind:",
        "math_task_correct": "Genau! Jedes Kind bekommt **1/4** des Brotes. 🥙",
        "health_story": (
            "Manchmal ist Tara müde, wenn sie zur Schule läuft. Im Unterricht lernt sie über das **Herz** "
            "und warum Bewegung, gute Ernährung und Schlaf wichtig sind."
        ),
        "heart_quiz_question": "Was ist die Hauptaufgabe des Herzens?",
        "heart_quiz_options": [
            "Blut durch den Körper zu pumpen",
            "Dir im Dunkeln das Sehen zu ermöglichen",
            "Essen zu verdauen",
        ],
        "heart_quiz_feedback_correct": "Super! ❤️ Das Herz pumpt Blut und hält Tara stark.",
        "heart_quiz_feedback_wrong": "Noch nicht. Überlege, was sich im Körper bewegt, wenn das Herz schlägt.",
        "rights_story": (
            "Tara hört manchmal, dass Schule für Mädchen ‘nicht so wichtig’ sei. "
            "Sie lernt aber: **Jedes Kind** hat das **Recht auf Bildung**, Sicherheit und eigene Träume."
        ),
        "rights_affirmation": "Sprich den Satz gemeinsam mit Tara:",
        "rights_affirmation_text": "_Ich bin stark. Ich kann lernen. Ich habe eine Zukunft._",
        "rights_quiz_question": "Wer hat das Recht, in die Schule zu gehen?",
        "rights_quiz_options": [
            "Nur Jungen",
            "Nur Kinder in der Stadt",
            "Alle Kinder – Mädchen und Jungen",
        ],
        "rights_quiz_correct": "Ja! 🎓 Jedes Kind hat dieses Recht.",
        "rights_quiz_wrong": "Denke an Gerechtigkeit: Wer sollte lernen dürfen?",
        "english_vocab_title": "Grundwortschatz – Alltagswörter",
        "english_vocab_text": "Wichtige Wörter, die Tara in der Schule hört:",
        "english_vocab_table": [
            ("Hello", "Hallo", "Namaste / Habari"),
            ("Thank you", "Danke", "Dhanyavaad / Asante"),
            ("School", "Schule", "School / Shule"),
            ("Book", "Buch", "Kitaab"),
        ],
        "digital_story": (
            "Tara hat keinen Computer, aber die Familie besitzt ein älteres Smartphone. "
            "Sie lernt, es sicher zu nutzen: für **WhatsApp-Lerngruppen**, Lernvideos und Englischübungen."
        ),
        "digital_checklist_title": "Checkliste Digitale Kompetenzen",
        "digital_checklist_items": [
            "Ich kann eine App auf dem Handy öffnen.",
            "Ich frage eine erwachsene Person, bevor ich mobile Daten nutze.",
            "Ich kann bei YouTube oder im Web nach Schulthemen suchen.",
            "Ich weiß, dass ich meinen vollen Namen, Adresse oder Telefonnummer nicht an Fremde weitergeben darf."
        ],
        "farming_story": (
            "TARAs Familie bewirtschaftet ein kleines Feld. Mit besserem Wissen – "
            "z.B. **Kompost, Fruchtfolge und Wassersparen** – können sie nachhaltiger und erfolgreicher anbauen."
        ),
        "farming_activity_title": "Plane ein smartes Feld",
        "farming_activity_text": "Wähle zwei Pflanzen, die Tara abwechselnd anbauen kann, damit der Boden gesund bleibt:",
        "quiz_header": "Mini-Quiz: Hilf Tara bei einer Aufgabe",
        "footer": "💬 Dieser Raum ist für Lernende wie Tara – zwischen Arbeit, Familie und Träumen."
    }
}

# --- LANGUAGE SELECTION ---
language = st.sidebar.selectbox(
    "🌐 Language / Sprache / Lugha",
    list(translations.keys())
)
t = translations[language]

# --- SIDEBAR: GAMIFICATION STATUS ---
st.sidebar.markdown("### 👧 Tara’s Profile")
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Indian_girl_in_school_uniform.jpg/240px-Indian_girl_in_school_uniform.jpg",
    caption="Tara (Symbolbild)",
    use_container_width=True
)

# XP & Level
st.sidebar.markdown(f"**{t['level_label']}:** {st.session_state.level}")
current_xp_in_level = st.session_state.xp % XP_PER_LEVEL
st.sidebar.markdown(f"**{t['xp_label']}:** {st.session_state.xp} XP")
st.sidebar.progress(current_xp_in_level / XP_PER_LEVEL)

# --- MAIN LAYOUT ---
col1, col2 = st.columns([2, 1])

with col1:
    st.title(t["title"])
    st.markdown(t["intro"])
    st.markdown(f"#### 🎮 {t['journey_title']}")
    st.caption(t["journey_subtitle"])

with col2:
    st.markdown("### 📊 Progress Overview")
    st.metric(label=t["level_label"], value=st.session_state.level)
    st.metric(label=t["xp_label"], value=f"{st.session_state.xp} XP")
    st.markdown(f"**Next Level:** {XP_PER_LEVEL - current_xp_in_level} XP to go")

    st.markdown(f"### 🏅 {t['badges_title']}")
    badges = []
    if st.session_state.xp >= 20:
        badges.append("📘 First Steps Badge – Finished first activity")
    if st.session_state.xp >= 60:
        badges.append("🧠 Critical Thinker Badge – Solved multiple quizzes")
    if st.session_state.xp >= 120:
        badges.append("🌱 Community Hero Badge – Learned about rights & sustainability")

    if badges:
        for b in badges:
            st.markdown(f"- {b}")
    else:
        st.caption(t["no_badges"])

st.markdown("---")

# --- MODULE SELECTION ---
module = st.selectbox(t["choose_module"], t["modules"])

# --- MODULE CONTENT WITH TABS (LEARN / PRACTICE / REFLECT) ---
learn_tab, practice_tab, reflect_tab = st.tabs(["📖 Learn", "🕹 Practice", "💭 Reflect"])

# Helper: small function for XP feedback
def xp_feedback(amount: int):
    add_xp(amount)
    st.success(f"+{amount} XP earned for Tara! 🌟")

# --- MATH MODULE ---
if module in ["Math for Everyday Life", "Hisabati ya Maisha ya Kila Siku", "Mathematik im Alltag"]:
    with learn_tab:
        st.subheader("📖 " + module)
        st.write(t["math_story"])
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Fraction_1_2.svg/120px-Fraction_1_2.svg.png",
            caption="Fractions help Tara understand parts of a whole."
        )

    with practice_tab:
        st.subheader("🧮 " + t["quiz_header"])
        st.write(t["math_quiz_question"])
        answer = st.text_input("Your answer (e.g. 3/4, 0.75, drei viertel):")

        correct_answers = ["3/4", "¾", "0.75", "0,75", "drei viertel", "tatu robo", "three quarters"]
        if answer:
            if not st.session_state.math_quiz_done and answer.strip().lower() in correct_answers:
                st.success(t["math_quiz_correct"])
                xp_feedback(20)
                st.session_state.math_quiz_done = True
            elif st.session_state.math_quiz_done and answer.strip().lower() in correct_answers:
                st.success(t["math_quiz_correct"])
                st.info("✅ XP already earned for this activity.")
            else:
                st.info(t["math_quiz_wrong"])

        st.markdown("---")
        st.write(t["math_task"])
        rot_answer = st.text_input(t["math_task_label"], key="roti_task")
        if rot_answer:
            if rot_answer.strip().replace(" ", "") == t["math_task_answer"]:
                st.success(t["math_task_correct"])
            else:
                st.info(t["math_task_hint"])

    with reflect_tab:
        st.subheader("💭 Reflection")
        st.write(
            "- When does Tara use fractions in daily life?\n"
            "- Where do **you** see halves, quarters or thirds (e.g. food, money, time)?"
        )

# --- HEALTH MODULE ---
elif module in ["Health & Body Awareness", "Afya na Mwili", "Gesundheit & Körper"]:
    with learn_tab:
        st.subheader("❤️ " + module)
        st.write(t["health_story"])
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Diagram_of_the_human_heart_%28cropped%29.svg/200px-Diagram_of_the_human_heart_%28cropped%29.svg.png",
            caption="The human heart"
        )

    with practice_tab:
        st.subheader("🧠 Quiz: " + t["heart_quiz_question"])
        option = st.radio(
            t["heart_quiz_question"],
            t["heart_quiz_options"]
        )

        if option:
            if not st.session_state.heart_quiz_done and option == t["heart_quiz_options"][0]:
                st.success(t["heart_quiz_feedback_correct"])
                xp_feedback(20)
                st.session_state.heart_quiz_done = True
            elif option == t["heart_quiz_options"][0]:
                st.success(t["heart_quiz_feedback_correct"])
                st.info("✅ XP already earned for this activity.")
            else:
                st.info(t["heart_quiz_feedback_wrong"])

    with reflect_tab:
        st.subheader("💭 Reflection")
        st.write(
            "- What can Tara do to keep her heart healthy?\n"
            "- What can **you** do today (e.g. walking, drinking water, sleep)?"
        )

# --- EMPOWERMENT & RIGHTS MODULE ---
elif module in ["Empowerment & Rights", "Uwezeshaji na Haki", "Empowerment & Rechte"]:
    with learn_tab:
        st.subheader("⚖️ " + module)
        st.write(t["rights_story"])
        st.markdown("**" + t["rights_affirmation"] + "**")
        st.markdown(t["rights_affirmation_text"])

    with practice_tab:
        st.subheader("🎓 Quiz: " + t["rights_quiz_question"])
        option = st.radio(
            t["rights_quiz_question"],
            t["rights_quiz_options"]
        )

        if option:
            if not st.session_state.rights_quiz_done and option == t["rights_quiz_options"][2]:
                st.success(t["rights_quiz_correct"])
                xp_feedback(25)
                st.session_state.rights_quiz_done = True
            elif option == t["rights_quiz_options"][2]:
                st.success(t["rights_quiz_correct"])
                st.info("✅ XP already earned for this activity.")
            else:
                st.info(t["rights_quiz_wrong"])

    with reflect_tab:
        st.subheader("💭 Reflection")
        st.write(
            "- Was bedeutet es für Tara, dass sie ein Recht auf Bildung hat?\n"
            "- Wo in deinem Alltag merkst du, dass Rechte wichtig sind?"
        )

# --- ENGLISH BASICS MODULE ---
elif module in ["English Basics", "Misingi ya Kiingereza", "Englisch-Grundlagen"]:
    with learn_tab:
        st.subheader("📚 " + module)
        st.write(t["english_vocab_text"])
        import pandas as pd
        df = pd.DataFrame(t["english_vocab_table"], columns=["English", "German", "Local / Mixed"])
        st.table(df)

    with practice_tab:
        st.subheader("🗣 Speaking Practice")
        st.write(
            "Try to read these sentences out loud as if Tara were practising in front of a small mirror:\n\n"
            "- Hello, my name is Tara.\n"
            "- Thank you for helping me.\n"
            "- I go to school every day."
        )

    with reflect_tab:
        st.subheader("💭 Reflection")
        st.write(
            "- Which English words do you already know?\n"
            "- How could Tara use English to talk to someone from another country?"
        )

# --- DIGITAL LITERACY MODULE ---
elif module in ["Digital Literacy", "Ujuzi wa Dijitali", "Digitale Kompetenz"]:
    with learn_tab:
        st.subheader("📱 " + module)
        st.write(t["digital_story"])
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Smartphone_icon.svg/120px-Smartphone_icon.svg.png",
            caption="A simple smartphone"
        )

    with practice_tab:
        st.subheader("✅ " + t["digital_checklist_title"])
        for item in t["digital_checklist_items"]:
            st.checkbox(item, value=False)

    with reflect_tab:
        st.subheader("💭 Reflection")
        st.write(
            "- Was könnte für Tara gefährlich sein, wenn sie das Smartphone allein nutzt?\n"
            "- Welche Regeln wären fair und hilfreich (z.B. Zeitlimits, mit Erwachsenen sprechen)?"
        )

# --- SUSTAINABLE FARMING MODULE ---
elif module in ["Sustainable Farming", "Kilimo Endelevu", "Nachhaltige Landwirtschaft"]:
    with learn_tab:
        st.subheader("🌱 " + module)
        st.write(t["farming_story"])

    with practice_tab:
        st.subheader("🌾 " + t["farming_activity_title"])
        st.write(t["farming_activity_text"])
        crops = ["Tomatoes", "Beans", "Spinach", "Corn", "Lentils"]
        selected = st.multiselect("Choose 2 crops:", crops)
        if selected:
            if len(selected) == 2:
                st.success(f"Nice choice! Rotating **{selected[0]}** and **{selected[1]}** can keep soil healthier.")
            elif len(selected) > 2:
                st.info("Try to pick **exactly two** crops for simple rotation.")

    with reflect_tab:
        st.subheader("💭 Reflection")
        st.write(
            "- Wie hilft nachhaltige Landwirtschaft Tara und ihrer Familie?\n"
            "- Was bedeutet es, ‘den Boden für die Zukunft zu schützen’?"
        )

# --- GLOBAL FOOTER ---
st.markdown("---")
st.markdown(t["footer"])
