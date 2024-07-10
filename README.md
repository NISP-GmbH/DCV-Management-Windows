# DCV Server Management for Windows

# Overview: Dynamic DCV Sessions

The standard approach for NICE DCV Console sessions is to have a session statically created for a specific user. In some cases it is preferred to enable users to connect to NICE DCV and dynamically be able to use the DCV Console Session without installing and configuring the [DCV Session Manager](https://docs.aws.amazon.com/dcv/latest/sm-admin/what-is-sm.html).

Below we show 2 approaches for managing console sessions - based on permissions and a more controlled via a Python API server

## Always on Console session, permissions for all and only one connection allowed

To implement this we automatically create a console sessions for a specific standard user and set the maximal number of connection to the DCV console session to 1 so no other user can connect and allow all users to connect to the session in the permissions file. The guide to implement this approach is here: https://www.ni-sp.com/nice-dcv-dynamic-console-sessions/

## DCV Management Python API Server to manage DCV virtual and console sessions

The DCV Management service is currently capable to do:
* Count sessions by owner
* Create a session
* Close a session
* List connections
* List sessions
* List sessions by owner
* Check session timedout and automatically close them
* Create a session when the user do the DCV Server login

New features coming:
* Request token access to access your session using SSH service

# Software requirements
- PowerShell 7.x or gerater
- Python 3.11 or lower; 3.12 can not be used due pywin32 issues; Python needs to be installed as administrator and for all users (or, if you understand how, give the right permissions to this service)
- Python pip package 
```bash
# download get-pip.py from
# https://pip.pypa.io/en/stable/installation/
# and execute:
python.exe get-pip.py
py -m pip install --upgrade pip
```
- Python libraries: Flask, pywin32, configparse, requests
```bash
python -m pip install --upgrade configparser Flask pywin32 requests
```

# How to install
- Create a directory to store the files. If you do not know where, "C:\dcv-management-windows\" can be an option.
- Copy the git directory content to this directory
- Go to the same dirctory using Windows explorer
- Edit the settings.ini file and set all the variables:

```bash
[Service]
AppBaseUrl=http://localhost:5000
PythonPath=C:\Program Files\Python311\
AppPath=C:\dcv-management-windows\
DcvPath=C:\Program Files\NICE\DCV\Server\bin\dcv.exe
DcvLogPath=C:\ProgramData\NICE\dcv\log\server.log
CurlPath=C:\Windows\System32\curl.exe
TimeToCloseUnusedSection=1800
SessionType=console
```

Explained:

```bash
AppBaseUrl  # the base url where DCV Management will be called
PythonPath  # python path where python.exe is, without include python.exe
AppPath     # all the service files from this git
DcvPath     # full path where dcv.exe is installed, with dcv.exe included
DcvLogPath  # full path where server.log, by DCV Server, is located
CurlPath    # full path of windows native curl, including curl.exe
TimeToCloseUnusedSection    # time, in secons, to close unused sessions
SessionType # type of session (Windows can run only console)
```

- Open Powershell as Administrator
- Go to the AppPath directory (using Powershell)
- We recommend to ByPass security checks for this session:
```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
- Execute the PowerShell script below that will read settings.ini and replace the variables where needed

```bash
.\pre-install.ps1
```

- Execute the .bat below to setup the services

```bash
.\install.bat
```

# How to uninstall
- Open the Powershell as administrator
- Execute:

```bash
.\uninstall.bat
```

- Remove the directory that used to store all DCV Management service files

# How to restart the DCV Management API

```bash
.\restart_dcv_management.bat
```

# How to test the DCV Management API

Execute:
```bash
C:\Windows\System32\curl.exe -s -X GET "http://localhost:5000/echo?owner=guest" -w "\nStatus Code: %{http_code}\n"
```

You can expect something like this:

```bash
{"returncode":"200","stderr":"error","stdout":"test"}
200
```

# HTTP requests to the DCV Management API Service

* Counting how much sessions a specific owner has:
```
curl -s http://localhost:5000/count-sessions-by-owner?owner=francisco
```

* List all sessions
```
curl -s http://localhost:5000/list-sessions
```

* Create a session with specific owner:
```
curl -s http://localhost:5000/create-session?owner=centos
```
* Check a session with specific owner and close the session if there are no one connected in last 30 minutes
```
 curl -s http://localhost:5000/check-session-timedout?owner=francisco
```

* List all owners with sessions created
```
curl -s http://localhost:5000/list-sessions-owners
