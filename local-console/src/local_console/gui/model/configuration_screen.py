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
from typing import Optional

from local_console.gui.model.base_model import BaseScreenModel


class ConfigurationScreenModel(BaseScreenModel):
    """
    The Model for the Configuration screen.
    """

    def __init__(self) -> None:
        self._image_directory: Optional[Path] = None
        self._inferences_directory: Optional[Path] = None
        self._flatbuffers_schema: Optional[Path] = None
        self._flatbuffers_process_result: Optional[str] = None
        self._flatbuffers_schema_status: bool = False
        self._app_type: Optional[str] = None
        self._app_configuration: Optional[str] = None
        self._app_labels: Optional[str] = None

    @property
    def image_directory(self) -> Optional[Path]:
        return self._image_directory

    @image_directory.setter
    def image_directory(self, value: Optional[Path]) -> None:
        self._image_directory = value
        self.notify_observers()

    @property
    def inferences_directory(self) -> Optional[Path]:
        return self._inferences_directory

    @inferences_directory.setter
    def inferences_directory(self, value: Optional[Path]) -> None:
        self._inferences_directory = value
        self.notify_observers()

    @property
    def flatbuffers_schema(self) -> Optional[Path]:
        return self._flatbuffers_schema

    @flatbuffers_schema.setter
    def flatbuffers_schema(self, value: Optional[Path]) -> None:
        self._flatbuffers_schema = value
        self.notify_observers()

    @property
    def app_type(self) -> Optional[str]:
        return self._app_type

    @app_type.setter
    def app_type(self, value: Optional[str]) -> None:
        self._app_type = value
        self.notify_observers()

    @property
    def app_labels(self) -> Optional[str]:
        return self._app_labels

    @app_labels.setter
    def app_labels(self, value: Optional[str]) -> None:
        self._app_labels = value
        self.notify_observers()

    @property
    def app_configuration(self) -> Optional[str]:
        return self._app_configuration

    @app_configuration.setter
    def app_configuration(self, value: Optional[str]) -> None:
        self._app_configuration = value
        self.notify_observers()

    @property
    def flatbuffers_process_result(self) -> Optional[str]:
        return self._flatbuffers_process_result

    @flatbuffers_process_result.setter
    def flatbuffers_process_result(self, value: Optional[str]) -> None:
        self._flatbuffers_process_result = value
        self.notify_observers()

    @property
    def flatbuffers_schema_status(self) -> bool:
        return self._flatbuffers_schema_status

    @flatbuffers_schema_status.setter
    def flatbuffers_schema_status(self, value: bool) -> None:
        self._flatbuffers_schema_status = value
        self.notify_observers()
