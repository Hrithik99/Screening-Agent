import os
import re
import spacy
from pdfminer.high_level import extract_text
from docx import Document
from dateutil import parser as dateparser

# Initialize spaCy once
NLP = spacy.load("en_core_web_sm")

# You should expand these lists for production!
SKILLS_LIST = [
    'Python', 'SQL', 'PySpark', 'Shell', 'R', 'NLTK', 'TensorFlow', 'Pandas', 'Scikit-Learn', 'NumPy',
    'TFDV', 'PyTorch', 'Airflow', 'ML Flow', 'statsmodels', 'Dask', 'pydantic', 'DASH', 'AWS',
    'Azure', 'GCP', 'Snowflake', 'Apache Spark', 'Hadoop', 'dbt', 'Talend', 'Informatica', 'SSIS',
    'TIDAL', 'Oracle', 'SQL Server', 'PostgreSQL', 'MySQL', 'Teradata', 'MongoDB', 'Cosmos DB',
    'NoSQL', 'Apache Kafka', 'Apache Flink', 'Docker', 'Kubernetes', 'Terraform', 'GitHub Actions',
    'CI/CD', 'Power BI', 'Tableau', 'EDA', 'Statistical Modeling', 'Trend Analysis', 'matplotlib',
    'seaborn', 'Plotly', 'Agile-Scrum', 'Kanban', 'Data Modelling', 'Data Warehousing', 'GDPR/HIPAA compliance',
    'OpenAI embeddings', 'ChromaDB', 'RAG pipelines', 'Supervised & Unsupervised Learning', 'Feature Engineering', 'Model Evaluation metrics'
]
DEGREE_KEYWORDS = [
    'bachelor', 'master', 'doctor', 'phd', 'msc', 'bachelors', 'masters', 'engineering', 'm.tech', 'b.tech'
]
CERT_KEYWORDS = ['certification', 'certificate', 'certified', 'certifications', 'licenses']
SECTION_HEADERS = {
    'education': ['education', 'academic background', 'academics'],
    'experience': ['professional experience', 'work experience', 'employment', 'experience'],
    'skills': ['skills', 'technical skills', 'key skills'],
    'certifications': ['certifications', 'certificates', 'licenses'],
    'projects': ['projects', 'key projects', 'personal projects']
}


def pdf_to_text(pdf_path):
    return extract_text(pdf_path)

def docx_to_text(docx_path):
    doc = Document(docx_path)
    return '\n'.join([para.text for para in doc.paragraphs])

def extract_text_from_file(path):
    if path.endswith('.pdf'):
        return pdf_to_text(path)
    elif path.endswith('.docx'):
        return docx_to_text(path)
    else:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

def extract_email(text):
    match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    return match.group(0) if match else None

def extract_phone(text):
    match = re.search(r'(\+?\d[\d\s\-\(\)]{7,}\d)', text)
    return match.group(0) if match else None

def extract_name(text):
    # Try to find the first likely candidate (all-caps or title case at top)
    for line in text.split('\n')[:10]:
        line_strip = line.strip()
        if line_strip and not any(x in line_strip.lower() for x in ['curriculum', 'resume', 'summary']):
            if re.match(r'^[A-Z\s]{6,}$', line_strip) or re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+', line_strip):
                return line_strip
    return None

def extract_sections(text):
    lines = text.split('\n')
    section_map = {}
    current_section = None
    buffer = []

    def header_key(line):
        line_clean = line.strip().lower()
        for key, variants in SECTION_HEADERS.items():
            if any(line_clean.startswith(h) for h in variants):
                return key
        return None

    for line in lines:
        section = header_key(line)
        if section:
            if current_section and buffer:
                section_map[current_section] = '\n'.join(buffer).strip()
                buffer = []
            current_section = section
        elif current_section:
            buffer.append(line)
    # Capture last section
    if current_section and buffer:
        section_map[current_section] = '\n'.join(buffer).strip()
    return section_map

