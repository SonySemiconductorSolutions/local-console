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
import importlib
import json
import random
import shutil
import sys
from pathlib import Path
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis import strategies as st
from local_console.core.camera import StreamStatus
from local_console.core.config import config_to_schema
from local_console.core.config import get_default_config
from local_console.core.schemas.edge_cloud_if_v1 import StartUploadInferenceData
from local_console.core.schemas.schemas import AgentConfiguration
from local_console.gui.enums import ApplicationConfiguration
from local_console.gui.utils.axis_mapping import SENSOR_SIZE
from local_console.gui.utils.enums import Screen
from local_console.utils.local_network import LOCAL_IP

from tests.mocks.mock_paho_mqtt import MockAsyncIterator
from tests.mocks.mock_paho_mqtt import MockMQTTMessage
from tests.strategies.configs import generate_text

# The following lines need to be in this order, in order to
# be able to mock the run_on_ui_thread decorator with
# an identity function
patch(
    "local_console.gui.utils.sync_async.run_on_ui_thread", lambda fn: fn
).start()  # noqa
# TODO: simplify patching
try:
    importlib.reload(sys.modules["local_console.gui.driver"])
except Exception as e:
    print(f"Error while reloading: {e}")
from local_console.gui.driver import Driver  # noqa


def get_default_config_as_schema() -> AgentConfiguration:
    return config_to_schema(get_default_config())


def create_new(root: Path) -> Path:
    new_file = root / f"{random.randint(1, 1e6)}"
    new_file.write_bytes(b"0")
    return new_file


@pytest.fixture(autouse=True)
def common_patches():
    with (
        patch("local_console.gui.driver.TimeoutBehavior"),
        # This test does not use Hypothesis' strategies as they are not readily
        # integrable with the 'tmpdir' fixture, and anyway the functionality tested
        # by this suite is completely independent on the persistent configuration.
        patch("local_console.gui.driver.get_config", get_default_config_as_schema),
        patch("local_console.clients.agent.get_config", get_default_config_as_schema),
    ):
        yield


def test_file_move(tmpdir):
    origin = Path(tmpdir.join("fileA"))
    origin.write_bytes(b"0")

    target = Path(tmpdir.mkdir("sub").mkdir("subsub"))
    moved = Path(shutil.move(origin, target))
    assert moved.parent == target


def test_storage_paths(tmpdir):
    tgd = Path(tmpdir.mkdir("images"))
    driver = Driver(MagicMock())

    # Set default image dir
    driver.temporary_image_directory = tgd
    driver.set_image_directory(tgd)

    # Storing an image when image dir has not changed default
    new_image = create_new(tgd)
    saved = driver.save_into_image_directory(new_image)
    assert saved.parent == tgd

    # Change the target image dir
    new_image_dir = Path(tmpdir.mkdir("another_image_dir"))
    driver.set_image_directory(new_image_dir)

    # Storing an image when image dir has been changed
    new_image = create_new(tgd)
    saved = driver.save_into_image_directory(new_image)
    assert saved.parent == new_image_dir


def test_save_into_image_directory(tmpdir):
    root = Path(tmpdir)
    tgd = root / "notexists"

    driver = Driver(MagicMock())

    assert not tgd.exists()
    driver.temporary_image_directory = tgd
    driver.set_image_directory(tgd)
    assert tgd.exists()

    tgd.rmdir()

    assert not tgd.exists()
    driver.save_into_image_directory(create_new(root))
    assert tgd.exists()


def test_save_into_inferences_directory(tmpdir):
    root = Path(tmpdir)
    tgd = root / "notexists"

    driver = Driver(MagicMock())

    assert not tgd.exists()
    driver.temporary_inference_directory = tgd
    driver.set_inference_directory(tgd)
    assert tgd.exists()

    tgd.rmdir()

    assert not tgd.exists()
    driver.save_into_inferences_directory(create_new(root))
    assert tgd.exists()


def test_process_camera_upload_images(tmp_path):
    root = tmp_path

    with (
        patch.object(
            Driver, "save_into_image_directory"
        ) as mock_save_into_image_directory,
        patch.object(Driver, "update_images_display") as mock_update_display,
    ):
        driver = Driver(MagicMock())
        file = root / "images/a.png"
        driver.process_camera_upload(file)
        mock_save_into_image_directory.assert_called_once_with(file)
        mock_update_display.assert_not_called()
        driver.process_camera_upload(file)
        mock_update_display.assert_called_once_with(
            mock_save_into_image_directory.return_value
        )


