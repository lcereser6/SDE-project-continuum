



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
log_queue_host = os.getenv("LOG_QUEUE_HOST", "rabbitmq")
log_queue_port = os.getenv("LOG_QUEUE_PORT", "5672")
log_queue_name = os.getenv("LOG_QUEUE_NAME", "log-queue")
log_queue = LogQueue(log_queue_host, log_queue_port, log_queue_name)

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

@app.route("/api/v1/trigger-deploy" , methods=["POST"]) 
def trigger_scan():
    total_time_str = "N/A"
    dbproxy_url = 'http://dbproxy:5000/api/v1/update-action'
    action_uid = request.json.get("action_uid")
    status = request.json.get("status")
    image_tag = request.json.get("image_tag")
    if status == "OK":
        start_time = time.time()
        time.sleep(5)
        #write on the dbproxy
        try:
            process = subprocess.Popen(["docker", "run", image_tag], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in io.TextIOWrapper(process.stdout, encoding="utf-8"):  # Ensure correct encoding
                log_queue.send({"action_uid": action_uid,"service":"scanner","time":time.time(), "log": line})
            if process.returncode == 0:
                status = "OK"
            else:
                status = "ERROR"
            
        except subprocess.CalledProcessError as e:
            print(f"Deploy failed: {e}")
            status = "ERROR"      




        print("DEPLOY DONE", flush=True)
        print(action_uid, flush=True)
            #get end time
        end_time = time.time()
        total_time = end_time - start_time
        total_time_str = format_time(total_time)
    else:
        status = "N/A"
    requests.post(dbproxy_url, json={"action_uid": action_uid, "status_name": "deployer_status", "status": status, "eta_name": "deployer_eta", "eta": total_time_str})

    return jsonify({
        "status": status
    })


if __name__ == "__main__":

    time.sleep(15)
    log_queue.connect()
    app.run(debug=True, host="0.0.0.0")
    


