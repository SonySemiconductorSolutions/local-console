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
from local_console.core.camera import StreamStatus
from local_console.gui.driver import Driver
from local_console.gui.model.inference_screen import InferenceScreenModel
from local_console.gui.utils.enums import Screen
from local_console.gui.view.inference_screen.inference_screen import InferenceScreenView
from pygments.lexers import (
    JsonLexer,
)  # nopycln: import # Required by the screen's KV spec file


class InferenceScreenController:
    """
    The `InferenceScreenController` class represents a controller implementation.
    Coordinates work of the view with the model.
    The controller implements the strategy pattern. The controller connects to
    the view to control its actions.
    """

    def __init__(self, model: InferenceScreenModel, driver: Driver) -> None:
        self.model = model
        self.driver = driver
        self.view = InferenceScreenView(controller=self, model=self.model)

    def get_view(self) -> InferenceScreenView:
        return self.view

    def toggle_stream_status(self) -> None:
        camera_status = self.model.stream_status
        if camera_status == StreamStatus.Active:
            self.driver.from_sync(self.driver.streaming_rpc_stop)
        else:
            roi = self.driver.gui.views[Screen.STREAMING_SCREEN].model.image_roi
            self.driver.from_sync(self.driver.streaming_rpc_start, roi)

        self.model.stream_status = StreamStatus.Transitioning
