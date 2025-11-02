Enable Required APIs

gcloud services enable \
  aiplatform.googleapis.com \
  servicenetworking.googleapis.com \
  networkconnectivity.googleapis.com \
  networkservices.googleapis.com \
  compute.googleapis.com

Create or Use an Existing VPC
gcloud compute networks create gemini-vpc --subnet-mode=auto

Create a Private Service Connect Endpoint for Vertex AI
This allows your VM to access the Vertex AI Gemini APIs privately.
gcloud compute forwarding-rules create vertex-ai-psc-endpoint \
  --region=us-central1 \
  --network=gemini-vpc \
  --target-google-api-apis \
  --address-region=us-central1 \
  --purpose=PRIVATE_SERVICE_CONNECT \
  --ports=443
This creates a private IP endpoint in your VPC that routes to Google APIs, including Vertex AI.

Enable Private Google Access
This is needed for your VM subnet to reach Google APIs via private IPs.
gcloud compute networks subnets update default \
  --region=us-central1 \
  --enable-private-ip-google-access

Create a VM in That VPC
gcloud compute instances create gemini-vm \
  --zone=us-central1-a \
  --network=gemini-vpc \
  --subnet=default \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --scopes=https://www.googleapis.com/auth/cloud-platform

Test from Your VM (Python Code)
gcloud compute ssh gemini-vm --zone=us-central1-a

sudo apt update && sudo apt install -y python3-pip
pip install google-generativeai requests

import google.generativeai as genai
import time

# Replace with your API key
API_KEY = "YOUR_API_KEY"
genai.configure(api_key=API_KEY)

# Choose Gemini model
model = genai.GenerativeModel("gemini-1.5-flash")

prompt = "Explain how Private Service Connect improves latency and security in GCP."

start = time.time()
response = model.generate_content(prompt)
end = time.time()

print("Response:", response.text)
print(f"Latency: {end - start:.2f} seconds")

Verify It’s Using PSC
You can check VPC Flow Logs or traceroute to confirm your traffic stays within Google’s private network:
sudo apt install traceroute
traceroute www.googleapis.com
You’ll see private IPs like 199.36.153.8, which belong to Google’s PSC for APIs — meaning your traffic never left GCP’s internal backbone.

######################################################################################################################################################
## with cloud run
gcloud services enable run.googleapis.com \
    servicenetworking.googleapis.com \
    compute.googleapis.com \
    networkservices.googleapis.com \
    networkconnectivity.googleapis.com

Deploy your Cloud Run service (private)
gcloud run deploy gemma-small \
  --image us-docker.pkg.dev/cloudrun/container/gemma/gemma3-1b \
  --region us-central1 \
  --no-allow-unauthenticated \
  --gpu 1 --gpu-type nvidia-l4 \
  --cpu 8 --memory 32Gi --max-instances 1
Create a VPC network (if not existing)
gcloud compute networks create gemma-net --subnet-mode=auto

Create a Private Service Connect endpoint
This creates a private IP endpoint in your VPC that routes to the Cloud Run service.
gcloud compute forwarding-rules create gemma-psc-endpoint \
  --network gemma-net \
  --region us-central1 \
  --address-region us-central1 \
  --target-service-attachment="projects/PROJECT_NUMBER/regions/us-central1/serviceAttachments/run" \
  --ports=443
gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)'

Create a VM in that VPC
gcloud compute instances create gemma-vm \
  --zone=us-central1-a \
  --network=gemma-net \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --service-account=PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --scopes=cloud-platform
  
SSH into your VM:
gcloud compute ssh gemma-vm --zone=us-central1-a
Then, test the Cloud Run service via the PSC endpoint:
curl -v https://gemma-small-xxxxxx-uc.a.run.app --connect-to gemma-small-xxxxxx-uc.a.run.app:443:PRIVATE_IP_OF_PSC_ENDPOINT:443

You can find the private IP of the PSC endpoint using:
gcloud compute forwarding-rules describe gemma-psc-endpoint --region=us-central1 --format='value(IPAddress)'
If everything is set up correctly, you’ll get a valid Cloud Run response with private routing only.

# IAM still applies — you’ll still need to attach the right service account with roles/run.invoker.

You can measure latency directly with curl:
time curl -o /dev/null -s -w "Connect: %{time_connect}s\nTTFB: %{time_starttransfer}s\nTotal: %{time_total}s\n" \
  https://gemma-small-xxxxxx-uc.a.run.app \
  --connect-to gemma-small-xxxxxx-uc.a.run.app:443:PRIVATE_IP:443


########
## vm access from specific ip
Create a firewall rule to allow SSH only from that IP
gcloud compute firewall-rules create allow-ssh-from-trusted-ip \
  --network=gemini-vpc \
  --allow=tcp:22 \
  --source-ranges=203.0.113.45/32 \
  --target-tags=ssh-access

Remove the default open SSH rule
gcloud compute firewall-rules delete default-allow-ssh

# Tag your VM to match the new rule
gcloud compute instances create gemini-vm \
  --zone=us-central1-a \
  --network=gemini-vpc \
  --subnet=default \
  --tags=ssh-access \
  --image-family=debian-12 \
  --image-project=debian-cloud

If you already created the VM:
gcloud compute instances add-tags gemini-vm \
  --zone=us-central1-a \
  --tags=ssh-access

Verify the Firewall Rule
gcloud compute firewall-rules list --filter="name=allow-ssh-from-trusted-ip"
