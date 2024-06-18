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
from datetime import timedelta
from unittest.mock import ANY
from unittest.mock import AsyncMock
from unittest.mock import patch

import hypothesis.strategies as st
import pytest
from hypothesis import given
from hypothesis import settings
from local_console.clients.agent import Agent
from local_console.clients.agent import check_attributes_request
from local_console.commands.deploy import app
from local_console.core.camera import MQTTTopics
from local_console.core.commands.deploy import get_empty_deployment
from local_console.core.enums import Target
from local_console.core.schemas.schemas import AgentConfiguration
from local_console.core.schemas.schemas import DeploymentManifest
from local_console.core.schemas.schemas import OnWireProtocol
from typer.testing import CliRunner

from tests.strategies.configs import generate_agent_config
from tests.strategies.deployment import deployment_manifest_strategy

runner = CliRunner()


def test_get_empty_deployment():
    empty = get_empty_deployment()
    assert len(empty.deployment.modules) == 0
    assert len(empty.deployment.instanceSpecs) == 0
    assert len(empty.deployment.deploymentId) != 0


@given(generate_agent_config())
def test_deploy_empty_command(agent_config: AgentConfiguration) -> None:
    with (
        patch("local_console.commands.deploy.Agent") as mock_agent_client,
        patch(
            "local_console.commands.deploy.get_empty_deployment"
        ) as mock_get_deployment,
        patch("local_console.commands.deploy.get_config", return_value=agent_config),
        patch("local_console.commands.deploy.is_localhost", return_value=True),
        patch("local_console.commands.deploy.exec_deployment") as mock_exec_deploy,
    ):
        result = runner.invoke(app, ["-e"])
        mock_agent_client.assert_called_once()
        mock_get_deployment.assert_called_once()
        mock_exec_deploy.assert_called_once_with(
            mock_agent_client(), mock_get_deployment.return_value, True, ANY, ANY, ANY
        )
        assert result.exit_code == 0


@given(deployment_manifest_strategy(), st.sampled_from(Target), generate_agent_config())
def test_deploy_command_target(
    deployment_manifest: DeploymentManifest,
    target: Target,
    agent_config: AgentConfiguration,
) -> None:
    with (
        patch("local_console.commands.deploy.Agent") as mock_agent_client,
        patch("local_console.commands.deploy.get_config", return_value=agent_config),
        patch("local_console.commands.deploy.is_localhost", return_value=True),
        patch("local_console.commands.deploy.exec_deployment") as mock_exec_deploy,
        patch(
            "local_console.commands.deploy.update_deployment_manifest"
        ) as mock_update_manifest,
        patch(
            "local_console.commands.deploy.make_unique_module_ids"
        ) as mock_make_unique_ids,
        patch(
            "local_console.commands.deploy.get_deployment_schema",
            return_value=deployment_manifest,
        ) as mock_get_deployment,
        patch("pathlib.Path.is_dir") as mock_check_dir,
    ):
        result = runner.invoke(app, [target.value])
        mock_agent_client.assert_called_once()
        mock_check_dir.assert_called_once()
        mock_get_deployment.assert_called_once()
        mock_update_manifest.assert_called_once_with(
            deployment_manifest,
            ANY,
            ANY,
            ANY,
            target,
            False,
        )
        mock_make_unique_ids.assert_called_once()
        mock_exec_deploy.assert_called_once_with(
            mock_agent_client(), deployment_manifest, ANY, ANY, ANY, ANY
        )
        assert result.exit_code == 0


@settings(deadline=timedelta(seconds=10))
@given(deployment_manifest_strategy(), generate_agent_config())
def test_deploy_command_signed(
    deployment_manifest: DeploymentManifest, agent_config: AgentConfiguration
) -> None:
    with (
        patch("local_console.commands.deploy.Agent") as mock_agent_client,
        patch("local_console.commands.deploy.get_config", return_value=agent_config),
        patch("local_console.commands.deploy.is_localhost", return_value=True),
        patch("local_console.commands.deploy.exec_deployment") as mock_exec_deploy,
        patch(
            "local_console.commands.deploy.update_deployment_manifest"
        ) as mock_update_manifest,
        patch(
            "local_console.commands.deploy.make_unique_module_ids"
        ) as mock_make_unique_ids,
        patch(
            "local_console.commands.deploy.get_deployment_schema",
            return_value=deployment_manifest,
        ) as mock_get_deployment,
        patch("pathlib.Path.is_dir") as mock_check_dir,
    ):
        result = runner.invoke(app, ["-s"])
        mock_agent_client.assert_called_once()
        mock_check_dir.assert_called_once()
        mock_get_deployment.assert_called_once()
        mock_update_manifest.assert_called_once_with(
            deployment_manifest,
            ANY,
            ANY,
            ANY,
            ANY,
            True,
        )
        mock_make_unique_ids.assert_called_once()
        mock_exec_deploy.assert_called_once_with(
            mock_agent_client(), deployment_manifest, ANY, ANY, ANY, ANY
        )
        assert result.exit_code == 0


