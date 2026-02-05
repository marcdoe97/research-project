# app.py
import streamlit as st
import sqlite3

# --- 1. Datenbank-Verbindung & Tabelle ---
conn = sqlite3.connect("prototype.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS faelle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titel TEXT NOT NULL,
    beschreibung TEXT,
    status TEXT
)
""")
conn.commit()

# --- 2. Navigation ---
st.sidebar.title("Navigation")
seite = st.sidebar.radio("Choose", ["Start", "Create new case", "Show cases"])

# --- 3. Startseite ---
if seite == "Start":
    st.title("Prototyp – Example interface")
    st.write("""
    This Prototyp shows exemplary:
    - Recording cases via a form    
    - Storing them in an SQLite database
    - Displaying the recorded cases in a list
    
    You can later adapt the fields to your research domain
    (e.g., requirements, incidents, process steps, etc.).
    """)

# --- 4. Formular zum Anlegen ---
elif seite == "Create new case":
    st.title("Create new case")

    titel = st.text_input("Titel")
    beschreibung = st.text_area("Description")
    status = st.selectbox("Status", ["Open", "In Progress", "Done"])

    if st.button("Save"):
        if titel.strip() == "":
            st.error("Please enter a title.")
        else:
            c.execute(
                "INSERT INTO faelle (titel, beschreibung, status) VALUES (?, ?, ?)",
                (titel, beschreibung, status)
            )
            conn.commit()
            st.success("Case saved successfully!")

# --- 5. Liste der Fälle anzeigen ---
elif seite == "Show cases":
    st.title("Show cases")

    c.execute("SELECT id, titel, beschreibung, status FROM faelle ORDER BY id DESC")
    faelle = c.fetchall()

    if not faelle:
        st.info("No cases found.")
    else:
        for f in faelle:
            fid, ftitel, fbeschreibung, fstatus = f
            with st.expander(f"#{fid} – {ftitel} ({fstatus})"):
                st.write(f"**Description:** {fbeschreibung if fbeschreibung else '–'}")
                st.write(f"**Status:** {fstatus}")
