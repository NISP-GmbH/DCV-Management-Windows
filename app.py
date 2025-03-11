from flask import Flask, request, jsonify
import configparser
import subprocess
import os
import json
import signal
import sys
from datetime import datetime, timezone

app = Flask(__name__)

return_root = {"return": "This is an API used to manage your DCV services."}

# Read the settings.ini file
def get_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.ini')
    config.read(config_path)
    return config

# handle termination signal (only when running as the main program)
def signal_handler(signum, frame):
    print(f"Received signal {signum}. Shutting down gracefully...")
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

@app.route('/check-all-sessions', methods=['GET'])
def check_all_sessions():
    try:
        # Get the list of sessions (each tuple: (session_id, owner, num-of-connections, last-disconnection-time, creation-time))
        sessions_response, status_code = get_list_sessions()
        if status_code != 200:
            return sessions_response, status_code

        sessions_data = sessions_response.get_json()
        sessions_list = sessions_data['message']

        results = {}
        for session in sessions_list:
            session_id = session[0]
            # Use session id directly for checking timeout.
            timeout_response, timeout_status = check_session_timedout(session_identifier=session_id)
            results[session_id] = {
                'status': timeout_status,
                'message': timeout_response.get_json()['message'] if timeout_status == 200 else timeout_response.get_json()
            }

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"message": f"Unexpected error: {str(e)}"}), 500

@app.route('/request_token', methods=['POST'])
def execute_ssh_command():
    data = request.get_json()
    user = data.get('user')
    host = data.get('host')
    port = data.get('port')
    time_token_expire = data.get('time_token_expire')
    private_key = data.get('private_key')

    if time_token_expire == None:
        time_token_expire = 3600

    command = '/usr/bin/dcv_get_token ' + time_token_expire

    try:
        key = paramiko.RSAKey.from_private_key(StringIO(private_key))
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=host, username=user, port=port, pkey=key)

        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()

        ssh.close()

        return { 'message': output}, 200

    except Exception as e:
        return { 'message': str(e) }, 500

@app.route('/count-sessions-by-id', methods=['GET'])
def count_sessions_by_id(session_identifier=None):
    if session_identifier is None:
        session_identifier = request.args.get('session_id')
    if not session_identifier:
        return jsonify({"message": "Missing session identifier. Please specify session_id in the query string."}), 400

    response, _ = get_list_sessions()
    data = response.get_json()
    sessions_list = data['message']
    # Count sessions based on the session id in position 0
    count = sum(1 for session in sessions_list if session[0] == session_identifier)

    return jsonify({"message": count}), 200

@app.route('/count-sessions-by-owner', methods=['GET'])
def count_sessions(owner=None):
    try:
        if not owner:
            owner = request.args.get('owner')
        if not owner:
            return jsonify({"message": "Missing owner parameter. Please specify owner in the query string."}), 400

        response, status_code = get_list_sessions()
        if status_code != 200:
            return response, status_code

        data = response.get_json()
        sessions_list = data['message']
        # Count sessions where the second item (owner) equals the provided owner
        count = sum(1 for session in sessions_list if session[1] == owner)

        return jsonify({"message": count}), 200

    except Exception as e:
        return jsonify({"message": f"Error: Failed to run count-sessions. {str(e)}"}), 500

@app.route('/create-session', methods=['GET'])
def create_session(owner=None):
    if not owner:
        owner = request.args.get('owner')
    if not owner:
        return jsonify({"message": "Missing owner parameter. Please specify owner in the query string."}), 400

    response = count_sessions(owner)
    data = response[0]  # json part
    data_parsed = json.loads(data.get_data(as_text=True))
    owner_count = int(data_parsed["message"])

    if owner_count == 0:
        # Read config dynamically
        config = get_config()
        dcv_path = config.get('Service', 'DcvPath')
        session_type = config.get('Service', 'SessionType')
        command = [dcv_path, "create-session", "--owner", owner, "--name", owner, "--type", session_type, owner]
        try:
            process = subprocess.run(command, capture_output=True, text=True, check=True)
            return jsonify({"message": "created"}), 200
        except subprocess.CalledProcessError as error:
            app.logger.error(f"Error creating session: {error.stderr}")
            return jsonify({"message": f"Error: Failed to run create-session. {error.stderr}"}), 500
    else:
        return jsonify({"message": "Session already exists.", "count": owner_count}), 409

@app.route('/close-session', methods=['GET'])
def close_session(session_identifier=None):
    # Get session id from query parameter "session_id"
    if not session_identifier:
        session_identifier = request.args.get('session_id')
    if not session_identifier:
        return jsonify({"message": "Missing session identifier. Please specify session_id in the query string."}), 400

    response, _ = get_list_sessions()
    data = response.get_json()
    sessions_list = data['message']
    # Count sessions based on the session id (first element).
    count = sum(1 for session in sessions_list if session[0] == session_identifier)

    if count > 0:
        config = get_config()
        dcv_path = config.get('Service', 'DcvPath')
        command = [dcv_path, "close-session", session_identifier]
        try:
            process = subprocess.run(command, capture_output=True, text=True, check=True)
            return jsonify({"message": "closed"}), 200
        except subprocess.CalledProcessError as error:
            return jsonify({"message": f"Error: Failed to run close-session. {error.stderr}"}), 500
    else:
        return jsonify({"message": "No session found to be closed."}), 200

