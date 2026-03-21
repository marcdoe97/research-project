"""
Local Quality Checker (no LLM required)
Fast regex-based smell detection and EARS conformance validation.
Results are merged with the LLM quality report in the orchestrator.
"""
import re

# Extend this list to add new smell patterns
SMELL_PATTERNS: list[tuple[str, str]] = [
    (r"\bshould\b",       "Ambiguity: 'should' implies optionality — use 'shall'"),
    (r"\bmight\b",        "Ambiguity: 'might' is non-committal"),
    (r"\bmaybe\b",        "Ambiguity: 'maybe' is non-committal"),
    (r"\bpossibly\b",     "Ambiguity: 'possibly' is non-committal"),
    (r"\busually\b",      "Ambiguity: 'usually' is context-dependent"),
    (r"\bnormally\b",     "Ambiguity: 'normally' is context-dependent"),
    (r"\bgenerally\b",    "Ambiguity: 'generally' is context-dependent"),
    (r"\boften\b",        "Ambiguity: 'often' lacks a measurable threshold"),
    (r"\bsometimes\b",    "Ambiguity: 'sometimes' lacks a measurable threshold"),
    (r"\bappropriate\b",  "Vagueness: 'appropriate' is not measurable"),
    (r"\badequate\b",     "Vagueness: 'adequate' is not measurable"),
    (r"\bsufficient\b",   "Vagueness: 'sufficient' is not measurable"),
    (r"\betc\.?\b",       "Incompleteness: 'etc.' leaves scope undefined"),
    (r"\band/or\b",       "Ambiguity: 'and/or' creates ambiguous logic"),
    (r"\bmany\b",         "Vagueness: 'many' has no measurable threshold"),
    (r"\bfew\b",          "Vagueness: 'few' has no measurable threshold"),
    (r"\bsome\b",         "Vagueness: 'some' has no measurable threshold"),
    (r"\bvarious\b",      "Vagueness: 'various' is undefined in scope"),
    (r"\buser.friendly\b","Vagueness: 'user-friendly' is subjective"),
    (r"\bfast\b",         "Vagueness: 'fast' requires a measurable threshold"),
    (r"\bslow\b",         "Vagueness: 'slow' requires a measurable threshold"),
]

EARS_WHEN = re.compile(r"\bWHEN\b", re.IGNORECASE)
EARS_SHALL = re.compile(r"\bTHE SYSTEM SHALL\b", re.IGNORECASE)


def detect_smells_local(text: str) -> list[str]:
    """Return list of smell descriptions found in text (regex-based, instant)."""
    found = []
    for pattern, description in SMELL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            found.append(description)
    return found


def check_conformance_local(structured_req: str) -> tuple[bool, str]:
    """
    Verify that structured_req contains WHEN ... THE SYSTEM SHALL ...
    Returns (is_conformant, notes).
    """
    has_when = bool(EARS_WHEN.search(structured_req))
    has_shall = bool(EARS_SHALL.search(structured_req))

    if has_when and has_shall:
        return True, ""

    missing = []
    if not has_when:
        missing.append("WHEN clause")
    if not has_shall:
        missing.append("THE SYSTEM SHALL clause")
    return False, "Missing: " + ", ".join(missing)
