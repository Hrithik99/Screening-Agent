import json
import os
from typing import List, Dict, Any

from openai_model import generate as openai_generate

PROMPT_PATH = os.path.join(os.path.dirname(__file__), '../prompts/skills_match.txt')


def _load_prompt_template(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def score_skills(required_skills: List[str],
                 resume_skills: List[str],
                 past_roles: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """Score how well resume skills match required skills using OpenAI."""
    prompt_template = _load_prompt_template(PROMPT_PATH)

    jd_section = '\n'.join(f"- {skill}" for skill in required_skills)
    resume_section = ', '.join(resume_skills)

    experience_lines: List[str] = []
    if past_roles:
        for role in past_roles:
            title = role.get('title', '')
            company = role.get('company', '')
            start = role.get('start_year_month', '')
            end = role.get('end_year_month', '')
            experience_lines.append(f"{title} at {company} ({start} - {end})")
    experience_text = '\n'.join(experience_lines)

    prompt = prompt_template.format(
        REQUIRED_SKILLS=jd_section,
        RESUME_SKILLS=resume_section,
        EXPERIENCE=experience_text,
    )

    system = "You are an HR assistant who carefully scores candidate skills." \
             " Return strict JSON."

    response = openai_generate(prompt, system=system, max_tokens=800, temperature=0.3)

    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model did not return valid JSON: {e}\nResponse: {response}")


if __name__ == '__main__':
    import argparse
    from pprint import pprint

    parser = argparse.ArgumentParser(description='Score resume skills against JD requirements.')
    parser.add_argument('--jd-json', required=True, help='Path to JSON file with required_skills field')
    parser.add_argument('--resume-json', required=True, help='Path to resume JSON file with skills and past_roles')
    args = parser.parse_args()

    with open(args.jd_json, 'r', encoding='utf-8') as f:
        jd_data = json.load(f)
    with open(args.resume_json, 'r', encoding='utf-8') as f:
        resume_data = json.load(f)

    scores = score_skills(jd_data.get('required_skills', []),
                          resume_data.get('skills', []),
                          resume_data.get('past_roles', []))

    pprint(scores)
