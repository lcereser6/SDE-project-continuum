

from flask import session
from flask_login import LoginManager, UserMixin


class User(UserMixin):
    def __init__(self, id, username, token):
        self.id = id
        self.username = username
        self.token = token

    @staticmethod
    def get(user_id):
        # Here, you would ideally fetch user details from your database or session
        # For simplicity, we're just instantiating a new user with the same ID
        user_info = session.get('user_info', {})
        if user_info.get('id') == user_id:
            return User(id=user_id, username=user_info.get('username'), token=user_info.get('oauth_token'))
        return None


