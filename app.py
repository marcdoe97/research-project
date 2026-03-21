"""
DSR Prototype — Requirements Engineering with Local LLM (Ollama)
Main Streamlit entry point.

Pages:
  1. New Requirement  — run the full pipeline
  2. History          — browse all stored requirements + test cases
  3. Traceability     — REQ → TC trace matrix
  4. Metrics          — evaluation dashboard
"""
import logging
import os
import streamlit as st

# ─── Logging Setup ────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/evaluation.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

from core.orchestrator import run_pipeline
from persistence import database

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DSR Requirements Prototype",
    layout="wide",
)

# ─── Sandbox Toggle ───────────────────────────────────────────────────────────
st.sidebar.title("DSR Prototype")
st.sidebar.caption("Local LLM · Ollama · SQLite")
st.sidebar.markdown("---")

sandbox_mode = st.sidebar.toggle("Sandbox Mode (kein echtes Speichern)", value=False)

if sandbox_mode:
    database.set_db_path("sandbox.db")
    st.sidebar.warning("Sandbox aktiv — nichts wird in der Forschungs-DB gespeichert.")
    if st.sidebar.button("Sandbox leeren"):
        import os
        if os.path.exists("sandbox.db"):
            os.remove("sandbox.db")
        st.sidebar.success("Sandbox geleert.")
else:
    database.set_db_path("prototype.db")

database.init_db()

# ─── Sandbox Banner ───────────────────────────────────────────────────────────
if sandbox_mode:
    st.warning("SANDBOX MODE — Eingaben werden nicht in der Forschungsdatenbank gespeichert.", icon="🧪")

# ─── Navigation ───────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation",
    ["New Requirement", "History", "Traceability", "Metrics"],
)
st.sidebar.markdown("---")
if not sandbox_mode:
    import socket
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = "unbekannt"
    st.sidebar.markdown("**Teilnehmer-URL:**")
    st.sidebar.code(f"http://{local_ip}:8501", language=None)
    st.sidebar.caption("Nur im gleichen WLAN erreichbar.")
st.sidebar.markdown("---")
st.sidebar.caption("Logs: `logs/evaluation.log`")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — NEW REQUIREMENT
# ═══════════════════════════════════════════════════════════════════════════════
def page_new_requirement():
    st.title("New Requirement")
    st.caption("Enter a raw, unstructured requirement. The pipeline transforms it, checks quality, and generates test cases.")

    raw_input = st.text_area(
        "Raw requirement (as written in practice)",
        height=150,
        placeholder="e.g. The system should be fast and the user can log in somehow...",
    )

    run_btn = st.button("Run Pipeline", type="primary", disabled=not raw_input.strip())

    if run_btn and raw_input.strip():
        with st.spinner("Running pipeline... (this may take 30–90s depending on your hardware)"):
            result = run_pipeline(raw_input.strip())

        if result["error"]:
            st.error(result["error"])
            if "Cannot reach Ollama" in result["error"]:
                st.info("Start Ollama with: `ollama serve`  —  then pull a model: `ollama pull llama3`")
            return

        st.success(f"Pipeline complete in {result['duration_s']}s — {result['req_id']}")

        tab_req, tab_quality, tab_tests, tab_trace = st.tabs([
            "Structured Requirement",
            "Quality Report",
            "Test Cases",
            "Trace Links",
        ])

        # --- Structured Requirement ---
        with tab_req:
            st.subheader(result["req_id"])
            st.code(result["structured_req"], language=None)
            st.caption("Format: EARS (WHEN <trigger> THE SYSTEM SHALL <response>)")

        # --- Quality Report ---
        with tab_quality:
            q = result["quality"] or {}
            col1, col2 = st.columns(2)
            conformant = q.get("conformance", False)
            col1.metric("Template Conformance", "Pass" if conformant else "Fail")
            col2.metric("Smell Count", q.get("smell_count", 0))

            if not conformant:
                st.warning(f"Conformance issue: {q.get('conformance_notes', '')}")

            smells = q.get("smells", [])
            if smells:
                st.markdown("**Detected smells:**")
                for s in smells:
                    st.markdown(f"- {s}")
            else:
                st.success("No smells detected.")

        # --- Test Cases ---
        with tab_tests:
            st.subheader(f"Test cases: {', '.join(result['tc_ids'])}")
            st.code(result["test_cases_raw"], language=None)

        # --- Trace Links ---
        with tab_trace:
            st.markdown(f"**{result['req_id']}** is traced to:")
            for tc_id in result["tc_ids"]:
                st.markdown(f"- `{tc_id}`")
            st.caption("Stored in SQLite test_cases table (req_id foreign key).")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — HISTORY
