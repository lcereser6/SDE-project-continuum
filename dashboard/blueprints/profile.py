



import os
from flask import Blueprint, render_template, session
from flask_login import login_required
import requests
from requests_oauthlib import OAuth2Session



profile_bp = Blueprint('profile', __name__)
client_id = os.getenv("GITHUB_CLIENT_ID")

@profile_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    github = OAuth2Session(client_id, token=session.get('oauth_token'))
    profile_info = github.get('https://api.github.com/user').json()
    user_id = profile_info.get('id', 'Unknown User ID')
    username = profile_info.get('login', 'Unknown Username')
    session['username'] = username
    return render_template('index.html', user_id=user_id, username=username)



@profile_bp.route("/repositories", methods=["GET"])
@login_required
def repositories():
    github = OAuth2Session(client_id, token=session.get('oauth_token'))
    profile_info = github.get('https://api.github.com/user').json()
    repos_info = github.get('https://api.github.com/user/repos').json()
    print(session.get('username'),flush=True)
    return render_template('repositories.html', username=session.get('username'), repos=repos_info)


@profile_bp.route("/repositories/<repo_name>", methods=["GET"])
@login_required
def repo_details(repo_name):

    github = OAuth2Session(client_id, token=session.get('oauth_token'))
    repos_info = github.get('https://api.github.com/user/repos').json()
    # filter the repository details
    
    repo_info = [repo for repo in repos_info if repo['name'] == repo_name]
    # Render the repository details template with the repository details
    jwt_token = session.get("jwt_token")
    #add the jwt token to the request header
    
    action_list = requests.get('http://dbproxy:5000/api/v1/read-action/'+repo_name, headers={'Authorization': 'Bearer '+jwt_token}).json()
    print(action_list,flush=True)



    return render_template('repo_details.html', repo_info=repo_info[0], action_list=action_list)
