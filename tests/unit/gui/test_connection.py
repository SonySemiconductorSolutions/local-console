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
from contextlib import contextmanager
from unittest.mock import MagicMock
from unittest.mock import patch

import hypothesis.strategies as st
from hypothesis import given
from local_console.core.config import config_to_schema
from local_console.core.config import get_default_config
from local_console.gui.controller.connection_screen import ConnectionScreenController
from local_console.gui.model.connection_screen import ConnectionScreenModel
from local_console.gui.utils.observer import Observer
from pytest import fixture
from pytest import mark

from tests.strategies.configs import generate_invalid_hostname_long
from tests.strategies.configs import generate_invalid_ip
from tests.strategies.configs import generate_invalid_ip_long
from tests.strategies.configs import generate_invalid_port_number
from tests.strategies.configs import generate_random_characters
from tests.strategies.configs import generate_valid_ip
from tests.strategies.configs import generate_valid_ip_strict
from tests.strategies.configs import generate_valid_port_number


def mock_get_config():
    return config_to_schema(get_default_config())


@fixture(autouse=True)
def fixture_get_config():
    with patch(
        "local_console.gui.model.connection_screen.get_config",
        mock_get_config,
    ) as _fixture:
        yield _fixture


class ModelObserver(Observer):
    def __init__(self):
        self.is_called = False

    def model_is_changed(self) -> None:
        self.is_called = True


@contextmanager
def create_model() -> ConnectionScreenModel:
    model = ConnectionScreenModel()
    observer = ModelObserver()
    model.add_observer(observer)
    yield model
    assert observer.is_called


def test_initialization():
    model = ConnectionScreenModel()
    # Settings
    assert model.mqtt_host == mock_get_config().mqtt.host.ip_value
    assert model.mqtt_port == f"{mock_get_config().mqtt.port}"
    assert model.ntp_host == "pool.ntp.org"
    assert model.ip_address == ""
    assert model.subnet_mask == ""
    assert model.gateway == ""
    assert model.dns_server == ""
    assert model.wifi_ssid == ""
    assert model.wifi_password == ""
    assert model.wifi_password_hidden is True
    assert model.wifi_icon_eye == "eye-off"
    # Settings validity
    assert not model.mqtt_host_error
    assert not model.mqtt_port_error
    assert not model.ntp_host_error
    assert not model.ip_address_error
    assert not model.subnet_mask_error
    assert not model.gateway_error
    assert not model.dns_server_error
    # Others
    assert not model.connected
    assert model.warning_message == ""


# local ip
@given(st.ip_addresses(v=4))
def test_local_ip_valid_updated(valid_ip: str):
    with create_model() as model:
        model.local_ip = valid_ip
        assert model.local_ip == valid_ip
        assert not model.mqtt_host_error
        assert not model.mqtt_port_error
        assert not model.ntp_host_error
        assert not model.ip_address_error
        assert not model.subnet_mask_error
        assert not model.gateway_error
        assert not model.dns_server_error
        assert model.warning_message == "Warning, Local IP Address is updated."


# local ip
@given(generate_invalid_ip())
def test_local_ip_invalid_updated(invalid_ip: str):
    with create_model() as model:
        model.local_ip = invalid_ip
        assert model.local_ip == invalid_ip
        assert not model.mqtt_host_error
        assert not model.mqtt_port_error
        assert not model.ntp_host_error
        assert not model.ip_address_error
        assert not model.subnet_mask_error
        assert not model.gateway_error
        assert not model.dns_server_error
        assert model.warning_message == "Warning, Local IP Address is updated."


# local ip
def test_local_ip_not_updated():
    with create_model() as model:
        ip = model.local_ip
        model.local_ip = ip
        assert model.local_ip == ip
        assert not model.mqtt_host_error
        assert not model.mqtt_port_error
        assert not model.ntp_host_error
        assert not model.ip_address_error
        assert not model.subnet_mask_error
        assert not model.gateway_error
        assert not model.dns_server_error
        assert model.warning_message == ""


# local ip
def test_local_ip_empty():
    with create_model() as model:
        model.local_ip = ""
        assert model.local_ip == ""
        assert not model.mqtt_host_error
        assert not model.mqtt_port_error
        assert not model.ntp_host_error
        assert not model.ip_address_error
        assert not model.subnet_mask_error
        assert not model.gateway_error
        assert not model.dns_server_error
        assert (
            model.warning_message
            == "Warning, No Local IP Address.\nPlease check connectivity."
        )


# List of addresses to check
addresses_to_check = [
    "1.2.3.4.5",  # DTSS-25
    "1A.2B.3C.4D.5C",  # DTSS-26
    "123.345.567.789",  # DTSS-44
    "!@#$%^^",  # DTSS-45
    "AB1.CD2.ED3.GH4",  # DTSS-47
]


