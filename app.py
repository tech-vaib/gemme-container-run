from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

app = Flask(__name__)
model_name = "google/gemma-2b"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")

@app.route("/predict", methods=["POST"])
def predict():
    text = request.json.get("prompt")
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=100)
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return jsonify({"response": result})

@app.route("/")
def health():
    return "Gemma model running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
