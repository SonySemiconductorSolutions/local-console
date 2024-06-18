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
from typing import Any

import cv2  # type: ignore
from local_console.core.schemas.tasks.objectdetection import ObjectDetection


def process_frame(image: Path, output_tensor: Any) -> None:
    if not isinstance(output_tensor, dict):
        return

    img = cv2.imread(image)

    obj = ObjectDetection(**output_tensor)
    for detection in obj.perception.object_detection_list:
        bbox_2d = detection.bounding_box
        xmin, xmax = bbox_2d.left, bbox_2d.right
        ymax, ymin = bbox_2d.bottom, bbox_2d.top

        img = cv2.rectangle(img, (xmin, ymin), (xmax, ymax), (0, 0, 255), 2)
        img = cv2.putText(
            img,
            f"{detection.class_name if detection.class_name else detection.class_id}: {detection.score:.2f}",
            (xmin, ymin),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )
    cv2.imwrite(image, img)
