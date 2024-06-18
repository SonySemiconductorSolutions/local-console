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
from unittest.mock import MagicMock
from unittest.mock import patch

import hypothesis.strategies as st
from hypothesis import given
from local_console.gui.controller.configuration_screen import (
    ConfigurationScreenController,
)
from local_console.gui.enums import ApplicationSchemaFilePath
from local_console.gui.enums import ApplicationType
from local_console.gui.model.configuration_screen import ConfigurationScreenModel

from tests.strategies.configs import generate_text


def test_apply_configuration():
    with (
        patch(
            "local_console.gui.controller.configuration_screen.ConfigurationScreenView"
        ),
        patch.object(
            ConfigurationScreenController, "apply_flatbuffers_schema"
        ) as mock_apply_fb,
        patch.object(
            ConfigurationScreenController, "apply_application_configuration"
        ) as mock_apply_app_cfg,
    ):
        ctrl = ConfigurationScreenController(ConfigurationScreenModel(), MagicMock())
        ctrl.apply_configuration()
        mock_apply_fb.assert_any_call()
        mock_apply_app_cfg.assert_any_call()


def test_apply_flatbuffers_schema(tmpdir):
    model, mock_driver = ConfigurationScreenModel(), MagicMock()
    with (
        patch(
            "local_console.gui.controller.configuration_screen.ConfigurationScreenView"
        ),
        patch(
            "local_console.gui.controller.configuration_screen.FlatBuffers"
        ) as mock_flatbuffers,
    ):
        ctrl = ConfigurationScreenController(model, mock_driver)
        model.flatbuffers_schema = None
        ctrl.apply_flatbuffers_schema()
        assert model.flatbuffers_process_result == "Please select a schema file."

        model.flatbuffers_schema = Path(tmpdir)
        ctrl.apply_flatbuffers_schema()
        assert model.flatbuffers_process_result == "Not a file or file does not exist!"

        mock_flatbuffers.return_value.conform_flatbuffer_schema.return_value = (
            False,
            None,
        )
        file = Path(tmpdir) / "file.bin"
        file.write_bytes(b"0")
        model.flatbuffers_schema = file
        ctrl.apply_flatbuffers_schema()
        assert model.flatbuffers_process_result == "Not a valid flatbuffers schema"

        assert mock_driver.flatbuffers_schema != model.flatbuffers_schema
        mock_flatbuffers.return_value.conform_flatbuffer_schema.return_value = (
            True,
            None,
        )
        ctrl.apply_flatbuffers_schema()
        assert model.flatbuffers_process_result == "Success!"
        assert mock_driver.flatbuffers_schema == model.flatbuffers_schema


def test_apply_application_configuration(tmpdir):
    model, mock_driver = ConfigurationScreenModel(), MagicMock()
    with (
        patch(
            "local_console.gui.controller.configuration_screen.ConfigurationScreenView"
        ),
    ):
        ctrl = ConfigurationScreenController(model, mock_driver)

        ctrl.apply_application_configuration()
        assert model.flatbuffers_process_result is None

        file = Path(tmpdir) / "config.json"
        ctrl.update_app_configuration(str(file))
        ctrl.apply_application_configuration()
        assert model.flatbuffers_process_result == "App configuration does not exist"

        file.write_text("{")
        ctrl.apply_application_configuration()
        assert (
            model.flatbuffers_process_result == "Error parsing app configuration JSON"
        )

        file.write_text('{"a": 3}')
        model.flatbuffers_process_result = ""
        ctrl.apply_application_configuration()
        assert model.flatbuffers_process_result == ""


def test_apply_application_configuration_error(tmpdir):
    model, mock_driver = ConfigurationScreenModel(), MagicMock()
    with (
        patch(
            "local_console.gui.controller.configuration_screen.ConfigurationScreenView"
        ),
        patch("local_console.gui.controller.configuration_screen.json") as mock_json,
    ):
        ctrl = ConfigurationScreenController(model, mock_driver)

        file = Path(tmpdir) / "config.json"
        file.write_text('{"a": 3}')

        mock_json.load.side_effect = Exception
        ctrl.update_app_configuration(str(file))
        ctrl.apply_application_configuration()
        assert model.flatbuffers_process_result == "App configuration unknown error"

        mock_json.load.side_effect = PermissionError
        ctrl.apply_application_configuration()
        assert model.flatbuffers_process_result == "App configuration permission error"


