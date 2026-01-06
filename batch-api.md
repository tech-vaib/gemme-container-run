curl -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:batchGenerateContent?key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "requests": [
      {
        "contents": [
          {
            "role": "user",
            "parts": [{"text": "Say hello"}]
          }
        ]
      }
    ]
  }'