# warning of local ip updated
@mark.parametrize("invalid_ip", addresses_to_check)
def test_local_ip_invalid_mqtt_ntp(invalid_ip: str):
    with create_model() as model:
        model.mqtt_host = invalid_ip
        model.ntp_host = invalid_ip
        model.local_ip = "192.168.11.11"
        assert model.local_ip == "192.168.11.11"
        assert model.mqtt_host == invalid_ip
        assert model.mqtt_host_error
        assert not model.mqtt_port_error
        assert model.ntp_host == invalid_ip
        assert model.ntp_host_error
        assert not model.ip_address_error
        assert not model.subnet_mask_error
        assert not model.gateway_error
        assert not model.dns_server_error
        assert (
            model.warning_message == "Warning, invalid parameters:"
            "\n- MQTT host address"
            "\n- NTP server address"
            "\nWarning, Local IP Address is updated."
        )


# warning of invalid mqtt host and ntp server
@mark.parametrize("invalid_ip", addresses_to_check)
def test_same_local_ip_invalid_mqtt_ntp(invalid_ip: str):
    with create_model() as model:
        ip = model.local_ip
        model.mqtt_host = invalid_ip
        model.ntp_host = invalid_ip
        model.local_ip = ip
        assert model.local_ip == ip
        assert model.mqtt_host == invalid_ip
        assert model.mqtt_host_error
        assert not model.mqtt_port_error
        assert model.ntp_host == invalid_ip
        assert model.ntp_host_error
        assert not model.ip_address_error
        assert not model.subnet_mask_error
        assert not model.gateway_error
        assert not model.dns_server_error
        assert (
            model.warning_message == "Warning, invalid parameters:"
            "\n- MQTT host address"
            "\n- NTP server address"
        )


# warning of invalid mqtt port and local ip updated
def test_local_ip_mqtt_port_all_characters():
    with create_model() as model:
        model.mqtt_port = "aaa"
        model.local_ip = "192.168.11.11"
        assert model.local_ip == "192.168.11.11"
        assert model.mqtt_port == ""
        assert not model.mqtt_host_error
        assert model.mqtt_port_error
        assert not model.ntp_host_error
        assert not model.ip_address_error
        assert not model.subnet_mask_error
        assert not model.gateway_error
        assert not model.dns_server_error
        assert (
            model.warning_message == "Warning, invalid parameters:"
            "\n- MQTT port"
            "\nWarning, Local IP Address is updated."
        )


# warning of invalid mqtt port and local ip updated
def test_local_ip_mqtt_port_full_invalid():
    with create_model() as model:
        model.mqtt_port = "!@#$%^^"
        model.local_ip = "192.168.11.11"
        assert model.local_ip == "192.168.11.11"
        assert model.mqtt_port == ""
        assert not model.mqtt_host_error
        assert model.mqtt_port_error
        assert not model.ntp_host_error
        assert not model.ip_address_error
        assert not model.subnet_mask_error
        assert not model.gateway_error
        assert not model.dns_server_error
        assert (
            model.warning_message == "Warning, invalid parameters:"
            "\n- MQTT port"
            "\nWarning, Local IP Address is updated."
        )


# invalid mqtt port and warning of local ip updated
def test_local_ip_mqtt_port_part_invalid():
    with create_model() as model:
        model.mqtt_port = "1883c"
        model.local_ip = "192.168.11.11"
        assert model.local_ip == "192.168.11.11"
        assert model.mqtt_port == "1883"
        assert not model.mqtt_host_error
        assert not model.mqtt_port_error
        assert not model.ntp_host_error
        assert not model.ip_address_error
        assert not model.subnet_mask_error
        assert not model.gateway_error
        assert not model.dns_server_error
        assert model.warning_message == "Warning, Local IP Address is updated."


@mark.parametrize("invalid_ip", addresses_to_check)
def test_local_ip_full_warning(invalid_ip: str):
    with create_model() as model:
        model.mqtt_host = invalid_ip
        model.mqtt_port = "99999"
        model.ntp_host = invalid_ip
        model.ip_address = invalid_ip
        model.subnet_mask = invalid_ip
        model.gateway = invalid_ip
        model.dns_server = invalid_ip
        model.local_ip = "192.168.11.11"
        assert model.local_ip == "192.168.11.11"
        assert model.mqtt_host == invalid_ip
        assert model.mqtt_port == "99999"
        assert model.ntp_host == invalid_ip
        assert model.mqtt_host_error
        assert model.mqtt_port_error
        assert model.ntp_host_error
        assert model.ip_address_error
        assert model.subnet_mask_error
        assert model.gateway_error
        assert model.dns_server_error
        assert (
            model.warning_message == "Warning, invalid parameters:"
            "\n- MQTT host address"
            "\n- MQTT port"
            "\n- NTP server address"
            "\n- IP Address"
            "\n- Subnet Mask"
            "\n- Gateway"
            "\n- DNS server"
            "\nWarning, Local IP Address is updated."
        )


