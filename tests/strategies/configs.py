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
from pathlib import Path
from socket import inet_ntoa
from string import printable
from struct import pack

from hypothesis import strategies as st
from local_console.core.schemas.edge_cloud_if_v1 import DeviceConfiguration
from local_console.core.schemas.edge_cloud_if_v1 import Hardware
from local_console.core.schemas.edge_cloud_if_v1 import OTA
from local_console.core.schemas.edge_cloud_if_v1 import Permission
from local_console.core.schemas.edge_cloud_if_v1 import Status
from local_console.core.schemas.edge_cloud_if_v1 import Version
from local_console.core.schemas.schemas import AgentConfiguration
from local_console.core.schemas.schemas import EVPParams
from local_console.core.schemas.schemas import IPAddress
from local_console.core.schemas.schemas import MQTTParams
from local_console.core.schemas.schemas import TLSConfiguration
from local_console.core.schemas.schemas import WebserverParams


@st.composite
def generate_text(draw: st.DrawFn, min_size: int = 1, max_size: int = 5):
    characters = st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=0, max_codepoint=0x10FFFF
    )
    return draw(st.text(alphabet=characters, min_size=min_size, max_size=max_size))


@st.composite
def generate_random_characters(draw: st.DrawFn, min_size: int, max_size: int) -> str:
    return draw(st.text(alphabet=printable, min_size=min_size, max_size=max_size))


@st.composite
def generate_identifiers(
    draw: st.DrawFn,
    max_size: int,
    min_size: int = 0,
    categories_first_char=("Ll", "Lu", "Nd"),
    categories_next_chars=("Ll", "Lu", "Nd"),
    include_in_first_char="",
    include_in_next_chars="",
    codec="ascii",
) -> str:
    """
    Generates strings whose first character can have different settings
    than the remaining characters.

    Initial usages of the `from_regex` built-in strategy incurred in
    run times that exceeded the Hypothesis' deadline, since that
    strategy performs a brute-force approach of generating arbitrarily
    long strings, then filtering them out via the regex.
    It's an inefficient approach overall.
    """
    assert max_size > 0
    return draw(
        st.tuples(
            st.characters(
                codec=codec,
                categories=categories_first_char,
                include_characters=include_in_first_char,
            ),
            st.lists(
                st.characters(
                    codec=codec,
                    categories=categories_next_chars,
                    include_characters=include_in_next_chars,
                ),
                max_size=max_size - 1,
                min_size=min_size,
            ),
        ).map(lambda t: t[0] + "".join(t[1]))
    )


@st.composite
def generate_valid_ip(draw: st.DrawFn) -> str:
    return draw(generate_identifiers(max_size=10, include_in_next_chars="-."))


@st.composite
def generate_invalid_ip(draw: st.DrawFn) -> str:
    return draw(
        generate_identifiers(
            max_size=10, categories_first_char=("S", "Z"), include_in_first_char=" +.-"
        )
    )


@st.composite
def generate_invalid_ip_long(draw: st.DrawFn) -> str:
    return draw(
        generate_identifiers(
            max_size=42,
            min_size=38,
            categories_first_char=("S", "Z"),
            include_in_first_char=" +.-",
        )
    )


@st.composite
def generate_invalid_hostname_long(draw: st.DrawFn) -> str:
    return draw(
        generate_identifiers(
            max_size=66,
            min_size=63,
            categories_first_char=("S", "Z"),
            include_in_first_char=" +.-",
        )
    )


@st.composite
def generate_valid_ip_strict(draw: st.DrawFn) -> str:
    ip_int = draw(st.integers(min_value=1, max_value=0xFFFFFFFF))
    return inet_ntoa(pack(">I", ip_int))


@st.composite
def generate_valid_port_number(draw: st.DrawFn) -> int:
    return draw(st.integers(min_value=0, max_value=65535))


@st.composite
def generate_invalid_port_number(draw: st.DrawFn) -> int:
    return draw(
        st.integers(min_value=-100, max_value=-1)
        | st.integers(min_value=65536, max_value=100000)
    )


@st.composite
def generate_agent_config(draw: st.DrawFn) -> AgentConfiguration:
    return AgentConfiguration(
        evp=EVPParams(
            iot_platform=draw(
                generate_identifiers(max_size=10, categories_first_char=("Ll", "Lu"))
            ),
        ),
        mqtt=MQTTParams(
            host=IPAddress(ip_value=draw(generate_valid_ip())),
            port=draw(generate_valid_port_number()),
            device_id=draw(
                generate_identifiers(
                    max_size=10,
                    categories_first_char=("Ll", "Lu"),
                    include_in_first_char="_",
                    include_in_next_chars="-",
                )
            ),
        ),
        webserver=WebserverParams(
            host=IPAddress(ip_value=draw(generate_valid_ip())),
            port=draw(generate_valid_port_number()),
        ),
        tls=TLSConfiguration.model_construct(
            ca_certificate=draw(st.none()),
            ca_key=draw(st.none()),
        ),
    )


@st.composite
def generate_tls_config(draw: st.DrawFn) -> TLSConfiguration:
    return TLSConfiguration.model_construct(
        ca_certificate=draw(st.just(Path("ca.crt"))),
        ca_key=draw(st.just(Path("ca.key"))),
    )


@st.composite
def generate_valid_device_configuration(draw: st.DrawFn) -> DeviceConfiguration:
    # TODO: generate data at random
    # Use https://polyfactory.litestar.dev/latest/
    # while pydantic hypothesis support is missing https://docs.pydantic.dev/latest/integrations/hypothesis/
    return DeviceConfiguration(
        Hardware=Hardware(
            Sensor="", SensorId="", KG="", ApplicationProcessor="", LedOn=True
        ),
        Version=Version(
            SensorFwVersion="",
            SensorLoaderVersion="",
            DnnModelVersion=[],
            ApFwVersion="",
            ApLoaderVersion="",
        ),
        Status=Status(Sensor="", ApplicationProcessor=""),
        OTA=OTA(
            SensorFwLastUpdatedDate="",
            SensorLoaderLastUpdatedDate="",
            DnnModelLastUpdatedDate=[],
            ApFwLastUpdatedDate="",
            UpdateProgress=75,
            UpdateStatus="Updating",
        ),
        Permission=Permission(FactoryReset=False),
    )
