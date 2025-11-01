from flask import Flask, request, jsonify, abort
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

app = Flask(__name__)
ALLOWED_IPS = ["162.246.216.28"]

@app.before_request
def limit_remote_addr():
    if request.remote_addr not in ALLOWED_IPS:
        abort(403)

MODEL_NAME = "google/gemma-2b"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, device_map="auto")

@app.route("/predict", methods=["POST"])
def predict():
    text = request.json.get("prompt", "")
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=50)
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return jsonify({"response": result})

@app.route("/")
def home():
    return "✅ Gemma Cloud Run POC - IP restricted"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