# ═══════════════════════════════════════════════════════════════════════════════
def page_history():
    st.title("History")
    st.caption("All stored requirements with their structured forms, quality reports, and test cases.")

    requirements = database.load_all_requirements()
    if not requirements:
        st.info("No requirements stored yet. Run the pipeline on the 'New Requirement' page.")
        return

    for req_id, raw_input, structured_req, created_at, version in requirements:
        quality_row = database.load_quality_for_req(req_id)
        test_cases = database.load_test_cases_for_req(req_id)

        smell_count = quality_row[0] if quality_row else "—"
        conformant = bool(quality_row[1]) if quality_row else None
        conformance_label = ("Pass" if conformant else "Fail") if conformant is not None else "—"

        header = f"{req_id}   |   Smells: {smell_count}   |   Conformance: {conformance_label}   |   {created_at}"
        with st.expander(header):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Raw input:**")
                st.write(raw_input)

            with col2:
                st.markdown("**Structured requirement:**")
                st.code(structured_req or "—", language=None)

            if quality_row:
                smells_json = quality_row[3]
                import json
                try:
                    smells = json.loads(smells_json) if smells_json else []
                except Exception:
                    smells = []
                if smells:
                    st.markdown("**Smells:**")
                    for s in smells:
                        st.markdown(f"- {s}")

            if test_cases:
                st.markdown("**Test cases:**")
                for tc_id, raw_output in test_cases:
                    st.markdown(f"`{tc_id}`")
                st.code(test_cases[0][1] if test_cases else "", language=None)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — TRACEABILITY
# ═══════════════════════════════════════════════════════════════════════════════
def page_traceability():
    st.title("Traceability Matrix")
    st.caption("Links between structured requirements and generated test cases.")

    links = database.load_all_trace_links()
    if not links:
        st.info("No trace links yet.")
        return

    import pandas as pd

    # Build matrix: rows = REQ-IDs, columns = TC-IDs
    req_ids = sorted(set(r for r, _ in links))
    tc_ids = sorted(set(t for _, t in links))
    link_set = set(links)

    matrix = {
        tc: [("X" if (req, tc) in link_set else "") for req in req_ids]
        for tc in tc_ids
    }
    df = pd.DataFrame(matrix, index=req_ids)
    df.index.name = "REQ \\ TC"

    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.markdown("**Flat link list:**")
    for req_id, tc_id in links:
        st.markdown(f"- `{req_id}` → `{tc_id}`")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — METRICS
# ═══════════════════════════════════════════════════════════════════════════════
def page_metrics():
    st.title("Evaluation Metrics")
    st.caption("Aggregated quality indicators across all stored requirements.")

    m = database.load_metrics()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Requirements", m["total_reqs"])
    col2.metric("Test Cases", m["total_tcs"])
    col3.metric("Avg. Smell Count", m["avg_smells"])
    col4.metric("Conformance Rate", f"{m['conformance_rate']} %")
    col5.metric("Traceability Coverage", f"{m['traceability_coverage']} %")

    st.markdown("---")
    st.markdown("""
**Metric definitions (aligned with DSR evaluation):**

| Metric | Definition |
|---|---|
| Avg. Smell Count | Mean number of detected quality smells per requirement |
| Conformance Rate | % of requirements that match the EARS template |
| Traceability Coverage | % of requirements with at least one linked test case |
""")

    st.caption("All data sourced from SQLite. Full log at `logs/evaluation.log`.")


# ─── Router ───────────────────────────────────────────────────────────────────
if page == "New Requirement":
    page_new_requirement()
elif page == "History":
    page_history()
elif page == "Traceability":
    page_traceability()
elif page == "Metrics":
    page_metrics()
