import os
import json
from dotenv import load_dotenv
import openai
import dateparser
from typing import Dict

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

PROMPT_TEMPLATE = """
Extract financial transaction details from the following user text.
Return a strict JSON object only, with keys:
- amount
- category (Food, Shopping, Bills, Transport, Health, Education, Entertainment, Other)
- date (YYYY-MM-DD)
- description

Now analyse this text:
"{text}"
"""

def call_openai_extract(text: str) -> Dict:
    prompt = PROMPT_TEMPLATE.format(text=text.replace('"', '\\"'))
    
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = resp.choices[0].message["content"].strip()

    # Try loading JSON
    try:
        data = json.loads(content)
    except:
        start = content.find('{')
        end = content.rfind('}')
        json_text = content[start:end+1]
        data = json.loads(json_text)

    # Normalize amount
    try:
        data["amount"] = float(data.get("amount"))
    except:
        data["amount"] = None

    # Normalize date
    parsed = dateparser.parse(data.get("date"))
    if parsed:
        data["date"] = parsed.strftime("%Y-%m-%d")
    else:
        data["date"] = dateparser.parse("today").strftime("%Y-%m-%d")

    # Defaults
    if not data.get("category"):
        data["category"] = "Other"

    if not data.get("description"):
        data["description"] = text[:80]

    return data