def extract_skills(skills_text):
    skills_found = set()
    text_lower = skills_text.lower()
    for skill in SKILLS_LIST:
        if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
            skills_found.add(skill)
    # Add anything in a comma/list line in skills section
    for line in skills_text.split('\n'):
        if ',' in line:
            for word in line.split(','):
                word_clean = word.strip()
                if word_clean and word_clean not in skills_found:
                    skills_found.add(word_clean)
    return list(skills_found)

def extract_education(edu_text):
    education = []
    lines = [line.strip() for line in edu_text.split('\n') if line.strip()]
    i = 0
    while i < len(lines):
        line = lines[i].lower()
        if any(degree in line for degree in DEGREE_KEYWORDS):
            degree = lines[i]
            institution = ""
            year = None
            # Look ahead for institution on next line
            if i + 1 < len(lines) and ("university" in lines[i+1].lower() or "institute" in lines[i+1].lower()):
                institution = lines[i+1]
                i += 1
            # Try to extract years
            years = re.findall(r'(20\d{2}|19\d{2})', degree + ' ' + institution)
            if years:
                year = years[-1]  # Take latest year (end year)
            education.append({'degree': degree, 'institution': institution, 'year': year})
        i += 1
    return education

def extract_certifications(cert_text):
    certifications = []
    for line in cert_text.split('\n'):
        if any(key in line.lower() for key in CERT_KEYWORDS):
            certifications.append(line.strip())
    return certifications


def extract_skills(skills_text):
    skills = []
    for line in skills_text.split('\n'):
        line = line.strip()
        if not line or line.lower().startswith("skill"):
            continue
        # Split by common separators
        for skill in re.split(r'[,\•;|]', line):
            skill = skill.strip()
            if skill:
                skills.append(skill)
    # Remove duplicates, standardize capitalization
    return sorted(set([s.title() for s in skills]))


def extract_experience(exp_text):
    exp = []
    # Regex: Title, Company, (Location) Month Year – Month Year/Present
    pattern = re.compile(
        r'([A-Za-z0-9\/\-\& ]+), ([A-Za-z0-9\.\-& ]+), ([A-Za-z ]+)? ?([A-Za-z]{3,9} \d{4}) ?[–-] ?([A-Za-z]{3,9} \d{4}|Present)',
        re.IGNORECASE)
    for match in pattern.finditer(exp_text):
        title, company, location, start, end = match.groups()
        exp.append({
            "title": title.strip(),
            "company": company.strip(),
            "start_year_month": start.strip(),
            "end_year_month": end.strip()
        })
    return exp

def calc_total_exp(experiences):
    
    years = []
    for role in experiences:
        try:
            start = dateparser.parse(role.get("start_year_month"))
            end_str = role.get("end_year_month")
            end = dateparser.parse(end_str) if end_str and end_str.lower() != "present" else None
            if end:
                years.append((end - start).days / 365.25)
            else:
                from datetime import datetime
                years.append((datetime.now() - start).days / 365.25)
        except Exception:
            continue
    return round(sum(years), 1) if years else None

def nlp_resume_parse(resume_path):
    text = extract_text_from_file(resume_path)
    sections = extract_sections(text)

    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    skills = extract_skills(sections.get('skills', '')) if 'skills' in sections else []
    education = extract_education(sections.get('education', '')) if 'education' in sections else []
    certifications = extract_certifications(sections.get('certifications', '')) if 'certifications' in sections else []
    experience = extract_experience(sections.get('experience', '')) if 'experience' in sections else []
    projects = []  # Implement if needed: extract_projects(sections.get('projects', ''))
    soft_skills = []  # Optional: can do keyword match or use spaCy's NER
    other_notes = []

    out = {
        'name': name,
        'email': email,
        'phone': phone,
        'skills': skills,
        'education': education,
        'certifications': certifications,
        'past_roles': experience,
        'projects': projects,
        'soft_skills': soft_skills,
        'other_notes': other_notes,
        'total_years_of_experience': calc_total_exp(experience)
    }
    return out

# CLI for quick test
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        resume_path = sys.argv[1]
    else:
        resume_path = "data\\resumes\\Hrithik_Resume.pdf"
        print(f"No file specified, using default: {resume_path}")
    from pprint import pprint
    pprint(nlp_resume_parse(resume_path))
