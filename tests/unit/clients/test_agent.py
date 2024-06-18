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
import base64
import json
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis import strategies as st
from local_console.clients.agent import Agent
from local_console.core.camera import MQTTTopics
from local_console.core.schemas.schemas import AgentConfiguration
from local_console.core.schemas.schemas import OnWireProtocol
from paho.mqtt.client import MQTT_ERR_ERRNO
from paho.mqtt.client import MQTT_ERR_SUCCESS

from tests.strategies.configs import generate_agent_config
from tests.strategies.configs import generate_text


@given(
    generate_text(),
    generate_text(),
    generate_text(),
    generate_agent_config(),
    st.sampled_from(OnWireProtocol),
)
@pytest.mark.trio
async def test_configure_instance(
    instance_id: str,
    topic: str,
    config: str,
    agent_config: AgentConfiguration,
    onwire_schema: OnWireProtocol,
):
    with (
        patch("local_console.clients.agent.get_config", return_value=agent_config),
        patch(
            "local_console.clients.agent.OnWireProtocol.from_iot_spec",
            return_value=onwire_schema,
        ),
        patch("local_console.clients.agent.paho.Client"),
        patch("local_console.clients.agent.AsyncClient"),
        patch("local_console.clients.agent.Agent.publish"),
    ):
        agent = Agent()
        async with agent.mqtt_scope([]):
            await agent.configure(instance_id, topic, config)

        payload = json.dumps(
            {
                f"configuration/{instance_id}/{topic}": base64.b64encode(
                    config.encode("utf-8")
                ).decode("utf-8")
            }
        )
        agent.publish.assert_called_once_with(
            MQTTTopics.ATTRIBUTES.value, payload=payload
        )


@given(generate_text(), generate_agent_config(), st.sampled_from(OnWireProtocol))
@pytest.mark.trio
async def test_rpc(
    instance_id: str, agent_config: AgentConfiguration, onwire_schema: OnWireProtocol
):
    with (
        patch("local_console.clients.agent.get_config", return_value=agent_config),
        patch(
            "local_console.clients.agent.OnWireProtocol.from_iot_spec",
            return_value=onwire_schema,
        ),
        patch("local_console.clients.agent.paho.Client"),
        patch("local_console.clients.agent.AsyncClient"),
    ):
        method = "$agent/set"
        params = '{"log_enable": true}'
        agent = Agent()
        async with agent.mqtt_scope([]):
            agent.client.publish_and_wait = AsyncMock(
                return_value=(MQTT_ERR_SUCCESS, None)
            )
            await agent.rpc(instance_id, method, params)

        agent.client.publish_and_wait.assert_called_once()


@given(generate_text(), generate_agent_config(), st.sampled_from(OnWireProtocol))
@pytest.mark.trio
async def test_rpc_error(
    instance_id: str, agent_config: AgentConfiguration, onwire_schema: OnWireProtocol
):
    with (
        patch("local_console.clients.agent.get_config", return_value=agent_config),
        patch(
            "local_console.clients.agent.OnWireProtocol.from_iot_spec",
            return_value=onwire_schema,
        ),
        patch("local_console.clients.agent.paho.Client"),
        patch("local_console.clients.agent.AsyncClient"),
    ):
        method = "$agent/set"
        params = '{"log_enable": true}'
        agent = Agent()
        async with agent.mqtt_scope([]):
            agent.client.publish_and_wait = AsyncMock(
                return_value=(MQTT_ERR_ERRNO, None)
            )
            with pytest.raises(ConnectionError):
                await agent.rpc(instance_id, method, params)

        agent.client.publish_and_wait.assert_called_once()
