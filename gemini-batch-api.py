import requests
import json

API_KEY = "YOUR_VERTEX_AI_API_KEY"

# Gemini 2.5 Pro batch endpoint
URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-2.5-pro:batchGenerateContent"
)

headers = {
    "Content-Type": "application/json"
}

# Inline batch requests
payload = {
    "requests": [
        {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": "Explain batch APIs in one sentence."}]
                }
            ]
        },
        {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": "What is Gemini 2.5 Pro?"}]
                }
            ]
        }
    ]
}

response = requests.post(
    f"{URL}?key={API_KEY}",
    headers=headers,
    data=json.dumps(payload),
    timeout=60,
)

response.raise_for_status()
result = response.json()

# Print responses
for i, r in enumerate(result["responses"]):
    text = r["candidates"][0]["content"]["parts"][0]["text"]
    print(f"Response {i+1}: {text}")
