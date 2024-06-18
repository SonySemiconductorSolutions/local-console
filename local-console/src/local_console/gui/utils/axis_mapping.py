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
from typing import Union

# Type of ROI units: raw pixel coordinates
PixelROI = tuple[tuple[int, int], tuple[int, int]]
# Type of ROI units: normalized (from 0 to 1) with
# respect to the pixel matrix dimensions
UnitROI = tuple[tuple[float, float], tuple[float, float]]

# Fundamental constant: IMX500 pixel matrix dimensions
SENSOR_SIZE = 4056, 3040

# Default Unit ROI
DEFAULT_ROI: UnitROI = ((0, 0), (1, 1))


def pixel_roi_from_normals(normal_roi: Optional[UnitROI]) -> PixelROI:
    """
    This function maps a normalized ROI (in units from 0 to 1)
    to pixel size coordinates in the IMX500 matrix.
    """
    sensor_size = SENSOR_SIZE

    if normal_roi is None:
        return (0, 0), (sensor_size[0], sensor_size[1])

    n_start, n_size = normal_roi

    h_offset = int(denormalize_in_set(n_start[0], (0, sensor_size[0] - 1)))
    # Whereas our ROI's start is its lower-left corner,
    # the camera's ROI start is its upper-left one.
    v_offset = int(
        denormalize_in_set(1 - (n_start[1] + n_size[1]), (0, sensor_size[1] - 1))
    )
    h_size = int(denormalize_in_set(n_size[0], (0, sensor_size[0])))
    v_size = int(denormalize_in_set(n_size[1], (0, sensor_size[1])))

    return (h_offset, v_offset), (h_size, v_size)


# Typing for the number mapping functions below
Number = Union[int, float]
NumberSet = tuple[Number, Number]


def as_normal_in_set(value: Number, set_: NumberSet) -> Number:
    return (value - set_[0]) / (set_[1] - set_[0])


def denormalize_in_set(value: Number, set_: NumberSet) -> Number:
    return set_[0] + (value * (set_[1] - set_[0]))


def delta(set_: NumberSet) -> Number:
    return set_[1] - set_[0]


def get_normalized_center_subregion(
    subregion_size: tuple[int, int], widget_size: tuple[int, int]
) -> list[tuple[float, float]]:
    normalized = [(0.0, 0.0), (0.0, 0.0)]
    for dim in (0, 1):
        min_dim = as_normal_in_set(
            (widget_size[dim] - subregion_size[dim]) / 2, (0, widget_size[dim])
        )
        max_dim = as_normal_in_set(
            (widget_size[dim] + subregion_size[dim]) / 2, (0, widget_size[dim])
        )
        normalized[dim] = (min_dim, max_dim)

    return normalized


def get_dead_zone_within_widget(
    dead_zone_px: int, image_size: tuple[int, int], widget_size: tuple[int, int]
) -> list[tuple[float, float]]:
    # Dead zone removes two strips of self.dead_zone_px of width, on each dimension
    dead_zone_size = [(sz - 2 * dead_zone_px) for sz in image_size]
    return get_normalized_center_subregion(
        (dead_zone_size[0], dead_zone_size[1]), widget_size
    )


def get_dead_zone_within_image(
    dead_zone_in_widget: list[tuple[float, float]],
    active_subregion: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    # Now normalize the dead zone within the image area
    normalized = [(0.0, 0.0), (0.0, 0.0)]
    for dim in (0, 1):
        normalized[dim] = (
            as_normal_in_set(dead_zone_in_widget[dim][0], active_subregion[dim]),
            as_normal_in_set(dead_zone_in_widget[dim][1], active_subregion[dim]),
        )

    return normalized


def snap_point_in_deadzone(
    pos: tuple[float, float], dead_zone: list[tuple[float, float]]
) -> tuple[float, float]:
    snapped = list(pos)
    for dim in (0, 1):
        if pos[dim] < dead_zone[dim][0]:
            snapped[dim] = 0
        elif pos[dim] > dead_zone[dim][1]:
            snapped[dim] = 1

    return (snapped[0], snapped[1])
