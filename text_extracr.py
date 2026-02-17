import os
import base64
import json
import glob
import time
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"


def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def extract_content_from_image(image_path, max_retries=3, retry_delay=2):
    """
    Extract full answer sheet structure:
    Questions -> Parts -> Topics -> Subtopics
    """

    prompt = """
Extract handwritten answers into STRICT JSON.

The paper may contain:
- Multiple questions ONLY if explicitly written (Q1, Question 2, etc.)
- Each question may have parts (a, b, c…)
- Each part contains topics and explanations

Return JSON EXACTLY in this structure:

{
  "questions": [
    {
      "question_id": "",
      "question_title": "",
      "parts": [
        {
          "part_id": "main",
          "topic": "",
          "content": "",
          "sub_topics": [
            {
              "topic": "",
              "content": "",
              "sub_topics": []
            }
          ]
        }
      ]
    }
  ]
}

CRITICAL RULES:
- Create multiple questions ONLY if numbering is explicitly written
- If no question number is written → treat as ONE question
- If no parts → use part_id="main"
- Do NOT infer new questions from headings
- Return valid JSON only
"""


    encoded = encode_image(image_path)

    for attempt in range(1, max_retries + 1):
        try:
            res = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}}
                    ]
                }],
                response_format={"type": "json_object"},
                seed=42,
                temperature=0.0,
                top_p=1
            )

            data = json.loads(res.choices[0].message.content)

            if "questions" in data:
                return data
            else:
                raise ValueError("Missing questions key")

        except Exception as e:
            print(f"⚠️ Attempt {attempt} failed for {os.path.basename(image_path)}: {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                print(f"❌ Failed to extract {os.path.basename(image_path)}")
                return None


def process_folder(folder_path):
    patterns = ["**/*.jpg", "**/*.jpeg", "**/*.png"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(folder_path, p), recursive=True))

    results = []

    for file in files:
        print(f"-> Processing: {os.path.basename(file)}")
        data = extract_content_from_image(file)

        if data:
            data["source"] = os.path.basename(file)
            results.append(data)
        else:
            print(f"⚠️ Skipped {os.path.basename(file)}")

        time.sleep(1.2)

    return results