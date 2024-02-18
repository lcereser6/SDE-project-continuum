"""
Module for handling authentication flow using GitHub OAuth and JWT for a Flask application.

This module sets up endpoints for the OAuth flow with GitHub, including login, callback processing,
and logout functionalities. It leverages Flask-Login for session management and JWT for token generation.
"""

import datetime
import os
from flask import Blueprint, render_template, session, redirect, url_for, request
from flask_login import login_user, logout_user
import jwt
from requests_oauthlib import OAuth2Session
from modules import User

# Ensure necessary environment variables are set
required_env_vars = ["GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET", "JWT_SECRET_KEY"]
for var in required_env_vars:
    if not os.getenv(var):
        raise EnvironmentError(f"Required environment variable {var} is not set.")

# Initialize Flask Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

# OAuth configuration
client_id = os.getenv("GITHUB_CLIENT_ID")
client_secret = os.getenv("GITHUB_CLIENT_SECRET")
authorization_base_url = 'https://github.com/login/oauth/authorize'
token_url = 'https://github.com/login/oauth/access_token'
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

@auth_bp.route("/")
def index():
    """Render the login page."""
    return render_template('login.html')

@auth_bp.route("/login")
def login():
    """Initiate the OAuth flow by redirecting the user to GitHub's authorization page."""
    github = OAuth2Session(client_id)
    authorization_url, state = github.authorization_url(authorization_base_url)
    session['oauth_state'] = state
    return redirect(authorization_url)

@auth_bp.route("/callback", methods=["GET"])
def callback():
    """Handle the callback from GitHub after user authorization.

    Fetches the access token, retrieves user information, generates a JWT token, and logs the user in.
    """
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
            'username': user.username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token expires in 1 hour
        }

        jwt_token = jwt.encode(jwt_payload, JWT_SECRET_KEY, algorithm='HS256')
        session['jwt_token'] = jwt_token
        session['user_info'] = {'id': user.id, 'username': user.username, 'oauth_token': token}
        
        login_user(user)
        return redirect(url_for('profile.profile'))
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"An error occurred: {e}"

@auth_bp.route("/logout")
def logout():
    """Log out the current user and clear the session."""
    logout_user()
    session.clear()
    return redirect(url_for('.index'))
