from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import sys

# Add modules folder to path so existing absolute imports work
MODULES_DIR = os.path.join(os.path.dirname(__file__), "modules")
if MODULES_DIR not in sys.path:
    sys.path.append(MODULES_DIR)

from screening_agent.modules.feature_generator import generate_features
from screening_agent.modules.scoring import run_scoring

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCHEMA_DIR = os.path.join(ROOT_DIR, 'data', 'outputs', 'feature_schemas')
SCORING_DIR = os.path.join(ROOT_DIR, 'data', 'outputs', 'scoring_sheets')
RESUME_BASE_DIR = os.path.join(ROOT_DIR, 'data', 'resumes')

app = FastAPI()


def _schema_path(job_id: str) -> str:
    return os.path.join(SCHEMA_DIR, f"{job_id}_features.json")


def _results_path(job_id: str) -> str:
    return os.path.join(SCORING_DIR, f"{job_id}_scored_candidates.xlsx")


@app.post('/jobs')
async def create_job(jd: str, checklist: str | None = None):
    """Generate scoring schema for a new job."""
    schema_path = generate_features(jd, checklist)
    job_id = os.path.basename(schema_path).split('_')[0]
    return {"job_id": job_id}


@app.post('/jobs/{job_id}/resumes')
async def upload_resumes(job_id: str, files: list[UploadFile] = File(...)):
    """Upload resumes for a job."""
    dest_dir = os.path.join(RESUME_BASE_DIR, job_id)
    os.makedirs(dest_dir, exist_ok=True)
    saved = []
    for file in files:
        dest_path = os.path.join(dest_dir, file.filename)
        with open(dest_path, 'wb') as f:
            f.write(await file.read())
        saved.append(file.filename)
    return {"uploaded": saved}


@app.post('/jobs/{job_id}/score')
async def score_job(job_id: str):
    """Run scoring for uploaded resumes."""
    schema_path = _schema_path(job_id)
    resumes_dir = os.path.join(RESUME_BASE_DIR, job_id)
    if not os.path.exists(schema_path):
        raise HTTPException(status_code=404, detail='Job not found')
    if not os.path.isdir(resumes_dir):
        raise HTTPException(status_code=404, detail='No resumes uploaded')

    run_scoring(schema_path, resumes_dir)
    result_path = _results_path(job_id)
    if not os.path.exists(result_path):
        raise HTTPException(status_code=500, detail='Scoring failed')
    return {"result_path": result_path}


@app.get('/jobs/{job_id}/results')
async def get_results(job_id: str):
    """Download scoring results."""
    result_path = _results_path(job_id)
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail='Results not found')
    return FileResponse(result_path, filename=os.path.basename(result_path))
