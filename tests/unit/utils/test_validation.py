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

from local_console.utils.validation import validate_app_file
from local_console.utils.validation import validate_imx500_model_file


def test_validate_app_file():
    with patch("pathlib.Path.open", side_effect=PermissionError):
        app_file = Path("/tmp/node.xtensa.aot.signed")
        assert not validate_app_file(app_file)


def test_validate_imx500_model_file():
    with patch("pathlib.Path.open", side_effect=PermissionError):
        model_file = Path("/tmp/network.pkg")
        assert not validate_imx500_model_file(model_file)
