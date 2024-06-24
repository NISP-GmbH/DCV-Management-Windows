from flask import Flask, request, jsonify
import configparser
import subprocess
import os
import json
from datetime import datetime, timezone

app = Flask(__name__)

return_root = {"return": "This is an API used to manage your DCV services."}

# Read the settings.ini file
config = configparser.ConfigParser()
config.read('settings.ini')
dcv_path = config.get('Service', 'DcvPath')
time_to_close = int(config.get('Service', 'TimeToCloseUnusedSection'))
session_type = config.get('Service', 'SessionType')

@app.route('/check-all-sessions', methods=['GET'])
def check_all_sessions():
    try:
        # Step 1: Get list of sessions
        sessions_response, status_code = get_list_sessions()
        if status_code != 200:
            return sessions_response, status_code

        sessions_data = sessions_response.get_json()
        sessions_output = sessions_data['message']

        # Extract owners from the sessions output
        owners = set()
        for line in sessions_output.split('\n'):
            if 'owner:' in line:
                owner = line.split('owner:')[1].split()[0]
                owners.add(owner)

        # Step 2: Check timeout for each owner
        results = {}
        for owner in owners:
            timeout_response, timeout_status = check_session_timedout(owner)
            results[owner] = {
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
        sessions_output = data['message']
        count = sessions_output.count(f"owner:{owner}")

        return jsonify({"message": count}), 200
    except Exception as e:
        return jsonify({"message": f"Error: Failed to run count-sessions. {str(e)}"}), 500

@app.route('/create-session', methods=['GET'])
def create_session(owner=None):
    if not owner:
        owner = request.args.get('owner')
    if not owner:
        return jsonify({"message": "Missing owner parameter. Please specify owner in the query string."}), 400

    response = count_sessions(owner)  # tuple: json, http code
    data = response[0]  # json part
    data_parsed = json.loads(data.get_data(as_text=True))
    owner_count = int(data_parsed["message"])

    if owner_count == 0:
        command = [dcv_path, "create-session", "--owner", owner, "--name", owner, "--type", session_type, owner]
        try:
            process = subprocess.run(command, capture_output=True, text=True, check=True)
            return jsonify({"message": "created"}), 200
        except subprocess.CalledProcessError as error:
            app.logger.error(f"Error creating session: {error.stderr}")
            return jsonify({"message": f"Error: Failed to run create-session. {error.stderr}"}), 500
    else:
        return jsonify({"message": "Session already exists.", "count": owner_count}), 409  # Using 409 Conflict for existing session


@app.route('/close-session', methods=['GET'])
def close_session(owner=None):
    if not owner:
        owner = request.args.get('owner')
    if not owner:
        return jsonify({"message": "Missing owner parameter. Please specify owner in the query string."}), 400

    response = count_sessions(owner)  # tuple: json, http code
    data = response[0]  # json part
    data_parsed = json.loads(data.get_data(as_text=True))
    owner_count = int(data_parsed["message"])

    if owner_count > 0:
        command = [dcv_path, "close-session", owner]
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
    command= " ".join([dcv_path, "list-connections", owner])
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        output, error = process.communicate()  # Capture stdout and stderr
    except subprocess.CalledProcessError as error:
            print("Error:", error)
    output = output.decode("utf-8")
    
    return jsonify({"message": output}), 20

@app.route('/check-session-timedout', methods=['GET'])
def check_session_timedout(owner=None):
    if owner is None:
        owner = request.args.get('owner')
    if not owner:
        return jsonify({"message": "Missing owner parameter. Please specify owner in the query string."}), 400

    command = [dcv_path, "describe-session", owner, "--json"]

    try:
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        output = process.stdout
        data = json.loads(output)
        time_to_close = int(config.get('Service', 'TimeToCloseUnusedSection'))
        num_connections = data["num-of-connections"]
        creation_time_str = data["creation-time"]
        last_disconnection_time_str = data.get("last-disconnection-time")

        format_string = "%Y-%m-%dT%H:%M:%S.%fZ"
        creation_time = datetime.strptime(creation_time_str, format_string)
        print(last_disconnection_time_str)
        if last_disconnection_time_str:
            # If there's a disconnection time, use it
            disconnection_time = datetime.strptime(last_disconnection_time_str, format_string)
        else:
            # If there's no disconnection time, use the current time
            disconnection_time = datetime.now(timezone.utc)

        time_difference = disconnection_time - creation_time.replace(tzinfo=timezone.utc)
        difference_in_seconds = time_difference.total_seconds()

        if num_connections == 0:
            if difference_in_seconds > time_to_close:
                close_response, close_status = close_session(owner)
                return close_response, close_status
            else:
                return jsonify({"message": f"There are no users connected, but the time to timeout ({time_to_close} seconds) has not been reached yet. Current idle time: {difference_in_seconds:.2f} seconds"}), 200
        else:
            return jsonify({"message": "There are users still connected under DCV session."}), 200

    except subprocess.CalledProcessError as error:
        return jsonify({"message": f"Error: {error.stderr}"}), 500
    except Exception as e:
        return jsonify({"message": f"Unexpected error: {str(e)}"}), 500

@app.route('/list-sessions-owners', methods=['GET'])
def list_sessions_owners():
    try:
        response = get_list_sessions()
        response_code = response[1]
        data = response[0]
        data_parsed_json = json.loads(data.get_data(as_text=True))
        message = data_parsed_json["message"]
        lines = message.splitlines()
        owners = []
        for line in lines:
            parts = line.split()
            owners.append(parts[1].strip("'"))
        return jsonify({"message": owners}), 200
        
    except subprocess.CalledProcessError:
        return jsonify({"message": "Error: Failed to run 'dcv list-sessions"}), 500


@app.route('/list-sessions', methods=['GET'])
def get_list_sessions():
    try:
        command = [dcv_path, "list-sessions"]
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        output = process.stdout
        return jsonify({"message": output}), 200
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
    app.run(debug=False)  # Set debug=False for production
