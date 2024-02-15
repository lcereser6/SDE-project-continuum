import time
import jwt
import redis
from flask import Flask, redirect, url_for, session, request, jsonify, render_template
import os
from jwt.exceptions import InvalidTokenError
import psycopg2 as psycopg2

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")
app.config['SESSION_TYPE'] = os.getenv("SESSION_TYPE")
app.config['SESSION_PERMANENT'] = os.getenv("SESSION_PERMANENT")
app.config['SESSION_USE_SIGNER'] = os.getenv("SESSION_USE_SIGNER")
app.config['SESSION_REDIS'] = redis.from_url('redis://redis:6379')
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")


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


#get all actions for a repo filtered by user and ordered by latest, extract username from jwt token
@app.route("/api/v1/read-action/<repo>", methods=["GET"])

def get_builds(repo):
    username = validate_token(request.headers.get("Authorization").split(" ")[1])
    print(username,flush=True)
    print(repo,flush=True)
    query = """
        SELECT * 
        FROM actions 
        WHERE git_repo_name = %s
        AND git_user_uid = %s
        ORDER BY time_action_start DESC
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, (repo, username))
        builds = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(builds), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/write-action", methods=["POST"])
def log_build():
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
            scanner_eta,
            scanner_status
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
        build_info["scanner_eta"] if build_info["scanner_eta"] != "None" else None,
        build_info["scanner_status"] if build_info["scanner_status"] != "None" else None,

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
    


if __name__ == "__main__":

    time.sleep(15)
    app.run(debug=True, host="0.0.0.0")
    


