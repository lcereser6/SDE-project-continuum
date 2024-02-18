import os
from flask import Blueprint, jsonify, request, session
from flask_login import login_required
import requests

# Initialize Flask Blueprint for actions routes
actions_bp = Blueprint('actions', __name__)

# Ensure the GITHUB_CLIENT_ID environment variable is set
if not os.getenv("GITHUB_CLIENT_ID"):
    raise EnvironmentError("GITHUB_CLIENT_ID environment variable is not set.")

@actions_bp.route("/trigger_action", methods=["POST"])
@login_required  # Ensure the user is logged in before allowing action triggering
def trigger_action():
    """
    Trigger an action for a given repository.

    This endpoint expects a JSON payload with 'repo_name' and 'action_type'.
    It forwards these along with the user's OAuth and JWT tokens to an orchestrator service.
    """
    # Extract data from request
    data = request.get_json()
    if not data or 'repo_name' not in data or 'action_type' not in data:
        return jsonify({'error': 'Missing required parameters.'}), 400

    repo_name = data['repo_name']
    action_type = data['action_type']
    rest_server_url = 'http://orchestrator:5000/api/v1/trigger-action'

    # Prepare the request parameters
    params = {
        'repo_name': repo_name,
        'action_type': action_type,
        'oauth_token': session.get('oauth_token'),
        'jwt_token': session.get("jwt_token")
    }

    try:
        # Make a POST request to the orchestrator service
        response = requests.post(rest_server_url, json=params)
        if response.status_code == 200 or response.status_code == 202:
            # Assuming 200 and 202 indicate success
            return jsonify({'message': 'Action triggered successfully!'}), response.status_code
        else:
            # Log and return the error response from the orchestrator
            error_message = response.json().get('error', 'Failed to trigger action due to an unknown error.')
            return jsonify({'error': error_message}), response.status_code
    except requests.exceptions.RequestException as e:
        # Handle errors from the requests library
        return jsonify({'error': f'Request to orchestrator service failed: {str(e)}'}), 500

#Define the route for the logs, taking the action_uid and the service as parameters
@actions_bp.route("/logs", methods=["GET"])
@login_required
def get_logs():

    #throw generic error
    """
    Fetch logs for a specific action and service.

    This endpoint forwards the request to the orchestrator service, which in turn
    retrieves the logs from the appropriate service.
    """

    #get action_uid and service 
    action_uid = request.args.get("action_uid")
    service = request.args.get("service")
    
    print("Fetching logs for action", action_uid, "from service", service, flush=True)
    rest_server_url = f'http://dbproxy:5000/api/v1/logs/{action_uid}/{service}'
    headers = {'Authorization': f'Bearer {session.get("jwt_token")}'}

    try:
        # Make a GET request to the orchestrator service
        response = requests.get(rest_server_url, headers=headers)
        if response.status_code == 200:
            # Assuming 200 indicates success
            return jsonify(response.json()), response.status_code
        else:
            # Log and return the error response from the orchestrator
            error_message = response.json().get('error', 'Failed to fetch logs due to an unknown error.')
            return jsonify({'error': error_message}), response.status_code
    except requests.exceptions.RequestException as e:
        # Handle errors from the requests library
        return jsonify({'error': f'Request to orchestrator service failed: {str(e)}'}), 500