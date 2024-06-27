import os
import time
import re
import requests
import configparser

# Configuration
POLL_INTERVAL = 1  # Time in seconds between checks

config = configparser.ConfigParser()
config.read('settings.ini')
dcv_log_path = config.get('Service', 'DcvLogPath')
app_base_url = config.get('Service', 'AppBaseUrl')

class LogMonitor:
    def __init__(self):
        print("Initializing LogMonitor")
        self.last_inode = os.stat(dcv_log_path).st_ino
        self.last_position = os.path.getsize(dcv_log_path)
        print(f"Initial file size: {self.last_position}")

    def check_log(self):
        print("Checking log file")
        try:
            current_stat = os.stat(dcv_log_path)
            current_inode = current_stat.st_ino
            current_size = current_stat.st_size

            if current_inode != self.last_inode:
                print("Log file has been rotated. Resetting position.")
                self.last_inode = current_inode
                self.last_position = 0
                current_size = 0

            if current_size < self.last_position:
                print("File size decreased. Resetting position.")
                self.last_position = 0

            if current_size > self.last_position:
                print(f"File size changed. Old: {self.last_position}, New: {current_size}")
                with open(dcv_log_path, 'r', encoding='utf-8') as file:
                    file.seek(self.last_position)
                    new_lines = file.readlines()
                
                print(f"New lines: {len(new_lines)}")

                last_match = None
                for line in new_lines:
                    match = re.search(r'INFO\s+authenticator - Sending authentication result OK to .+ for user (\w+) \(0 sessions\)', line)
                    if match:
                        last_match = match
                        print(f"Found match: {line.strip()}")

                if last_match:
                    username = last_match.group(1)
                    print(f"Last matched username: {username}")
                    self.check_and_create_session(username)
                
                self.last_position = current_size
            else:
                print("No new content in log file")

        except FileNotFoundError:
            print("Log file not found. Waiting for it to be created.")
            self.last_inode = None
            self.last_position = 0

    def check_and_create_session(self, username):
        print(f"Checking and creating session for user: {username}")
        # Check if there are any existing sessions
        response = requests.get(f'{app_base_url}/list-sessions')
        print(f"List sessions response: {response.text}")
        if response.json()['message'] == '':
            # No existing sessions, create a new one
            create_url = f'{app_base_url}/create-session?owner={username}'
            response = requests.get(create_url)
            print(f"Create session response: {response.text}")
            if response.json()['message'] == 'created':
                print(f"Created session for user: {username}")
            else:
                print(f"Failed to create session for user: {username}")
        else:
            print("Session already exists, skipping creation")

def main():
    print("Starting main function")
    monitor = LogMonitor()

    try:
        while True:
            monitor.check_log()
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("Keyboard interrupt received")

if __name__ == "__main__":
    main()