# local ip
def test_local_ip_empty_with_invalid_parameters():
    with create_model() as model:
        model.mqtt_host = "1.2.3.4.5"
        model.mqtt_port = "aaa"
        model.ntp_host = "1.2.3.4.5"
        model.local_ip = ""
        assert model.local_ip == ""
        assert model.mqtt_host == "1.2.3.4.5"
        assert model.mqtt_port == ""
        assert model.ntp_host == "1.2.3.4.5"
        assert not model.mqtt_host_error
        assert not model.mqtt_port_error
        assert not model.ntp_host_error
        assert not model.ip_address_error
        assert not model.subnet_mask_error
        assert not model.gateway_error
        assert not model.dns_server_error
        assert (
            model.warning_message
            == "Warning, No Local IP Address.\nPlease check connectivity."
        )


# mqtt host
@given(generate_valid_ip())
def test_mqtt_host(valid_ip: str):
    with create_model() as model:
        model.mqtt_host = valid_ip
        assert model.mqtt_host == valid_ip
        assert not model.mqtt_host_error
        assert model.warning_message == ""


@given(generate_invalid_ip())
def test_mqtt_host_invalid(invalid_ip: str):
    with create_model() as model:
        model.mqtt_host = invalid_ip
        assert model.mqtt_host == invalid_ip
        assert not model.mqtt_host_error
        assert model.warning_message == ""


@given(generate_invalid_hostname_long())
def test_mqtt_host_invalid_long(ip: str):
    with create_model() as model:
        model.mqtt_host = ip
        assert not model.mqtt_host_error
        assert len(model.mqtt_host) <= model.MAX_LEN_DOMAIN_NAME


# ntp host
@given(generate_valid_ip())
def test_ntp_host(valid_ip: str):
    with create_model() as model:
        model.ntp_host = valid_ip
        assert model.ntp_host == valid_ip
        assert not model.ntp_host_error
        assert model.warning_message == ""


@given(generate_invalid_ip())
def test_ntp_host_invalid(invalid_ip: str):
    with create_model() as model:
        model.ntp_host = invalid_ip
        assert model.ntp_host == invalid_ip
        assert not model.ntp_host_error
        assert model.warning_message == ""


@given(generate_invalid_hostname_long())
def test_ntp_host_invalid_long(ip: str):
    with create_model() as model:
        model.ntp_host = ip
        assert not model.ntp_host_error
        assert len(model.ntp_host) <= model.MAX_LEN_DOMAIN_NAME


# mqtt port
@given(generate_valid_port_number())
def test_mqtt_port(port: int):
    with create_model() as model:
        model.mqtt_port = str(port)
        assert model.mqtt_port == str(port)
        assert not model.mqtt_port_error
        assert model.warning_message == ""


@given(generate_invalid_port_number())
def test_mqtt_port_invalid(port: int):
    with create_model() as model:
        model.mqtt_port = str(port)
        assert model.mqtt_port == str(abs(port))[:5]
        assert not model.mqtt_port_error
        assert model.warning_message == ""


# ip address
@given(generate_valid_ip())
def test_ip_address(ip: str):
    with create_model() as model:
        model.ip_address = ip
        assert len(model.ip_address) <= model.MAX_LEN_IP_ADDRESS


@given(generate_invalid_ip())
def test_ip_address_invalid(ip: str):
    with create_model() as model:
        model.ip_address = ip
        assert len(model.ip_address) <= model.MAX_LEN_IP_ADDRESS


@given(generate_invalid_ip_long())
def test_ip_address_invalid_long(ip: str):
    with create_model() as model:
        model.ip_address = ip
        model.subnet_mask = ip
        model.gateway = ip
        model.dns_server = ip
        assert not model.ip_address_error
        assert not model.subnet_mask_error
        assert not model.gateway_error
        assert not model.dns_server_error
        assert len(model.ip_address) <= model.MAX_LEN_IP_ADDRESS
        assert len(model.subnet_mask) <= model.MAX_LEN_IP_ADDRESS
        assert len(model.gateway) <= model.MAX_LEN_IP_ADDRESS
        assert len(model.dns_server) <= model.MAX_LEN_IP_ADDRESS


