


import os
from flask import Blueprint, jsonify, request, session
from flask_login import login_required

import requests
actions_bp = Blueprint('actions', __name__)
client_id = os.getenv("GITHUB_CLIENT_ID")

@actions_bp.route("/trigger_action", methods=["POST"])
@login_required
def trigger_action():
    data = request.get_json()
    repo_name = data['repo_name']
    action_type = data['action_type']
    rest_server_url = 'http://orchestrator:5000/api/v1/trigger-action'



    params = {'repo_name': repo_name, 'action_type': action_type, 'oauth_token': session.get('oauth_token'), 'jwt_token': session.get("jwt_token")}  # Adjust based on the needs
    try:
        response = requests.post(rest_server_url, json=params)
        if response.status_code == 200:
            print(response)
            return jsonify({'message': 'Action triggered successfully!'}), 200
        else:
            return jsonify({'error': 'Failed to trigger action'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


