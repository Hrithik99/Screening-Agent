# openai_model.py
from dotenv import load_dotenv
from openai import OpenAI
import textwrap

load_dotenv()
client = OpenAI()
MODEL = "gpt-4o-mini"     # or "gpt-4o"

def generate(prompt: str,
             system: str,
             max_tokens: int = 1000,
             temperature: float = 0.4) -> str:
    prompt = textwrap.dedent(prompt).strip()
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return resp.choices[0].message.content.strip()
