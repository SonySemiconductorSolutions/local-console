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
from local_console.gui.model.base_model import BaseScreenModel
from local_console.gui.utils.axis_mapping import DEFAULT_ROI
from local_console.gui.utils.axis_mapping import UnitROI


class StreamingScreenModel(BaseScreenModel):
    """
    The Model for the Streaming screen is composed of two data:
    - The stream status: Active(True) or Inactive(False)
    - The image ROI: a bounding box within the image
    """

    def __init__(self) -> None:
        self._stream_status = StreamStatus.Inactive
        self._image_roi: UnitROI = DEFAULT_ROI

    @property
    def stream_status(self) -> StreamStatus:
        return self._stream_status

    @stream_status.setter
    def stream_status(self, value: StreamStatus) -> None:
        self._stream_status = value
        self.notify_observers()

    @property
    def image_roi(self) -> UnitROI:
        return self._image_roi

    @image_roi.setter
    def image_roi(self, value: UnitROI) -> None:
        self._image_roi = value
        self.notify_observers()

    @property
    def has_default_roi(self) -> bool:
        return self.image_roi == DEFAULT_ROI
