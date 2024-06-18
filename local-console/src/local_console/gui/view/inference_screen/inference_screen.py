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
from local_console.gui.view.base_screen import BaseScreenView
from local_console.gui.view.common.components import (
    CodeInputCustom,
)  # nopycln: import # Required by the screen's KV spec file
from local_console.gui.view.common.components import (
    ImageWithROI,
)  # nopycln: import # Required by the screen's KV spec file


class InferenceScreenView(BaseScreenView):
    def entry_actions(self) -> None:
        self.model_is_changed()

    def toggle_stream_status(self) -> None:
        self.controller.toggle_stream_status()

    def model_is_changed(self) -> None:
        """
        Called whenever any change has occurred in the data model.
        The view in this method tracks these changes and updates the UI
        according to these changes.
        """
        stream_active = self.model.stream_status == StreamStatus.Active

        self.ids.stream_flag.text = self.model.stream_status.value
        self.ids.btn_stream_control.style = (
            "elevated" if not stream_active else "filled"
        )
