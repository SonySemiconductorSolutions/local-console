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

import hypothesis.strategies as st
from hypothesis import given
from local_console.commands.qr import app
from local_console.core.schemas.schemas import AgentConfiguration
from typer.testing import CliRunner

from tests.strategies.configs import generate_agent_config
from tests.strategies.configs import generate_valid_ip
from tests.strategies.configs import generate_valid_port_number

runner = CliRunner()


@given(generate_agent_config())
def test_qr_with_defaults(config: AgentConfiguration) -> None:
    with (
        patch("local_console.commands.qr.get_config", return_value=config),
        patch("local_console.commands.qr.is_localhost", return_value=False),
        patch("local_console.commands.qr.get_my_ip_by_routing", return_value="1.2.3.4"),
        patch("local_console.core.camera.qr_string", return_value="") as mock_qr_string,
    ):
        result = runner.invoke(app, [])
        assert result.exit_code == 0

        mock_qr_string.assert_called_once_with(
            config.mqtt.host.ip_value,
            config.mqtt.port,
            config.is_tls_enabled,
            "pool.ntp.org",
            "",
            "",
            "",
            "",
            "",
            "",
        )


@given(
    generate_agent_config(),
    generate_valid_ip(),
    generate_valid_port_number(),
    st.booleans(),
    generate_valid_ip(),
)
def test_qr_with_overrides(
    config: AgentConfiguration,
    host_override: str,
    port_override: int,
    tls_enable_override: bool,
    ntp_override: str,
) -> None:
    with (
        patch("local_console.commands.qr.get_config", return_value=config),
        patch("local_console.commands.qr.is_localhost", return_value=False),
        patch("local_console.commands.qr.get_my_ip_by_routing", return_value="1.2.3.4"),
        patch("local_console.core.camera.qr_string", return_value="") as mock_qr_string,
    ):
        result = runner.invoke(
            app,
            [
                "--host",
                host_override,
                "--port",
                port_override,
                f"--{'' if tls_enable_override else 'no-'}enable-tls",
                "--ntp-server",
                ntp_override,
            ],
        )
        assert result.exit_code == 0

        mock_qr_string.assert_called_once_with(
            host_override,
            port_override,
            tls_enable_override,
            ntp_override,
            "",
            "",
            "",
            "",
            "",
            "",
        )


@given(generate_agent_config(), generate_valid_ip())
def test_qr_for_local_host(config: AgentConfiguration, local_host_alias: str) -> None:
    """
    This test showcases how the command will generate the QR with the host set to the
    IP address that a camera could use over the local network, when the specified host
    is determined to match localhost.
    """
    with (
        patch("local_console.commands.qr.get_config", return_value=config),
        patch("local_console.commands.qr.is_localhost", return_value=True),
        patch("local_console.commands.qr.get_my_ip_by_routing", return_value="1.2.3.4"),
        patch("local_console.core.camera.qr_string", return_value="") as mock_qr_string,
    ):
        result = runner.invoke(app, ["--host", local_host_alias])
        assert result.exit_code == 0

        mock_qr_string.assert_called_once_with(
            "1.2.3.4",
            config.mqtt.port,
            config.is_tls_enabled,
            "pool.ntp.org",
            "",
            "",
            "",
            "",
            "",
            "",
        )
