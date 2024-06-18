# Windows install scripts

## Preparation of the executable installer

The executable installer now bundles the python wheel, which enhances reproducibility of installations across the various target environments. Hence, the wheel must be created as a prerequisite to compiling the installer with InnoSetup. Here are the steps, to be performed from the root of your clone of this git repository:

1. Prepare a python 3.11 virtual environment

```powershell
python -m venv buildenv
```

2. Install the `build` tool in that environment

```powershell
.\buildenv\Scripts\python.exe -m pip install build
```

3. Compile the wheel

```powershell
.\buildenv\Scripts\python.exe -m build --wheel --outdir . local-console/
```

You should have a new file named like `local_console-*.whl` in your repository clone's root.


4. Run InnoSetup, load `inno-setup.iss` onto it and build the installer. By default, it produces the installer under the `Output\` subfolder.

## Alternative management of the Local Console & GUI for Windows

Follow this procedure in case your Windows installation rejects the executable installer (e.g. Windows Defender throws a virus false-positive or unsigned installers are disallowed).

### Installing

Prior to starting, make sure you have either cloned the [local-console repository](https://github.com/midokura/local-console) or you have unpacked a source tarball into your machine. We shall refer to its location at `$local_console_repository_root`. Now, open a PowerShell window at that location and proceed with the steps below:

1. First, set the shell at the location of this README, and allow execution of the helper script for this step:
```powershell
> cd $local_console_repository_root\local-console\windows
> Unblock-File -Path .\install.ps1
```

2. Then, enable executing local scripts only for the current shell. You may be asked to confirm the action.
```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

Execution Policy Change
The execution policy helps protect you from scripts that you do not trust. Changing the execution policy might expose
you to the security risks described in the about_Execution_Policies help topic at
https:/go.microsoft.com/fwlink/?LinkID=135170. Do you want to change the execution policy?
[Y] Yes  [A] Yes to All  [N] No  [L] No to All  [S] Suspend  [?] Help (default is "N"): Y
```

2. Execute the installer script. It will download all prerequisites, install them, and then install the CLI+GUI from the repository root.
```powershell
> .\install.ps1

> .\install.ps1
[2024-04-02 09:31:58] Downloading installer for the Mosquitto MQTT broker...
[2024-04-02 09:32:00] Installing the Mosquitto MQTT broker...
[2024-04-02 09:32:04] Mosquitto installation complete.
[2024-04-02 09:32:04] Found Windows Service for Mosquitto. Preparing to remove...
DisplayName: Mosquitto Broker
Status: Stopped
ServiceName: mosquitto
StartType: Automatic
Removing the Mosquitto service...
[SC] DeleteService SUCCESS
[2024-04-02 09:32:04] Mosquitto service removed successfully.
[2024-04-02 09:32:04] Downloading Git installer...
[2024-04-02 09:34:14] Installing Git...
[2024-04-02 09:35:25] Git installation complete.
[2024-04-02 09:35:25] Python is not installed.
[2024-04-02 09:35:25] Downloading installer for Python 3.11...
[2024-04-02 09:36:11] Installing Python 3.11...
[2024-04-02 09:36:55] Python 3.11 installation complete.
[2024-04-02 09:36:55] Directory created successfully: C:\Users\User\AppData\Roaming\LocalConsole
Virtual environment will be created in C:\Users\User\AppData\Roaming\LocalConsole\virtualenv
Virtual environment created.
Requirement already satisfied: pip in c:\users\user\appdata\roaming\localconsole\virtualenv\lib\site-packages (24.0)
Processing z:\local-console
  Installing build dependencies ... done
  Getting requirements to build wheel ... done
  Preparing metadata (pyproject.toml) ... done
  ...
  ...
Successfully built local-console paho-mqtt kivymd
Installing collected packages: types-retry...
Successfully installed Kivy-2.3.0 ... local-console-1.7.0 ...
[2024-04-02 09:38:47] Local Console has been installed.
[2024-04-02 09:38:47] Virtual environment has been updated.
[2024-04-02 09:38:50] Flatc Zipball downloaded.
[2024-04-02 09:38:51] Flatc Executable unpacked into C:\Users\User\AppData\Roaming\LocalConsole\virtualenv\Scripts
Created desktop shortcut at: C:\Users\User\Desktop\Local Console.lnk
```

3. The script created a shortcut icon at your Windows desktop. Please click on it, and if asked allow network connections through the Windows firewall. You are now ready to use the GUI.

### Uninstalling

Just repeat the same procedure as above, but targeting the `uninstall.ps1` script instead of `install.ps1`. The script will remove the desktop shortcut and all files within your user's `%APPDATA%` folder. System dependencies such as Git, Mosquitto and Python 3.11 will remain installed. Should you want to remove them, you'll need to do so manually.
