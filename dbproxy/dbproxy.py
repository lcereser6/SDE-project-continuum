import time
import jwt
import redis
from flask import Flask, redirect, url_for, session, request, jsonify, render_template
import os
from jwt.exceptions import InvalidTokenError
import psycopg2 as psycopg2
from logQueue import LogQueue
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
log_queue_host = os.getenv("LOG_QUEUE_HOST", "rabbitmq")
log_queue_port = os.getenv("LOG_QUEUE_PORT", "5672")
log_queue_name = os.getenv("LOG_QUEUE_NAME", "log-queue")
db_config = {
    "host": os.getenv("POSTGRES_HOST"),
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "port": os.getenv("POSTGRES_PORT")
}
log_queue = LogQueue(log_queue_host, log_queue_port, log_queue_name, db_config)


@app.route("/")
def index():
    return ("Database Proxy is running")

@app.route("/api/v1/info")
def info():
    return jsonify({
        "name": "Database Proxy",
        "status": "running"
    })


def validate_token(token):
    '''
    Validates a JWT token and returns the username if valid.
    :param token: JWT token to be validated.
    :return: Username if token is valid, None otherwise.
    '''
    try:
        # Decode token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload['username']  # Return the username from the payload
    except InvalidTokenError:
        # Handle invalid token (e.g., expired, tampered, etc.)
        return None

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT")
    )
    return conn



@app.route("/api/v1/read-action/<repo>", methods=["GET"])
def get_actions(repo):
    '''
    Retrieves all actions for a specified repository, filtered by user and ordered by the latest.
    :param repo: The name of the repository to retrieve actions for.
    :return: A list of actions for the specified repository.

    '''
    username = validate_token(request.headers.get("Authorization").split(" ")[1])
    if username is None:
        return jsonify({"error": "Unauthorized"}), 401

    query = """
        SELECT action_uid, git_user_uid, time_action_start, git_repo_uid, git_commit_hash,
               git_branch_name, git_repo_name, current_status, builder_status, tester_status,
               deployer_status, builder_eta, tester_eta, deployer_eta, action_type,
               scanner_status, scanner_eta
        FROM actions 
        WHERE git_repo_name = %s AND git_user_uid = %s
        ORDER BY time_action_start DESC
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, (repo, username))
        rows = cur.fetchall()
        # Convert each row to a dict with properly formatted dates
        builds = [
            {
                "action_uid": row[0],
                "git_user_uid": row[1],
                "time_action_start": row[2].isoformat() if row[2] else None,
                "git_repo_uid": row[3],
                "git_commit_hash": row[4],
                "git_branch_name": row[5],
                "git_repo_name": row[6],
                "current_status": row[7],
                "builder_status": row[8],
                "tester_status": row[9],
                "deployer_status": row[10],
                "builder_eta": row[11],
                "tester_eta": row[12],
                "deployer_eta": row[13],
                "action_type": row[14],
                "scanner_status": row[15],
                "scanner_eta": row[16],
            } for row in rows
        ]
        cur.close()
        conn.close()
        return jsonify(builds), 200
    except Exception as e:
        print(e, flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/write-action", methods=["POST"])
def log_action():
    '''
    Logs a new action to the database.
    :return: A JSON response indicating the success or failure of the operation.

    '''
    build_info = request.get_json()
    query = """
        INSERT INTO actions (
            action_uid,
            git_user_uid,
            time_action_start,
            git_repo_uid,
            git_commit_hash,
            git_branch_name,
            git_repo_name,
            current_status,
            builder_status,
            tester_status,
            deployer_status,
            builder_eta,
            tester_eta,
            deployer_eta,
            action_type,
            scanner_status,
            scanner_eta

        ) VALUES (%s, %s, to_timestamp(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    data = (
        build_info["action_uid"],
        build_info["git_user_uid"],
        build_info["time_action_start"] if build_info["time_action_start"] is not None else None,
        build_info["git_repo_uid"],
        build_info["git_commit_hash"],
        build_info["git_branch_name"],
        build_info["git_repo_name"],
        build_info["current_status"],
        build_info["builder_status"] if build_info["builder_status"] != "None" else None,
        build_info["tester_status"] if build_info["tester_status"] != "None" else None,
        build_info["deployer_status"] if build_info["deployer_status"] != "None" else None,
        build_info["builder_eta"] if build_info["builder_eta"] != "None" else None,
        build_info["tester_eta"] if build_info["tester_eta"] != "None" else None,
        build_info["deployer_eta"] if build_info["deployer_eta"] != "None" else None,
        build_info["action_type"] if build_info["action_type"] != "None" else None,
        build_info["scanner_status"] if build_info["scanner_status"] != "None" else None,
        build_info["scanner_eta"] if build_info["scanner_eta"] != "None" else None,        

    )

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query,data)
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Build log successfully created"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/api/v1/logs/<action_uid>/<service>", methods=["GET"])
def get_logs(action_uid, service):
    '''
    Retrieves logs for a specific action and service.
    :param action_uid: The unique identifier of the action to retrieve logs for.
    :param service: The service to retrieve logs from.

    :return: A list of logs for the specified action and service.
    '''

    query = """
        SELECT time, log_text
        FROM logs
        WHERE action_uid = %s AND service = %s
        ORDER BY time
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, (action_uid, service))
        rows = cur.fetchall()
        logs = [
            {
                #convert the time string to isoformat
                "time": row[0],
                "log_text": row[1]
            } for row in rows
        ]
        cur.close()
        conn.close()
        return jsonify(logs), 200
    except Exception as e:
        print(e, flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/update-action", methods=["POST"])
def update_action():
    '''
    Updates the status and ETA of an action in the database.
    :return: A JSON response indicating the success or failure of the operation.

    '''

    build_info = request.get_json()
    print(build_info,flush=True)

    query = f"""
        UPDATE actions
        SET 
            {build_info['status_name']} = %s,
            {build_info['eta_name']} = %s
        WHERE action_uid = %s
    """
    
    data = (
        build_info["status"],
        build_info["eta"],
        build_info["action_uid"]
    )
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query,data)
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Build log successfully updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


if __name__ == "__main__":

    time.sleep(15)
    log_queue.connect()
    log_queue.start_consuming()
    app.run(debug=True, host="0.0.0.0")
    


