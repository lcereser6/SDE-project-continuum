import time
from flask import Blueprint, Flask, redirect, session, url_for, request, jsonify, render_template
import os
from flask_session import Session
import uuid
import jwt
from jwt.exceptions import InvalidTokenError
import requests
from requests_oauthlib import OAuth2Session

actions_bp = Blueprint('actions', __name__)
client_id = os.getenv("GITHUB_CLIENT_ID")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")



@actions_bp.route("/")
def index():
    return ("Orchestrator is running")

@actions_bp.route("/api/v1/info")
def info():
    return jsonify({
        "name": "Orchestrator",
        "status": "running"
    })


@actions_bp.route("/api/v1/trigger-action", methods=["POST"])
def trigger_action():
    data = request.get_json()
    
    repo_name = data.get('repo_name')
    auth_token = data.get('oauth_token')
    jwt_token = data.get('jwt_token')
    action_type = data.get('action_type')
    username = validate_token(jwt_token)    

    github = OAuth2Session(client_id, token= auth_token)
    repos_info = github.get('https://api.github.com/user/repos').json()
    repo_info = [repo for repo in repos_info if repo['name'] == repo_name]
    repo_info = repo_info[0] if repo_info else None
    if repo_info:
        # Assume dbproxy service is accessible at this URL, adjust as needed
        # generate unique action_uid

        action_uid = str(uuid.uuid4())
        dbproxy_url = 'http://dbproxy:5000/api/v1/write-action'


        build_info = {
            "action_uid": action_uid,
            "git_user_uid": username,
            "time_action_start": time.time(),
            "git_repo_uid": repo_info.get('id'),
            "git_commit_hash": "None",
            "git_branch_name": repo_info.get('default_branch'),
            "git_repo_name": repo_info.get('name'),
            "current_status": "triggered",
            "builder_status": "pending",
            "tester_status": "pending",
            "deployer_status": "pending",
            "builder_eta": "None",
            "tester_eta": "None",
            "deployer_eta": "None",
            "action_type": action_type,
            "scanner_eta": "None",
            "scanner_status": "pending",
        }
        
        try:
            # Send a POST request to dbproxy to log the build trigger
            response = requests.post(dbproxy_url, json=build_info)
            
            # Check if dbproxy handled our request successfully
            if response.status_code == 200:
                return jsonify({"message": f"Build triggered for repository: {repo_name}. Logged successfully."}), 200
            else:
                # dbproxy responded with an error
                return jsonify({"error": "Failed to log build trigger in dbproxy", "details": response.text}), response.status_code
        except requests.RequestException as e:
            # Handle exceptions that occur during the request to dbproxy
            return jsonify({"error": "Communication with dbproxy failed", "details": str(e)}), 500
    else:
        return jsonify({"error": "Repository name is missing"}), 400

def validate_token(token):
    try:
        # Decode token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload['username']  # Return the username from the payload
    except InvalidTokenError:
        # Handle invalid token (e.g., expired, tampered, etc.)
        return None
