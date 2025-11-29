from google import genai
from google.genai import types
from google.oauth2 import service_account

def main():
    # ---------------------------------------------------------------------
    # Load service-account credentials
    # ---------------------------------------------------------------------
    credentials = service_account.Credentials.from_service_account_file(
        "/path/to/service-account.json"
    )

    # ---------------------------------------------------------------------
    # Initialize Gemini client (Vertex AI mode)
    # ---------------------------------------------------------------------
    client = genai.Client(
        vertexai=True,
        http_options=types.HttpOptions(api_version="v1"),
        location="us-central1",   # NOT global
        project="your-gcp-project-id",
        credentials=credentials,
    )

    # ---------------------------------------------------------------------
    # Build cached content
    # ---------------------------------------------------------------------
    use_message = "my body fat is 20%, my bmi is 22, and my body water is 55%"
    CACHE_NAME = "keyword_rag_extraction"

    rag_system_prompt = "You are an expert health and fitness metrics analyzer."

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(use_message)]
        )
    ]

    # ---------------------------------------------------------------------
    # Create cache
    # ---------------------------------------------------------------------
    cached = client.caches.create(
        model="gemini-2.5-flash",
        config=types.CreateCachedContentConfig(
            display_name=CACHE_NAME,
            system_instruction=rag_system_prompt,
            contents=contents,
            ttl="3600s",  # 1-hour TTL
        ),
    )

    print("✅ Cache created:", cached.name)
    print("Token usage for cached content:", cached.usage_metadata.total_token_count)

    # ---------------------------------------------------------------------
    # Use the cache in a model request
    # ---------------------------------------------------------------------
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text("Summarize my health status.")]
            )
        ],
        config=types.GenerateContentConfig(
            cached_content=cached.name
        ),
    )

    print("\n--- Model Response ---")
    print(response.text)

    # Uncomment if you want to clean up
    # client.caches.delete(cached.name)


if __name__ == "__main__":
    main()
