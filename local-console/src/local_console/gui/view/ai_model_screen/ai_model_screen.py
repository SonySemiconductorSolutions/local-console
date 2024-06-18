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
from typing import Any

from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.snackbar import MDSnackbarButtonContainer
from kivymd.uix.snackbar import MDSnackbarCloseButton
from kivymd.uix.snackbar import MDSnackbarSupportingText
from local_console.gui.schemas import OtaData
from local_console.gui.utils.sync_async import run_on_ui_thread
from local_console.gui.view.base_screen import BaseScreenView
from local_console.gui.view.common.components import (
    CodeInputCustom,
)  # nopycln: import # Required by the screen's KV spec file
from local_console.gui.view.common.components import (
    PathSelectorCombo,
)  # nopycln: import # Required by the screen's KV spec file

logger = logging.getLogger(__name__)


class AIModelScreenView(BaseScreenView):
    def model_is_changed(self) -> None:
        # If Done or Failed
        leaf_update_status = False

        if self.model.device_config:
            self.ids.txt_ota_data.text = OtaData(
                **self.model.device_config.model_dump()
            ).model_dump_json(indent=4)

            update_status = self.model.device_config.OTA.UpdateStatus
            leaf_update_status = update_status in ("Done", "Failed")
            self.ids.lbl_ota_status.text = update_status

        if self.model.model_file.is_file():
            self.ids.model_pick.accept_path(str(self.model.model_file))

        can_deploy = (
            self.app.is_ready and self.model.model_file_valid and leaf_update_status
        )
        self.ids.btn_ota_file.disabled = not can_deploy

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.app.bind(is_ready=self.app_state_refresh)

    def select_path(self, path_str: str) -> None:
        """
        It will be called when the user clicks on the file name
        or the catalog selection button.

        :param path: path to the selected directory or file;
        """
        path = Path(path_str)
        self.model.model_file = path

        if not self.model.model_file_valid:
            MDSnackbar(
                MDSnackbarSupportingText(
                    text="Invalid AI Model file header!",
                ),
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
            ).open()

    def app_state_refresh(self, app: MDApp, value: bool) -> None:
        """
        Makes the deploy button react to the camera readiness state.
        """
        self.ids.btn_ota_file.disabled = not self.app.is_ready

    @run_on_ui_thread
    def notify_deploy_timeout(self) -> None:
        MDSnackbar(
            MDSnackbarSupportingText(
                text="Model deployment timed out!",
            ),
            MDSnackbarButtonContainer(
                MDSnackbarCloseButton(
                    icon="close",
                ),
                pos_hint={"center_y": 0.5},
            ),
            y=dp(24),
            orientation="horizontal",
            pos_hint={"center_x": 0.5},
            size_hint_min_x=0.5,
            size_hint_max_x=0.9,
        ).open()
