# Copyright 2024 Sony Semiconductor Solutions Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0
import enum
import json
import logging
from base64 import b64decode
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Optional

import qrcode
from local_console.core.schemas.edge_cloud_if_v1 import DeviceConfiguration
from local_console.core.schemas.schemas import OnWireProtocol
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class Camera:
    """
    This class is a live, read-only interface to most status
    information that the Camera Firmware reports.
    """

    EA_STATE_TOPIC = "state/backdoor-EA_Main/placeholder"
    SYSINFO_TOPIC = "systemInfo"
    DEPLOY_STATUS_TOPIC = "deploymentStatus"

    CONNECTION_STATUS_TIMEOUT = timedelta(seconds=180)

    def __init__(self) -> None:
        self.sensor_state = StreamStatus.Inactive
        self.app_state = ""
        self.deploy_status: dict[str, str] = {}
        self.device_config: DeviceConfiguration | None = None
        self.onwire_schema: Optional[OnWireProtocol] = None
        self.attributes_available = False
        self._last_reception: Optional[datetime] = None
        self._is_new_device_config = False

    @property
    def is_ready(self) -> bool:
        # Attributes report interval cannot be controlled in EVP1
        return (
            self.onwire_schema is not OnWireProtocol.EVP1 and self.attributes_available
        )

    @property
    def connected(self) -> bool:
        if self._last_reception is None:
            return False
        else:
            return (
                datetime.now() - self._last_reception
            ) < self.CONNECTION_STATUS_TIMEOUT

    @property
    def is_new_device_config(self) -> bool:
        """
        Property indicating whether there's a new device configuration since the last check.

        This property toggles a boolean flag each time it's accessed.
        It returns True if a new device configuration has been detected
        since the last time this property was accessed, otherwise False.
        """
        self._is_new_device_config = not self._is_new_device_config
        return not self._is_new_device_config

    @property
    def is_streaming(self) -> bool:
        return self.sensor_state == StreamStatus.Active

    def process_incoming(self, topic: str, payload: dict[str, Any]) -> None:
        sent_from_camera = False
        if topic == MQTTTopics.ATTRIBUTES.value:
            if self.EA_STATE_TOPIC in payload:
                sent_from_camera = True
                self.process_state_topic(payload)

            if self.SYSINFO_TOPIC in payload:
                sent_from_camera = True
                self.process_sysinfo_topic(payload)

            if self.DEPLOY_STATUS_TOPIC in payload:
                sent_from_camera = True
                self.process_deploy_status_topic(payload)

        if topic == MQTTTopics.TELEMETRY.value:
            sent_from_camera = True

        if sent_from_camera:
            self._last_reception = datetime.now()
            logger.debug("Incoming on %s: %s", topic, str(payload))

    def process_state_topic(self, payload: dict[str, Any]) -> None:
        firmware_is_supported = False
        try:
            decoded = json.loads(b64decode(payload[self.EA_STATE_TOPIC]))
            firmware_is_supported = True
        except UnicodeDecodeError:
            decoded = json.loads(payload[self.EA_STATE_TOPIC])

        if firmware_is_supported:
            try:
                self.device_config = DeviceConfiguration.model_validate(decoded)
                self.sensor_state = StreamStatus.from_string(
                    self.device_config.Status.Sensor
                )
                self._is_new_device_config = True
            except ValidationError as e:
                logger.warning(f"Error while validating device configuration: {e}")

    def process_sysinfo_topic(self, payload: dict[str, Any]) -> None:
        sys_info = payload[self.SYSINFO_TOPIC]
        if "protocolVersion" in sys_info:
            self.onwire_schema = OnWireProtocol(sys_info["protocolVersion"])
        self.attributes_available = True

    def process_deploy_status_topic(self, payload: dict[str, Any]) -> None:
        if self.onwire_schema == OnWireProtocol.EVP1 or self.onwire_schema is None:
            self.deploy_status = json.loads(payload[self.DEPLOY_STATUS_TOPIC])
        else:
            self.deploy_status = payload[self.DEPLOY_STATUS_TOPIC]
        self.attributes_available = True


