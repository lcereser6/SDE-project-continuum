from flask import Flask, redirect, url_for, session, request, jsonify, render_template
from requests_oauthlib import OAuth2Session
import os

# This information is obtained upon registration of a new GitHub OAuth application here: https://github.com/settings/applications/new
client_id = ""
client_secret = ""
authorization_base_url = 'https://github.com/login/oauth/authorize'
token_url = 'https://github.com/login/oauth/access_token'

app = Flask(__name__)
# This secret should be a random string in a production application.
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

# Ensure session is not permanent and browser close clears the session
@app.before_request
def make_session_permanent():
    session.permanent = False

@app.route("/")
def index():
    return render_template('login.html')

@app.route("/login")
def login():
    """Step 1: User Authorization.

    Redirect the user/resource owner to the OAuth provider (i.e. GitHub)
    using an URL with a few key OAuth parameters.
    """
    github = OAuth2Session(client_id)
    authorization_url, state = github.authorization_url(authorization_base_url)

    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route("/callback", methods=["GET"])
def callback():
    """Step 2: User authorization, this happens on the provider."""
    # Log the full authorization response URL (helpful for debugging)
    print(f"Full callback URL: {request.url}")

    github = OAuth2Session(client_id, state=session['oauth_state'])
    try:
        token = github.fetch_token(token_url, client_secret=client_secret,
                                   authorization_response=request.url)
        session['oauth_token'] = token
        return redirect(url_for('.profile'))
    except Exception as e:
        # Log the exception (helpful for debugging)
        print(f"An error occurred: {e}")
        return f"An error occurred: {e}"

@app.route("/profile", methods=["GET"])
def profile():
    """Fetching a protected resource using an OAuth 2 token."""
    github = OAuth2Session(client_id, token=session.get('oauth_token'))
    profile_info = github.get('https://api.github.com/user').json()
    
    # Extracting the user ID and username from the response.
    user_id = profile_info.get('id', 'Unknown User ID')
    username = profile_info.get('login', 'Unknown Username')

    # Render the profile template with the user information
    return render_template('index.html', user_id=user_id, username=username)



@app.route("/repositories", methods=["GET"])
def repositories():
    """Fetching a list of user repositories using an OAuth 2 token."""
    github = OAuth2Session(client_id, token=session.get('oauth_token'))
    profile_info = github.get('https://api.github.com/user').json()
    repos_info = github.get('https://api.github.com/user/repos').json()
    
    username = profile_info.get('login', 'Unknown Username')
    # Render the repositories template with the list of repositories
    return render_template('repositories.html', username=username, repos=repos_info)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('.index'))

if __name__ == "__main__":
    # Run the application on http://127.0.0.1:5000/
    
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(debug=True)