# subnet mask
@given(generate_valid_ip_strict())
def test_subnet_mask(ip: str):
    with create_model() as model:
        model.subnet_mask = ip
        assert not model.subnet_mask_error
        assert len(model.subnet_mask) <= model.MAX_LEN_IP_ADDRESS


@given(generate_invalid_ip())
def test_subnet_mask_invalid(ip: str):
    with create_model() as model:
        model.subnet_mask = ip
        assert not model.subnet_mask_error
        assert len(model.subnet_mask) <= model.MAX_LEN_IP_ADDRESS


@given(generate_invalid_ip_long())
def test_subnet_mask_invalid_long(ip: str):
    with create_model() as model:
        model.subnet_mask = ip
        assert not model.subnet_mask_error
        assert len(model.subnet_mask) <= model.MAX_LEN_IP_ADDRESS


# gateway
@given(generate_valid_ip())
def test_gateway(ip: str):
    with create_model() as model:
        model.gateway = ip
        assert not model.gateway_error
        assert len(model.gateway) <= model.MAX_LEN_IP_ADDRESS


@given(generate_invalid_ip())
def test_gateway_invalid(ip: str):
    with create_model() as model:
        model.gateway = ip
        assert not model.gateway_error
        assert len(model.gateway) <= model.MAX_LEN_IP_ADDRESS


@given(generate_invalid_ip_long())
def test_gateway_invalid_long(ip: str):
    with create_model() as model:
        model.gateway = ip
        assert not model.gateway_error
        assert len(model.gateway) <= model.MAX_LEN_IP_ADDRESS


# dns_server
@given(generate_valid_ip())
def test_dns_server(ip: str):
    with create_model() as model:
        model.dns_server = ip
        assert not model.dns_server_error
        assert len(model.dns_server) <= model.MAX_LEN_IP_ADDRESS


@given(generate_invalid_ip())
def test_dns_server_invalid(ip: str):
    with create_model() as model:
        model.dns_server = ip
        assert not model.dns_server_error
        assert len(model.dns_server) <= model.MAX_LEN_IP_ADDRESS


@given(generate_invalid_ip_long())
def test_dns_server_invalid_long(ip: str):
    with create_model() as model:
        model.dns_server = ip
        assert not model.dns_server_error
        assert len(model.dns_server) <= model.MAX_LEN_IP_ADDRESS


# wifi ssid / password
@given(
    generate_random_characters(min_size=0, max_size=32),
    generate_random_characters(min_size=0, max_size=32),
)
def test_wifi_ssid_password(ssid: str, password: str):
    with (
        create_model() as model,
        patch("local_console.gui.controller.connection_screen.ConnectionScreenView"),
    ):
        mock_driver = MagicMock()
        controller = ConnectionScreenController(model, mock_driver)
        model.wifi_ssid = ssid
        assert model.wifi_ssid == ssid
        assert len(model.wifi_ssid) <= model.MAX_LEN_WIFI_SSID
        model.wifi_password = password
        assert model.wifi_password == password
        assert len(model.wifi_password) <= model.MAX_LEN_WIFI_PASSWORD
        assert model.wifi_password_hidden is True
        assert model.wifi_icon_eye == "eye-off"
        controller.toggle_password_visibile()
        assert model.wifi_password_hidden is False
        assert model.wifi_icon_eye == "eye"


@given(
    generate_random_characters(min_size=33, max_size=35),
    generate_random_characters(min_size=33, max_size=35),
)
def test_wifi_ssid_password_long(ssid: str, password: str):
    with (
        create_model() as model,
        patch("local_console.gui.controller.connection_screen.ConnectionScreenView"),
    ):
        mock_driver = MagicMock()
        controller = ConnectionScreenController(model, mock_driver)
        model.wifi_ssid = ssid
        assert model.wifi_ssid == ssid[: model.MAX_LEN_WIFI_SSID]
        assert len(model.wifi_ssid) <= model.MAX_LEN_WIFI_SSID
        model.wifi_password = password
        assert model.wifi_password == password[: model.MAX_LEN_WIFI_PASSWORD]
        assert len(model.wifi_password) <= model.MAX_LEN_WIFI_PASSWORD
        assert model.wifi_password_hidden is True
        assert model.wifi_icon_eye == "eye-off"
        controller.toggle_password_visibile()
        assert model.wifi_password_hidden is False
        assert model.wifi_icon_eye == "eye"
        controller.toggle_password_visibile()
        assert model.wifi_password_hidden is True
        assert model.wifi_icon_eye == "eye-off"


# connection status
@given(st.booleans())
def test_connected(connected: bool):
    with create_model() as model:
        model.connected = connected
