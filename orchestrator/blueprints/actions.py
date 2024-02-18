import threading
import time
from flask import Blueprint, current_app, Flask, jsonify, request
import os
import uuid
import jwt
from jwt.exceptions import InvalidTokenError
import requests
from requests_oauthlib import OAuth2Session

# Blueprint setup for Flask application
actions_bp = Blueprint('actions', __name__)

# Environment variables for configuration
client_id = os.getenv("GITHUB_CLIENT_ID")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

def validate_token(token):
    """
    Validates a JWT token and returns the username if valid.

    :param token: JWT token to be validated.
    :return: Username if token is valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload['username']
    except InvalidTokenError:
        return None

def log_action_to_db(app, action_info):
    """
    Logs action information to a database through a proxy service.

    :param app: Flask application context.
    :param action_info: Information about the action to log.
    """
    dbproxy_url = 'http://dbproxy:5000/api/v1/write-action'
    try:
        response = requests.post(dbproxy_url, json=action_info)
        if response.status_code == 200:
            print(f"Action triggered for repository: {action_info['git_repo_name']}. Logged successfully.")
        else:
            print(f"Failed to log build trigger in dbproxy: {response.text}")
    except requests.RequestException as e:
        print(f"Communication with dbproxy failed: {str(e)}")

def start_action(action_type, resp, repo_name, auth_token, jwt_token, action_uid, username, git_repo_url):
    """
    Starts a specified action for a repository.

    :param action_type: The type of action to start (build, scan, deploy, test).
    :param resp: The response status from the previous action.
    :param repo_name: The name of the repository.
    :param auth_token: OAuth token for authentication.
    :param jwt_token: JWT token for user identification.
    :param action_uid: Unique identifier for the action.
    :param username: Username of the user initiating the action.
    :return: Status of the action triggered.
    """
    print(f"Starting action {action_type}", flush=True)
    print(f"action_uid : {action_uid}", flush=True)

    # Adjust URL based on action type
    url = f'http://{action_type}er:5000/api/v1/trigger-{action_type}' if action_type != "scan" else f'http://scanner:5000/api/v1/trigger-scan'
    
    data = {
        "repo_name": repo_name,
        "oauth_token": auth_token,
        "jwt_token": jwt_token,
        "action_uid": action_uid,
        "username": username,
        "status": resp.get("status"),
        "git_repo_url": git_repo_url,
        "image_tag": resp.get("image_tag")
    }
    
    response = requests.post(url, json=data)
    return response.json()

def start_process(repo_name, auth_token, jwt_token, action_uid, username, git_repo_url):
    """
    Starts the full process for a repository action (build, scan, deploy, test).

    :param repo_name: The name of the repository.
    :param auth_token: OAuth token for authentication.
    :param jwt_token: JWT token for user identification.
    :param action_uid: Unique identifier for the action.
    :param username: Username of the user initiating the action.
    """
    actions = ["build", "scan", "deploy", "test"]

    for action in actions:
        resp = start_action(action, resp if action != "build" else {"status" : "OK"}, repo_name, auth_token, jwt_token, action_uid, username, git_repo_url)
        print(f"{action.capitalize()} response: {resp}", flush=True)

def trigger_build_action(repo_name, auth_token, jwt_token, action_uid, username, action_type, git_repo_url):
    """
    Triggers a build action for a repository based on the action type.

    :param repo_name: The name of the repository.
    :param auth_token: OAuth token for authentication.
    :param jwt_token: JWT token for user identification.
    :param action_uid: Unique identifier for the action.
    :param username: Username of the user initiating the action.
    :param action_type: The type of action to start (full, build, test, deploy, scan).
    """
    print("Triggering build action", flush=True)
    if action_type == "full":
        print("Full process triggered")
        start_process(repo_name, auth_token, jwt_token, action_uid, username, git_repo_url)
    else:
        print(f"{action_type.capitalize()} triggered")
        start_action(action_type, {"status" : "OK", "image_tag":f"{repo_name}_image:latest".lower()}, repo_name, auth_token, jwt_token, action_uid, username, git_repo_url)

def trigger_async_action(action_type, repo_name, auth_token, jwt_token, username):
    """
    Triggers an asynchronous action for a repository.

    :param action_type: The type of action to start (full, build, test, deploy, scan).
    :param repo_name: The name of the repository.
    :param auth_token: OAuth token for authentication.
    :param jwt_token: JWT token for user identification.
    :param username: Username of the user initiating the action.
    :return: A message and status code indicating the result of the action trigger.
    """
    action_uid = str(uuid.uuid4())  # Generate unique action UID
    github = OAuth2Session(client_id, token=auth_token)
    repos_info = github.get('https://api.github.com/user/repos').json()
    repo_info = next((repo for repo in repos_info if repo['name'] == repo_name), None)
    git_repo_url = repo_info.get('clone_url') if repo_info else None
    if not repo_info:
        return {"error": "Repository not found"}, 404

    print(action_type, flush=True)
    action_info = {
        "action_uid": action_uid,
        "git_user_uid": username,
        "time_action_start": time.time(),
        "git_repo_uid": repo_info.get('id'),
        "git_commit_hash": "None",
        "git_branch_name": repo_info.get('default_branch'),
        "git_repo_name": repo_info.get('name'),
        "current_status": "triggered",
        # Statuses and ETAs are set to "Pending" or "N/A" based on action type
        "builder_status": "Pending" if action_type in ["full", "build"] else "N/A",
        "tester_status": "Pending" if action_type in ["full", "test"] else "N/A",
        "deployer_status": "Pending" if action_type in ["full", "deploy"] else "N/A",
        "builder_eta": "Pending" if action_type in ["full", "build"] else "N/A",
        "tester_eta": "Pending" if action_type in ["full", "test"] else "N/A",
        "deployer_eta": "Pending" if action_type in ["full", "deploy"] else "N/A",
        "action_type": action_type,
        "scanner_eta": "Pending" if action_type in ["full", "scan"] else "N/A",
        "scanner_status": "Pending" if action_type in ["full", "scan"] else "N/A"
    }
    print(f"Triggering {action_type} action for repository: {repo_name} by user: {username}", flush=True)

    if action_type in ["full", "build", "test", "deploy", "scan"]:
        threading.Thread(target=trigger_build_action, args=(repo_name, auth_token, jwt_token, action_uid, username, action_type, git_repo_url)).start()
    else:
        return {"error": "Invalid action type"}, 400

    app = current_app._get_current_object()
    threading.Thread(target=log_action_to_db, args=(app, action_info)).start()
    
    return {"message": f"{action_type.capitalize()} action triggered for repository: {repo_name}."}, 202

@actions_bp.route("/")
def index():
    """Endpoint to check if the orchestrator is running."""
    return "Orchestrator is running", 200

@actions_bp.route("/api/v1/info")
def info():
    """Provides basic information about the orchestrator."""
    return jsonify({
        "name": "Orchestrator",
        "status": "running"
    }), 200

@actions_bp.route("/api/v1/trigger-action", methods=["POST"])
def trigger_action():
    """
    Endpoint to trigger an action for a repository.

    Expects a JSON payload with repository name, OAuth token, JWT token, and action type.
    """
    data = request.get_json()
    
    repo_name = data.get('repo_name')
    auth_token = data.get('oauth_token')
    jwt_token = data.get('jwt_token')
    action_type = data.get('action_type')

    username = validate_token(jwt_token)    
    if not username:
        return jsonify({"error": "Invalid or expired token"}), 401

    # Trigger the action asynchronously
    message, status_code = trigger_async_action(action_type, repo_name, auth_token, jwt_token, username)
    return jsonify(message), status_code
