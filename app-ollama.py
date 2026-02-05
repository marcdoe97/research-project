import streamlit as st
import sqlite3
import requests
import time

# ===========================
# 1. GRUNDKONFIGURATION
# ===========================

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3"  # oder ein anderes Modell, das du mit ollama pull geladen hast

DB_NAME = "requirements.db"


# ===========================
# 2. DATENBANK-FUNKTIONEN
# ===========================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            improved_text TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def save_requirement(title, raw_text, improved_text, category):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO requirements (title, raw_text, improved_text, category)
        VALUES (?, ?, ?, ?)
        """,
        (title, raw_text, improved_text, category),
    )
    conn.commit()
    conn.close()


def load_requirements():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        SELECT id, title, category, created_at, raw_text, improved_text
        FROM requirements
        ORDER BY created_at DESC
        """
    )
    rows = c.fetchall()
    conn.close()
    return rows


# ===========================
# 3. OLLAMA-AUFRUF
# ===========================

def call_ollama(raw_text, category):
    """
    Ruft das lokale Ollama-Model auf und bittet um eine
    bessere, strukturierte Version der Anforderung.
    """
    system_prompt = (
        "Du bist ein Assistent für Requirements Engineering. "
        "Du erhältst eine rohe Anforderung und sollst sie "
        "verständlich, vollständig und strukturiert formulieren. "
        "Nutze klare, kurze Sätze und, wenn sinnvoll, Aufzählungen. "
        "Sprache: Englisch."
    )

    user_prompt = f"""
Kategorie: {category}
Roh-Anforderung:
\"\"\"{raw_text}\"\"\"

Aufgabe:
1. Formuliere die Anforderung klar und strukturiert neu.
2. Wenn Informationen fehlen, formuliere neutrale Platzhalter (z. B. '…').
3. Nutze eine sachliche, professionelle Sprache.
"""

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        # Ollama-Chat-API antwortet mit data["message"]["content"]
        return data["message"]["content"].strip()
    except Exception as e:
        # Fehlerbehandlung für UI
        return f"FEHLER beim Aufruf von Ollama: {e}"


# ===========================
# 4. STREAMLIT-UI
# ===========================

def main():
    st.set_page_config(
        page_title="Ollama Prototyp – Requirements-Assistent",
        page_icon="🧠",
        layout="wide",
    )

    # DB initialisieren
    init_db()

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Seite wählen", ["Neue Anforderung", "Historie"])

    st.sidebar.markdown("---")
    st.sidebar.write(f"Modell: `{OLLAMA_MODEL}`")
    st.sidebar.write(f"Ollama-URL: `{OLLAMA_URL}`")

    if page == "Neue Anforderung":
        page_new_requirement()
    elif page == "Historie":
        page_history()


def page_new_requirement():
    st.title("Neue Anforderung mit KI-Unterstützung erfassen")

    col1, col2 = st.columns(2)

    with col1:
        title = st.text_input("Titel der Anforderung")
        category = st.selectbox(
            "Kategorie",
            ["Allgemein", "Fachlich", "Technisch", "Nicht-funktional"],
        )
        raw_text = st.text_area(
            "Roh-Anforderung (so wie sie aktuell in der Praxis formuliert würde)",
            height=200,
        )

        generate_button = st.button("KI-Vorschlag generieren")

    with col2:
        st.subheader("KI-optimierte Anforderung")

        if "improved_text" not in st.session_state:
            st.session_state["improved_text"] = ""

        improved_area = st.empty()

        if generate_button:
            if not raw_text.strip() or not title.strip():
                st.warning("Bitte mindestens Titel und Roh-Anforderung ausfüllen.")
            else:
                with st.spinner("Ollama denkt nach…"):
                    start_time = time.time()
                    improved = call_ollama(raw_text, category)
                    duration = time.time() - start_time

                st.session_state["improved_text"] = improved

                st.success(f"KI-Vorschlag generiert (Dauer: {duration:.1f} Sekunden)")

        improved_text = st.session_state.get("improved_text", "")
        improved_value = improved_area.text_area(
            "Überarbeiteter Vorschlag (editierbar)",
            improved_text,
            height=260,
        )

        # Button zum Speichern
        if st.button("Anforderung speichern"):
            if not title.strip() or not raw_text.strip():
                st.error("Titel und Roh-Anforderung dürfen nicht leer sein.")
            else:
                save_requirement(title, raw_text, improved_value, category)
                st.success("Anforderung wurde gespeichert.")
                # Session-Text zurücksetzen
                st.session_state["improved_text"] = ""


def page_history():
    st.title("Historie der erfassten Anforderungen")

    requirements = load_requirements()

    if not requirements:
        st.info("Es wurden noch keine Anforderungen gespeichert.")
        return

    for req in requirements:
        req_id, title, category, created_at, raw_text, improved_text = req

        with st.expander(f"#{req_id} – {title} ({category}, {created_at})"):
            st.markdown("**Roh-Anforderung:**")
            st.write(raw_text)

            st.markdown("---")
            st.markdown("**KI-optimierte Anforderung:**")
            st.write(improved_text if improved_text else "_(kein Vorschlag gespeichert)_")


if __name__ == "__main__":
    main()
