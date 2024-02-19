from datetime import timedelta
import io
import subprocess
import time
from logQueue import LogQueue  # Assuming this is a custom module for handling log queue operations.
from flask import Flask, redirect, url_for, session, request, jsonify, render_template
import os
from jwt.exceptions import InvalidTokenError
import requests

app = Flask(__name__)

# Environment variables for the log queue configuration.
log_queue_host = os.getenv("LOG_QUEUE_HOST", "rabbitmq")
log_queue_port = os.getenv("LOG_QUEUE_PORT", "5672")
log_queue_name = os.getenv("LOG_QUEUE_NAME", "log-queue")
log_queue = LogQueue(log_queue_host, log_queue_port, log_queue_name)

def clone_repo(github_token, repo_url, clone_path):
    """
    Clones a GitHub repository using an OAuth token for authentication.
    
    Args:
    - github_token (str): GitHub OAuth token.
    - repo_url (str): The HTTPS URL of the GitHub repository.
    - clone_path (str): Local path to clone the repository into.
    """
    # Authenticate the repo URL with the provided GitHub token.
    auth_url = repo_url.replace("https://", f"https://{github_token}@")
    
    # Attempt to clone the repository and handle potential errors.
    try:
        subprocess.run(["git", "clone", auth_url, clone_path], check=True)
        print(f"Repository cloned successfully into {clone_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e}")

def format_time(total_seconds):
    """
    Formats a time duration given in seconds to a more readable format.
    
    Args:
    - total_seconds (float): Total time duration in seconds.
    
    Returns:
    - formatted_time (str): Formatted time string.
    """
    whole_seconds = int(total_seconds)
    milliseconds = int((total_seconds - whole_seconds) * 1000)
    
    hours = whole_seconds // 3600
    minutes = (whole_seconds % 3600) // 60
    seconds = whole_seconds % 60
    
    formatted_time = ""
    if hours > 0:
        formatted_time += f"{hours}h"
    if minutes > 0:
        formatted_time += f"{minutes}m"
    if seconds > 0 or (hours == 0 and minutes == 0):
        formatted_time += f"{seconds}s"
    if milliseconds > 0 and (hours == 0 and minutes == 0):
        formatted_time += f"{milliseconds}ms"
    
    return formatted_time

@app.route("/api/v1/trigger-build", methods=["POST"])
def trigger_scan():
    """
    Endpoint to trigger a build process, including repository cloning and Docker image creation.
    """
    dbproxy_url = 'http://dbproxy:5000/api/v1/update-action'
    total_time_str = "N/A"
    status = request.json.get("status")
    action_uid = request.json.get("action_uid")
    repo_url = request.json.get("git_repo_url")
    repo_name = request.json.get("repo_name")
    image_tag = f"{repo_name}_image:latest".lower()
    
    if status == "OK":
        start_time = time.time()
        
        clone_path = f"/tmp/{action_uid}"
        clone_repo(request.json.get("oauth_token")['access_token'], repo_url, clone_path)
        
        # Attempt to build Docker image from the cloned repository.
        try:
            process = subprocess.Popen(["docker", "build", "-t", image_tag, clone_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in io.TextIOWrapper(process.stdout, encoding="utf-8"):
                log_queue.send({"action_uid": action_uid, "service": "builder", "time": time.time(), "log": line})
            process.wait()
            status = "OK" if process.returncode == 0 else "ERROR"
        except subprocess.CalledProcessError as e:
            print(f"Build failed: {e}")
            status = "ERROR"
        
        # Clean up the cloned repository to free up space.
        try:
            subprocess.run(["rm", "-rf", clone_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error cleaning up: {e}")

        end_time = time.time()
        total_time = end_time - start_time
        total_time_str = format_time(total_time)
    else:
        status = "N/A"
    
    # Report the build status and time taken to a database proxy service.
    try:
        requests.post(dbproxy_url, json={"action_uid": action_uid, "status_name": "builder_status", "status": status, "eta_name": "builder_eta", "eta": total_time_str})
    except requests.exceptions.RequestException as e:
        print(f"Failed to report to dbproxy: {e}")

    return jsonify({
        "status": status,
        "image_tag": image_tag
    })


if __name__ == "__main__":
    # Delay to ensure dependent services are up.
    time.sleep(15)
    log_queue.connect()
    app.run(debug=True, host="0.0.0.0")
