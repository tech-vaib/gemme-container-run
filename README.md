
gcloud services enable run.googleapis.com compute.googleapis.com cloudbuild.googleapis.com cloudarmor.googleapis.com

gcloud run services describe gemma-poc --region us-central1 --format='value(status.url)'
gcloud compute security-policies create allowlist-policy \
  --description "Allow only 162.246.216.28 to access Cloud Run"

gcloud compute security-policies rules create 1000 \
  --security-policy allowlist-policy \
  --src-ip-ranges=162.246.216.28 \
  --action=allow \
  --description="Allow access from office IP"

gcloud compute security-policies rules create 2147483647 \
  --security-policy allowlist-policy \
  --action=deny-403 \
  --description="Deny all other IPs"


Build
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/gemma-poc

Deploy:
gcloud run deploy gemma-poc \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/gemma-poc \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 1 \
  --allow-unauthenticated


Get URL:
gcloud run services describe gemma-poc --region us-central1 --format 'value(status.url)'

Test:
curl -X POST -H "Content-Type: application/json" \
  -d '{"prompt": "Explain what Gemma is in simple terms."}' \
  https://YOUR_CLOUD_RUN_URL/predict
