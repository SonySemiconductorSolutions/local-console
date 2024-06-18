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

from pydantic import BaseModel


class Bbox(BaseModel):
    left: int
    top: int
    right: int
    bottom: int


class Detection(BaseModel):
    class_id: int
    bounding_box_type: str
    bounding_box: Bbox
    score: float
    class_name: Optional[str] = None


class Perception(BaseModel):
    object_detection_list: list[Detection]


class ObjectDetection(BaseModel):
    perception: Perception
