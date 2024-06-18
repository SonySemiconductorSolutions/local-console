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
import json
from pathlib import Path
from typing import Optional

from local_console.gui.driver import Driver
from local_console.gui.enums import ApplicationSchemaFilePath
from local_console.gui.enums import ApplicationType
from local_console.gui.model.configuration_screen import ConfigurationScreenModel
from local_console.gui.view.configuration_screen.configuration_screen import (
    ConfigurationScreenView,
)
from local_console.utils.flatbuffers import FlatBuffers


class ConfigurationScreenController:
    """
    The `ConfigurationScreenController` class represents a controller implementation.
    Coordinates work of the view with the model.
    The controller implements the strategy pattern. The controller connects to
    the view to control its actions.
    """

    def __init__(self, model: ConfigurationScreenModel, driver: Driver) -> None:
        self.model = model
        self.driver = driver
        self.view = ConfigurationScreenView(controller=self, model=self.model)
        self.flatbuffers = FlatBuffers()

    def get_view(self) -> ConfigurationScreenView:
        return self.view

    def update_image_directory(self, path: Path) -> None:
        self.driver.set_image_directory(path)
        self.model.image_directory = path

    def update_inferences_directory(self, path: Path) -> None:
        self.driver.set_inference_directory(path)
        self.model.inferences_directory = path

    def update_total_max_size(self, size: int) -> None:
        self.driver.total_dir_watcher.set_storage_limit(size)

    def update_flatbuffers_schema(self, path: Optional[Path]) -> None:
        self.model.flatbuffers_schema = path

    def update_app_labels(self, path: str) -> None:
        self.model.app_labels = path

    def update_app_configuration(self, path: Optional[str]) -> None:
        self.model.app_configuration = path

    def update_application_type(self, app: str) -> None:
        self.model.app_type = app
        self.view.ids.labels_pick.disabled = app == ApplicationType.CUSTOM.value
        self.view.ids.schema_pick.disabled = app != ApplicationType.CUSTOM.value

        if app == ApplicationType.CUSTOM.value:
            self.update_flatbuffers_schema(None)
        elif app == ApplicationType.CLASSIFICATION.value:
            self.update_flatbuffers_schema(ApplicationSchemaFilePath.CLASSIFICATION)
        else:
            self.update_flatbuffers_schema(ApplicationSchemaFilePath.DETECTION)

    def apply_application_configuration(self) -> None:
        self.driver.map_class_id_to_name()

        if self.model.app_configuration is None:
            return
        try:
            with open(self.model.app_configuration) as f:
                config = json.load(f)
            self.driver.from_sync(self.driver.send_app_config, json.dumps(config))
        except FileNotFoundError:
            self.model.flatbuffers_process_result = "App configuration does not exist"
        except ValueError:
            self.model.flatbuffers_process_result = (
                "Error parsing app configuration JSON"
            )
        except PermissionError:
            self.model.flatbuffers_process_result = "App configuration permission error"
        except Exception:
            self.model.flatbuffers_process_result = "App configuration unknown error"

    def apply_flatbuffers_schema(self) -> None:
        if self.model.flatbuffers_schema is not None:
            if self.model.flatbuffers_schema.is_file():
                result, _ = self.flatbuffers.conform_flatbuffer_schema(
                    self.model.flatbuffers_schema
                )
                if result is True:
                    self.driver.flatbuffers_schema = self.model.flatbuffers_schema
                    self.model.flatbuffers_process_result = "Success!"
                else:
                    self.model.flatbuffers_process_result = (
                        "Not a valid flatbuffers schema"
                    )
            else:
                self.model.flatbuffers_process_result = (
                    "Not a file or file does not exist!"
                )
        else:
            self.model.flatbuffers_process_result = "Please select a schema file."

    def apply_configuration(self) -> None:
        self.apply_flatbuffers_schema()
        self.apply_application_configuration()
