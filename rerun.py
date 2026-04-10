import json
import re
from ollama import Client
import os
IP_PAUL = os.getenv("IP_PAUL")
IP_TUTI = os.getenv("IP_TUTI")
IP_SERVER = os.getenv("IP_SERVER")
client_str = Client(host=IP_SERVER)


def build_structuring_prompt(md_text, attempt, error_msg=None):
    base = f"""
    You are an expert medical document structuring system.
    
    Return ONLY valid JSON.
    
    RULES:
    - Use double quotes for ALL keys and values
    - Use true/false/null ONLY for booleans (no variations like true_crossed)
    - Do NOT use arrays [] unless values are lists
    - Do NOT put key-value pairs inside arrays
    - Ensure JSON is syntactically valid
    
    INPUT:
    {md_text}
    """

    if attempt == 1:
        base += "\n\nIMPORTANT: Your previous output was INVALID JSON. Fix all syntax errors."

    if attempt >= 2:
        base += "\n\nSTRICT: Output MUST pass json.loads(). No trailing commas. No invalid tokens."

    if error_msg:
        base += f"\n\nPrevious error:\n{error_msg}"

    return base


####################################3
def structure_with_retry(md_text, model, client_str, max_retries=3):
    error_msg = None

    for attempt in range(max_retries):
        print(f" Attempt {attempt + 1}")

        response = client_str.chat(
            model=model,
            messages=[{
                "role": "user",
                "content": build_structuring_prompt(md_text, attempt, error_msg)
            }],
            options={"seed": 42}
        )

        raw_output = response["message"]["content"]


        cleaned = re.sub(r"^```json\s*|\s*```$", "", raw_output.strip(), flags=re.DOTALL)

        try:
            return json.loads(cleaned)

        except json.JSONDecodeError as e:
            error_msg = str(e)
            print(f"❌ Failed attempt {attempt + 1}: {error_msg}")
            print("Raw model output:\n", raw_output)

    return None