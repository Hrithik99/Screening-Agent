import json
import os
import time
import uuid
from local_model import _call_ollama
from openai_model import generate as gpt_generate  # fallback

# ---------- paths -----------------------------------------------------------
BASE_DIR      = os.path.dirname(__file__)               # …/screening_agent/modules
PROMPT_PATH   = os.path.join(BASE_DIR, "../prompts/jd_extraction.txt")
OUTPUT_DIR    = os.path.join(BASE_DIR, "../../data/JD_JSON_Extracted")

# ---------- helpers ---------------------------------------------------------
def load_prompt_template(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

def _save_json(job_id: str, data: dict):
    _ensure_output_dir()
    out_path = os.path.join(OUTPUT_DIR, f"{job_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[JD Parser] Saved JSON to {out_path}")

# ---------- main extraction -------------------------------------------------
def extract_jd_requirements(jd_text: str, max_retries: int = 3) -> dict:
    """
    Extract structured JD requirements → dict, add JOB_ID, write to disk.
    """
    prompt_template = load_prompt_template(PROMPT_PATH)
    prompt = prompt_template.replace("{JD_TEXT}", jd_text)
    system = (
        "You are an HR assistant who extracts structured job requirements from "
        "job descriptions and always returns well-formatted JSON."
    )
    jd_data=None
    '''
    # Try local model first
    for attempt in range(1, max_retries + 1):
        print(f"[JD Parser] Attempt {attempt}: Extracting with local model…")
        output = _call_ollama(prompt, system=system, max_tokens=1000, temperature=0.1)
        try:
            jd_data = json.loads(output)
            print("[JD Parser] Parsed JSON from local model.")
            break
        except json.JSONDecodeError:
            print(f"[JD Parser] JSON parse failed (attempt {attempt}).")
            time.sleep(1)
            jd_data = None
    '''
    # Fallback → GPT-4o-mini
    if jd_data is None:
        print("[JD Parser] Local model failed. Falling back to GPT-4o-mini…")
        output = gpt_generate(prompt, system=system, max_tokens=1000, temperature=0.4)
        try:
            jd_data = json.loads(output)
            print("[JD Parser] Parsed JSON with GPT-4o-mini.")
        except json.JSONDecodeError:
            raise ValueError("Could not parse JD JSON after retries + fallback.")

    # ---------- add JOB_ID & persist ---------------------------------------
    job_id = str(uuid.uuid4())          # universal unique ID
    jd_data["JOB_ID"] = job_id
    _save_json(job_id, jd_data)

    return jd_data

def parse_jd_from_file(jd_path: str) -> dict:
    with open(jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()
    return extract_jd_requirements(jd_text)

# ---------------------- CLI test block --------------------------------------
if __name__ == "__main__":
    import sys, pprint

    jd_path = sys.argv[1] if len(sys.argv) > 1 else "data\job_descriptions\DY_FS.txt"
    print(f"[JD Parser] Using JD file: {jd_path}")

    try:
        result = parse_jd_from_file(jd_path)
        print("\n--- Extracted JD Structure ---")
        pprint.pprint(result)
    except Exception as exc:
        print(f"Error extracting JD requirements: {exc}")
