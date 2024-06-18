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
from unittest.mock import patch

import local_console.gui.config as config
from local_console.gui.config import CONFIG_PATH
from local_console.gui.config import configure
from local_console.gui.config import resource_path


def test_configure():
    with patch("local_console.gui.config.Config.read") as mock_read:
        configure()
        mock_read.assert_called_once_with(CONFIG_PATH)


def test_configure_file_no_exists():
    with (
        patch("local_console.gui.config.Path.is_file") as mock_is_file,
        patch("local_console.gui.config.Config.read") as mock_read,
    ):
        mock_is_file.return_value = False
        configure()
        mock_read.assert_not_called()


def test_resource_path():
    assert resource_path("assets/config.ini") == str(
        Path(config.__file__).parent / "assets/config.ini"
    )
    assert resource_path("config.py") == str(Path(config.__file__).parent / "config.py")
    assert resource_path("wrong_file.txt") is None
