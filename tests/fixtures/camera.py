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
from contextlib import asynccontextmanager

import pytest
import trio
from local_console.core.camera.state import CameraState
from local_console.core.schemas.edge_cloud_if_v1 import DeviceConfiguration
from local_console.core.schemas.schemas import OnWireProtocol
from local_console.utils.tracking import TrackingVariable


@pytest.fixture
async def cs_init():
    send_channel, _ = trio.open_memory_channel(0)
    camera_state = CameraState(send_channel, trio.lowlevel.current_trio_token())
    camera_state.mqtt_port.value = 1883

    yield camera_state


@asynccontextmanager
async def cs_init_context(
    mqtt_host: str = "localhost",
    mqtt_port: int = 1883,
    device_config: DeviceConfiguration | None = None,
):
    # For using within Hypothesis-driven tests
    send_channel, _ = trio.open_memory_channel(0)
    camera_state = CameraState(send_channel, trio.lowlevel.current_trio_token())
    camera_state.mqtt_host = TrackingVariable(mqtt_host)
    camera_state.mqtt_port = TrackingVariable(mqtt_port)
    camera_state._onwire_schema = OnWireProtocol.EVP1
    if device_config:
        camera_state.device_config = TrackingVariable(device_config)

    yield camera_state