def test_update_application_type():
    model, mock_driver = ConfigurationScreenModel(), MagicMock()
    with (
        patch(
            "local_console.gui.controller.configuration_screen.ConfigurationScreenView"
        ),
    ):
        ctrl = ConfigurationScreenController(model, mock_driver)

        ctrl.update_application_type(ApplicationType.CUSTOM)
        assert model.app_type == ApplicationType.CUSTOM
        assert ctrl.view.ids.labels_pick.disabled
        assert not ctrl.view.ids.schema_pick.disabled

        ctrl.update_application_type(ApplicationType.CLASSIFICATION)
        assert model.app_type == ApplicationType.CLASSIFICATION
        assert model.flatbuffers_schema == ApplicationSchemaFilePath.CLASSIFICATION
        assert not ctrl.view.ids.labels_pick.disabled
        assert ctrl.view.ids.schema_pick.disabled

        ctrl.update_application_type(ApplicationType.DETECTION)
        assert model.app_type == ApplicationType.DETECTION
        assert model.flatbuffers_schema == ApplicationSchemaFilePath.DETECTION
        assert not ctrl.view.ids.labels_pick.disabled
        assert ctrl.view.ids.schema_pick.disabled

        ctrl.update_application_type(ApplicationType.CUSTOM)
        assert ctrl.view.ids.labels_pick.disabled
        assert not ctrl.view.ids.schema_pick.disabled


@given(generate_text())
def test_update_labels(path: str):
    model = ConfigurationScreenModel()

    with (
        patch(
            "local_console.gui.controller.configuration_screen.ConfigurationScreenView"
        ),
    ):
        ctrl = ConfigurationScreenController(model, MagicMock())
        ctrl.update_app_labels(path)

        assert model.app_labels == path


@given(generate_text())
def test_update_flatbuffers_schema(path: str):
    model = ConfigurationScreenModel()

    with (
        patch(
            "local_console.gui.controller.configuration_screen.ConfigurationScreenView"
        ),
    ):
        ctrl = ConfigurationScreenController(model, MagicMock())
        ctrl.update_flatbuffers_schema(path)

        assert model.flatbuffers_schema == path


@given(st.integers(min_value=1))
def test_update_total_max_size(value: int):
    driver = MagicMock()
    with (
        patch(
            "local_console.gui.controller.configuration_screen.ConfigurationScreenView"
        ),
    ):
        ctrl = ConfigurationScreenController(MagicMock(), driver)
        ctrl.update_total_max_size(value)

        driver.total_dir_watcher.set_storage_limit.assert_called_once_with(value)


@given(generate_text())
def test_update_image_directory(path: str):
    driver = MagicMock()
    model = ConfigurationScreenModel()
    with (
        patch(
            "local_console.gui.controller.configuration_screen.ConfigurationScreenView"
        ),
    ):
        ctrl = ConfigurationScreenController(model, driver)
        ctrl.update_image_directory(path)

        driver.set_image_directory.assert_called_once_with(path)
        assert model.image_directory == path


@given(generate_text())
def test_update_inferences_directory(path: str):
    driver = MagicMock()
    model = ConfigurationScreenModel()
    with (
        patch(
            "local_console.gui.controller.configuration_screen.ConfigurationScreenView"
        ),
    ):
        ctrl = ConfigurationScreenController(model, driver)
        ctrl.update_inferences_directory(path)

        driver.set_inference_directory.assert_called_once_with(path)
        assert model.inferences_directory == path


def test_get_view():
    with (
        patch(
            "local_console.gui.controller.configuration_screen.ConfigurationScreenView"
        ),
    ):
        ctrl = ConfigurationScreenController(MagicMock(), MagicMock())
        assert ctrl.view == ctrl.get_view()
