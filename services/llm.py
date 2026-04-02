import json
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


MAX_RETRIES = 2


def call_llm(prompt: str, temperature: float = 0.2) -> str:
    from groq import Groq

    # Read fresh from env every call so Streamlit sidebar key works
    api_key = os.environ.get("GROQ_API_KEY", "")
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not set. Enter it in the sidebar or add to .env\n"
            "Get a free key at: https://console.groq.com"
        )
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=4096,
    )
    return response.choices[0].message.content


def _extract_json(raw: str) -> dict:
    """Extract a JSON object from raw LLM output, handling common issues."""
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()

    # 1. Try parsing as-is (works for clean output)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return {"solutions": parsed, "recommended": parsed[0]["title"] if parsed else "N/A"}
        return parsed
    except json.JSONDecodeError:
        pass

    # 2. Try extracting a JSON object {...}
    match_obj = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match_obj:
        try:
            return json.loads(match_obj.group())
        except json.JSONDecodeError:
            pass

    # 3. Try extracting a JSON array [...]
    match_arr = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if match_arr:
        try:
            parsed = json.loads(match_arr.group())
            if isinstance(parsed, list):
                return {"solutions": parsed, "recommended": parsed[0]["title"] if parsed else "N/A"}
        except json.JSONDecodeError:
            pass

    # 4. Fix trailing commas and retry
    fixed = re.sub(r",\s*([}\]])", r"\1", cleaned)
    try:
        parsed = json.loads(fixed)
        if isinstance(parsed, list):
            return {"solutions": parsed, "recommended": parsed[0]["title"] if parsed else "N/A"}
        return parsed
    except json.JSONDecodeError:
        pass

    # 5. Fix truncated JSON — close open braces/brackets
    truncated = cleaned.rstrip()
    # Remove trailing incomplete key-value pair
    truncated = re.sub(r',\s*"[^"]*"?\s*:?\s*"?[^"]*$', '', truncated)
    # Count open/close braces and brackets
    open_braces = truncated.count("{") - truncated.count("}")
    open_brackets = truncated.count("[") - truncated.count("]")
    truncated += "}" * max(0, open_braces)
    truncated += "]" * max(0, open_brackets)
    # Fix trailing commas again after repair
    truncated = re.sub(r",\s*([}\]])", r"\1", truncated)
    try:
        parsed = json.loads(truncated)
        if isinstance(parsed, list):
            return {"solutions": parsed, "recommended": parsed[0]["title"] if parsed else "N/A"}
        return parsed
    except json.JSONDecodeError:
        pass

    raise ValueError(f"Could not parse JSON from LLM output:\n{raw[:600]}")


def call_llm_json(prompt: str, temperature: float = 0.1) -> dict:
    full_prompt = (
        prompt
        + "\n\nCRITICAL: Your response must be ONLY a valid JSON object. "
        "Do not include any text before or after the JSON. "
        "Do not use markdown code fences. Do not add comments. "
        "Start your response with { and end with }."
    )

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            raw = call_llm(full_prompt, temperature=temperature)
            return _extract_json(raw)
        except ValueError as e:
            last_error = e
            if attempt < MAX_RETRIES:
                print(f"  [LLM] JSON parse failed (attempt {attempt + 1}), retrying...")
                temperature = min(temperature + 0.1, 0.5)
            continue

    raise last_error