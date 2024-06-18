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
import shutil
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests
from local_console.servers.webserver import SyncWebserver

logger = logging.getLogger(__name__)


@pytest.fixture
def sync_webserver(tmp_path):
    with SyncWebserver(tmp_path) as server:
        yield server


def test_happy_path(sync_webserver):
    file_name = "testfile.txt"
    url = f"http://localhost:{sync_webserver.port}/{file_name}"
    data = b"This is a test file"

    # Upload file
    response = requests.put(url, data=data)
    assert response.status_code == 200

    # Verify the file was created
    content = sync_webserver.dir.joinpath(file_name).read_bytes()
    assert content == data


def test_save_error(sync_webserver, caplog):
    file_name = "testfile.txt"
    url = f"http://localhost:{sync_webserver.port}/{file_name}"
    data = b"data"

    with patch(
        "local_console.servers.webserver.Path.write_bytes", side_effect=IOError()
    ):
        response = requests.put(url, data=data)
        assert response.status_code == 200
        assert "Error while receiving data" in caplog.text


def test_callback_error(sync_webserver, caplog):
    file_name = "testfile.txt"
    url = f"http://localhost:{sync_webserver.port}/{file_name}"
    data = b"data"

    mock_callback = Mock(side_effect=IOError())
    sync_webserver.on_incoming = mock_callback

    response = requests.put(url, data=data)
    assert response.status_code == 200
    assert "Error while receiving data" not in caplog.text
    assert "Error while invoking callback" in caplog.text


def test_unexpected_deletion_of_save_directory(sync_webserver, tmp_path_factory):
    save_dir = tmp_path_factory.mktemp("savedir")
    sync_webserver.dir = save_dir

    file_name = "testfile.txt"
    url = f"http://localhost:{sync_webserver.port}/{file_name}"
    data = b"data"

    # Upload before deletion should be normal
    response = requests.put(url, data=data)
    assert response.status_code == 200
    content = save_dir.joinpath(file_name).read_bytes()
    assert content == data

    # Unexpectedly remove the save directory and upload again
    shutil.rmtree(save_dir)
    response = requests.put(url, data=data)

    # Outcome should be success
    assert response.status_code == 200
    content = save_dir.joinpath(file_name).read_bytes()
    assert content == data
