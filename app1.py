from flask import Flask, request, abort

ALLOWED_IPS = ["162.246.216.28"]
app = Flask(__name__)

@app.before_request
def limit_remote_addr():
    if request.remote_addr not in ALLOWED_IPS:
        abort(403)

@app.route("/")
def index():
    return "Access granted only from approved IP"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
