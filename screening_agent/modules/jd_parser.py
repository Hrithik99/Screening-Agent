import json
import time
from local_model import _call_ollama
from openai_model import generate as gpt_generate   # fallback
import os

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "../prompts/jd_extraction.txt")

def load_prompt_template(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_jd_requirements(jd_text, max_retries=3):
    """
    Extracts structured requirements from a job description using local LLM (Ollama).
    Retries up to max_retries times if output is not valid JSON as required by the prompt.
    Falls back to GPT-4o-mini if all retries fail.
    Returns: dict with fields (required_skills, preferred_skills, min_experience_years, etc.)
    """
    prompt_template = load_prompt_template(PROMPT_PATH)
    prompt = prompt_template.replace("{JD_TEXT}", jd_text)
    system = "You are an HR assistant who extracts structured job requirements from job descriptions and always returns well-formatted JSON."

    # --- Try local model (Ollama) ---
    for attempt in range(1, max_retries + 1):
        print(f"[JD Parser] Attempt {attempt}: Extracting with local model...")
        output = _call_ollama(prompt, system=system, max_tokens=1000, temperature=0.1)
        try:
            jd_data = json.loads(output)
            print("[JD Parser] Successfully parsed JSON from local model.")
            print(jd_data) 
        except json.JSONDecodeError:
            print(f"[JD Parser] Failed to parse JSON on attempt {attempt}. Output was:\n{output}\n")
            time.sleep(1)

    # --- Fallback: GPT-4o-mini, only once ---
    print("[JD Parser] All local model attempts failed. Using GPT-4o-mini fallback.")
    output = gpt_generate(prompt, system=system, max_tokens=1000, temperature=0.4)
    try:
        jd_data = json.loads(output)
        print("[JD Parser] Successfully parsed JSON using fallback GPT-4o-mini.")
        return jd_data
    except json.JSONDecodeError:
        print(f"[JD Parser] Fallback GPT-4o-mini also failed to produce JSON. Output was:\n{output}\n")
        raise ValueError("Unable to parse JD requirements as valid JSON after all retries and fallback.")

def parse_jd_from_file(jd_path):
    """
    Loads a job description from a file and extracts requirements using extract_jd_requirements.
    """
    with open(jd_path, 'r', encoding='utf-8') as f:
        jd_text = f.read()
    return extract_jd_requirements(jd_text)

# Remove after testing NOT PART OF MAIN CODE
if __name__ == "__main__":
    import sys
    # Accept JD file path from command line argument, or use default for quick testing
    if len(sys.argv) > 1:
        jd_path = sys.argv[1]
    else:
        jd_path = "data/job_descriptions/sample_jd.txt"
        print(f"No file specified, using default: {jd_path}")

    try:
        result = parse_jd_from_file(jd_path)
        print("\n--- Extracted Job Description Structure ---")
        import pprint
        pprint.pprint(result)
    except Exception as e:
        print(f"Error extracting JD requirements: {e}")