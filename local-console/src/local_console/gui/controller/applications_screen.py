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
from pathlib import Path

from local_console.clients.agent import Agent
from local_console.core.commands.deploy import DeployStage
from local_console.core.commands.deploy import exec_deployment
from local_console.core.commands.deploy import module_deployment_setup
from local_console.core.config import get_config
from local_console.gui.driver import Driver
from local_console.gui.enums import ApplicationConfiguration
from local_console.gui.model.applications_screen import ApplicationsScreenModel
from local_console.gui.utils.sync_async import run_on_ui_thread
from local_console.gui.view.applications_screen.applications_screen import (
    ApplicationsScreenView,
)


logger = logging.getLogger(__name__)


class ApplicationsScreenController:
    """
    The `ApplicationsScreenController` class represents a controller implementation.
    Coordinates work of the view with the model.

    The controller implements the strategy pattern. The controller connects to
    the view to control its actions.
    """

    def __init__(self, model: ApplicationsScreenModel, driver: Driver):
        self.model = model
        self.driver = driver
        self.view = ApplicationsScreenView(controller=self, model=self.model)

    def get_view(self) -> ApplicationsScreenView:
        return self.view

    def deploy(self, module_file_str: str) -> None:
        self.driver.from_sync(self.deploy_task, Path(module_file_str))

    async def deploy_task(self, module_file: Path) -> bool:
        config: AgentConfiguration = get_config()  # type:ignore
        port = config.webserver.port

        with module_deployment_setup(
            ApplicationConfiguration.NAME, module_file, port
        ) as (
            tmpdir,
            deployment_manifest,
        ):
            self.model.manifest = deployment_manifest
            try:
                await exec_deployment(
                    Agent(),
                    deployment_manifest,
                    True,
                    tmpdir,
                    port,
                    60,
                    self.update_deploy_stage,
                )
            except Exception as e:
                logger.exception("Deployment error", exc_info=e)
                return False
            return True

    @run_on_ui_thread
    def update_deploy_stage(self, deploy_stage: DeployStage) -> None:
        logger.info(f"WASM deployment stage is now: {deploy_stage.name}")
        self.model.deploy_stage = deploy_stage
