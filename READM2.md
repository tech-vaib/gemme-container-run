Create a Docker repository in Artifact Registry:
gcloud artifacts repositories create gemma-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Gemma POC Docker images"

Configure Docker to authenticate with Artifact Registry:
gcloud auth configure-docker us-central1-docker.pkg.dev

Build and tag the Docker image:
docker build -t us-central1-docker.pkg.dev/<PROJECT_ID>/gemma-repo/gemma-poc:latest .

docker push us-central1-docker.pkg.dev/<PROJECT_ID>/gemma-repo/gemma-poc:latest

deploy:
gcloud run deploy gemma-poc \
  --image us-central1-docker.pkg.dev/<PROJECT_ID>/gemma-repo/gemma-poc:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --port 8080

Test:
curl -X POST -H "Content-Type: application/json" \
  -d '{"prompt": "Write a haiku about AI."}' \
  https://gemma-poc-xyz123-uc.a.run.app/predict
