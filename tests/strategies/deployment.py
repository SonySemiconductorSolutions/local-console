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
from hypothesis import strategies as st
from local_console.core.schemas.schemas import Deployment
from local_console.core.schemas.schemas import DeploymentManifest
from local_console.core.schemas.schemas import InstanceSpec
from local_console.core.schemas.schemas import Module
from local_console.core.schemas.schemas import Topics

from tests.strategies.configs import generate_text


@st.composite
def instance_spec_strategy(draw):
    return InstanceSpec(
        moduleId=draw(generate_text()),
        subscribe=draw(
            st.dictionaries(
                generate_text(),
                generate_text(),
                min_size=1,
                max_size=5,
            )
        ),
        publish=draw(
            st.dictionaries(
                generate_text(),
                generate_text(),
                min_size=1,
                max_size=5,
            )
        ),
    )


@st.composite
def module_strategy(draw):
    return Module(
        entryPoint=draw(generate_text()),
        moduleImpl=draw(generate_text()),
        downloadUrl=draw(generate_text()),
        hash=draw(generate_text()),
    )


@st.composite
def topics_strategy(draw):
    return Topics(
        type=draw(generate_text()),
        topic=draw(generate_text()),
    )


@st.composite
def deployment_strategy(draw):
    return Deployment(
        deploymentId=draw(generate_text()),
        instanceSpecs=draw(
            st.dictionaries(
                generate_text(),
                instance_spec_strategy(),
                min_size=1,
                max_size=5,
            )
        ),
        modules=draw(
            st.dictionaries(
                generate_text(),
                module_strategy(),
                min_size=1,
                max_size=5,
            )
        ),
        publishTopics=draw(
            st.dictionaries(
                generate_text(),
                topics_strategy(),
                min_size=1,
                max_size=5,
            )
        ),
        subscribeTopics=draw(
            st.dictionaries(
                generate_text(),
                topics_strategy(),
                min_size=1,
                max_size=5,
            )
        ),
    )


@st.composite
def deployment_manifest_strategy(draw):
    return DeploymentManifest(deployment=draw(deployment_strategy()))
