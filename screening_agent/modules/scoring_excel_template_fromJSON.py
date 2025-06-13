# scoring_template_builder.py

import os
import json
import pandas as pd

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "../data/feature_schemas")
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "../data/scoring_sheets")
#os.makedirs(TEMPLATE_DIR, exist_ok=True)

def create_excel_template_from_schema(schema_path):
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    job_id = schema.get("job_id") or os.path.basename(schema_path).split("_")[0]
    feature_list = schema.get("features", [])

    base_columns = ["candidate_id", "resume_path", "total_score", "comments"]
    feature_columns = [f["feature_name"] for f in feature_list if "feature_name" in f]
    df = pd.DataFrame(columns=base_columns + feature_columns)

    criteria_notes = {f["feature_name"]: f.get("scoring_criteria", "") for f in feature_list if "feature_name" in f}
    notes_row = ["", "", "", ""] + [criteria_notes.get(col, "") for col in feature_columns]
    df.loc[-1] = notes_row
    df.index = df.index + 1
    df.sort_index(inplace=True)

    file_path = os.path.join(TEMPLATE_DIR, f"{job_id}_scoring_template.xlsx")
    df.to_excel(file_path, index=False)
    print(f"[Template Builder] Scoring template created at: {file_path}")
    return file_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python scoring_template_builder.py <schema_json_file>")
        exit(1)

    schema_file = sys.argv[1]
    create_excel_template_from_schema(schema_file)
