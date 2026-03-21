"""
LLM Interaction Layer
Encapsulates all Ollama API calls, prompt templates, and output parsing.
Prompts are module-level constants — easy to adjust for research iterations.
"""
import json
import logging
import requests

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3"  # change to "mistral" or any pulled model

# ─── System Persona ────────────────────────────────────────────────────────────

_SYSTEM = (
    "You are a senior requirements engineer specialising in EARS-style requirements "
    "and acceptance test design. You produce precise, unambiguous, testable output. "
    "Always respond ONLY with the requested format. No preamble, no explanation."
)

# ─── Prompt Templates (adjust for research iterations) ────────────────────────

PROMPT_TRANSFORM = """\
Transform the following raw requirement into EARS template format.

Output format (use EXACTLY this structure, nothing else):
WHEN <trigger condition>
THE SYSTEM SHALL <system response / behaviour>

Rules:
- One WHEN/THE SYSTEM SHALL pair per requirement.
- Replace all vague words with concrete, measurable terms.
- If information is missing, insert [PLACEHOLDER].
- Do NOT add headers, bullets, or explanations.

Raw requirement:
\"\"\"{raw_text}\"\"\"\
"""

PROMPT_TEST_GENERATION = """\
Generate exactly 2 acceptance test cases for the structured requirement below.

Use this EXACT format — no deviations:

TC-ID: {tc_id_1}
PRECONDITIONS: <what must be true before the test>
STEPS:
1. <action step>
2. <action step>
EXPECTED RESULT: <observable outcome>

TC-ID: {tc_id_2}
PRECONDITIONS: <what must be true before the test>
STEPS:
1. <action step>
2. <action step>
EXPECTED RESULT: <observable outcome>

Rules:
- TC {tc_id_1} covers the happy path.
- TC {tc_id_2} covers an edge case or failure scenario.
- Do NOT add any text before or after the two test cases.

Linked requirement ({req_id}):
\"\"\"{structured_req}\"\"\"\
"""

PROMPT_QUALITY = """\
Evaluate the requirement pair below for quality issues.
Respond with a single valid JSON object — no markdown fences, no explanation.

JSON schema:
{{
  "smells": ["<smell description>", ...],
  "conformance": true | false,
  "conformance_notes": "<short note if not conformant, else empty string>",
  "smell_count": <integer>
}}

Smell categories to detect:
- Ambiguity: vague words such as "should", "might", "appropriate", "adequate", "and/or"
- Incompleteness: missing trigger, actor, or system response
- Inconsistency: contradictory statements
- Vagueness: no measurable success criterion

Raw requirement:
\"\"\"{raw_text}\"\"\"

Structured requirement:
\"\"\"{structured_req}\"\"\"\
"""

# ─── Core Call ────────────────────────────────────────────────────────────────

def _call(user_prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        content = resp.json()["message"]["content"].strip()
        logger.debug("Ollama response (%d chars): %s...", len(content), content[:80])
        return content
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"Cannot reach Ollama at {OLLAMA_URL}. "
            "Start it with: ollama serve"
        )
    except Exception as exc:
        logger.error("Ollama call failed: %s", exc)
        raise

# ─── Domain Functions ─────────────────────────────────────────────────────────

def transform_requirement(raw_text: str) -> str:
    """Convert free-text requirement into EARS-format structured requirement."""
    return _call(PROMPT_TRANSFORM.format(raw_text=raw_text))


def generate_test_cases(
    req_id: str, structured_req: str, tc_id_1: str, tc_id_2: str
) -> str:
    """Generate two acceptance test cases for a structured requirement."""
    return _call(
        PROMPT_TEST_GENERATION.format(
            req_id=req_id,
            structured_req=structured_req,
            tc_id_1=tc_id_1,
            tc_id_2=tc_id_2,
        )
    )


def evaluate_quality(raw_text: str, structured_req: str) -> dict:
    """Ask the LLM to evaluate quality and return a parsed dict."""
    raw = _call(PROMPT_QUALITY.format(raw_text=raw_text, structured_req=structured_req))
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Could not parse quality JSON — returning empty report. Raw: %s", raw[:200])
        return {
            "smells": ["[Parse error — LLM did not return valid JSON]"],
            "conformance": False,
            "conformance_notes": "Quality evaluation parse error.",
            "smell_count": 1,
        }
