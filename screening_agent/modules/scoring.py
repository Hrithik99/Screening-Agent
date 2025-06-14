import os
import json
import pandas as pd
import re
from datetime import datetime

from openai_model import generate as gpt_generate
from resume_parser import parse_resume_from_file

# ---------------- Utility helpers ----------------

def clean_llm_json(output: str):
    output = re.sub(r"```(json)?", "", output).strip("` \n")
    return json.loads(output)


def parse_score(score_str):
    match = re.match(r"(\d+)\s*/\s*(\d+)", score_str.strip())
    if match:
        return int(match.group(1)), int(match.group(2))
    return 0, 5


def load_schema(schema_path):
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


# -------------- Prompt builder -------------------

def build_individual_feature_prompt(resume_data, feature):
    fname = feature["feature_name"]
    fdesc = feature["feature_description"]
    fexp = feature["explanation"]
    fsc = feature["scoring_criteria"]
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
    "score": "X/Y",
    "reason": "..."
    }}
    ```
    Do NOT return anything other than valid JSON.
    """


# -------------- Core scoring engine ---------------

def score_feature_by_feature(resume_data: str, feature_list):
    """Return a list[dict] each holding feature_name, score(int), max_score, reason"""

    system_msg = (
        "You are an expert recruiter assistant. "
        "You evaluate individual resumes against scoring criteria of the given feature and output structured JSON with score and reasoning."
    )

    scored_features = []
    for feature in feature_list:
        prompt = build_individual_feature_prompt(resume_data, feature)
        try:
            output = gpt_generate(prompt, system_msg, max_tokens=600, temperature=0.3)
            result = clean_llm_json(output)
            numeric_score, max_score = parse_score(result["score"])
            scored_features.append(
                {
                    "feature_name": result["feature_name"],
                    "score": numeric_score,
                    "max_score": max_score,
                    "reason": result["reason"],
                }
            )
        except Exception as e:
            print(f"[Scoring] Feature '{feature.get('feature_name')}' failed: {e}")
            scored_features.append(
                {
                    "feature_name": feature.get("feature_name"),
                    "score": 0,
                    "max_score": 5,
                    "reason": "Scoring failed or feature not found in resume.",
                }
            )
    return scored_features


# -------------- Main public function --------------

def run_scoring(schema_path: str, resumes_folder: str):
    """Append new scoring rows for unprocessed resumes or create file if first time."""

    schema = load_schema(schema_path)
    job_id = schema["job_id"]

    out_path = f"../data/outputs/scoring_sheets/{job_id}_scored_candidates.xlsx"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # ---------- Load previous workbook (if any) ----------
    existing_scores_df = None
    existing_reasons_df = None
    processed_candidates = set()

    if os.path.exists(out_path):
        try:
            existing_scores_df = pd.read_excel(out_path, sheet_name="Scores")
            existing_reasons_df = pd.read_excel(out_path, sheet_name="Reasons")
            processed_candidates = set(existing_scores_df["candidate_id"].astype(str))
            print(
                f"[Scoring] Found existing workbook with {len(processed_candidates)} processed resumes."
            )
        except Exception as e:
            print(f"[Scoring] Could not read existing workbook, will overwrite. Reason: {e}")
            existing_scores_df = None
            existing_reasons_df = None

    # ---------- Identify resumes to process ----------
    to_process = []
    for fname in os.listdir(resumes_folder):
        if not fname.lower().endswith((".pdf", ".docx", ".txt")):
            continue
        candidate_id = os.path.splitext(fname)[0]
        if candidate_id in processed_candidates:
            print(f"[Scoring] Skipping already processed resume: {fname}")
            continue
        to_process.append(fname)

    if not to_process:
        print("[Scoring] No new resumes to process. Returning existing path.")
        return out_path  # nothing more to do

    # ---------- Score each new resume --------------
    results_rows = []
    reason_rows = []

    feature_list = schema["features"]

    for fname in to_process:
        print(f"[Scoring] Processing new resume: {fname}")
        resume_path = os.path.join(resumes_folder, fname)
        try:
            resume_text = parse_resume_from_file(resume_path)
            feature_scores = score_feature_by_feature(resume_text, feature_list)
            total_score = sum(f["score"] for f in feature_scores)
            max_total = sum(f["max_score"] for f in feature_scores) or 1
            normalized = round((total_score / max_total) * 100, 2)

            row = {
                "candidate_id": os.path.splitext(fname)[0],
                "resume_path": resume_path,
                "total_score": normalized,
                "comments": "",
            }
            reason_row = {"candidate_id": os.path.splitext(fname)[0]}
            for f in feature_scores:
                row[f["feature_name"]] = f["score"]
                reason_row[f["feature_name"] + "_reason"] = f["reason"]
            results_rows.append(row)
            reason_rows.append(reason_row)
        except Exception as e:
            print(f"[Scoring] Failed for {fname}: {e}")

    new_scores_df = pd.DataFrame(results_rows)
    new_reasons_df = pd.DataFrame(reason_rows)

    # ---------- Combine with existing (if any) ----------
    if existing_scores_df is not None:
        combined_scores = pd.concat([existing_scores_df, new_scores_df], ignore_index=True)
        combined_reasons = pd.concat([existing_reasons_df, new_reasons_df], ignore_index=True)
    else:
        combined_scores = new_scores_df
        combined_reasons = new_reasons_df

    # ---------- Save (overwrite or create) ----------
    with pd.ExcelWriter(out_path, engine="xlsxwriter", mode="w") as writer:
        combined_scores.to_excel(writer, sheet_name="Scores", index=False)
        combined_reasons.to_excel(writer, sheet_name="Reasons", index=False)

    print(
        f"[Scoring] Workbook saved with {combined_scores.shape[0]} total scored resumes -> {out_path}"
    )
    return out_path


# ---------------- CLI test harness ----------------
if __name__ == "__main__":
    schema_file = "data/outputs/feature_schemas/sample_job_features.json"
    resume_dir = "data/resumes/sample_job"
    run_scoring(schema_file, resume_dir)
