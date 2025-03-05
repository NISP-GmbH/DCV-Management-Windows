import time
import requests

def main():
    url = "http://localhost:5000/check-all-sessions"
    while True:
        try:
            response = requests.get(url)
            # Assume the endpoint returns JSON; adjust as needed.
            data = response.json()
            print("API call response:", data)
        except Exception as e:
            print("Error calling API:", str(e))
        time.sleep(30)  # wait for 30 seconds

if __name__ == '__main__':
    main()
