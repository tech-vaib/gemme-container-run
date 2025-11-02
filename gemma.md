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


########################################################################################################################################################################

### Find your Cloud Run URL
gcloud run services describe gemma-small \
  --region us-central1 \
  --format='value(status.url)'

Run this command from your local terminal or Cloud Shell:
# Replace VM_NAME and ZONE with your VM details
gcloud compute instances describe VM_NAME --zone=ZONE \
  --format='value(serviceAccounts.email)'
  
### Give Your VM Permission to Call the Service
# Replace with your VM's service account email
VM_SA="my-vm@my-project.iam.gserviceaccount.com"
REGION="us-central1"
SERVICE_NAME="gemma-small"

gcloud run services add-iam-policy-binding $SERVICE_NAME \
  --region=$REGION \
  --member="serviceAccount:$VM_SA" \
  --role="roles/run.invoker"

### Call Cloud Run Securely from Inside the VM
# Replace with your Cloud Run URL
CLOUD_RUN_URL="https://gemma-small-xxxxxx-uc.a.run.app"

# Get an identity token for the Cloud Run audience
TOKEN=$(curl -s -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=$CLOUD_RUN_URL")

# Call the Cloud Run service
curl -X POST "$CLOUD_RUN_URL/api/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:1b",
    "prompt": "Write a haiku about clouds."
  }'

## or program


import requests
import google.auth.transport.requests
import google.oauth2.id_token

url = "https://gemma-small-xxxxxx-uc.a.run.app/api/generate"
audience = url  # audience must match your service URL

creds_request = google.auth.transport.requests.Request()
token = google.oauth2.id_token.fetch_id_token(creds_request, audience)

response = requests.post(
    url,
    headers={"Authorization": f"Bearer {token}"},
    json={"model": "gemma3:1b", "prompt": "Hello Gemma!"}
)
print(response.text)

########################################################################################################################################################################
#### only from specific ip

# 1️⃣ Create a Cloud Armor policy
gcloud compute security-policies create allow-specific-ip \
  --description="Allow only my office/home IPs"

# 2️⃣ Add a rule to allow your IP
gcloud compute security-policies rules create 1000 \
  --security-policy=allow-specific-ip \
  --expression="inIpRange(origin.ip, '203.0.113.42/32')" \
  --action=allow

# 3️⃣ Add a default deny rule
gcloud compute security-policies rules create 2147483647 \
  --security-policy=allow-specific-ip \
  --action=deny-403

# 4️⃣ Deploy your Cloud Run service (private)
gcloud run deploy gemma-small \
  --image us-docker.pkg.dev/cloudrun/container/gemma/gemma3-1b \
  --no-allow-unauthenticated \
  --region us-central1 \
  ... (other flags)

# 5️⃣ Expose Cloud Run via a HTTPS Load Balancer (Serverless NEG)
# In the console: Cloud Run → “Create External HTTPS Load Balancer” → attach security policy
