gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Enable required APIs
gcloud services enable run.googleapis.com \
    artifactregistry.googleapis.com \
    compute.googleapis.com


  3. Request GPU quota (if you haven’t)
# (You only need to do this once per project per region)
# Go to: https://console.cloud.google.com/iam-admin/quotas
# Search "L4" under Cloud Run API and request 1 GPU in your target region

gcloud run deploy gemma-small \
  --image us-docker.pkg.dev/cloudrun/container/gemma/gemma3-1b \
  --region us-central1 \
  --gpu 1 \
  --gpu-type nvidia-l4 \
  --cpu 8 \
  --memory 32Gi \
  --concurrency 4 \
  --set-env-vars OLLAMA_NUM_PARALLEL=4 \
  --max-instances 1 \
  --no-allow-unauthenticated \
  --no-cpu-throttling \
  --no-gpu-zonal-redundancy \
  --timeout=600


  3. Test Your Deployment Securely

You can’t call it directly (it’s protected).
Use the Cloud Run proxy for local testing:

# Start a proxy (keeps running)
gcloud run services proxy gemma-small --port=9090

In another terminal tab, test it with curl:
curl http://localhost:9090/api/generate -d '{
  "model": "gemma3:1b",
  "prompt": "Explain why the sky is blue in simple terms."
}'

4. cleanup
5. gcloud run services delete gemma-small --region us-central1
6. Keep Costs Near Zero
7. gcloud run services update gemma-small \
  --min-instances 0 \
  --region us-central1