def test_process_camera_upload_inferences_with_schema(tmp_path):
    root = tmp_path

    with (
        patch.object(Driver, "save_into_inferences_directory") as mock_save,
        patch.object(Driver, "update_inference_data") as mock_update_data,
        patch.object(Driver, "update_images_display") as mock_update_display,
        patch.object(
            Driver, "get_flatbuffers_inference_data"
        ) as mock_get_flatbuffers_inference_data,
        patch("local_console.gui.driver.FlatBuffers") as mock_flatbuffers,
        patch("local_console.gui.driver.process_frame") as mock_process_frame,
    ):
        driver = Driver(MagicMock())
        driver.latest_image_file = root / "inferences/a.png"
        driver.flatbuffers_schema = "objectdetection.fbs"
        file = root / "inferences/a.txt"
        mock_save.return_value = file

        mock_get_flatbuffers_inference_data.return_value = {"a": 3}
        mock_process_frame.side_effect = Exception
        driver.process_camera_upload(file)

        mock_save.assert_called_once_with(file)
        mock_flatbuffers.return_value.get_output_from_inference_results.assert_called_once_with(
            file
        )
        mock_update_data.assert_called_once_with(json.dumps({"a": 3}, indent=2))
        mock_process_frame.assert_called_once_with(driver.latest_image_file, {"a": 3})
        mock_update_display.assert_called_once_with(driver.latest_image_file)


def test_process_camera_upload_inferences_missing_schema(tmp_path):
    root = tmp_path

    with (
        patch.object(Driver, "save_into_inferences_directory") as mock_save,
        patch.object(Driver, "update_inference_data") as mock_update_data,
        patch.object(Driver, "update_images_display") as mock_update_display,
        patch("local_console.gui.driver.FlatBuffers") as mock_flatbuffers,
        patch("local_console.gui.driver.process_frame") as mock_process_frame,
        patch.object(Path, "read_text", return_value=""),
    ):
        driver = Driver(MagicMock())
        driver.latest_image_file = root / "inferences/a.png"
        file = root / "inferences/a.txt"
        mock_save.return_value = file

        driver.process_camera_upload(file)

        mock_save.assert_called_once_with(file)
        mock_flatbuffers.return_value.get_output_from_inference_results.assert_called_once_with(
            file
        )
        mock_update_data.assert_called_once_with(
            mock_save.return_value.read_text.return_value
        )
        mock_process_frame.assert_called_once_with(
            driver.latest_image_file,
            mock_flatbuffers.return_value.get_output_from_inference_results.return_value,
        )
        mock_update_display.assert_called_once_with(driver.latest_image_file)


def test_process_camera_upload_unknown(tmpdir):
    root = Path(tmpdir)

    with (
        patch.object(Driver, "update_inference_data") as mock_update_data,
        patch.object(Driver, "update_images_display") as mock_update_display,
    ):
        driver = Driver(MagicMock())
        file = root / "unknown/a.txt"

        driver.process_camera_upload(file)
        mock_update_display.assert_not_called()
        mock_update_data.assert_not_called()


@pytest.mark.trio
@given(st.integers(min_value=0, max_value=65535))
async def test_streaming_stop_required(req_id: int):
    with (
        patch("local_console.gui.driver.Agent") as mock_agent,
        patch("local_console.gui.driver.spawn_broker"),
        patch.object(
            Driver, "streaming_rpc_stop", AsyncMock()
        ) as mock_streaming_rpc_stop,
    ):
        mock_agent.return_value.publish = AsyncMock()
        mock_agent.return_value.rpc = AsyncMock()

        msg = MockMQTTMessage(f"v1/devices/me/attributes/request/{req_id}", b"{}")
        mock_agent.return_value.client.messages.return_value.__aenter__.return_value = (
            MockAsyncIterator([msg])
        )
        driver = Driver(MagicMock())
        await driver.mqtt_setup()
        mock_streaming_rpc_stop.assert_awaited_once()


@pytest.mark.trio
async def test_streaming_rpc_stop():
    with (
        patch("local_console.gui.driver.Agent") as mock_agent,
        patch("local_console.gui.driver.spawn_broker"),
    ):
        mock_agent.return_value.publish = AsyncMock()
        mock_rpc = AsyncMock()
        mock_agent.return_value.rpc = mock_rpc

        driver = Driver(MagicMock())
        await driver.streaming_rpc_stop()
        mock_rpc.assert_awaited_with(
            "backdoor-EA_Main", "StopUploadInferenceData", "{}"
        )


