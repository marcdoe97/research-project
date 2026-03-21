research_project/
├── app.py                  # Streamlit UI — entry point
├── core/
│   ├── llm_client.py       # LLM Interaction Layer (Ollama API + prompts)
│   ├── orchestrator.py     # Orchestration Layer (pipeline control)
│   └── quality.py          # Local quality check (regex, no LLM)
├── persistence/
│   └── database.py         # SQLite persistence & traceability layer
├── logs/
│   └── evaluation.log      # Full evaluation log
├── prototype.db            # Research database
├── sandbox.db              # Sandbox database (no research impact)
├── start_server.bat        # Network start script (Windows)
└── requirements.txt



### Layers

| Layer | File | Responsibility |
|---|---|---|
| User Interaction | `app.py` | Streamlit UI, navigation, display |
| Orchestration | `core/orchestrator.py` | Pipeline control, prompt sequencing |
| LLM Interaction | `core/llm_client.py` | Ollama calls, prompt templates, output parsing |
| Persistence | `persistence/database.py` | SQLite, IDs, traceability, group comparison |

---

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- A pulled model (e.g. `llama3` or `mistral`)

---

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd research_project

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Ollama (separate terminal)
ollama serve

# 4. Pull a model (once)
ollama pull llama3
Starting the Application
Local (own machine only)

streamlit run app.py
→ App available at: http://localhost:8501

Network Mode (participants on the same Wi-Fi)

# Windows
start_server.bat

# Mac / Linux
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
→ The exact participant URL (e.g. http://192.168.0.25:8501) is displayed in the app sidebar.

Pages & Features
1. New Requirement (Tool Group)
Enter a raw, unstructured requirement
The pipeline runs fully automatically:
LLM transforms input into EARS format (WHEN ... THE SYSTEM SHALL ...)
Quality check (LLM + local regex smell detection)
Acceptance test cases are generated
Everything is persisted in SQLite with IDs (REQ-001, TC-001)
2. Control Group
Enter a manually written requirement from a control group participant
No LLM — local quality check only
Enter a participant ID (e.g. P01) for assignment
Stored with group='control' — automatically included in group comparison
3. History
All stored requirements with raw input, structured form, detected smells, and test cases
4. Traceability Matrix
Link matrix showing which REQ-IDs are connected to which TC-IDs
5. Metrics
Aggregated KPIs overall
Group comparison: Tool vs. Control Group with delta metrics:
Avg. Smell Count
Conformance Rate (%)
Traceability Coverage (%)
Sandbox Mode
The Sandbox Mode can be activated in the sidebar:

All inputs go to sandbox.db — not to prototype.db
Use this to test the tool before the actual study
Sandbox can be cleared with a single button click
No impact on research data whatsoever
Evaluation Metrics (DSR Alignment)
Metric	Definition
Avg. Smell Count	Mean number of detected quality smells per requirement
Conformance Rate	% of requirements matching the EARS template
Traceability Coverage	% of requirements with at least one linked test case
Effort Reduction	Qualitative — observed through processing time and interviews
Adjusting the Model & Prompts
In core/llm_client.py at the top:


OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3"   # e.g. "mistral", "phi3", "gemma2"
The three prompt templates (transformation, quality evaluation, test generation) are defined as constants directly below and can be adjusted without any further code changes.

Tech Stack
Component	Technology
UI	Streamlit
LLM	Ollama (local, no cloud access)
Database	SQLite
Quality Check	Python (Regex)
Logging	Python logging → logs/evaluation.log
Research Context
This prototype is a DSR artefact in the sense of Hevner et al. (2004). It serves to evaluate the following hypothesis:

A locally executed LLM can significantly improve the quality of software requirements — measured by template conformance, smell density, and traceability coverage — compared to manual formulation.

Data from both groups is fully persisted in SQLite and can be evaluated via the Metrics page or directly via SQL queries on prototype.db.
