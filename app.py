import streamlit as st  # type: ignore
import requests

API_URL = "http://localhost:8000"

# ------------- Helper functions -------------

def job_exists_remote(job_id: str) -> bool:
    """Ask the FastAPI backend whether a feature schema already exists for this job_id."""
    try:
        resp = requests.get(f"{API_URL}/jobs/{job_id}/exists")
        resp.raise_for_status()
        return resp.json().get("exists", False)
    except Exception:
        return False

# ------------- App State -------------

if "stage" not in st.session_state:
    st.session_state.stage = "enter_job"  # stages: enter_job, confirm_existing, create_job, resume
if "job_id" not in st.session_state:
    st.session_state.job_id = ""
if "results_ready" not in st.session_state:
    st.session_state.results_ready = False

# ------------- UI Logic -------------

st.title("Screening Agent UI")

# ---------------- Stage: enter_job ----------------
if st.session_state.stage == "enter_job":
    job_id_input = st.text_input("Enter Job ID")
    if st.button("Submit Job ID") and job_id_input.strip():
        st.session_state.job_id = job_id_input.strip()
        if job_exists_remote(st.session_state.job_id):
            st.session_state.stage = "confirm_existing"
        else:
            st.session_state.stage = "create_job"
        st.rerun()

# ---------------- Stage: confirm_existing ----------------
if st.session_state.stage == "confirm_existing":
    st.success(f"Job ID '{st.session_state.job_id}' exists.")
    col1, col2 = st.columns(2)
    if col1.button("Upload & Score Resumes"):
        st.session_state.stage = "resume"
        st.rerun()
    if col2.button("Enter Another ID"):
        st.session_state.stage = "enter_job"
        st.session_state.job_id = ""
        st.rerun()

# ---------------- Stage: create_job ----------------
if st.session_state.stage == "create_job":
    st.warning(f"Job ID '{st.session_state.job_id}' not found. Create a new job below.")
    jd_file = st.file_uploader("Upload Job Description (.txt)", type=["txt"])
    checklist_file = st.file_uploader("Upload Checklist (.txt, optional)", type=["txt"])
    if st.button("Create Job"):
        if jd_file is None:
            st.error("Please upload a job description text file.")
        else:
            payload = {
                "job_id": st.session_state.job_id,
                "jd": jd_file.read().decode("utf-8"),
                "checklist": checklist_file.read().decode("utf-8") if checklist_file else None,
            }
            try:
                resp = requests.post(f"{API_URL}/jobs", json=payload)
                resp.raise_for_status()
                st.success("Job created successfully!")
                st.session_state.stage = "resume"
                st.rerun()
            except Exception as e:
                st.error(f"Job creation failed: {e}")
    if st.button("Back"):
        st.session_state.stage = "enter_job"
        st.session_state.job_id = ""
        st.rerun()

# ---------------- Stage: resume ----------------
if st.session_state.stage == "resume":
    job_id = st.session_state.job_id
    st.success(f"Current Job ID: {job_id}")

    st.header("Upload Resumes")
    resumes = st.file_uploader("Resumes", type=["pdf", "docx", "txt"], accept_multiple_files=True)
    if st.button("Upload Resumes"):
        if not resumes:
            st.error("Select at least one resume file to upload.")
        else:
            files = [("files", (r.name, r.read(), r.type or "application/octet-stream")) for r in resumes]
            try:
                resp = requests.post(f"{API_URL}/jobs/{job_id}/resumes", files=files)
                resp.raise_for_status()
                uploaded = resp.json().get("uploaded", [])
                st.success(f"Uploaded {len(uploaded)} resume(s).")
            except Exception as e:
                st.error(f"Upload failed: {e}")

    if st.button("Run Scoring"):
        try:
            resp = requests.post(f"{API_URL}/jobs/{job_id}/score")
            resp.raise_for_status()
            st.session_state.results_ready = True
            st.success("Scoring completed. You can download the results below.")
        except Exception as e:
            st.error(f"Scoring failed: {e}")

    if st.session_state.results_ready:
        if st.button("Download Results"):
            try:
                resp = requests.get(f"{API_URL}/jobs/{job_id}/results")
                resp.raise_for_status()
                st.download_button(
                    label="Download Excel",
                    data=resp.content,
                    file_name=f"{job_id}_scored_candidates.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            except Exception as e:
                st.error(f"Download failed: {e}")

    if st.button("Reset Job"):
        st.session_state.stage = "enter_job"
        st.session_state.job_id = ""
        st.session_state.results_ready = False
        st.rerun()