class StreamStatus(enum.Enum):
    # Camera states:
    # https://github.com/SonySemiconductorSolutions/EdgeAIPF.smartcamera.type3.mirror/blob/vD7.00.F6/src/edge_agent/edge_agent_config_state_private.h#L309-L314
    Inactive = "Inactive"
    Active = "Active"
    Transitioning = (
        "..."  # Not a CamFW state. Used to describe transition in Local Console.
    )

    @classmethod
    def from_string(cls, value: str) -> "StreamStatus":
        if value in ("Standby", "Error", "PowerOff"):
            return cls.Inactive
        elif value == "Streaming":
            return cls.Active
        return cls.Transitioning


class MQTTTopics(enum.Enum):
    ATTRIBUTES = "v1/devices/me/attributes"
    TELEMETRY = "v1/devices/me/telemetry"
    ATTRIBUTES_REQ = "v1/devices/me/attributes/request/+"
    RPC_RESPONSES = "v1/devices/me/rpc/response/+"


def get_qr_object(
    mqtt_host: str,
    mqtt_port: Optional[int],
    tls_enabled: bool,
    ntp_server: str,
    ip_address: str = "",
    subnet_mask: str = "",
    gateway: str = "",
    dns_server: str = "",
    wifi_ssid: str = "",
    wifi_password: str = "",
    border: int = 5,
) -> qrcode.main.QRCode:
    """
    This function generates the QR code object that encodes the connection
    settings for a camera device.

    :param mqtt_host:   Address of MQTT broker host
    :param mqtt_port:   TCP port on which the MQTT broker is listening
    :param tls_enabled: Is TLS enabled?
    :param ntp_server:  NTP server for the camera to get its time synced
    :param ip_address:  Static IP address of the camera device
    :param subnet_mask: Address of Subnet Mask
    :param gateway:     Address of Gateway
    :param dns_server:  Address of DNS server
    :param wifi_ssid:   Wireless LAN router SSID
    :param wifi_password: Wireless LAN router connection password
    :param border:      size of padding around the QR code
    :return: the QR object containing the code for the camera
    """

    # Minimum border is 4 according to the specs
    border = 4 if border < 4 else border

    # This verbosity is to blame between types-qrcode and mypy
    # It should be instead: qr_code = qrcode.QRCode(...
    qr_code: qrcode.main.QRCode = qrcode.main.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        border=border,
    )
    qr_code.add_data(
        qr_string(
            mqtt_host,
            mqtt_port,
            tls_enabled,
            ntp_server,
            ip_address,
            subnet_mask,
            gateway,
            dns_server,
            wifi_ssid,
            wifi_password,
        )
    )
    qr_code.make(fit=True)

    return qr_code


def qr_string(
    mqtt_host: str,
    mqtt_port: Optional[int],
    tls_enabled: bool,
    ntp_server: str,
    ip_address: str = "",
    subnet_mask: str = "",
    gateway: str = "",
    dns_server: str = "",
    wifi_ssid: str = "",
    wifi_password: str = "",
) -> str:
    # Followed the order of the Setup Enrollment on the Console.
    tls_flag = 0 if tls_enabled else 1
    output = f"AAIAAAAAAAAAAAAAAAAAAA==N=11;E={mqtt_host};H={mqtt_port};t={tls_flag}"
    if wifi_ssid:
        output += f";S={wifi_ssid}"
    if wifi_password:
        output += f";P={wifi_password}"
    if ip_address:
        output += f";I={ip_address}"
    if subnet_mask:
        output += f";K={subnet_mask}"
    if gateway:
        output += f";G={gateway}"
    if dns_server:
        output += f";D={dns_server}"
    output += f";T={ntp_server};U1FS"
    return output
