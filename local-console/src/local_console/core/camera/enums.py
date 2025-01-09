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
from enum import Enum
from pathlib import Path

from local_console.utils.enums import StrEnum


class StreamStatus(Enum):
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


class MQTTTopics(Enum):
    ATTRIBUTES = "v1/devices/me/attributes"
    TELEMETRY = "v1/devices/me/telemetry"
    ATTRIBUTES_REQ = "v1/devices/me/attributes/request/+"
    RPC_RESPONSES = "v1/devices/me/rpc/response/+"

    @classmethod
    def topic_matches_pattern(cls, topic: str, pattern: str) -> bool:
        topic_levels = topic.split("/")
        pattern_levels = pattern.split("/")

        if len(topic_levels) != len(pattern_levels):
            return False

        for topic_level, pattern_level in zip(topic_levels, pattern_levels):
            if pattern_level == "+":
                continue
            if topic_level != pattern_level:
                return False

        return True

    def matches(self, topic: str) -> bool:
        return self.topic_matches_pattern(topic, self.value)


class OTAUpdateStatus(StrEnum):
    DOWNLOADING = "Downloading"
    UPDATING = "Updating"
    REBOOTING = "Rebooting"
    DONE = "Done"
    FAILED = "Failed"


class ConnectionState(StrEnum):
    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"
    # PERIODIC = "Periodic"  # This is for v2


class OTAUpdateModule(StrEnum):
    APFW = "ApFw"
    SENSORFW = "SensorFw"
    DNNMODEL = "DnnModel"


class FirmwareExtension(StrEnum):
    APPLICATION_FW = ".bin"
    SENSOR_FW = ".fpk"
    ZIPPED_FW = ".zip"


class DeployStage(Enum):
    WaitFirstStatus = "WaitFirstStatus"
    WaitAppliedConfirmation = "WaitAppliedConfirmation"
    Done = "Done"
    Error = "Error"


class DeploymentType(Enum):
    Application = "Application"


class UnitScale(StrEnum):
    KB = "KB"
    MB = "MB"
    GB = "GB"


class ApplicationType(StrEnum):
    CLASSIFICATION = "classification"
    DETECTION = "detection"


class ApplicationConfiguration:
    FB_SCHEMA_PATH = Path(__file__).parent.parent / "assets/schemas"
    NAME = "node"
    CONFIG_TOPIC = "PPL_Parameters"
