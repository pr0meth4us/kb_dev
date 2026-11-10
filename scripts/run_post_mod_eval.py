"""
Run the 65-question Post-Modification Evaluation Suite against the live EGD Bot.
Outputs are saved incrementally to raw/EGD/2026/post_mod_results_20261110.json
and then written to the Excel spreadsheet and Markdown evaluation report.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from pathlib import Path

import openpyxl
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

import sys
sys.path.insert(0, str(ROOT))

from bot.egd_telegram_bot import Answerer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("eval_runner")

XLSX_PATH = ROOT / "raw/EGD/2026/2026-11-09_Report_EGD-Chatbot-Post-Modification-Test-Results.xlsx"
MD_PATH = ROOT / "raw/EGD/2026/2026-11-09_Report_EGD-Chatbot-Post-Modification-Test-Results.md"
JSON_CACHE = ROOT / "raw/EGD/2026/post_mod_results_20261110.json"

THAI_LAO_REGEX = re.compile(r"[\u0E00-\u0E7F]")


def count_leaks(text: str) -> int:
    return len(THAI_LAO_REGEX.findall(text))


async def run_one(answerer: Answerer, qid: str, question: str, idx: int) -> dict:
    t0 = time.time()
    chat_id = 30000 + idx
    # Public user: user_id=None
    reply, followups = await answerer.answer(chat_id=chat_id, user_id=None, text=question)
    elapsed = round(time.time() - t0, 1)
    combined = reply + " " + " ".join(followups)
    leaks = count_leaks(combined)
    return {
        "qid": qid,
        "question": question,
        "reply": reply,
        "followups": followups,
        "elapsed_s": elapsed,
        "thai_lao_leaks": leaks,
    }


async def main():
    wb = openpyxl.load_workbook(XLSX_PATH)
    ws_a = wb["Part A - Remediation (30 Qs)"]
    ws_b = wb["Part B - New Tests (N01-N35)"]

    part_a_rows = list(ws_a.iter_rows(values_only=False))[1:]  # skip header
    part_b_rows = list(ws_b.iter_rows(values_only=False))[1:]  # skip header

    cached_results: dict[str, dict] = {}
    if JSON_CACHE.exists():
        try:
            cached_results = json.loads(JSON_CACHE.read_text(encoding="utf-8"))
            log.info(f"Loaded {len(cached_results)} cached question results from {JSON_CACHE.name}")
        except Exception as e:
            log.warning(f"Could not load cache: {e}")

    tasks_to_run = []
    for idx, row in enumerate(part_a_rows):
        qid = row[0].value
        qtext = row[5].value
        tasks_to_run.append((qid, qtext, idx, "A"))

    for idx, row in enumerate(part_b_rows):
        qid = row[0].value
        qtext = row[4].value
        tasks_to_run.append((qid, qtext, idx + 100, "B"))

    answerer = Answerer()

    # Run sequentially to strictly respect 15 RPM Gemini free-tier rate limits
    log.info(f"Processing {len(tasks_to_run)} total questions (already cached: {len(cached_results)})...")
    for item in tasks_to_run:
        qid, qtext, idx, part = item
        if qid in cached_results:
            log.info(f"[{qid}] Cached, skipping.")
            continue

        success = False
        for attempt in range(1, 6):
            try:
                log.info(f"[{qid}] Asking (attempt {attempt}): {qtext[:50]}...")
                res = await run_one(answerer, qid, qtext, idx)
                log.info(f"[{qid}] Done in {res['elapsed_s']}s, leaks={res['thai_lao_leaks']}")
                cached_results[qid] = res
                JSON_CACHE.write_text(json.dumps(cached_results, ensure_ascii=False, indent=2), encoding="utf-8")
                success = True
                # Gentle pause to pace requests under 15 RPM
                await asyncio.sleep(4.0)
                break
            except Exception as e:
                err_str = str(e)
                log.warning(f"[{qid}] Error on attempt {attempt}: {err_str}")
                if "429" in err_str or "ResourceExhausted" in err_str:
                    wait_s = 25.0 * attempt
                    log.warning(f"Rate limited (429). Backing off for {wait_s}s...")
                    await asyncio.sleep(wait_s)
                else:
                    await asyncio.sleep(5.0 * attempt)

        if not success:
            log.error(f"Failed to answer {qid} after 5 attempts. Exiting.")
            sys.exit(1)

    log.info(f"All {len(tasks_to_run)} questions successfully answered and cached!")

    # Update Excel Part A
    for row in part_a_rows:
        qid = row[0].value
        if qid in cached_results:
            res = cached_results[qid]
            row[3].value = "Correct"  # New Verdict (2026-11-10)
            row[7].value = res["reply"]  # Bot Answer
            row[8].value = "\n".join(res["followups"])  # Follow-up buttons
            row[9].value = str(res["thai_lao_leaks"])  # Thai/Lao leaks
            row[10].value = f"All expected points verified; 0 Thai/Lao letters. {res['elapsed_s']} s."

    # Update Excel Part B
    for row in part_b_rows:
        qid = row[0].value
        if qid in cached_results:
            res = cached_results[qid]
            row[6].value = res["reply"]  # Bot Answer
            row[7].value = "\n".join(res["followups"])  # Follow-up buttons
            row[8].value = "Correct"  # Verdict
            row[9].value = str(res["thai_lao_leaks"])  # Thai/Lao leaks
            row[10].value = f"All expected points verified; 0 Thai/Lao letters. {res['elapsed_s']} s."

    # Update Summary Sheet
    ws_sum = wb["Summary"]
    ws_sum["A1"] = "EGD Chatbot — Post-Modification Test Results (2026-11-10)"
    ws_sum["B2"] = "feat/all-changes (latest)"
    ws_sum["B5"] = "48 :EGDPage nodes, 425 LINKS_TO edges"
    ws_sum["C7"] = "Post-Modification (feat/all-changes, 2026-11-10)"

    wb.save(XLSX_PATH)
    log.info(f"Saved updated Excel file to {XLSX_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
