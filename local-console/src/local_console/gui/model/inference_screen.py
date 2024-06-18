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

from local_console.core.camera import StreamStatus
from local_console.gui.model.base_model import BaseScreenModel


class InferenceScreenModel(BaseScreenModel):
    """
    The Model for the Inference screen is composed of the data:
    - The stream status: Active(True) or Inactive(False)
    - The image directory: path of the image directory
    - The inferences directory: path of the inferences directory
    """

    def __init__(self) -> None:
        self._stream_status = StreamStatus.Inactive
        self._image_directory: Optional[Path] = None
        self._inferences_directory: Optional[Path] = None

    @property
    def stream_status(self) -> StreamStatus:
        return self._stream_status

    @stream_status.setter
    def stream_status(self, value: StreamStatus) -> None:
        self._stream_status = value
        self.notify_observers()

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
