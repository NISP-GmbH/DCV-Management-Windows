import win32serviceutil
import win32service
import win32event
import servicemanager
import threading
import os
from app import app  # Import the Flask app from app.py
import dcv_session_monitor  # Import the module containing the session monitor
import invoke_api  # Import the new API invocation module

os.chdir(os.path.dirname(os.path.abspath(__file__)))

class CombinedDCVService(win32serviceutil.ServiceFramework):
    _svc_name_ = "DCVManagement"
    _svc_display_name_ = "DCV Management Service"
    _svc_description_ = "Runs the DCV Management Flask API, the DCV Session Monitor, and periodic API invocation."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        # Create an event to wait on for a stop signal.
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.stop_requested = False

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.stop_requested = True
        # Signal the stop event.
        win32event.SetEvent(self.hWaitStop)
        servicemanager.LogInfoMsg("DCVManagement - Stop signal received.")

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("DCVManagement - Service is starting...")

        # Start the Flask API in a separate thread.
        self.flask_thread = threading.Thread(target=self.start_flask_app)
        self.flask_thread.start()

        # Start the DCV session monitor in another thread.
        self.monitor_thread = threading.Thread(target=self.start_session_monitor)
        self.monitor_thread.start()

        # Start the periodic API invocation thread.
        self.invoke_api_thread = threading.Thread(target=self.start_invoke_api)
        self.invoke_api_thread.start()

        # Wait until a stop signal is received.
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

        servicemanager.LogInfoMsg("DCVManagement - Service is stopping...")

        # Optionally, add any graceful shutdown functionality here.
        self.flask_thread.join(timeout=5)
        self.monitor_thread.join(timeout=5)
        self.invoke_api_thread.join(timeout=5)

    def start_flask_app(self):
        try:
            # Start the Flask app (running on port 5000 as defined in app.py).
            app.run(host='0.0.0.0', port=5000)
        except Exception as e:
            servicemanager.LogErrorMsg("Error in Flask app: " + str(e))

    def start_session_monitor(self):
        try:
            # Start the session monitor (this function runs an infinite loop)
            dcv_session_monitor.main()
        except Exception as e:
            servicemanager.LogErrorMsg("Error in Session Monitor: " + str(e))
    
    def start_invoke_api(self):
        try:
            # Call the main function from invoke_api.py which runs forever.
            invoke_api.main()
        except Exception as e:
            servicemanager.LogErrorMsg("Error in API invocation: " + str(e))

if __name__ == '__main__':
    # Handles command-line options like "install", "start", "stop", etc.
    win32serviceutil.HandleCommandLine(CombinedDCVService)
