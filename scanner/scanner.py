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

app = Flask(__name__)

# Load environment variables for connecting to the log queue
log_queue_host = os.getenv("LOG_QUEUE_HOST", "rabbitmq")
log_queue_port = os.getenv("LOG_QUEUE_PORT", "5672")
log_queue_name = os.getenv("LOG_QUEUE_NAME", "log-queue")

# Initialize the LogQueue with environment variables
log_queue = LogQueue(log_queue_host, log_queue_port, log_queue_name)

def format_time(total_seconds):
    """
    Converts total seconds to a formatted string (hours, minutes, seconds, milliseconds).
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

@app.route("/api/v1/trigger-scan", methods=["POST"]) 
def trigger_scan():
    """
    Endpoint to trigger a vulnerability scan on a specified image tag.
    Updates the scan status and ETA through a POST request to dbproxy.
    """
    total_time_str = "N/A"
    status = request.json.get("status")
    dbproxy_url = 'http://dbproxy:5000/api/v1/update-action'
    action_uid = request.json.get("action_uid")
    image_tag = request.json.get("image_tag")

    if status == "OK":
        start_time = time.time()

        try:
            process = subprocess.Popen(["grype", image_tag], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in io.TextIOWrapper(process.stdout, encoding="utf-8"):
                log_queue.send({"action_uid": action_uid, "service": "scanner", "time": time.time(), "log": line})
            process.wait()
            if process.returncode == 0:
                status = "OK"
            else:
                status = "ERROR"
            
            print("Image scanned successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error scanning image: {e}")
            status = "ERROR"
        except Exception as e:
            print(f"Unexpected error during scanning: {e}")
            status = "ERROR"
        
        # Calculate total time taken for scanning
        end_time = time.time()
        total_time = end_time - start_time
        total_time_str = format_time(total_time)
    else:
        status = "N/A"

    # Attempt to update the dbproxy with the scan results
    try:
        requests.post(dbproxy_url, json={"action_uid": action_uid, "status_name": "scanner_status", "status": status, "eta_name": "scanner_eta", "eta": total_time_str})
    except requests.RequestException as e:
        print(f"Failed to update dbproxy: {e}")

    return jsonify({
        "status": status,
        "image_tag": image_tag
    })

if __name__ == "__main__":
    # Delay to ensure dependent services are up
    time.sleep(15)
    try:
        log_queue.connect()
    except Exception as e:
        print(f"Failed to connect to log queue: {e}")
    app.run(debug=True, host="0.0.0.0")
