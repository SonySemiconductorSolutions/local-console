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
from typing import Optional

from kivy.config import Config

logger = logging.getLogger(__name__)

CONFIG_PATH = str(Path(__file__).parent / "assets/config.ini")


def configure() -> None:
    if Path(CONFIG_PATH).is_file():
        Config.read(CONFIG_PATH)
    else:
        logger.warning("Error while reading configuration file")


def resource_path(relative_path: str) -> Optional[str]:
    base_path = Path(__file__).parent
    target = base_path.joinpath(relative_path).resolve()
    if target.is_file():
        return str(target)
    return None