@given(deployment_manifest_strategy(), generate_agent_config())
def test_deploy_command_timeout(
    deployment_manifest: DeploymentManifest,
    agent_config: AgentConfiguration,
) -> None:
    # TODO: improve timeout management
    timeout = 6
    with (
        patch("local_console.commands.deploy.Agent") as mock_agent_client,
        patch("local_console.commands.deploy.get_config", return_value=agent_config),
        patch("local_console.commands.deploy.is_localhost", return_value=True),
        patch("local_console.commands.deploy.exec_deployment") as mock_exec_deploy,
        patch(
            "local_console.commands.deploy.update_deployment_manifest"
        ) as mock_update_manifest,
        patch(
            "local_console.commands.deploy.make_unique_module_ids"
        ) as mock_make_unique_ids,
        patch(
            "local_console.commands.deploy.get_deployment_schema",
            return_value=deployment_manifest,
        ) as mock_get_deployment,
        patch("pathlib.Path.is_dir") as mock_check_dir,
    ):
        result = runner.invoke(app, ["-t", timeout])
        mock_agent_client.assert_called_once()
        mock_check_dir.assert_called_once()
        mock_get_deployment.assert_called_once()
        mock_update_manifest.assert_called_once_with(
            deployment_manifest,
            ANY,
            ANY,
            ANY,
            None,
            False,
        )
        mock_make_unique_ids.assert_called_once()
        mock_exec_deploy.assert_called_once_with(
            mock_agent_client(), deployment_manifest, ANY, ANY, ANY, timeout
        )
        assert result.exit_code == 0


@given(
    st.booleans(),
    st.integers(),
    st.sampled_from(Target),
    generate_agent_config(),
)
def test_deploy_manifest_no_bin(
    signed: bool,
    timeout: int,
    target: Target,
    agent_config: AgentConfiguration,
):
    with (
        patch("local_console.commands.deploy.is_localhost", return_value=True),
        patch("local_console.commands.deploy.Agent") as mock_agent_client,
        patch("local_console.commands.deploy.get_config", return_value=agent_config),
        patch(
            "local_console.commands.deploy.Path.is_dir", return_value=False
        ) as mock_is_dir,
    ):
        result = runner.invoke(
            app, ["-t", timeout, *(["-s"] if signed else []), target.value]
        )
        assert result.exit_code != 0
        mock_agent_client.assert_called_once()
        mock_is_dir.assert_called_once()


@given(
    st.integers(min_value=1), generate_agent_config(), st.sampled_from(OnWireProtocol)
)
@pytest.mark.trio
async def test_attributes_request_handling(
    mqtt_req_id: int,
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
    ):
        request_topic = MQTTTopics.ATTRIBUTES_REQ.value.replace("+", str(mqtt_req_id))

        agent = Agent()
        agent.publish = AsyncMock()
        async with agent.mqtt_scope([MQTTTopics.ATTRIBUTES_REQ.value]):
            check = await check_attributes_request(agent, request_topic, "{}")

        response_topic = request_topic.replace("request", "response")
        agent.publish.assert_called_once_with(response_topic, "{}")
        assert check


@given(deployment_manifest_strategy(), generate_agent_config())
def test_deploy_forced_webserver(
    deployment_manifest: DeploymentManifest, agent_config: AgentConfiguration
) -> None:
    with (
        patch("local_console.commands.deploy.Agent") as mock_agent_client,
        patch("local_console.commands.deploy.get_config", return_value=agent_config),
        patch("local_console.commands.deploy.is_localhost", return_value=False),
        patch("local_console.commands.deploy.exec_deployment") as mock_exec_deploy,
        patch(
            "local_console.commands.deploy.update_deployment_manifest"
        ) as mock_update_manifest,
        patch(
            "local_console.commands.deploy.make_unique_module_ids"
        ) as mock_make_unique_ids,
        patch(
            "local_console.commands.deploy.get_deployment_schema",
            return_value=deployment_manifest,
        ) as mock_get_deployment,
        patch("pathlib.Path.is_dir") as mock_check_dir,
    ):
        result = runner.invoke(app, ["-f"])
        mock_agent_client.assert_called_once()
        mock_check_dir.assert_called_once()
        mock_get_deployment.assert_called_once()
        mock_update_manifest.assert_called_once_with(
            deployment_manifest,
            ANY,
            ANY,
            ANY,
            ANY,
            False,
        )
        mock_make_unique_ids.assert_called_once()
        mock_exec_deploy.assert_called_once_with(
            mock_agent_client(), deployment_manifest, True, ANY, ANY, ANY
        )
        assert result.exit_code == 0
