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
from unittest.mock import patch

from hypothesis import given
from local_console.commands.rpc import app
from local_console.core.schemas.schemas import AgentConfiguration
from typer.testing import CliRunner

from tests.strategies.configs import generate_agent_config
from tests.strategies.configs import generate_text

runner = CliRunner()


@given(
    generate_text(),
    generate_text(),
    generate_text(),
    generate_agent_config(),
)
def test_rpc_command(
    instance_id: str, method: str, params: str, agent_config: AgentConfiguration
):
    with (
        patch("local_console.commands.rpc.Agent"),
        patch("local_console.commands.rpc.rpc_task") as mock_rpc,
        patch("local_console.commands.rpc.Agent.get_config", return_value=agent_config),
    ):
        result = runner.invoke(app, [instance_id, method, params])
        mock_rpc.assert_called_with(instance_id, method, params)
        assert result.exit_code == 0


@given(
    generate_text(),
    generate_text(),
    generate_text(),
    generate_agent_config(),
)
def test_rpc_command_exception(
    instance_id: str, method: str, params: str, agent_config: AgentConfiguration
):
    with (
        patch("local_console.commands.rpc.Agent") as mock_agent,
        patch("local_console.commands.rpc.Agent.mqtt_scope") as mock_mqtt,
        patch("local_console.commands.rpc.Agent.get_config", return_value=agent_config),
    ):
        mock_mqtt.side_effect = ConnectionError
        result = runner.invoke(app, [instance_id, method, params])
        mock_agent.assert_called()
        assert result.exit_code == 1
