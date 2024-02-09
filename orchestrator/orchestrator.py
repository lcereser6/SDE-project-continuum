from flask import Flask, redirect, url_for, session, request, jsonify, render_template
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

@app.route("/")
def index():
    return ("Orchestrator is running")

@app.route("/api/v1/info")
def info():
    return jsonify({
        "name": "Orchestrator",
        "status": "running"
    })


if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0")
    