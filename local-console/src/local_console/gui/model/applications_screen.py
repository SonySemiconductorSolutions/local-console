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
from typing import Optional

from local_console.commands.deploy import get_empty_deployment
from local_console.core.commands.deploy import DeployStage
from local_console.core.schemas.schemas import DeploymentManifest
from local_console.gui.model.base_model import BaseScreenModel


class ApplicationsScreenModel(BaseScreenModel):
    """
    Implements the logic of the
    :class:`~View.settings_screen.ApplicationsScreen.ApplicationsScreenView` class.
    """

    def __init__(self) -> None:
        self._manifest: DeploymentManifest = get_empty_deployment()
        self._deploy_status: dict[str, str] = {}
        self._deploy_stage: Optional[DeployStage] = None

    @property
    def manifest(self) -> DeploymentManifest:
        return self._manifest

    @manifest.setter
    def manifest(self, value: DeploymentManifest) -> None:
        self._manifest = value
        self.notify_observers()

    @property
    def deploy_status(self) -> dict[str, str]:
        return self._deploy_status

    @deploy_status.setter
    def deploy_status(self, value: dict[str, str]) -> None:
        self._deploy_status = value
        self.notify_observers()

    @property
    def deploy_stage(self) -> Optional[DeployStage]:
        return self._deploy_stage

    @deploy_stage.setter
    def deploy_stage(self, value: DeployStage) -> None:
        self._deploy_stage = value
        self.notify_observers()
