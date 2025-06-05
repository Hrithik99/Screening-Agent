# app/core/local_model.py
"""
local_generate(prompt, system, …) will try the local Ollama model first.
If Ollama is unreachable or OLLAMA_DISABLED=1, it falls back to GPT‑4o‑mini.
"""

import os, json, textwrap, requests
from requests.exceptions import RequestException, Timeout
from openai_model import generate as gpt_generate   # fallback

OLLAMA_DISABLED = os.getenv("OLLAMA_DISABLED", "0") == "1"
OLLAMA_HOST     = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "orca-mini")
URL             = f"{OLLAMA_HOST}/api/generate"
HEADERS         = {"Content-Type": "application/json"}

print(f"[local_model] {OLLAMA_MODEL} Disabled Flag = {OLLAMA_DISABLED}")

def _call_ollama(prompt: str, system: str | None, max_tokens: int, temperature: float):
    print("[local_model] → Trying Ollama")
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": textwrap.dedent(prompt).strip(),
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": temperature},
    }
    if system:
        payload["system"] = system
    r = requests.post(URL, headers=HEADERS, data=json.dumps(payload), timeout=20)
    r.raise_for_status()
    return r.json()["response"].strip()

def generate(prompt: str,
             system: str | None = None,
             max_tokens: int = 1000,
             temperature: float = 0.4) -> str:
    """
    Unified interface for draft / feedback loops.
    Tries Ollama; falls back to GPT‑4o‑mini on failure or when disabled.
    """
    if not OLLAMA_DISABLED:
        try:
            return _call_ollama(prompt, system, max_tokens, temperature)
        except (RequestException, Timeout) as e:
            # Log once, then continue to fallback
            print("[local_model] Ollama unavailable – using GPT‑4o‑mini. Reason:", e)
    else:
        print("[local_model] Ollama disabled, using GPT‑4o directly")
    # --- Fallback ---
    fallback_system = system or "You are an HR assistant who writes concise draft job descriptions."
    return gpt_generate(prompt, fallback_system, max_tokens=max_tokens, temperature=temperature)
