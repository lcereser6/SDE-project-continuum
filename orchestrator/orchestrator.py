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

@app.route("/api/v1/trigger_build", methods=["POST"])
def trigger_build():
    # Extract the JSON data sent with the POST request
    data = request.get_json()
    
    # For demonstration, let's assume the data contains a 'repo_name'
    repo_name = data.get('repo_name')
    
    if repo_name:
        # Here, you would add the logic to trigger a build based on the repo_name
        # For this example, let's just return a confirmation message
        return jsonify({"message": f"Build triggered for repository: {repo_name}"}), 200
    else:
        return jsonify({"error": "Repository name is missing"}), 400


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
