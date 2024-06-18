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
import sys
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from local_console.core.config import config_to_schema
from local_console.core.config import get_default_config

sys.modules["local_console.gui.driver"] = MagicMock()

from local_console.gui.controller.ai_model_screen import AIModelScreenController
from local_console.core.commands.ota_deploy import get_package_hash
from local_console.utils.local_network import get_my_ip_by_routing

# To allow other tests to load driver
del sys.modules["local_console.gui.driver"]


@pytest.fixture(params=["Done", "Failed"])
def update_status(request):
    return request.param


@pytest.fixture(params=["000001"])
def network_id(request):
    return request.param


def mock_get_config():
    return config_to_schema(get_default_config())


@pytest.fixture(autouse=True)
def fixture_get_config():
    with patch(
        "local_console.gui.controller.ai_model_screen.get_config",
        mock_get_config,
    ) as _fixture:
        yield _fixture


@pytest.mark.trio
async def test_undeploy_step_rpc_sent(network_id: str):
    mock_model = AsyncMock()
    mock_model.ota_event = AsyncMock()
    mock_driver = MagicMock()
    mock_agent = MagicMock()
    mock_agent.mqtt_scope.return_value = AsyncMock()
    mock_agent.configure = AsyncMock()
    with patch(
        "local_console.gui.controller.ai_model_screen.Agent", return_value=mock_agent
    ):
        mock_model.device_config.OTA.UpdateStatus = "Done"
        controller = AIModelScreenController(mock_model, mock_driver, MagicMock())
        await controller.undeploy_step(network_id)
        payload = (
            f'{{"OTA":{{"UpdateModule":"DnnModel","DeleteNetworkID":"{network_id}"}}}}'
        )
        mock_agent.configure.assert_called_once_with(
            "backdoor-EA_Main", "placeholder", payload
        )


@pytest.mark.trio
async def test_undeploy_step_not_deployed_model(update_status: str):
    mock_model = AsyncMock()
    mock_model.ota_event = AsyncMock()
    mock_driver = MagicMock()
    mock_agent = MagicMock()
    mock_agent.mqtt_scope.return_value = AsyncMock()
    mock_agent.configure = AsyncMock()
    with patch(
        "local_console.gui.controller.ai_model_screen.Agent", return_value=mock_agent
    ):
        mock_model.device_config.OTA.UpdateStatus = update_status
        controller = AIModelScreenController(mock_model, mock_driver, MagicMock())
        await controller.undeploy_step("000001")
        mock_model.ota_event.assert_not_awaited()


@pytest.mark.trio
async def test_deploy_step(tmp_path, network_id, update_status: str):
    filename = "dummy.bin"
    tmp_file = tmp_path / filename

    mock_model = AsyncMock()
    mock_model.ota_event = AsyncMock()
    mock_driver = MagicMock()
    mock_agent = MagicMock()
    mock_agent.mqtt_scope.return_value = AsyncMock()
    mock_agent.configure = AsyncMock()
    with (
        patch(
            "local_console.gui.controller.ai_model_screen.Agent",
            return_value=mock_agent,
        ),
        patch(
            "local_console.gui.controller.ai_model_screen.AsyncWebserver",
            return_value=mock_agent,
        ),
        patch(
            "local_console.gui.controller.ai_model_screen.get_network_ids",
            return_value=[network_id],
        ),
    ):
        mock_model.device_config.OTA.UpdateStatus = update_status
        controller = AIModelScreenController(mock_model, mock_driver, MagicMock())
        with open(tmp_file, "w") as f:
            f.write("dummy")
        await controller.deploy_step(network_id, tmp_file)
        hashvalue = get_package_hash(tmp_file)
        payload = (
            '{"OTA":{"UpdateModule":"DnnModel","DesiredVersion":"",'
            f'"PackageUri":"http://{get_my_ip_by_routing()}:8000/dummy.bin",'
            f'"HashValue":"{hashvalue}"'
            "}}"
        )
        mock_agent.configure.assert_called_once_with(
            "backdoor-EA_Main", "placeholder", payload
        )
        mock_model.ota_event.assert_not_awaited()
