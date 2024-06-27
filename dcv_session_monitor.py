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
        self.last_inode = os.stat(dcv_log_path).st_ino
        self.last_position = os.path.getsize(dcv_log_path)

    def check_log(self):
        try:
            current_stat = os.stat(dcv_log_path)
            current_inode = current_stat.st_ino
            current_size = current_stat.st_size

            if current_inode != self.last_inode:
                self.last_inode = current_inode
                self.last_position = 0
                current_size = 0

            if current_size < self.last_position:
                self.last_position = 0

            if current_size > self.last_position:
                with open(dcv_log_path, 'r', encoding='utf-8') as file:
                    file.seek(self.last_position)
                    new_lines = file.readlines()
                
                last_match = None
                for line in new_lines:
                    match = re.search(r'INFO\s+authenticator - Sending authentication result OK to .+ for user (\w+) \(0 sessions\)', line)
                    if match:
                        last_match = match

                if last_match:
                    username = last_match.group(1)
                    self.check_and_create_session(username)
                
                self.last_position = current_size

        except FileNotFoundError:
            self.last_inode = None
            self.last_position = 0

    def check_and_create_session(self, username):
        # Check if there are any existing sessions
        response = requests.get(f'{app_base_url}/list-sessions')
        if response.json()['message'] == '':
            # No existing sessions, create a new one
            create_url = f'{app_base_url}/create-session?owner={username}'
            response = requests.get(create_url)
            if response.json()['message'] == 'created':
                print(f"Created session for user: {username}")
            else:
                print(f"Failed to create session for user: {username}")
        else:
            print("Session already exists, skipping creation")

def main():
    monitor = LogMonitor()

    while True:
        monitor.check_log()
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
