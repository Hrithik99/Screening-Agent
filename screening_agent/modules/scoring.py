import os
import json
#from pdfminer.high_level import extract_text
#from docx import Document
import pandas as pd
#from local_model import _call_ollama
from openai_model import generate as gpt_generate
#from utils.text_helpers import clean_llm_json
import re
from resume_parser import parse_resume_from_file

def clean_llm_json(output: str):
    output = re.sub(r"```(json)?", "", output).strip("` \n")
    return json.loads(output)

def parse_score(score_str):
    match = re.match(r"(\d+)\s*/\s*(\d+)", score_str.strip())
    if match:
        return int(match.group(1)), int(match.group(2))
    return 0, 5

def load_schema(schema_path):
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def score_feature_by_feature(resume_data, feature_list):
    scored_features = []
    system = "You are an expert recruiter assistant. You evaluate individual resumes against scoring criteria of the given feature and output structured JSON with score and reasoning."

    for feature in feature_list:
        feature_prompt = build_individual_feature_prompt(resume_data,feature)
        try:

            output = gpt_generate(feature_prompt, system, max_tokens=600, temperature=0.3)
            result = clean_llm_json(output)
            assert "feature_name" in result and "score" in result and "reason" in result
            numeric_score, max_score = parse_score(result["score"])
            result["score"] = numeric_score
            result["max_score"] = max_score            
            scored_features.append(result)
        except Exception as e:
            print(f"[Scoring] Feature '{feature.get('feature_name')}' failed: {e}")
            scored_features.append({
                "feature_name": feature.get("feature_name"),
                "score": 0,
                "max_score": 5,
                "reason": "Scoring failed or feature not found in resume."
            })
    return scored_features

def build_individual_feature_prompt(resume_data, feature):
    fname=feature['feature_name']
    fdesc=feature['feature_description']
    fexp=feature['explanation']
    fsc=feature['scoring_criteria']
    return f"""
    You are an expert technical recruiter evaluating resumes based on specific skill/feature criteria.

    You are scoring the candidate on the feature: **{fname}**

    Feature Description:
    {fdesc}

    Scoring Criteria ({fsc}):
    {fexp}

    ---

    Task:
    Read the following candidate resume and assign a score from {fsc} for **{fname}**.
    Also, provide an impactful and straightforward 2-3 line explanation for the score based on the criteria. Use your domain knowledge as a technical recruiter and give the scores.

    Candidate Resume:
    {resume_data}


    Output Format:
    ```json
    {{
    "feature_name": "{fname}",
    "score": X out of max limit, [JSON -  In double quotes , eg: "4/5", "7/10"]
    "reason": "..."
    }}

    Return the output as valid JSON. Wrap all scoring_criteria values in double quotes.
    Do NOT return anything other than valid JSON.
    """

def run_scoring(schema_path, resumes_folder):
    schema = load_schema(schema_path)
    jd_text = schema["job_description"]
    checklist_text = schema.get("checklist", "")
    feature_list = schema["features"]
    job_id = schema["job_id"]

    results = []
    explanations = []

    for fname in os.listdir(resumes_folder):
        if not fname.lower().endswith(('.pdf', '.docx', '.txt')):
            continue

        resume_path = os.path.join(resumes_folder, fname)
        print(f"\n[Scoring] Processing: {fname}")
        try:
            resume_data = parse_resume_from_file(resume_path)
            scoring = score_feature_by_feature(resume_data,  feature_list)
            total_score = sum([f.get("score", 0) for f in scoring])
            max_total_score = sum([f.get("max_score", 5) for f in scoring])
            normalized_score = round((total_score / max_total_score) * 100, 2) if max_total_score > 0 else 0.0
            row = {
                "candidate_id": os.path.splitext(fname)[0],
                "resume_path": resume_path,
                "total_score": normalized_score,
                "comments": ""
            }
            reason_row = {"candidate_id": os.path.splitext(fname)[0]}

            for f in scoring:
                row[f["feature_name"]] = f["score"]
                reason_row[f["feature_name"] + "_reason"] = f["reason"]

            results.append(row)
            explanations.append(reason_row)

        except Exception as e:
            print(f"[Scoring] Failed for {fname}: {e}")

    df = pd.DataFrame(results)
    df_reason = pd.DataFrame(explanations)

    out_path = f"data/outputs/scoring_sheets/{job_id}_scored_candidates.xlsx"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with pd.ExcelWriter(out_path) as writer:
        df.to_excel(writer, sheet_name="Scores", index=False)
        df_reason.to_excel(writer, sheet_name="Reasons", index=False)

    print(f"\n[Scoring] Final scored output saved to {out_path}")

# CLI usage
if __name__ == "__main__":

    schema_file = 'data\outputs\\feature_schemas\d097b5a8-58a4-40b1-8a44-6e4a1d3f77a9_features.json'
    resume_dir = "data\\resumes"
    run_scoring(schema_file,resume_dir)
