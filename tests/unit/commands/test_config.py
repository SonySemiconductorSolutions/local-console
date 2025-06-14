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
import json
from unittest.mock import AsyncMock
from unittest.mock import patch

from hypothesis import given
from hypothesis import strategies as st
from local_console.commands.config import app
from local_console.core.config import Config
from local_console.core.config import ConfigError
from local_console.core.enums import GetCommands
from local_console.core.schemas.schemas import DesiredDeviceConfig
from local_console.core.schemas.schemas import DeviceConnection
from local_console.core.schemas.schemas import GlobalConfiguration
from local_console.core.schemas.schemas import OnWireProtocol
from typer.testing import CliRunner

from tests.strategies.configs import generate_identifiers


runner = CliRunner()


def test_config_setget_command():
    result = runner.invoke(app, [GetCommands.GET.value])
    assert GlobalConfiguration(**json.loads(result.stdout)) == Config().get_config()


def test_get_active_device_has_been_removed():
    result = runner.invoke(app, [GetCommands.GET.value, "active_device"])

    assert result.exit_code == 1


def test_set_active_device_has_been_removed():
    result = runner.invoke(app, [GetCommands.SET.value, "active_device", "Another"])

    assert result.exit_code == 1


def test_config_set_command_active_device_none():
    result = runner.invoke(app, [GetCommands.SET.value, "active_device"])

    assert result.exit_code == 2

    assert "Usage" in result.output


def test_config_setget_command_devices(single_device_config):
    config_obj = Config()
    result = runner.invoke(app, [GetCommands.GET.value, "devices"])
    assert (
        DeviceConnection(**json.loads(result.stdout)[0])
        == config_obj.get_config().devices[0]
    )

    runner.invoke(
        app,
        [GetCommands.SET.value, "--device", "dev_0", "mqtt.host", "192.168.1.1"],
    )
    result = runner.invoke(app, [GetCommands.GET.value, "devices"])
    assert (
        DeviceConnection(**json.loads(result.stdout)[0])
        == config_obj.get_config().devices[0]
    )
    assert config_obj.get_config().devices[0].mqtt.host == "192.168.1.1"


@given(
    generate_identifiers(max_size=5),
    generate_identifiers(max_size=5),
    generate_identifiers(max_size=5),
    st.one_of(st.none(), st.just("1883")),  # assumes 1883 is present by default
)
def test_config_instance_command(
    instance_id: str, method: str, params: str, port: str | None
):
    with (
        patch("local_console.commands.config.Agent"),
        patch("local_console.commands.config.configure_task") as mock_configure,
    ):
        args = [instance_id, method, params]
        if port is not None:
            args = ["--port", port] + args
        result = runner.invoke(app, ["instance"] + args)
        mock_configure.assert_called_with(
            instance_id, method, params, int(port) if port else None
        )
        assert result.exit_code == 0


@given(
    generate_identifiers(max_size=5),
    generate_identifiers(max_size=5),
    generate_identifiers(max_size=5),
)
def test_config_instance_command_exception(instance_id: str, method: str, params: str):
    with (
        patch("local_console.commands.config.Agent") as mock_agent,
        patch("local_console.commands.config.Agent.mqtt_scope") as mock_mqtt,
    ):
        mock_mqtt.side_effect = ConnectionError
        result = runner.invoke(app, ["instance", instance_id, method, params])
        mock_agent.assert_called()
        assert result.exit_code == 1


@given(st.integers(min_value=0, max_value=300), st.integers(min_value=0, max_value=300))
def test_config_device_command(interval_max: int, interval_min: int):
    with (
        patch("local_console.commands.config.Agent") as mock_agent,
        # patch("local_console.commands.config.Agent.determine_onwire_schema", return_value=),
        patch(
            "local_console.commands.config.config_device_task", return_value=0
        ) as mock_configure,
    ):
        mock_agent.determine_onwire_schema = AsyncMock(return_value=OnWireProtocol.EVP2)
        result = runner.invoke(app, ["device", f"{interval_max}", f"{interval_min}"])
        desired_device_config = DesiredDeviceConfig(
            reportStatusIntervalMax=interval_max, reportStatusIntervalMin=interval_min
        )
        mock_configure.assert_awaited_with(
            desired_device_config, Config().get_first_device_config()
        )
        assert result.exit_code == 0


@given(
    st.integers(min_value=-100, max_value=-1), st.integers(min_value=-100, max_value=-1)
)
def test_config_device_command_invalid_range(interval_max: int, interval_min: int):
    with (patch("local_console.commands.config.config_device_task") as mock_configure,):
        result = runner.invoke(app, ["device", interval_max, interval_min])
        mock_configure.assert_not_awaited()
        assert result.exit_code == 1


def test_config_unknown_device(caplog):
    config_obj = Config()
    with patch.object(config_obj, "get_device_config_by_name", side_effect=ConfigError):
        result = runner.invoke(
            app,
            [GetCommands.GET.value, "--device", "Unknown"],
        )
        assert result.exit_code == 1
        assert "Configuration error" in caplog.text
