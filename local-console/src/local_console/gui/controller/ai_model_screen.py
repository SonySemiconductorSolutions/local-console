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
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import trio
from local_console.clients.agent import Agent
from local_console.core.camera import MQTTTopics
from local_console.core.commands.ota_deploy import configuration_spec
from local_console.core.commands.ota_deploy import get_network_id
from local_console.core.commands.ota_deploy import get_network_ids
from local_console.core.config import get_config
from local_console.core.schemas.edge_cloud_if_v1 import DnnDelete
from local_console.core.schemas.edge_cloud_if_v1 import DnnDeleteBody
from local_console.gui.driver import Driver
from local_console.gui.model.ai_model_screen import AIModelScreenModel
from local_console.servers.webserver import AsyncWebserver
from local_console.utils.local_network import get_my_ip_by_routing

if TYPE_CHECKING:
    from local_console.gui.view.base_screen import BaseScreenView

logger = logging.getLogger(__name__)


class AIModelScreenController:
    """
    The `AIModelScreenController` class represents a controller implementation.
    Coordinates work of the view with the model.

    The controller implements the strategy pattern. The controller connects to
    the view to control its actions.
    """

    def __init__(
        self, model: AIModelScreenModel, driver: Driver, view: type["BaseScreenView"]
    ):
        self.model = model
        self.driver = driver
        self.view = view(controller=self, model=self.model)

    def get_view(self) -> "BaseScreenView":
        return self.view

    def deploy(self) -> None:
        self.view.ids.btn_ota_file.disabled = True
        self.driver.from_sync(self.deployment_task, self.model.model_file)

    async def undeploy_step(self, network_id: str) -> None:
        ephemeral_agent = Agent()

        timeout_secs = 30
        model_is_deployed = True
        with trio.move_on_after(timeout_secs) as timeout_scope:
            async with ephemeral_agent.mqtt_scope([]):
                await ephemeral_agent.configure(
                    "backdoor-EA_Main",
                    "placeholder",
                    DnnDelete(
                        OTA=DnnDeleteBody(DeleteNetworkID=network_id)
                    ).model_dump_json(),
                )
                while True:
                    if self.model.device_config:
                        deployed_dnn_model_versions = get_network_ids(
                            self.model.device_config.Version.DnnModelVersion  # type: ignore
                        )
                        logger.debug(
                            f"Dnn deployed version: {deployed_dnn_model_versions}"
                        )
                        model_is_deployed = network_id in deployed_dnn_model_versions

                        if (
                            self.model.device_config.OTA.UpdateStatus
                            in ["Done", "Failed"]
                            and not model_is_deployed
                        ):
                            logger.debug("AI model not loaded")
                            break

                    await self.model.ota_event()
                    timeout_scope.deadline += timeout_secs

        if model_is_deployed:
            logger.warning("Model hasn't been undeployed")

    async def deploy_step(self, network_id: str, package_file: Path) -> None:
        config = get_config()
        ephemeral_agent = Agent()
        webserver_port = config.webserver.port

        with TemporaryDirectory(prefix="lc_deploy_") as temporary_dir:
            tmp_dir = Path(temporary_dir)
            tmp_module = tmp_dir / package_file.name
            shutil.copy(package_file, tmp_module)
            ip_addr = get_my_ip_by_routing()
            spec = configuration_spec(
                tmp_module, tmp_dir, webserver_port, ip_addr
            ).model_dump_json()

            # In my tests, the "Updating" phase may take this long:
            timeout_secs = 90
            model_is_deployed = False
            with trio.move_on_after(timeout_secs) as timeout_scope:
                async with (
                    ephemeral_agent.mqtt_scope(
                        [MQTTTopics.ATTRIBUTES_REQ.value, MQTTTopics.ATTRIBUTES.value]
                    ),
                    AsyncWebserver(tmp_dir, webserver_port, None, True),
                ):
                    assert ephemeral_agent.nursery  # make mypy happy
                    await ephemeral_agent.configure(
                        "backdoor-EA_Main", "placeholder", spec
                    )
                    while True:
                        if self.model.device_config:
                            model_is_deployed = network_id in get_network_ids(
                                self.model.device_config.Version.DnnModelVersion  # type: ignore
                            )

                            if (
                                self.model.device_config.OTA.UpdateStatus
                                in ("Done", "Failed")
                                and model_is_deployed
                            ):
                                break

                        await self.model.ota_event()
                        timeout_scope.deadline += timeout_secs

            if not model_is_deployed:
                logger.warning("Model is not deployed")

            if timeout_scope.cancelled_caught:
                self.view.notify_deploy_timeout()
                logger.error("Timeout when sending modules.")

    async def deployment_task(self, package_file: Path) -> None:
        network_id = get_network_id(package_file)
        logger.debug(f"Undeploying network with id {network_id}")
        await self.undeploy_step(network_id)
        logger.debug("Deploying network")
        await self.deploy_step(network_id, package_file)
