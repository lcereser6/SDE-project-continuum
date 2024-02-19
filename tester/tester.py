from datetime import timedelta
import random
import time
import jwt
import redis
from flask import Flask, redirect, url_for, session, request, jsonify, render_template
import os
from jwt.exceptions import InvalidTokenError
import requests

app = Flask(__name__)

def format_time(total_seconds):
    """
    Converts total seconds to a formatted string with hours, minutes, seconds, and milliseconds.
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

@app.route("/api/v1/trigger-test", methods=["POST"])
def trigger_scan():
    """
    Endpoint to trigger a test scan, simulate processing time, and update a remote database with the result.
    """
    dbproxy_url = 'http://dbproxy:5000/api/v1/update-action'
    total_time_str = "N/A"
    try:
        status = request.json.get("status")
        action_uid = request.json.get("action_uid")
    except Exception as e:
        # Error handling for malformed request data
        return jsonify({"error": "Bad request data"}), 400

    if status == "OK":
        start_time = time.time()
        time.sleep(5)  # Simulate processing delay

        # Randomly determine the new status
        status = "ERROR" if bool(random.getrandbits(1)) else "OK"
        
        end_time = time.time()
        total_time = end_time - start_time
        total_time_str = format_time(total_time)
    else:
        status = "N/A"
    
    # Attempt to post update to dbproxy and handle potential network errors
    try:
        response = requests.post(dbproxy_url, json={"action_uid": action_uid, "status_name": "tester_status", "status": status, "eta_name": "tester_eta", "eta": total_time_str})
        response.raise_for_status()  # Raises an error for 4XX or 5XX responses
    except requests.RequestException as e:
        print(f"Failed to update dbproxy: {e}", flush=True)
        # Return an error response indicating the failure to communicate with the dbproxy
        return jsonify({"error": "Failed to communicate with dbproxy"}), 500

    return jsonify({"status": status})

if __name__ == "__main__":
    time.sleep(15)  # Delay to ensure dependent services are up
    app.run(debug=True, host="0.0.0.0")
