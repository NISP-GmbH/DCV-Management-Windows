# NI SP DCV Windows Management

A single self-contained Windows service that manages
NICE / Amazon DCV console sessions, plus a local web admin console. It replaces
the previous Python implementation.

## Preview

<img width="1064" height="1150" alt="Image" src="https://github.com/user-attachments/assets/24bfeeb4-bd0f-4a0f-9c80-1134d44e828f" />

## What it does

* Count sessions by owner or by id
* Create / close sessions
* List sessions, owners, and connections
* Auto-close idle sessions after a configurable timeout
* Auto-create a session when a user logs in to the DCV server (log-driven)
* Optionally lock the local physical keyboard/mouse while a session is active or a user is connected to the session
* A loopback-only web admin console to edit configuration, view/manage sessions, and control the service

The service exposes an HTTP API (default `:5000`) and a browser admin UI at
`http://127.0.0.1:5000/admin`.

## Requirements

* Windows 10/11 or Windows Server (x64).
* NICE / Amazon DCV Server installed and running.

## Download

Download the latest installer from the
[**Releases** page](https://github.com/NISP-GmbH/DCV-Management-Windows/releases/latest),
or directly:
[**NI-SP-DCV-Windows-Management-v1.0.0.zip**](https://github.com/NISP-GmbH/DCV-Management-Windows/releases/download/v1.0.0/NI-SP-DCV-Windows-Management-v1.0.0.zip)
— the zip contains the MSI installer and an `INSTALL.txt`.

## Install (MSI)

1. Download and unzip the release above (or build it, see **Building**).
2. Run it (elevated):
   ```
   msiexec /i "NI-SP-DCV-Windows-Management.msi"
   ```
   The MSI installs the binary to
   `C:\Program Files\NI SP DCV Windows Management\`, registers and starts the
   `DCVManagement` service (LocalSystem, auto-start), and adds a Start-menu
   shortcut **NI SP DCV Windows Management** that opens the admin console.
3. Open `http://127.0.0.1:5000/admin` and adjust settings.

### Choosing the port at install time

The HTTP/admin port defaults to `5000`. To set a different port, pass the public
`PORT` property — it works for both **interactive** and **quiet** installs:

```
msiexec /i "NI-SP-DCV-Windows-Management.msi" PORT=5050
msiexec /i "NI-SP-DCV-Windows-Management.msi" PORT=5050 /qn      (quiet)
```

The installer records the port and the service writes it into `settings.ini` on
first run. `PORT` only applies to a **fresh install** (when no `settings.ini`
exists yet); on upgrades the existing `settings.ini` is kept. To change the port
later, edit it in the admin console (**Settings → API port**) and restart the
service.

On first run the service writes a default `settings.ini` next to the binary if
one does not exist. Upgrades never overwrite your edited `settings.ini`.

## Admin console

Browse to `http://127.0.0.1:5000/admin` **on the server itself**. Access is
restricted two ways:

* **Loopback only** — requests from any other host get HTTP 403 (the API on the
  same port stays reachable network-wide; only the `/admin*` routes are locked
  down).
* **Administrators only** — the service identifies the local process that opened
  the connection, resolves its Windows account, and requires membership in the
  machine's **Administrators** group. A standard user with a session on the box
  (e.g. a non-admin DCV console user) gets 403. No password or prompt: an admin
  just opens the page. (Works for non-elevated admin browsers too.)

Tabs:

* **Settings** — edit every `settings.ini` value with validation. Changes are
  written and applied live (the service **hot-reloads** its configuration; it is
  not restarted); only changing the **Port** needs a service restart, since the
  listener is bound at startup. Next to **DCV server log path** the **Open** and
  **Open dir** buttons open the log file / its folder on the server's desktop. At
  the bottom is a **Recover: unlock all input** button that re-enables any local
  input devices left disabled by an interrupted session.
* **Sessions** — list, create, and close DCV sessions.
* **Services** — status of `DCVManagement` (this service) and `dcvserver` (DCV
  Server), with a **Restart** button for each. Only these two services can be
  controlled.
* **API** — reference documentation for every HTTP endpoint the service exposes.

## Automatic session creation (on-demand sessions)

DCV Server cannot create a console session on demand: if no session exists, a
user's connect attempt simply fails. This service closes that gap.

The log monitor tails `DcvLogPath` once per second. When it sees a user
authenticate while **no session exists**, it creates a session for that user.

1. User connects → **fails** (no session yet) — DCV logs
   `authenticator - Sending authentication result OK to <ip> for user <name> (0 sessions)`
2. The monitor matches that line and runs `dcv create-session --owner <name>`.
3. User connects **again → succeeds**.

So the first attempt always fails and the second one works. This matches the
behaviour of the old Python `dcv_session_monitor.py`.

The trigger line's wording varies between DCV versions and platforms, so the
regex is configurable via **`DcvLogTriggerPattern`** (it must contain exactly one
capture group: the username). The service logs `monitor: watching …` and
`monitor: trigger pattern set to …` at startup, and
`monitor: connect attempt with no session detected for user …` when it fires —
check `logs\dcvm.log` in the install folder if auto-creation seems inactive.

> **Note — DCV Session Manager agent.** If the DCV Session Manager agent is
> installed, DCV delegates authentication to it (`Using external token verifier:
> …` appears in the server log) and the `authenticator … (0 sessions)` line is
> never written, so auto-creation never triggers. Remove the agent, or adjust
> `DcvLogTriggerPattern` to a line your setup actually logs.

## Managing the service

```
sc query   DCVManagement
sc stop    DCVManagement
sc start   DCVManagement
```
Or use the admin console **Service** tab, or `services.msc`.

The binary can also manage itself:
```
dcvm.exe install     dcvm.exe start    dcvm.exe stop
dcvm.exe uninstall   dcvm.exe restart  dcvm.exe run   (foreground, for testing)
```

## Migrating from the old Python version

The legacy Python service uses the **same** service name (`DCVManagement`).
Before installing this MSI, remove the old install as Administrator:

```
scripts\uninstall-old-python.bat
```

What it does:

1. **Safety guard** — inspects the installed `DCVManagement` service and only
   proceeds if its binary points at the Python host (`pythonservice.exe` /
   `python.exe`). If the service is the new Go build it **aborts**, so it can
   never remove the Go service by mistake (to remove the Go build, use
   "Apps & features" / `msiexec /x`).
2. Stops and deletes the Python service.
3. Removes the `AppPath` machine variable and the old app directory from the
   machine `PATH` (added by the old `setup_environment.ps1`). `PythonPath` and
   the Python/DCV `PATH` entries are left alone — Python may be used elsewhere,
   and DCV is invoked by full path.
4. Deletes the old application directory (`C:\dcv-management-windows\`).

Then install the MSI. The script requires an elevated prompt (it checks and
exits otherwise). Its full removal path and the safety-guard abort have both
been verified on a live machine.
