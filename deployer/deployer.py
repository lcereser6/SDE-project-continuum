from datetime import timedelta
import io
import subprocess
import time
import jwt
import redis
from flask import Flask, redirect, url_for, session, request, jsonify, render_template
import os
from jwt.exceptions import InvalidTokenError
import requests
from logQueue import LogQueue

# Initialize Flask app
app = Flask(__name__)

# Environment variables for log queue configuration
log_queue_host = os.getenv("LOG_QUEUE_HOST", "rabbitmq")
log_queue_port = os.getenv("LOG_QUEUE_PORT", "5672")
log_queue_name = os.getenv("LOG_QUEUE_NAME", "log-queue")

# Initialize log queue with environment configuration
log_queue = LogQueue(log_queue_host, log_queue_port, log_queue_name)

def format_time(total_seconds):
    """
    Formats a time duration from seconds to a human-readable string.

    Args:
        total_seconds (float): The total duration in seconds.

    Returns:
        str: The formatted duration as a string.
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

@app.route("/api/v1/trigger-deploy", methods=["POST"])
def trigger_scan():
    """
    Endpoint to trigger a deployment based on the status received in the request.
    Logs the deployment process and updates deployment status in a database proxy.

    Returns:
        json: The status of the deployment process.
    """
    dbproxy_url = 'http://dbproxy:5000/api/v1/update-action'
    action_uid = request.json.get("action_uid")
    status = request.json.get("status")
    image_tag = request.json.get("image_tag")
    total_time_str = "N/A"

    if status == "OK":
        start_time = time.time()
        time.sleep(5)  # Simulate deployment preparation time
        
        try:
            process = subprocess.Popen(["docker", "run", image_tag], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in io.TextIOWrapper(process.stdout, encoding="utf-8"):
                log_queue.send({"action_uid": action_uid, "service": "deployer", "time": time.time(), "log": line})
                status = "OK"
        except subprocess.CalledProcessError as e:
            print(f"Deploy failed: {e}")
            status = "ERROR"

        print("DEPLOY DONE", flush=True)
        end_time = time.time()
        total_time = end_time - start_time
        total_time_str = format_time(total_time)
    else:
        status = "N/A"

    try:
        # Attempt to send deployment status to the database proxy
        requests.post(dbproxy_url, json={"action_uid": action_uid, "status_name": "deployer_status", "status": status, "eta_name": "deployer_eta", "eta": total_time_str})
    except requests.exceptions.RequestException as e:
        print(f"Failed to update deployment status: {e}")

    return jsonify({"status": status})

if __name__ == "__main__":
    time.sleep(15)  # Wait for dependent services to be up
    log_queue.connect()
    app.run(debug=True, host="0.0.0.0")
