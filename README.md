# Screening Agent

**AI-Powered Employee Screening and Candidate Ranking System**

---

## Overview

The Screening Agent is a modular, multi-agent system designed to automate and accelerate the screening of candidates against job descriptions as part of a full employee lifecycle automation workflow.  
It combines fast NLP-based parsing, robust data extraction, and semantic matching (LLM or classical) to enable recruiters and organizations to shortlist, vet, and rank candidates at scale—cost-effectively and transparently.

---

## Features

- **Job Description Parsing**: Extracts key requirements (skills, experience, qualifications, domain, etc.) from raw job descriptions using local LLM or GPT fallback.
- **Resume Parsing**: Extracts candidate profile info (skills, roles, education, certifications, etc.) from PDF/DOCX/TXT using fast NLP-based and/or LLM-based approaches.
- **Section-Based Resume Analysis**: Robust section header extraction for highly accurate, rule-based parsing.
- **Semantic Matching**: Scores and ranks candidates based on multi-factor match with the job description (skills, experience, education, etc.).
- **Flexible Pipelines**: Easily configure to use fast NLP parsing for large volumes and LLMs for shortlists or hard cases.
- **Retry and Fallback Logic**: Automatic retries and seamless fallback to GPT-4o or similar when local models are unavailable.
- **CLI and Modular Design**: Run as command line scripts; future-ready for API/GUI/automation integration.
- **Logging and Traceability**: Full logs for every screening run; outputs rationale and scores for recruiter transparency.
- **Customizable and Extensible**: Easily add new skills, parsing rules, prompts, or modules.

---

## Project Structure

screening_agent/
│
├── README.md
├── requirements.txt
├── config/
│   └── config.yaml
├── data/
│   ├── resumes/
│   ├── job_descriptions/
│   └── outputs/
├── logs/
├── screening_agent/
│   ├── __init__.py
│   ├── main.py
│   ├── pipeline.py
│   ├── modules/
│   │   ├── jd_parser.py
│   │   ├── resume_parser.py
│   │   ├── resume_scraper_nlp.py
│   │   ├── semantic_matcher.py
│   │   └── local_model.py
│   └── prompts/
│       ├── jd_extraction.txt
│       ├── resume_extraction.txt
│       └── ...
│
└── .gitignore


---

## Getting Started

### Prerequisites

- Python 3.8+
- `pip` (Python package manager)
- [Ollama](https://ollama.com/) (for local LLM inference, optional but recommended)
- (Optional) OpenAI API key for GPT fallback

### Installation

1. **Clone the repo**
    ```sh
    git clone https://github.com/yourusername/your-repo-name.git
    cd your-repo-name
    ```

2. **Install dependencies**
    ```sh
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
    ```

3. **(Optional) Start Ollama server**
    ```sh
    ollama serve
    # and pull your preferred model, e.g.:
    ollama pull mistral
    ```

4. **(Optional) Set your OpenAI API key**
    ```sh
    export OPENAI_API_KEY=sk-...      # Unix/Mac
    $env:OPENAI_API_KEY="sk-..."      # Windows PowerShell
    ```

---

## Usage

### **1. Parse a Job Description**
```sh
python screening_agent/modules/jd_parser.py data/job_descriptions/sample_jd.txt

## 2. Parse a Resume (NLP‑based, section‑aware)

```sh
python screening_agent/modules/resume_scraper_nlp.py data/resumes/sample_resume.pdf

## 3. (Coming soon) Run the full semantic screening pipeline

### How It Works
- **Job Description** and **Resume** are parsed into structured JSON  
- **Section‑based logic** ensures robust field extraction even for noisy/complex resumes  
- **Semantic matcher** compares parsed fields, calculates sub‑scores, and ranks candidates  
- **Logging, config, and fallback** features make the system production‑ready  

### Configuration
Edit `config/config.yaml` to adjust scoring thresholds, weights, and pipeline settings.

### Roadmap
- Add full semantic matcher and scoring pipeline  
- Add recruiter feedback/override interface  
- Implement FastAPI/REST endpoints for integration  
- Add end‑to‑end pipeline runner CLI  
- Improve skills and experience normalization  
- Extend to GUI or dashboard  

### Contributing
PRs and issues welcome!  
Please raise issues for bugs, enhancement requests, or resume parsing edge cases.

### License
MIT

### Acknowledgments
Built using **spaCy**, **pdfminer.six**, **python‑docx**, and **Ollama**  
Inspired by best practices in large‑scale resume screening and ATS platforms.






