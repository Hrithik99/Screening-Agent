import streamlit as st # type: ignore
import requests

API_URL = "http://localhost:8000"

st.title("Screening Agent UI")

# Initialize session state
if "job_id" not in st.session_state:
    st.session_state.job_id = None
if "results_ready" not in st.session_state:
    st.session_state.results_ready = False

if st.session_state.job_id is None:
    st.header("Create Job")
    manual_job_id = st.text_input("Enter Job ID")
    jd_file = st.file_uploader("Job Description (.txt)", type=["txt"])
    checklist_file = st.file_uploader("Checklist (.txt, optional)", type=["txt"])
    if st.button("Create Job"):
        if jd_file is None:
            st.error("Please upload a job description text file.")
        else:
            jd_text = jd_file.read().decode("utf-8")
            checklist_text = checklist_file.read().decode("utf-8") if checklist_file else None
            payload = {
                "job_id": manual_job_id.strip(),
                "jd": jd_text,
                "checklist": checklist_text
            }

            try:
                resp = requests.post(f"{API_URL}/jobs", json=payload)
                resp.raise_for_status()
                job_id = resp.json().get("job_id")
                st.session_state.job_id = job_id
                st.success(f"Job created with ID: {job_id}")
                st.rerun()
            except Exception as e:
                st.error(f"Job creation failed: {e}")
else:
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
        st.session_state.job_id = None
        st.session_state.results_ready = False
        st.experimental_rerun()
