import os
import json
import pprint
import time
from pdfminer.high_level import extract_text
from docx import Document
from local_model import _call_ollama
from openai_model import generate as gpt_generate   # fallback

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "../prompts/resume_extraction.txt")

def load_prompt_template(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()
    
def pdf_to_text(pdf_path):    
    return extract_text(pdf_path)

def docx_to_text(docx_path):
    doc = Document(docx_path)
    return '\n'.join([para.text for para in doc.paragraphs])

def extract_resume_info(resume_text, max_retries=3):
    prompt_template = load_prompt_template(PROMPT_PATH)
    prompt = prompt_template.replace("{RESUME_TEXT}", resume_text)
    system = "You are an HR assistant who extracts structured candidate data from resumes and always returns well-formatted JSON."
    '''
    for attempt in range(1, max_retries + 1):
        print(f"[Resume Parser] Attempt {attempt}: Extracting with local model...")
        output = _call_ollama(prompt, system=system, max_tokens=1000, temperature=0.2)
        try:
            resume_data = json.loads(output)
            if isinstance(resume_data, dict):
                print("[Resume Parser] Successfully parsed resume JSON object.")
                return resume_data
            else:
                print(f"[Resume Parser] Output is not a JSON object: {output}")
        except json.JSONDecodeError:
            print(f"[Resume Parser] Failed to parse JSON on attempt {attempt}. Output was:\n{output}\n")
            time.sleep(1)
    '''
    print("[Resume Parser] All local model attempts failed. Using GPT-4o-mini fallback.")
    output = gpt_generate(prompt, system=system, max_tokens=1000, temperature=0.2)
    try:
        resume_data = json.loads(output)
        if isinstance(resume_data, dict):
            print("[Resume Parser] Successfully parsed resume using fallback GPT-4o-mini.")
            return resume_data
        else:
            print(f"[Resume Parser] Fallback output is not a JSON object: {output}")
    except json.JSONDecodeError:
        print(f"[Resume Parser] Fallback GPT-4o-mini also failed to produce JSON. Output was:\n{output}\n")
        raise ValueError("Unable to parse resume as valid JSON after all retries and fallback.")

def parse_resume_from_file(resume_path):
    if resume_path.endswith('.pdf'):
        resume_text = pdf_to_text(resume_path)
    elif resume_path.endswith('.docx'):
        resume_text = docx_to_text(resume_path)
    else:
        with open(resume_path, 'r', encoding='utf-8') as f:
            resume_text = f.read()
    return extract_resume_info(resume_text)

# CLI test runner
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        resume_path = sys.argv[1]
    else:
        resume_path = "data\\resumes\\Hrithik_Resume.pdf"
        print(f"No file specified, using default: {resume_path}")

    try:
        result = parse_resume_from_file(resume_path)
        print("\n--- Extracted Resume Structure ---")

        pprint.pprint(result)
    except Exception as e:
        print(f"Error extracting resume info: {e}")
