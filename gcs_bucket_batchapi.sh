#!/bin/bash

# -------------------------------
# CONFIGURATION - CHANGE THESE
# -------------------------------
PROJECT_ID="your-gcp-project-id"
BUCKET_NAME="my-vertex-batch-bucket-$(date +%s)"  # unique name
REGION="us-central1"   # use your desired region OR multi-region like "US"
VERTEX_SA_EMAIL="your-vertex-service-account@your-project-id.iam.gserviceaccount.com"

# -------------------------------
# 1️⃣ Set project
# -------------------------------
gcloud config set project $PROJECT_ID

# -------------------------------
# 2️⃣ Create the bucket
# -------------------------------
echo "Creating bucket $BUCKET_NAME in region $REGION..."
gsutil mb -l $REGION gs://$BUCKET_NAME/

# -------------------------------
# 3️⃣ Grant Vertex AI service account access
# -------------------------------
echo "Granting Storage Object Admin role to Vertex AI service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$VERTEX_SA_EMAIL" \
    --role="roles/storage.objectAdmin"

echo "Done!"
echo "Bucket created: gs://$BUCKET_NAME"
echo "Vertex AI SA granted access: $VERTEX_SA_EMAIL"