@app.route('/list-connections', methods=['GET'])
def list_connections(owner=None):
    owner = request.args.get('owner')
    if not owner:
        return jsonify({"message": "Missing owner parameter. Please specify owner in the query string."}), 400
    
    config = get_config()
    dcv_path = config.get('Service', 'DcvPath')
    command = " ".join([dcv_path, "list-connections", owner])
    try:
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, stdin=subprocess.PIPE
        )
        output, error = process.communicate()  # Capture stdout and stderr
    except subprocess.CalledProcessError as error:
        print("Error:", error)
    output = output.decode("utf-8")
    
    return jsonify({"message": output}), 200

@app.route('/check-session-timedout', methods=['GET'])
def check_session_timedout(session_identifier=None):
    if session_identifier is None:
        session_identifier = request.args.get('session_id')
    if not session_identifier:
        return jsonify({"message": "Missing session identifier. Please specify session_id in the query string."}), 400

    config = get_config()
    dcv_path = config.get('Service', 'DcvPath')
    time_to_close = int(config.get('Service', 'TimeToCloseUnusedSection'))

    command = [dcv_path, "describe-session", session_identifier, "--json"]

    try:
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        output = process.stdout
        data = json.loads(output)

        if time_to_close == 0:
            return jsonify({
                "message": "Automatic session closure is disabled because TimeToCloseUnusedSection is set to zero."
            }), 200

        num_connections = data["num-of-connections"]
        creation_time_str = data["creation-time"]
        last_disconnection_time_str = data.get("last-disconnection-time")

        format_string = "%Y-%m-%dT%H:%M:%S.%fZ"
        creation_time = datetime.strptime(creation_time_str, format_string).replace(tzinfo=timezone.utc)
        current_time = datetime.now(timezone.utc)

        if last_disconnection_time_str:
            disconnection_time = datetime.strptime(last_disconnection_time_str, format_string).replace(tzinfo=timezone.utc)
            idle_time = current_time - disconnection_time
        else:
            idle_time = current_time - creation_time

        idle_seconds = idle_time.total_seconds()

        if num_connections == 0:
            if idle_seconds > time_to_close:
                # Call close_session with the session id.
                close_response, close_status = close_session(session_identifier=session_identifier)
                return close_response, close_status
            else:
                return jsonify({
                    "message": f"There are no users connected, but the time to timeout ({time_to_close} seconds) has not been reached yet. Current idle time: {idle_seconds:.2f} seconds"
                }), 200
        else:
            return jsonify({"message": "There are users still connected under DCV session."}), 200

    except subprocess.CalledProcessError as error:
        return jsonify({"message": f"Error: {error.stderr}"}), 500
    except Exception as e:
        return jsonify({"message": f"Unexpected error: {str(e)}"}), 500

@app.route('/list-sessions-owners', methods=['GET'])
def list_sessions_owners():
    try:
        response, response_code = get_list_sessions()
        if response_code != 200:
            return response, response_code

        data = response.get_json()
        sessions_list = data["message"]
        # Extract owners from each tuple (second element)
        owners = [session[1] for session in sessions_list]
        return jsonify({"message": owners}), 200

    except subprocess.CalledProcessError:
        return jsonify({"message": "Error: Failed to get the owner session list.'"}), 500

@app.route('/list-sessions', methods=['GET'])
def get_list_sessions():
    try:
        config = get_config()  # Read settings dynamically
        dcv_path = config.get('Service', 'DcvPath')  # Get current dcv_path value

        # Execute the command with the --json flag
        command = [dcv_path, "list-sessions", "--json"]
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        output = process.stdout.strip()

        # If there's no output, return an empty list
        if not output:
            sessions = []
        else:
            sessions_data = json.loads(output)
            # Create a list of tuples: (id, owner, num-of-connections, last-disconnection-time, creation-time)
            sessions = []
            for session in sessions_data:
                session_tuple = (
                    session.get("id", ""),
                    session.get("owner", ""),
                    session.get("num-of-connections", 0),
                    session.get("last-disconnection-time", ""),
                    session.get("creation-time", "")
                )
                sessions.append(session_tuple)

        return jsonify({"message": sessions}), 200

    except subprocess.CalledProcessError as error:
        return jsonify({"message": f"Error: {error.stderr}"}), 500
    except Exception as e:
        return jsonify({"message": f"Unexpected error: {str(e)}"}), 500
   
@app.route('/echo', methods=['GET'])
def execute_echo():
    # Get JSON data from the request body
    data = request.get_json(silent=True)

    if not data or 'owner' not in data:
        return jsonify({
            "stdout": "",
            "stderr": "Error: Missing required parameter 'owner'",
            "returncode": 400
        }), 400

    owner = data['owner']

    return jsonify({
        "stdout": f"Echo: {owner}",
        "stderr": "",
        "returncode": 200
    })

@app.route('/', methods=['GET'])
def get_data():
    return jsonify(return_root)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("Interrupted. Shutting down...")
        sys.exit(0)