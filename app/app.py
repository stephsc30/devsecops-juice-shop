from flask import Flask, request
import os

app = Flask(__name__)

@app.route("/")
def hello():
    cmd = request.args.get("cmd")
    if cmd:
        os.system(cmd)  # Intentional vulnerability
    return "Hello DevSecOps"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
