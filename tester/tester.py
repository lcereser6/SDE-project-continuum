



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
    # Split total_seconds into whole seconds and fractional seconds (milliseconds)
    whole_seconds = int(total_seconds)
    milliseconds = int((total_seconds - whole_seconds) * 1000)  # Convert fractional seconds to milliseconds
    
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
    if milliseconds > 0 and (hours == 0 and minutes == 0):  # Only add milliseconds if there are no hours/minutes
        formatted_time += f"{milliseconds}ms"
    
    return formatted_time
 
@app.route("/api/v1/trigger-test" , methods=["POST"]) 
def trigger_scan():
    dbproxy_url = 'http://dbproxy:5000/api/v1/update-action'
    total_time_str = "N/A"
    status = request.json.get("status")
    action_uid = request.json.get("action_uid")
    if status == "OK":
        start_time = time.time()
        time.sleep(5)
        #generate a random boolean
        status ="ERROR" if bool(random.getrandbits(1)) else "OK"
        
        #write on the dbproxy


        print("TESTING DONE", flush=True)
        print(action_uid, flush=True)
        #get end time
        end_time = time.time()
        total_time = end_time - start_time
        total_time_str = format_time(total_time)
    else:
        status = "N/A"
    requests.post(dbproxy_url, json={"action_uid": action_uid, "status_name": "tester_status", "status": status, "eta_name": "tester_eta", "eta": total_time_str})

    return jsonify({
        "status": status
    })


if __name__ == "__main__":

    time.sleep(15)
    app.run(debug=True, host="0.0.0.0")
    


