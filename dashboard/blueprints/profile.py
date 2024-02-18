import os
from flask import Blueprint, render_template, session
from flask_login import login_required
import requests
from requests_oauthlib import OAuth2Session

# Ensure the GITHUB_CLIENT_ID environment variable is set
if not os.getenv("GITHUB_CLIENT_ID"):
    raise EnvironmentError("GITHUB_CLIENT_ID environment variable is not set.")

profile_bp = Blueprint('profile', __name__)

@profile_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    """Fetch and display GitHub profile information."""
    github = OAuth2Session(os.getenv("GITHUB_CLIENT_ID"), token=session.get('oauth_token'))
    profile_info = github.get('https://api.github.com/user').json()
    user_id = profile_info.get('id', 'Unknown User ID')
    username = profile_info.get('login', 'Unknown Username')
    # Store username in session for later use
    session['username'] = username
    return render_template('index.html', user_id=user_id, username=username)

@profile_bp.route("/repositories", methods=["GET"])
@login_required
def repositories():
    """Fetch and display user repositories."""
    github = OAuth2Session(os.getenv("GITHUB_CLIENT_ID"), token=session.get('oauth_token'))
    repos_info = github.get('https://api.github.com/user/repos').json()
    return render_template('repositories.html', username=session.get('username'), repos=repos_info)

@profile_bp.route("/repositories/<repo_name>", methods=["GET"])
@login_required
def repo_details(repo_name):
    """Fetch and display details for a specific repository, including custom actions."""
    github = OAuth2Session(os.getenv("GITHUB_CLIENT_ID"), token=session.get('oauth_token'))
    repos_info = github.get(f'https://api.github.com/user/repos').json()
    repo_info = [repo for repo in repos_info if repo['name'] == repo_name]
    repo_info = repo_info[0]

    jwt_token = session.get("jwt_token")
    headers = {'Authorization': f'Bearer {jwt_token}'}
    action_list = requests.get(f'http://dbproxy:5000/api/v1/read-action/{repo_name}', headers=headers).json()
  
    # Process action statuses
    for action in action_list:
        statuses = [action['scanner_status'], action['builder_status'], action['tester_status'], action['deployer_status']]
        if any(status == "ERROR" for status in statuses):
            action['current_status'] = "ERROR"
        elif any(status == "PENDING" for status in statuses): 
            action['current_status'] = "PENDING"
        elif all(status in ("OK", "N/A") for status in statuses):
            action['current_status'] = "OK"
            

    return render_template('repo_details.html', repo_info=repo_info, action_list=action_list)
