gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:your-service-account@your-project-id.iam.gserviceaccount.com" \
    --role="roles/serviceusage.serviceUsageConsumer"
from google import genai
from google.genai import types
from google.oauth2 import service_account

def main():
    # ---------------------------------------------------------------------
    # Load service-account credentials
    # ---------------------------------------------------------------------
    credentials = service_account.Credentials.from_service_account_file(
        "/path/to/service-account.json"  # <-- Replace with your service account key path
    )

    # ---------------------------------------------------------------------
    # Initialize Gemini client (Vertex AI mode)
    # ---------------------------------------------------------------------
    client = genai.Client(
        vertexai=True,
        project="your-gcp-project-id",  # <-- Replace with your project ID
        location="us-central1",          # MUST be regional
        credentials=credentials
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
            parts=[types.Part(text=use_message)]  # Correct syntax for version 1.52.0
        )
    ]

    # ---------------------------------------------------------------------
    # Create explicit cache
    # ---------------------------------------------------------------------
    cached = client.caches.create(
        model="gemini-2.5-flash",
        config=types.CreateCachedContentConfig(
            display_name=CACHE_NAME,
            system_instruction=rag_system_prompt,
            contents=contents,
            ttl="3600s",  # Cache TTL = 1 hour
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
                parts=[types.Part(text="Summarize my health status.")]
            )
        ],
        config=types.GenerateContentConfig(
            cached_content=cached.name
        ),
    )

    print("\n--- Model Response ---")
    print(response.text)

    # ---------------------------------------------------------------------
    # Optional: delete cache when done
    # ---------------------------------------------------------------------
    # client.caches.delete(cached.name)

if __name__ == "__main__":
    main()
