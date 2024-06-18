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

logger = logging.getLogger(__name__)

AOT_XTENSA_HEADER = (
    0x00,
    0x61,
    0x6F,
    0x74,
    0x03,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x24,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x01,
    0x00,
    0x5E,
    0x00,
    0x01,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x78,
    0x74,
    0x65,
    0x6E,
    0x73,
    0x61,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
)

IMX500_MODEL_HEADER = (0x34, 0x36, 0x34, 0x39)


def validate_app_file(app_file: Path) -> bool:
    try:
        with app_file.open("rb") as file_in:
            file_header = file_in.read(len(AOT_XTENSA_HEADER))
    except Exception as e:
        logger.warning(f"Exception: {e}")
        return False

    return file_header == bytes(AOT_XTENSA_HEADER)


def validate_imx500_model_file(model_file: Path) -> bool:
    try:
        with model_file.open("rb") as file_in:
            file_header = file_in.read(len(IMX500_MODEL_HEADER))
    except Exception as e:
        logger.warning(f"Exception: {e}")
        return False

    return file_header == bytes(IMX500_MODEL_HEADER)
