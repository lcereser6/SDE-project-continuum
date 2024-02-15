from flask import Flask, redirect, url_for, session, request, jsonify, render_template
import os
import redis

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")
app.config['SESSION_TYPE'] = os.getenv("SESSION_TYPE")
app.config['SESSION_PERMANENT'] = os.getenv("SESSION_PERMANENT")
app.config['SESSION_USE_SIGNER'] = os.getenv("SESSION_USE_SIGNER")
app.config['SESSION_REDIS'] = redis.from_url('redis://redis:6379')

@app.route("/")
def index():
    return ("Deployer is running")

@app.route("/api/v1/info")
def info():
    return jsonify({
        "name": "Deployer",
        "status": "running"
    })


if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0")
    