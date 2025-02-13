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
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import trio
from local_console.core.schemas.schemas import OnWireProtocol
from local_console.servers.broker import BrokerException

from tests.fixtures.agent import mocked_agent
from tests.fixtures.camera import cs_init


@pytest.mark.trio
async def test_process_incoming_telemetry(cs_init) -> None:
    with patch("local_console.core.camera.mixin_mqtt.datetime") as mock_time:
        camera = cs_init

        mock_now = Mock()
        mock_time.now.return_value = mock_now

        dummy_telemetry = {"a": "b"}
        await camera.process_incoming("v1/devices/me/telemetry", dummy_telemetry)

        assert camera._last_reception == mock_now


@pytest.mark.trio
async def test_streaming_rpc_stop(cs_init, nursery):

    async def mock_mqtt_setup(*args, task_status=trio.TASK_STATUS_IGNORED):
        task_status.started(True)

    with (
        mocked_agent() as mock_agent,
        patch(
            "local_console.core.camera.state.CameraState.startup", new=mock_mqtt_setup
        ),
        patch.object(cs_init, "startup", new=AsyncMock()),
    ):
        mock_agent.publish = AsyncMock()
        mock_rpc = AsyncMock()
        mock_agent.rpc = mock_rpc

        camera_state = cs_init
        camera_state.mqtt_client = mock_agent

        await camera_state.streaming_rpc_stop()
        mock_rpc.assert_awaited_with(
            "backdoor-EA_Main", "StopUploadInferenceData", "{}"
        )


@pytest.mark.trio
async def test_broker_port_already_open(cs_init) -> None:
    from local_console.core.camera.mixin_mqtt import MQTTMixin

    mixin = MQTTMixin()
    mixin.mqtt_host.value = "localhost"
    mixin.mqtt_port.value = 2000
    mixin._onwire_schema = OnWireProtocol.EVP1
    mock_channel = AsyncMock()
    mixin.message_send_channel = mock_channel

    with (
        patch("local_console.core.camera.mixin_mqtt.Agent"),
        patch(
            "local_console.core.camera.mixin_mqtt.spawn_broker",
            side_effect=BrokerException("Mosquitto already initialized"),
        ),
    ):
        await mixin.mqtt_setup()
