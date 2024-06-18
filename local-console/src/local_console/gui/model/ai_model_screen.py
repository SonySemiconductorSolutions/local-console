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

from local_console.core.schemas.edge_cloud_if_v1 import DeviceConfiguration
from local_console.gui.model.base_model import BaseScreenModel
from local_console.utils.validation import validate_imx500_model_file
from trio import Event


class AIModelScreenModel(BaseScreenModel):
    """
    Implements the logic of the
    :class:`~View.settings_screen.AIModelScreen.AIModelScreenView` class.
    """

    def __init__(self) -> None:
        self._device_config: DeviceConfiguration | None = None

        # These two variables enable signaling that the OTA
        # status has changed from a previous report
        self._ota_event = Event()
        self._device_config_previous: DeviceConfiguration | None = None

        self._model_file = Path()
        self._model_file_valid = False

    @property
    def device_config(self) -> DeviceConfiguration | None:
        return self._device_config

    @device_config.setter
    def device_config(self, value: DeviceConfiguration | None) -> None:
        self._device_config = value

        # detect content change
        if self._device_config_previous != value:
            self._device_config_previous = value
            self._ota_event.set()
            self.notify_observers()

    async def ota_event(self) -> None:
        self._ota_event = Event()
        await self._ota_event.wait()

    @property
    def model_file(self) -> Path:
        return self._model_file

    @model_file.setter
    def model_file(self, value: Path) -> None:
        self._model_file = value
        self._model_file_valid = validate_imx500_model_file(value)

        self.notify_observers()

    @property
    def model_file_valid(self) -> bool:
        return self._model_file_valid
