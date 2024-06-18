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
from collections.abc import Iterator
from contextlib import contextmanager
from unittest.mock import MagicMock
from unittest.mock import patch

from local_console.utils.logger import configure_logger
from local_console.utils.logger import LOG_FORMAT


@contextmanager
def mock_logging() -> Iterator[MagicMock]:
    with patch("local_console.utils.logger.logging") as mock_logging:
        yield mock_logging


def test_configure_logger():
    with mock_logging() as mock_log:
        configure_logger(False, False)
        mock_log.basicConfig.assert_called_once_with(
            format=LOG_FORMAT, level=mock_log.INFO
        )


def test_configure_logger_silent():
    with mock_logging() as mock_log:
        configure_logger(True, False)
        mock_log.basicConfig.assert_called_once_with(
            format=LOG_FORMAT, level=mock_log.WARNING
        )


def test_configure_logger_verbose():
    with mock_logging() as mock_log:
        configure_logger(False, True)
        mock_log.basicConfig.assert_called_once_with(
            format=LOG_FORMAT, level=mock_log.DEBUG
        )


def test_configure_logger_silent_verbose():
    with mock_logging() as mock_log:
        configure_logger(True, True)
        mock_log.basicConfig.assert_called_once_with(
            format=LOG_FORMAT, level=mock_log.WARNING
        )
