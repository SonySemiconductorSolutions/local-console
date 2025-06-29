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
import logging
import socket
from socket import AddressFamily
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from local_console.utils.local_network import get_network_ifaces
from local_console.utils.local_network import is_localhost
from local_console.utils.local_network import is_port_open
from psutil._common import snicaddr
from psutil._common import snicstats

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_psutil():
    mock = MagicMock()
    with patch("local_console.utils.local_network.psutil", mock):
        mock.net_if_stats.return_value = {
            "enp5s2": snicstats(True, 2, 0, 0, "up,broadcast,running,multicast")
        }
        mock.net_if_addrs.return_value = {
            "enp5s2": [
                snicaddr(
                    AddressFamily.AF_INET,
                    "192.168.1.123",
                    "255.255.255.0",
                    "192.168.1.255",
                    None,
                )
            ]
        }
        yield mock


def test_detect_interfaces():
    interfaces = get_network_ifaces()

    assert "lo" not in interfaces
    assert all("docker" not in iface for iface in interfaces)
    assert all("ppp" not in iface for iface in interfaces)


def test_is_localhost(mock_psutil):
    assert is_localhost("localhost")
    assert is_localhost("127.0.0.1")


@pytest.mark.parametrize(
    "exception",
    [
        socket.gaierror("Internal library error"),
        UnicodeError("Character 'ƃ' is invalid"),
        Exception("We are really failing in a way we did not forseen"),
    ],
)
def test_is_localhost_fail(exception: Exception):
    with patch(
        "socket.gethostbyname",
        side_effect=exception,
    ):
        assert not is_localhost("hostname")


@patch("socket.gethostbyname")
def test_is_localhost_raise_exception(mock_gethostbyname):
    mocked_error = KeyboardInterrupt("User ask for stop")
    mock_gethostbyname.side_effect = mocked_error
    with pytest.raises(KeyboardInterrupt) as raised:
        is_localhost("hostname")

    assert raised.value is mocked_error


def test_is_open_port():

    # Test when the port is already in use
    with patch("socket.socket.connect") as mock_connect:
        mock_connect.return_value = None
        in_use = is_port_open(9999)
        assert in_use
        mock_connect.assert_called_once_with(("localhost", 9999))

    with patch("socket.socket.connect") as mock_connect:
        mock_connect.side_effect = OSError()
        in_use = is_port_open(9999)
        assert not in_use
        mock_connect.assert_called_once_with(("localhost", 9999))
