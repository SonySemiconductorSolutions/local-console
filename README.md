# Local Console

An offline tool to interact with IMX500-equipped smart cameras and develop applications for them.

## Installation

### Windows

Download and run the Windows installer, which automatically handles all necessary dependencies.

### Linux

Make sure your system has installed:

* Python 3.10 (or higher) and pip
* [mosquitto](https://mosquitto.org/download)
* [flatc](https://github.com/google/flatbuffers/releases/tag/v24.3.25)
* xclip

Then, install Local Console with the following commands:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e local-console/
```

#### Mosquitto

By default, the mosquitto service runs on port 1883. You can check its status with:

```sh
systemctl status mosquitto.service
```

Make sure that its installation did not enable a running instance, by doing:

```sh
sudo systemctl disable mosquitto.service
sudo systemctl stop mosquitto.service
```

This action is only necessary once after installing the software.

## Usage

To display help information, use:

```sh
local-console --help
```

### Get Started

To run the Local Console GUI, use:

```sh
local-console gui
```

On start up, it spawns a MQTT broker instance listening on the configured port. Then a camera can connect to this broker, so that the GUI can provide access to camera actions such as image streaming.
