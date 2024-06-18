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

from kivy.metrics import dp
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.snackbar import MDSnackbarButtonContainer
from kivymd.uix.snackbar import MDSnackbarCloseButton
from kivymd.uix.snackbar import MDSnackbarSupportingText
from local_console.gui.view.base_screen import BaseScreenView


class ConfigurationScreenView(BaseScreenView):
    def model_is_changed(self) -> None:
        """
        Called whenever any change has occurred in the data model.
        The view in this method tracks these changes and updates the UI
        according to these changes.
        """
        if self.model.image_directory is not None:
            self.ids.image_dir_pick.accept_path(str(self.model.image_directory))
        if self.model.inferences_directory is not None:
            self.ids.inference_dir_pick.accept_path(
                str(self.model.inferences_directory)
            )

        self.ids.schema_pick.accept_path(
            ""
            if self.model.flatbuffers_schema is None
            else str(self.model.flatbuffers_schema)
        )
        self.ids.app_configuration_pick.accept_path(
            ""
            if self.model.app_configuration is None
            else str(self.model.app_configuration)
        )
        self.ids.labels_pick.accept_path(
            "" if self.model.app_labels is None else str(self.model.app_labels)
        )

        if self.model.flatbuffers_process_result is not None:
            self.show_flatbuffers_process_result(self.model.flatbuffers_process_result)
            self.model.flatbuffers_process_result = None

    def select_path_image(self, path: str) -> None:
        """
        It will be called when the user selects the directory.
        :param path: path to the selected directory;
        """
        self.controller.update_image_directory(Path(path))

    def select_path_inferences(self, path: str) -> None:
        """
        It will be called when the user selects the directory.
        :param path: path to the selected directory;
        """
        self.controller.update_inferences_directory(Path(path))

    def select_path_flatbuffers(self, path: str) -> None:
        """
        It will be called when the user selects the directory.
        :param path: path to the selected directory;
        """
        self.controller.update_flatbuffers_schema(Path(path))

    def select_path_labels(self, path: str) -> None:
        self.controller.update_app_labels(Path(path))

    def select_path_app_configuration(self, path: str) -> None:
        self.controller.update_app_configuration(path)

    def show_flatbuffers_process_result(self, result: str) -> None:
        MDSnackbar(
            MDSnackbarSupportingText(text=result),
            MDSnackbarButtonContainer(
                MDSnackbarCloseButton(
                    icon="close",
                ),
                pos_hint={"center_y": 0.5},
            ),
            y=dp(24),
            orientation="horizontal",
            pos_hint={"center_x": 0.5},
            size_hint_x=0.5,
            duration=5,
        ).open()