@pytest.mark.trio
async def test_streaming_rpc_start():
    with (
        patch("local_console.gui.driver.Agent") as mock_agent,
        patch("local_console.gui.driver.spawn_broker"),
    ):
        mock_agent.return_value.publish = AsyncMock()
        mock_rpc = AsyncMock()
        mock_agent.return_value.rpc = mock_rpc

        driver = Driver(MagicMock())
        driver.temporary_image_directory = Path("my_image_path")
        driver.temporary_inference_directory = Path("my_inference_path")
        upload_url = f"http://{LOCAL_IP}:{driver.upload_port}"
        h_size, v_size = SENSOR_SIZE

        await driver.streaming_rpc_start()
        mock_rpc.assert_awaited_with(
            "backdoor-EA_Main",
            "StartUploadInferenceData",
            StartUploadInferenceData(
                StorageName=upload_url,
                StorageSubDirectoryPath=driver.temporary_image_directory.name,
                StorageNameIR=upload_url,
                StorageSubDirectoryPathIR=driver.temporary_inference_directory.name,
                CropHOffset=0,
                CropVOffset=0,
                CropHSize=h_size,
                CropVSize=v_size,
            ).model_dump_json(),
        )


async def test_connection_status_timeout():
    driver = Driver(MagicMock())
    driver.camera_state.sensor_state = StreamStatus.Active
    await driver.connection_status_timeout()
    assert driver.camera_state.sensor_state == StreamStatus.Inactive


@pytest.mark.trio
@given(generate_text())
async def test_connection_status_timeout(config: str):
    mock_configure = AsyncMock()
    with (
        patch("local_console.gui.driver.Agent") as mock_agent,
        patch("local_console.gui.driver.spawn_broker"),
    ):
        mock_agent.return_value.configure = mock_configure
        driver = Driver(MagicMock())
        await driver.send_app_config(config)
        mock_configure.assert_awaited_with(
            ApplicationConfiguration.NAME,
            ApplicationConfiguration.CONFIG_TOPIC,
            config,
        )


def test_add_class_names() -> None:
    with (
        patch("local_console.gui.driver.Agent"),
        patch("local_console.gui.driver.spawn_broker"),
    ):
        class_id_to_name = {
            0: "Apple",
            1: "Banana",
        }
        data = {
            "perception": {
                "classification_list": [
                    {
                        "class_id": 0,
                        "score": 0.929688,
                    },
                    {
                        "class_id": 1,
                        "score": 0.070313,
                    },
                ]
            }
        }
        driver = Driver(MagicMock())
        driver.add_class_names(data, class_id_to_name)
        assert data["perception"]["classification_list"][0]["class_name"] == "Apple"
        assert data["perception"]["classification_list"][1]["class_name"] == "Banana"

        class_id_to_name = {
            0: "Apple",
        }
        driver.add_class_names(data, class_id_to_name)
        assert data["perception"]["classification_list"][0]["class_name"] == "Apple"
        assert data["perception"]["classification_list"][1]["class_name"] == "Unknown"


def test_map_class_id_to_name(tmp_path) -> None:
    label_file = tmp_path / "label.txt"
    with open(label_file, "w") as file:
        file.write("Apple\nBanana")

    with (
        patch("local_console.gui.driver.Agent"),
        patch("local_console.gui.driver.spawn_broker"),
    ):
        gui = MagicMock()
        gui.views[Screen.CONFIGURATION_SCREEN].model.app_labels = label_file
        driver = Driver(gui)
        driver.map_class_id_to_name()
        assert driver.class_id_to_name == dict({0: "Apple", 1: "Banana"})


def test_map_class_id_to_name_file_not_found(tmp_path) -> None:
    label_file = tmp_path / "label.txt"
    with open(label_file, "w") as file:
        file.write("Apple\nBanana")

    with (
        patch("local_console.gui.driver.Agent"),
        patch("local_console.gui.driver.spawn_broker"),
        patch("local_console.gui.driver.logger") as mock_logger,
        patch("builtins.open", side_effect=FileNotFoundError),
    ):
        gui = MagicMock()
        gui.views[Screen.CONFIGURATION_SCREEN].model.app_labels = label_file
        driver = Driver(gui)
        driver.map_class_id_to_name()
        mock_logger.warning.assert_called_once_with(
            "Error while reading labels text file."
        )


def test_map_class_id_to_name_exception(tmp_path) -> None:
    label_file = tmp_path / "label.txt"
    with open(label_file, "w") as file:
        file.write("Apple\nBanana")

    with (
        patch("local_console.gui.driver.Agent"),
        patch("local_console.gui.driver.spawn_broker"),
        patch("local_console.gui.driver.logger") as mock_logger,
        patch("builtins.open", side_effect=Exception),
    ):
        gui = MagicMock()
        gui.views[Screen.CONFIGURATION_SCREEN].model.app_labels = label_file
        driver = Driver(gui)
        driver.map_class_id_to_name()
        mock_logger.warning.assert_called_once_with(
            "Unknown error while reading labels text file "
        )


def test_map_class_id_to_name_none(tmp_path) -> None:
    with (
        patch("local_console.gui.driver.Agent"),
        patch("local_console.gui.driver.spawn_broker"),
    ):
        driver = Driver(MagicMock())
        driver.map_class_id_to_name()
        assert driver.class_id_to_name is None
