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
from local_console.gui.utils.axis_mapping import as_normal_in_set
from local_console.gui.utils.axis_mapping import DEFAULT_ROI
from local_console.gui.utils.axis_mapping import get_dead_zone_within_image
from local_console.gui.utils.axis_mapping import get_dead_zone_within_widget
from local_console.gui.utils.axis_mapping import get_normalized_center_subregion
from local_console.gui.utils.axis_mapping import pixel_roi_from_normals
from local_console.gui.utils.axis_mapping import SENSOR_SIZE
from local_console.gui.utils.axis_mapping import snap_point_in_deadzone
from pytest import approx


def test_normalizing():
    low = 1
    high = 3
    assert as_normal_in_set(2, (low, high)) == 0.5
    assert as_normal_in_set(low, (low, high)) == 0
    assert as_normal_in_set(high, (low, high)) == 1
    assert as_normal_in_set(0, (low, high)) == -0.5
    assert as_normal_in_set(4, (low, high)) == 1.5


def test_normals():
    low = 0.2
    high = 0.7
    assert as_normal_in_set(0.1, (low, high)) < 0
    assert 0.9 < as_normal_in_set(0.65, (low, high)) < 1
    assert 0 < as_normal_in_set(0.21, (low, high)) < 0.1


def test_unit_roi_denormalization():
    denorm = pixel_roi_from_normals(DEFAULT_ROI)
    assert denorm == ((0, 0), (SENSOR_SIZE[0], SENSOR_SIZE[1]))


def test_reference_point_denormalization():
    unit_v_offset = 0.1
    roi = ((0.5, unit_v_offset), (0.5, 0.5))
    (h_offset, v_offset), (h_size, v_size) = pixel_roi_from_normals(roi)

    assert h_size == SENSOR_SIZE[0] / 2
    assert v_size == SENSOR_SIZE[1] / 2
    assert h_offset == (SENSOR_SIZE[0] / 2 - 1)
    assert v_offset == (4 * SENSOR_SIZE[1] / 10 - 1)


def test_dead_zone_snapping_to_nearest_border():
    dead_zone_px = 20

    # This case is when the heights are equal
    widget_size = (400, 200)
    image_size = (300, 200)

    active_subregion = get_normalized_center_subregion(image_size, widget_size)
    assert active_subregion[1] == (0, 1)  # This is because heights are equal
    assert active_subregion[0] == approx((50 / 400, (400 - 50) / 400))

    dead_subregion_w = get_dead_zone_within_widget(
        dead_zone_px, image_size, widget_size
    )
    dead_subregion_i = get_dead_zone_within_image(dead_subregion_w, active_subregion)

    assert dead_subregion_i[1] == approx((20 / 200, (200 - 20) / 200))
    assert dead_subregion_i[0] == approx(
        (20 / (400 - 100), ((400 - 100) - 20) / (400 - 100))
    )

    # Point within the left dead zone
    pos_normalized = (0.5 * dead_zone_px / image_size[0], 0.5)
    snapped = snap_point_in_deadzone(pos_normalized, dead_subregion_i)
    assert snapped[0] == 0
    assert snapped[1] == 0.5

    # Point within the right dead zone
    pos_normalized = (1 - 0.5 * (dead_zone_px / image_size[0]), 0.5)
    snapped = snap_point_in_deadzone(pos_normalized, dead_subregion_i)
    assert snapped[0] == 1
    assert snapped[1] == 0.5

    # Point within the bottom dead zone
    pos_normalized = (0.5, 0.5 * dead_zone_px / image_size[1])
    snapped = snap_point_in_deadzone(pos_normalized, dead_subregion_i)
    assert snapped[0] == 0.5
    assert snapped[1] == 0

    # Point within the top dead zone
    pos_normalized = (0.5, 1 - 0.5 * (dead_zone_px / image_size[1]))
    snapped = snap_point_in_deadzone(pos_normalized, dead_subregion_i)
    assert snapped[0] == 0.5
    assert snapped[1] == 1
