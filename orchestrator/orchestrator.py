from flask import Flask, session
from flask_session import Session  # Import Session from flask_session
from config import Config
from blueprints.actions import actions_bp
app = Flask("orchestrator")
app.config.from_object(Config)

# Initialize Flask-Session
sess = Session(app)  # Initialize the session with your Flask app
app.register_blueprint(actions_bp)
