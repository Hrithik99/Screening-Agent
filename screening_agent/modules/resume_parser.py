import os
import json
import pprint
import time
from pdfminer.high_level import extract_text
from docx import Document
from local_model import _call_ollama
from openai_model import generate as gpt_generate  # fallback
import re
from difflib import SequenceMatcher

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "../prompts/resume_extraction.txt")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../../data/Resume_Parsing")



def similar(a, b):
    """Returns similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def extract_job_duties_from_text(text, parsed_json, similarity_threshold=0.75):
    """
    Extracts bullet-pointed duties from resume text and attaches them to parsed_json["past_roles"].
    It handles multiple resume formats and is robust to formatting variation.
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    print(lines)
    job_lines = []
    for i in range(len(lines) - 1):
        current = lines[i]
        next_line = lines[i + 1]

        # Look for 2-line pattern: role/company + date
        if not current.startswith(("•", "-", "*")):
            if re.search(r"(19|20)\d{2}", next_line) and re.search(r"–|-|—|to", next_line, re.IGNORECASE):
                job_lines.append((i, f"{current}, {next_line}"))

    job_lines.append((len(lines), "EOF"))  # Sentinel for range calculation

    print("Job Lines", job_lines)

    # Prepare titles and companies from parsed_json
    roles = parsed_json.get("past_roles", [])

    for idx in range(len(job_lines) - 1):
        start_idx, header_line = job_lines[idx]
        end_idx, _ = job_lines[idx + 1]

        block_lines = lines[start_idx + 1:end_idx]
        duties = []
        for line in block_lines:
            # Match bullet-style lines or paragraphs under job headers
            if line.startswith(("•", "-", "*")) or re.match(r"^\u2022", line) or len(line.split()) > 5:
                if line.lower().strip() in ["education", "skills", "certifications", "projects"]:
                    break
                duties.append(line.lstrip("•-* \u2022").strip())

        # Assign duties to best-matching role
        best_match = None
        highest_score = 0
        for role in roles:
            title = role.get("title", "")
            company = role.get("company", "")
            composite = f"{title} {company}"
            score = similar(header_line, composite)
            if score > highest_score and score > similarity_threshold:
                highest_score = score
                best_match = role

        if best_match:
            best_match["duties"] = duties

    return parsed_json



def load_prompt_template(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def pdf_to_text(pdf_path):
    return extract_text(pdf_path)

def docx_to_text(docx_path):
    doc = Document(docx_path)
    return '\n'.join([para.text for para in doc.paragraphs])

def save_resume_json(job_id, candidate_id, resume_data):
    folder = os.path.join(OUTPUT_DIR, job_id)
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, f"{candidate_id}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(resume_data, f, indent=2)
    print(f"[Resume Parser] Saved resume JSON to {file_path}")

def extract_resume_info(resume_text, job_id, max_retries=3):
    prompt_template = load_prompt_template(PROMPT_PATH)
    prompt = prompt_template.replace("{RESUME_TEXT}", resume_text)
    system = "You are an HR assistant who extracts structured candidate data from resumes and always returns well-formatted JSON."

    # --- Skipping local model block for now ---
    print("[Resume Parser] Using GPT-4o-mini fallback.")
    #output = gpt_generate(prompt, system=system, max_tokens=1000, temperature=0.2)
    try:
        #resume_data = json.loads(output)
        with open('data\\Resume_Parsing\\67c32787-fb6b-45f2-8f76-826118d37577\\HRITHIK SARDA.json','r') as f:
            resume_data=json.load(f)
        #print(resume_data)
        if isinstance(resume_data, dict):
            resume_data["JOB_ID"] = job_id
            resume_json=extract_job_duties_from_text(resume_text,resume_data)
            print("[Resume Parser] Successfully parsed resume using fallback GPT-4o-mini.")
            save_resume_json(job_id, resume_json['name'], resume_json)
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
    #print(resume_text)
    return resume_text

# ---------------------- CLI test runner ----------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        resume_path = sys.argv[1]
        job_id = sys.argv[2]
    else:
        resume_path = "data/resumes/Hrithik_Resume.pdf"
        job_id = "67c32787-fb6b-45f2-8f76-826118d37577"
        print(f"[Resume Parser] Using default resume: {resume_path}")
        print(f"[Resume Parser] Using default JOB_ID: {job_id}")

    try:
        resume_text=parse_resume_from_file(resume_path)
        result = extract_resume_info(resume_text, job_id, candidate_id='candidate')
        print("\n--- Extracted Resume Structure ---")
        pprint.pprint(result)
    except Exception as e:
        print(f"Error extracting resume info: {e}")
