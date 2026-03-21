"""
Orchestration Layer
Controls the deterministic DSR pipeline:
  1. Generate IDs
  2. Transform requirement (LLM)
  3. Quality evaluation (LLM + local)
  4. Generate test cases (LLM)
  5. Persist everything
  6. Return structured result dict
"""
import logging
import time

from core import llm_client, quality
from persistence import database

logger = logging.getLogger(__name__)


def run_pipeline(raw_input: str) -> dict:
    """
    Execute the full requirements engineering pipeline.

    Returns a result dict with keys:
      req_id, raw_input, structured_req, quality, test_cases_raw,
      tc_ids, duration_s, error
    """
    start = time.time()
    logger.info("=== Pipeline start | input length: %d chars ===", len(raw_input))

    # --- 1. Generate IDs -------------------------------------------------------
    req_id = database.next_req_id()
    tc_id_1 = database.next_tc_id(offset=0)
    tc_id_2 = database.next_tc_id(offset=1)

    result = {
        "req_id": req_id,
        "raw_input": raw_input,
        "structured_req": None,
        "quality": None,
        "test_cases_raw": None,
        "tc_ids": [tc_id_1, tc_id_2],
        "duration_s": None,
        "error": None,
    }

    try:
        # --- 2. Transform -------------------------------------------------------
        logger.info("[%s] Step 2: Transforming requirement...", req_id)
        structured_req = llm_client.transform_requirement(raw_input)
        result["structured_req"] = structured_req
        logger.info("[%s] Structured req: %s", req_id, structured_req[:120])

        # --- 3. Quality (LLM + local merge) ------------------------------------
        logger.info("[%s] Step 3: Evaluating quality...", req_id)
        llm_report = llm_client.evaluate_quality(raw_input, structured_req)

        local_smells = quality.detect_smells_local(raw_input)
        local_conformant, conf_notes = quality.check_conformance_local(structured_req)

        # Merge: add local smells not already in LLM report
        existing = set(llm_report.get("smells", []))
        merged_smells = llm_report.get("smells", []) + [s for s in local_smells if s not in existing]
        llm_report["smells"] = merged_smells
        llm_report["smell_count"] = len(merged_smells)

        # Local conformance check overrides if LLM missed it
        if not local_conformant:
            llm_report["conformance"] = False
            llm_report["conformance_notes"] = conf_notes

        result["quality"] = llm_report
        logger.info(
            "[%s] Quality: smells=%d, conformance=%s",
            req_id,
            llm_report["smell_count"],
            llm_report["conformance"],
        )

        # --- 4. Generate test cases --------------------------------------------
        logger.info("[%s] Step 4: Generating test cases %s, %s...", req_id, tc_id_1, tc_id_2)
        test_cases_raw = llm_client.generate_test_cases(req_id, structured_req, tc_id_1, tc_id_2)
        result["test_cases_raw"] = test_cases_raw

        # --- 5. Persist --------------------------------------------------------
        logger.info("[%s] Step 5: Persisting...", req_id)
        database.save_requirement(req_id, raw_input, structured_req)
        database.save_quality_report(
            req_id=req_id,
            smells=llm_report["smells"],
            smell_count=llm_report["smell_count"],
            conformance=llm_report["conformance"],
            conformance_notes=llm_report.get("conformance_notes", ""),
        )
        database.save_test_cases(
            tc_ids=[tc_id_1, tc_id_2],
            req_id=req_id,
            raw_output=test_cases_raw,
        )

    except ConnectionError as exc:
        result["error"] = str(exc)
        logger.error("[%s] Pipeline failed (connection): %s", req_id, exc)
    except Exception as exc:
        result["error"] = f"Unexpected error: {exc}"
        logger.exception("[%s] Pipeline failed unexpectedly", req_id)

    result["duration_s"] = round(time.time() - start, 1)
    logger.info(
        "=== Pipeline end | %s | %.1fs | error: %s ===",
        req_id,
        result["duration_s"],
        result["error"],
    )
    return result
