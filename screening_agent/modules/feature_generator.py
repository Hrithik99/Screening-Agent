# feature_generator.py

import os
import json
#import uuid
from datetime import datetime
from local_model import _call_ollama
from openai_model import generate as gpt_generate
import pandas as pd
import re

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..\\prompts\\feature_generation.txt")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..\\..\\data\\outputs\\feature_schemas")
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..\\..\\data\\outputs\\scoring_sheets")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMPLATE_DIR, exist_ok=True)
def clean_llm_json(output: str):
    output = re.sub(r"```(json)?", "", output).strip("` \n")
    #print(output)
    return json.loads(output)

def load_prompt_template(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def save_feature_schema(job_id, feature_data):
    filename = os.path.join(OUTPUT_DIR, f"{job_id}_features.json")
    #print('We are hereeeeeeeeeeeeeeeeeee',filename)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(feature_data, f, indent=2)
    print(f"[Feature Generator] Saved schema to {filename}")
    return filename

def create_excel_template(job_id, feature_list):
    base_columns = ["candidate_id", "resume_path", "total_score", "comments"]
    feature_columns = [f["feature_name"] for f in feature_list if "feature_name" in f]
    df = pd.DataFrame(columns=base_columns + feature_columns)

    # Optional: Add scoring criteria as second row or another sheet
    criteria_notes = {f["feature_name"]: f.get("scoring_criteria", "") for f in feature_list if "feature_name" in f}
    notes_row = ["", "", "", ""] + [criteria_notes.get(col, "") for col in feature_columns]
    df.loc[-1] = notes_row  # Insert as first row
    df.index = df.index + 1  # Shift index
    df.sort_index(inplace=True)

    file_path = os.path.join(TEMPLATE_DIR, f"{job_id}_scoring_template.xlsx")
    df.to_excel(file_path, index=False)
    print(f"[Feature Generator] Excel scoring template created: {file_path}")

    return file_path

def generate_features(job_id, jd_text, checklist_text=None):
    prompt_template = load_prompt_template(PROMPT_PATH)
    prompt = prompt_template.replace("{JD_TEXT}", jd_text.strip())
    if checklist_text:
        prompt = prompt.replace("{CHECKLIST_TEXT}", checklist_text.strip())
    else:
        prompt = prompt.replace("{CHECKLIST_TEXT}", "(No checklist provided)")

    system = "You are an HR assistant who reads job descriptions and recruiter checklists, and outputs a JSON list of scoring features for resume screening."

    output = None
    try:
        #print("[Feature Generator] Generating features using LLM...")
        output = gpt_generate(prompt, system, max_tokens=1500, temperature=0.3)
        #print(output)
        feature_list = clean_llm_json(output)
        #print('Feature List:  ', feature_list)
        assert isinstance(feature_list, list)
         
    except Exception as e:
        print(f"[Feature Generator] failed: {e}")

    #job_id = str(uuid.uuid4())
    schema = {
        "job_id": job_id,
        "created_at": datetime.utcnow().isoformat(),
        "job_description": jd_text,
        "checklist": checklist_text or "",
        "features": feature_list
    }
    #print("Job ID : ",job_id)
    schema_path = save_feature_schema(job_id, schema)
    #create_excel_template(job_id, feature_list)
    '''
    # Optionally review
    if validate_loop:
        print("\n--- Review the Features Below ---")
        for i, feat in enumerate(output, 1):
            print(f"\nFeature {i}:")
            print(json.dumps(feat, indent=2))
        input("\nReview completed. Press Enter to confirm and save.")
    '''
    return schema_path

# CLI usage
if __name__ == "__main__":

    jd_path = "data\job_descriptions\Data_Science.txt"
    checklist_path="data\Recruiter_Checklist\\recuiter_checlist_for_resume_eval.txt"
    

    with open(jd_path, 'r', encoding='utf-8') as f:
        jd_text = f.read()


    with open(checklist_path, 'r', encoding='utf-8') as f:
        checklist_text = f.read()

    generate_features(jd_text, checklist_text)
