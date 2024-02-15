import datetime
import os
from flask import Blueprint, render_template, session, redirect, url_for, request
from flask_login import login_user, logout_user
import jwt
from requests_oauthlib import OAuth2Session

from modules import User

auth_bp = Blueprint('auth', __name__)
client_id = os.getenv("GITHUB_CLIENT_ID")
client_secret = os.getenv("GITHUB_CLIENT_SECRET")
authorization_base_url = 'https://github.com/login/oauth/authorize'
token_url = 'https://github.com/login/oauth/access_token'
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

@auth_bp.route("/")
def index():
    return render_template('login.html')

@auth_bp.route("/login")
def login():
    github = OAuth2Session(client_id)
    authorization_url, state = github.authorization_url(authorization_base_url)
    session['oauth_state'] = state
    return redirect(authorization_url)


@auth_bp.route("/callback", methods=["GET"])
def callback():
    if 'oauth_state' not in session:
        print("Session state missing. Please start the login process again.")
        return redirect(url_for('auth.login'))
    github = OAuth2Session(client_id, state=session['oauth_state'])
    try:
        token = github.fetch_token(token_url, client_secret=client_secret, authorization_response=request.url)
        session['oauth_token'] = token
        user_info = github.get('https://api.github.com/user').json()
        user = User(id=str(user_info['id']), username=user_info['login'], token=token)

        jwt_payload = {
        'username': user.username,  # Assume `user` is the authenticated user object
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token expires in 1 hour
        }

        jwt_token = jwt.encode(jwt_payload, JWT_SECRET_KEY, algorithm='HS256')
        session['jwt_token'] = jwt_token
        session['user_info'] = {'id': user.id, 'username': user.username, 'oauth_token': token}
        
        login_user(user)
        return redirect(url_for('profile.profile'))
    
    except Exception as e:
        # Log the exception
        print(f"An error occurred: {e}")
        return f"An error occurred: {e}"


@auth_bp.route("/logout")
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('.index'))
