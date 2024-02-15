from flask import Flask, session
from flask_login import LoginManager
from config import Config
from blueprints.auth import auth_bp
from blueprints.profile import profile_bp
from blueprints.actions import actions_bp
from modules import User
app = Flask("dashboard")
app.config.from_object(Config)

# Initialize Flask-Session


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(actions_bp)

@login_manager.user_loader
def load_user(user_id,):
    # User loading logic here. This could involve loading a user from the session
    return User.get(user_id)