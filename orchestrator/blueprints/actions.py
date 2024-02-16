import threading
import time
from flask import Blueprint, current_app , Flask, redirect, session, url_for, request, jsonify, render_template
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

def validate_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload['username']  # Return the username from the payload
    except InvalidTokenError:
        return None

def log_action_to_db(app, action_info):
    with app.app_context():
        dbproxy_url = 'http://dbproxy:5000/api/v1/write-action'
        try:
            response = requests.post(dbproxy_url, json=action_info)
            if response.status_code == 200:
                print("Action triggered for repository: {}. Logged successfully.".format(action_info['git_repo_name']))
            else:
                print("Failed to log build trigger in dbproxy: {}".format(response.text))
        except requests.RequestException as e:
            print("Communication with dbproxy failed: {}".format(str(e)))


def start_action(action_type, resp, repo_name, auth_token, jwt_token,action_uid, username):
    print("Starting action", action_type, flush=True)
    print("action_uid : ", action_uid, flush=True)



    url = f'http://{action_type}er:5000/api/v1/trigger-{action_type}'
    if action_type == "scan":
        url = f'http://{action_type}ner:5000/api/v1/trigger-{action_type}'
    data = {
        "repo_name": repo_name,
        "oauth_token": auth_token,
        "jwt_token": jwt_token,
        "action_uid": action_uid,
        "username": username,
        "status": resp
    }
    response = requests.post(url, json=data)
    status = response.json().get("status")
    return status


def start_process(repo_name, auth_token, jwt_token, action_uid, username):
    resp = start_action("scan" , "OK", repo_name, auth_token, jwt_token, action_uid, username)
    print("Scan response", resp, flush=True)
    resp = start_action("build" , resp,repo_name, auth_token, jwt_token, action_uid, username)
    print("Build response", resp, flush=True)
    resp = start_action("test" , resp,repo_name, auth_token, jwt_token, action_uid, username)
    print("Test response", resp, flush=True)
    resp = start_action("deploy" , resp,repo_name, auth_token, jwt_token, action_uid, username)
    print("Deploy response", resp, flush=True)

def trigger_build_action(repo_name, auth_token, jwt_token, action_uid, username, action_type):
    print("Triggering build action", flush=True)
    if action_type == "full":
        print("Full process triggered")
        start_process(repo_name, auth_token, jwt_token, action_uid, username)
    elif action_type == "build":
        print("Build triggered")
        start_action("build","OK",repo_name, auth_token, jwt_token, action_uid, username)
    elif action_type == "test":
        print("Test triggered")
        start_action("test","OK",repo_name, auth_token, jwt_token, action_uid, username)
    elif action_type == "deploy":
        print("Deploy triggered")
        start_action("deploy","OK",repo_name, auth_token, jwt_token, action_uid, username)
    elif action_type == "scan":
        print("Scan triggered")
        resp = start_action("scan","OK", repo_name, auth_token, jwt_token, action_uid, username)


def trigger_async_action(action_type, repo_name, auth_token, jwt_token, username):
    
    action_uid = str(uuid.uuid4())  # Generate unique action UID
    github = OAuth2Session(client_id, token= auth_token)
    repos_info = github.get('https://api.github.com/user/repos').json()
    repo_info = [repo for repo in repos_info if repo['name'] == repo_name]
    repo_info = repo_info[0] if repo_info else None
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

    if action_type in ["full","build", "test", "deploy", "scan"]:
        
        threading.Thread(target=trigger_build_action, args=(repo_name, auth_token, jwt_token, action_uid, username, action_type)).start()
    else:
        return {"error": "Invalid action type"}, 400
    
    app = current_app._get_current_object()
    threading.Thread(target=log_action_to_db, args=(app, action_info)).start()
    
    return {"message": f"{action_type.capitalize()} action triggered for repository: {repo_name}."}, 202






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
    if not username:
        return jsonify({"error": "Invalid or expired token"}), 401

    # Trigger the action asynchronously
    message, status_code = trigger_async_action(action_type, repo_name, auth_token, jwt_token, username)
    return jsonify(message), status_code