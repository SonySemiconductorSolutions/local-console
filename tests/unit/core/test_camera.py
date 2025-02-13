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
import json
import random
from base64 import b64encode
from pathlib import Path
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import hypothesis.strategies as st
import pytest
import trio
from hypothesis import given
from local_console.core.camera.enums import ApplicationConfiguration
from local_console.core.camera.enums import ApplicationType
from local_console.core.camera.enums import DeploymentType
from local_console.core.camera.enums import DeployStage
from local_console.core.camera.enums import MQTTTopics
from local_console.core.camera.enums import StreamStatus
from local_console.core.camera.mixin_mqtt import DEPLOY_STATUS_TOPIC
from local_console.core.camera.mixin_mqtt import EA_STATE_TOPIC
from local_console.core.camera.mixin_mqtt import SYSINFO_TOPIC
from local_console.core.camera.qr.qr import get_qr_object
from local_console.core.camera.qr.qr import qr_string
from local_console.core.commands.deploy import EVP1DeployFSM
from local_console.core.commands.deploy import get_empty_deployment
from local_console.core.error.base import UserException
from local_console.core.error.code import ErrorCodes
from local_console.core.schemas.edge_cloud_if_v1 import DeviceConfiguration
from local_console.core.schemas.schemas import OnWireProtocol
from local_console.utils.tracking import TrackingVariable

from tests.fixtures.camera import cs_init
from tests.fixtures.camera import cs_init_context
from tests.mocks.mock_configs import config_without_io
from tests.strategies.configs import generate_invalid_ip
from tests.strategies.configs import generate_invalid_port_number
from tests.strategies.configs import generate_random_characters
from tests.strategies.configs import generate_valid_device_configuration
from tests.strategies.configs import generate_valid_ip
from tests.strategies.configs import generate_valid_port_number
from tests.strategies.samplers.configs import GlobalConfigurationSampler


def create_new(root: Path) -> Path:
    new_file = root / f"{random.randint(1, int(1e6))}"
    new_file.write_bytes(b"0")
    return new_file


@given(
    generate_valid_ip(),
    generate_valid_port_number(),
    st.booleans(),
    st.integers(min_value=-1, max_value=100),
    generate_random_characters(min_size=1, max_size=32),
)
def test_get_qr_object(
    ip: str,
    port: str,
    tls_enabled: bool,
    border: int,
    text: str,
) -> None:
    with patch(
        "local_console.core.camera.qr.qr.qr_string", return_value=""
    ) as mock_qr_string:
        qr_code = get_qr_object(
            mqtt_host=ip,
            mqtt_port=port,
            tls_enabled=tls_enabled,
            ntp_server=ip,
            ip_address=ip,
            subnet_mask=ip,
            gateway=ip,
            dns_server=ip,
            wifi_ssid=text,
            wifi_password=text,
            border=border,
        )
        assert qr_code is not None

        mock_qr_string.assert_called_once_with(
            ip,
            port,
            tls_enabled,
            ip,
            ip,
            ip,
            ip,
            ip,
            text,
            text,
        )


@given(
    generate_invalid_ip(),
    generate_invalid_port_number(),
    st.booleans(),
    st.integers(min_value=-1, max_value=100),
    generate_random_characters(min_size=1, max_size=32),
)
def test_get_qr_object_invalid(
    ip: str,
    port: str,
    tls_enabled: bool,
    border: int,
    text: str,
) -> None:
    with patch(
        "local_console.core.camera.qr.qr.qr_string", return_value=""
    ) as mock_qr_string:
        qr_code = get_qr_object(
            mqtt_host=ip,
            mqtt_port=port,
            tls_enabled=tls_enabled,
            ntp_server=ip,
            ip_address=ip,
            subnet_mask=ip,
            gateway=ip,
            dns_server=ip,
            wifi_ssid=text,
            wifi_password=text,
            border=border,
        )
        assert qr_code is not None

        mock_qr_string.assert_called_once_with(
            ip,
            port,
            tls_enabled,
            ip,
            ip,
            ip,
            ip,
            ip,
            text,
            text,
        )


@given(
    generate_valid_ip(),
    generate_valid_port_number(),
    st.booleans(),
    generate_random_characters(min_size=1, max_size=32),
)
def test_get_qr_string(
    ip: str,
    port: str,
    tls_enabled: bool,
    text: str,
) -> None:
    output = qr_string(
        mqtt_host=ip,
        mqtt_port=port,
        tls_enabled=tls_enabled,
        ntp_server=ip,
        ip_address=ip,
        subnet_mask=ip,
        gateway=ip,
        wifi_ssid=text,
        wifi_password=text,
        dns_server=ip,
    )

    tls_flag = 0 if tls_enabled else 1
    assert (
        output
        == f"AAIAAAAAAAAAAAAAAAAAAA==N=11;E={ip};H={port};t={tls_flag};S={text};P={text};I={ip};K={ip};G={ip};D={ip};T={ip};U1FS"
    )


@pytest.mark.trio
async def test_lifecycle(cs_init, nursery) -> None:
    camera_state = cs_init
    mock_webserver = AsyncMock()
    mock_dir_monitor = Mock()
    camera_state.blobs_webserver_task = mock_webserver
    camera_state.dir_monitor = mock_dir_monitor

    async def mock_mqtt_setup(*, task_status=trio.TASK_STATUS_IGNORED):
        task_status.started(True)

    camera_state.mqtt_setup = mock_mqtt_setup

    # State after instance construction
    assert not camera_state._started.is_set()
    assert camera_state._nursery is None
    assert camera_state._cancel_scope is None

    # Behavior of startup()
    assert await nursery.start(camera_state.startup, 1883)
    await camera_state._started.wait()
    mock_webserver.assert_called_once()
    mock_dir_monitor.start.assert_called_once()
    assert camera_state._nursery is not None
    assert not camera_state._cancel_scope.cancel_called

    # Behavior of shutdown()
    camera_state.shutdown()
    await camera_state._stopped.wait()
    mock_dir_monitor.stop.assert_called_once()
    assert camera_state._cancel_scope.cancel_called
    assert len(nursery.child_tasks) == 0


@given(
    generate_valid_ip(),
    generate_valid_port_number(),
    st.booleans(),
)
def test_get_qr_string_no_static_ip(
    ip: str,
    port: str,
    tls_enabled: bool,
) -> None:
    output = qr_string(
        mqtt_host=ip,
        mqtt_port=port,
        tls_enabled=tls_enabled,
        ntp_server=ip,
    )

    tls_flag = 0 if tls_enabled else 1
    assert (
        output
        == f"AAIAAAAAAAAAAAAAAAAAAA==N=11;E={ip};H={port};t={tls_flag};T={ip};U1FS"
    )


@pytest.mark.trio
@given(generate_valid_device_configuration(), st.sampled_from(OnWireProtocol))
async def test_process_state_topic_correct(
    device_config: DeviceConfiguration, onwire_schema: OnWireProtocol
) -> None:
    async with (
        trio.open_nursery() as nursery,
        cs_init_context() as camera,
    ):
        observer = AsyncMock()
        camera._onwire_schema = onwire_schema
        camera.mqtt_client = AsyncMock()
        camera.device_config.subscribe_async(observer)
        observer.assert_not_awaited()

        backdoor_state = {
            "state/backdoor-EA_Main/placeholder": b64encode(
                device_config.model_dump_json().encode("utf-8")
            ).decode("utf-8")
        }
        await camera._process_state_topic(backdoor_state)

        observer.assert_awaited_once_with(device_config, None)
        assert camera.device_config.value == device_config
        assert camera.stream_status.value == StreamStatus.from_string(
            device_config.Status.Sensor
        )
        nursery.cancel_scope.cancel()


@pytest.mark.trio
@pytest.mark.parametrize(
    "schema",
    [
        (OnWireProtocol.EVP1,),
        (OnWireProtocol.EVP2,),
    ],
)
async def test_process_state_topic_wrong(schema, caplog, cs_init) -> None:
    camera = cs_init
    camera._onwire_schema = schema
    wrong_obj = {"a": "b"}
    backdoor_state = {
        "state/backdoor-EA_Main/placeholder": b64encode(json.dumps(wrong_obj).encode())
    }
    await camera._process_state_topic(backdoor_state)
    assert "Error while validating device configuration" in caplog.text


@pytest.mark.trio
@given(proto_spec=st.sampled_from(OnWireProtocol))
async def test_process_systeminfo(proto_spec: OnWireProtocol) -> None:
    async with (
        trio.open_nursery() as nursery,
        cs_init_context() as camera,
    ):
        sysinfo_report = {"systemInfo": {"protocolVersion": str(proto_spec)}}
        await camera._process_sysinfo_topic(sysinfo_report)

        assert camera.attributes_available
        assert camera._onwire_schema == proto_spec
        nursery.cancel_scope.cancel()


@pytest.mark.trio
async def test_process_deploy_status_evp1(cs_init) -> None:
    camera = cs_init
    camera._onwire_schema = OnWireProtocol.EVP1
    dummy_deployment = {"a": "b"}

    status_report = {"deploymentStatus": json.dumps(dummy_deployment)}
    await camera._process_deploy_status_topic(status_report)

    assert camera.deploy_status.value == dummy_deployment
    assert camera.attributes_available


@pytest.mark.trio
async def test_process_deploy_status_evp2(cs_init) -> None:
    camera = cs_init
    camera._onwire_schema = OnWireProtocol.EVP2
    dummy_deployment = {"a": "b"}

    status_report = {"deploymentStatus": dummy_deployment}
    await camera._process_deploy_status_topic(status_report)

    assert camera.deploy_status.value == dummy_deployment
    assert camera.attributes_available


@pytest.mark.trio
async def test_process_incoming_telemetry(cs_init) -> None:
    with patch("local_console.core.camera.mixin_mqtt.datetime") as mock_time:
        camera = cs_init
        mock_now = Mock()
        mock_time.now.return_value = mock_now

        dummy_telemetry = {"a": "b"}
        await camera.process_incoming("v1/devices/me/telemetry", dummy_telemetry)

        assert camera._last_reception == mock_now


@pytest.mark.trio
@pytest.mark.parametrize(
    "topic, function",
    [
        (EA_STATE_TOPIC, "_process_state_topic"),
        (SYSINFO_TOPIC, "_process_sysinfo_topic"),
        (DEPLOY_STATUS_TOPIC, "_process_deploy_status_topic"),
    ],
)
async def test_process_incoming(topic, function, cs_init) -> None:
    camera = cs_init
    with (patch.object(camera, function) as mock_proc,):
        payload = {topic: {"a": "b"}}
        await camera.process_incoming(MQTTTopics.ATTRIBUTES.value, payload)
        mock_proc.assert_awaited_once_with(payload)


@pytest.mark.trio
async def test_process_deploy_fsm(nursery, tmp_path, cs_init) -> None:
    camera = cs_init
    camera.mqtt_client = AsyncMock()

    # setup for parsing deployment status messages
    camera.mqtt_client.onwire_schema = OnWireProtocol.EVP2

    # Dummy module to deploy
    module = tmp_path / "module"
    module.touch()

    # async setup
    simple_gconf = GlobalConfigurationSampler(num_of_devices=1).sample()
    device_conf = simple_gconf.devices[0]
    with (
        config_without_io(simple_gconf),
        patch("local_console.core.commands.deploy.SyncWebserver"),
        patch("local_console.core.camera.mixin_mqtt.Agent") as mock_agent,
        patch(
            "local_console.core.camera.state.config_obj.get_device_config",
            return_value=device_conf,
        ) as mock_device_config,
        patch(
            "local_console.core.camera.state.DeployFSM.instantiate"
        ) as mock_instantiate,
        patch("trio.Event") as mock_trio_event,
        patch(
            "local_console.core.camera.state.single_module_manifest_setup"
        ) as mock_single_module,
        patch.object(camera, "deploy_operation", AsyncMock()) as mock_deploy,
    ):
        mock_agent.deploy = AsyncMock()
        mock_instantiate.return_value = AsyncMock()
        mock_trio_event.return_value = AsyncMock()
        camera._nursery = nursery

        # trigger deployment
        camera.module_file.value = module
        await camera.do_app_deployment()

        assert mock_instantiate.call_count == 2
        mock_instantiate.assert_called_with(
            camera.mqtt_client.onwire_schema,
            camera.mqtt_client.deploy,
            camera.deploy_stage.aset,
        )
        mock_single_module.assert_called_once_with(
            ApplicationConfiguration.NAME,
            module,
            mock_instantiate.return_value.webserver,
            device_conf,
        )
        mock_instantiate.return_value.set_manifest.assert_called_with(
            mock_single_module.return_value
        )
        mock_deploy.aset.assert_awaited_once_with(DeploymentType.Application)
        mock_device_config.assert_called()


@pytest.mark.trio
async def test_process_undeploy_fsm(nursery, tmp_path, cs_init) -> None:
    camera = cs_init
    camera._nursery = nursery
    camera.mqtt_client = AsyncMock()
    camera._onwire_schema = OnWireProtocol.EVP1
    camera.mqtt_client.onwire_schema = camera._onwire_schema

    empty_depl = get_empty_deployment()
    dep_id = empty_depl.deployment.deploymentId

    waiting_event = trio.Event()
    applied_event = trio.Event()

    # Intercept FSM instantiation such that the stage callback is
    # augmented with the setting of the '*_event' signals above.
    def instantiate_intercept(
        onwire_schema, deploy_fn, stage_callback=None, **kwargs
    ) -> EVP1DeployFSM:

        async def sync_fn(stage: DeployStage) -> None:
            if stage == DeployStage.WaitAppliedConfirmation:
                waiting_event.set()
            elif stage == DeployStage.Done:
                applied_event.set()

            await stage_callback(stage)

        return EVP1DeployFSM(deploy_fn, sync_fn, **kwargs)

    async def test_fn():
        # patch()ing doesn't seem to cover async functions
        # called via nursery.start_soon()...
        with (
            patch("local_console.core.commands.deploy.TimeoutBehavior"),
            patch(
                "local_console.core.camera.state.get_empty_deployment",
                return_value=empty_depl,
            ),
            patch(
                "local_console.core.commands.deploy.DeployFSM.instantiate",
                instantiate_intercept,
            ),
        ):
            await camera._undeploy_apps()

    nursery.start_soon(test_fn)
    await waiting_event.wait()

    payload = {
        "deploymentStatus": '{"instances":{},"modules":{},"deploymentId":"'
        + dep_id
        + '","reconcileStatus":"ok"}'
    }
    await camera.process_incoming("v1/devices/me/attributes", payload)

    await applied_event.wait()
    assert applied_event.is_set()


@pytest.mark.trio
async def test_storage_paths(tmp_path_factory, cs_init) -> None:
    camera_state = cs_init
    tgd = Path(tmp_path_factory.mktemp("images"))

    # Set default image dir
    camera_state.image_dir_path.value = tgd

    # Storing an image when image dir has not changed default
    new_image = create_new(tgd)
    saved = camera_state._save_into_input_directory(
        new_image.name, new_image.read_bytes(), tgd
    )
    assert saved.parent == tgd

    # Change the target image dir
    new_image_dir = Path(tmp_path_factory.mktemp("another_image_dir"))
    camera_state.image_dir_path.value = new_image_dir

    # Storing an image when image dir has been changed
    new_image = create_new(tgd)
    saved = camera_state._save_into_input_directory(
        new_image.name, new_image.read_bytes(), new_image_dir
    )
    assert saved.parent == new_image_dir


@pytest.mark.trio
async def test_storage_paths_validation_on_windows(tmp_path_factory, cs_init) -> None:
    camera_state = cs_init
    root_dir = tmp_path_factory.mktemp("root")
    docs_dir = root_dir.joinpath("documents")
    docs_dir.mkdir()
    out_of_docs = root_dir.joinpath("rogue_dir")
    out_of_docs.mkdir()

    with (
        patch("platform.system", return_value="Windows"),
        patch(
            "local_console.core.camera.mixin_streaming.get_default_files_dir",
            return_value=docs_dir,
        ),
    ):
        with pytest.raises(
            UserException,
            match="Please select your folders under your main 'Documents' folder",
        ) as error:
            camera_state.image_dir_path.value = out_of_docs
        assert error.value.code == ErrorCodes.EXTERNAL_CANNOT_USE_DIRECTORY


@pytest.mark.trio
async def test_storage_paths_validation_other_error(tmp_path_factory, cs_init) -> None:
    camera_state = cs_init
    root_dir = tmp_path_factory.mktemp("root")
    tgd = root_dir.joinpath("good_dir")
    tgd.mkdir()

    with (
        patch("platform.system", return_value="Windows"),
        patch("pathlib.Path.write_bytes", side_effect=IOError("could not write")),
    ):
        with pytest.raises(UserException) as error:
            camera_state.image_dir_path.value = tgd
        assert error.value.code == ErrorCodes.EXTERNAL_CANNOT_USE_DIRECTORY


@pytest.mark.trio
async def test_save_into_image_directory(tmp_path, cs_init) -> None:
    camera_state = cs_init
    root = tmp_path
    tgd = root / "notexists"

    assert not tgd.exists()
    camera_state.image_dir_path.value = tgd
    assert tgd.exists()

    tgd.rmdir()

    assert not tgd.exists()
    in_file = create_new(root)
    camera_state._save_into_input_directory(in_file.name, in_file.read_bytes(), tgd)
    assert tgd.exists()


@pytest.mark.trio
async def test_save_into_image_directory_exists(tmp_path, cs_init) -> None:
    camera_state = cs_init
    root = tmp_path
    tgd = root / "notexists"
    incoming_file = create_new(root)

    assert not tgd.exists()
    camera_state.image_dir_path.value = tgd
    assert tgd.exists()

    camera_state._save_into_input_directory(
        incoming_file.name, incoming_file.read_bytes(), tgd
    )
    assert tgd.exists()

    # second path with the same name to force removing previous file
    incoming_file_2 = root / incoming_file.name
    incoming_file_2.write_bytes(b"0")

    camera_state._save_into_input_directory(
        incoming_file_2.name, incoming_file_2.read_bytes(), tgd
    )
    assert tgd.exists()


@pytest.mark.trio
async def test_save_into_inferences_directory(tmp_path, cs_init) -> None:
    camera_state = cs_init
    root = tmp_path
    tgd = root / "notexists"

    assert not tgd.exists()
    camera_state.inference_dir_path.value = tgd
    assert tgd.exists()

    tgd.rmdir()

    assert not tgd.exists()
    in_file = create_new(root)
    camera_state._save_into_input_directory(in_file.name, in_file.read_bytes(), tgd)
    assert tgd.exists()


@pytest.mark.trio
async def test_save_into_inferences_directory_already_exists(tmp_path, cs_init) -> None:
    camera_state = cs_init
    root = tmp_path
    tgd = root / "notexists"
    incoming_file = create_new(root)

    assert not tgd.exists()
    camera_state.inference_dir_path.value = tgd
    assert tgd.exists()

    camera_state._save_into_input_directory(
        incoming_file.name, incoming_file.read_bytes(), tgd
    )
    assert tgd.exists()

    # second path with the same name to force removing previous file
    incoming_file_2 = root / incoming_file.name
    incoming_file_2.write_bytes(b"0")

    camera_state._save_into_input_directory(
        incoming_file_2.name, incoming_file_2.read_bytes(), tgd
    )
    assert tgd.exists()


@pytest.mark.trio
async def test_process_camera_upload_image(tmp_path_factory, cs_init) -> None:
    inferences_dir = tmp_path_factory.mktemp("inferences")
    images_dir = tmp_path_factory.mktemp("images")

    camera_state = cs_init
    camera_state.inference_dir_path.value = inferences_dir
    camera_state.image_dir_path.value = images_dir

    with (
        patch.object(
            camera_state, "_save_into_input_directory", return_value=Path("/tmp/a.jpg")
        ) as mock_save,
    ):
        file_name = "/images/a.jpg"
        camera_state._process_camera_upload(b"", file_name)
        mock_save.assert_called()


@pytest.mark.trio
async def test_process_camera_upload_inferences_with_schema(
    tmp_path_factory, cs_init
) -> None:
    root = tmp_path_factory.getbasetemp()
    inferences_dir = tmp_path_factory.mktemp("inferences")
    images_dir = tmp_path_factory.mktemp("images")

    camera_state = cs_init
    camera_state.inference_dir_path.value = inferences_dir
    camera_state.image_dir_path.value = images_dir

    with (
        patch.object(
            camera_state, "_save_into_input_directory", return_value=Path("/tmp/a.jpg")
        ) as mock_save,
        patch(
            "local_console.core.camera.mixin_streaming.get_output_from_inference_results"
        ) as mock_get_output_from_inference_results,
        patch(
            "local_console.core.camera.mixin_streaming.Path.read_bytes",
            return_value=b"boo",
        ),
        patch(
            "local_console.core.camera.mixin_streaming.Path.read_text",
            return_value="boo",
        ),
    ):
        camera_state.vapp_type = TrackingVariable(ApplicationType.CLASSIFICATION.value)
        camera_state.vapp_schema_file.value = Path("objectdetection.fbs")

        image_file_in = root / "images/a.jpg"
        image_file_saved = images_dir / image_file_in.name
        mock_save.return_value = image_file_saved
        camera_state._process_camera_upload(b"", image_file_in)
        mock_save.assert_called_with(image_file_in.name, b"", images_dir)

        inference_file_in = root / "inferences/a.txt"
        inference_file_saved = inferences_dir / inference_file_in.name
        mock_save.return_value = inference_file_saved
        camera_state._process_camera_upload(b"", inference_file_in)
        mock_save.assert_called_with(inference_file_in.name, b"", inferences_dir)

        mock_get_output_from_inference_results.assert_called_once_with(b"boo")


@pytest.mark.trio
async def test_process_camera_upload_inferences_missing_schema(
    tmp_path_factory, cs_init
) -> None:
    root = tmp_path_factory.getbasetemp()
    inferences_dir = tmp_path_factory.mktemp("inferences")
    images_dir = tmp_path_factory.mktemp("images")

    camera_state = cs_init
    camera_state.inference_dir_path.value = inferences_dir
    camera_state.image_dir_path.value = images_dir

    with (
        patch.object(camera_state, "_save_into_input_directory") as mock_save,
        patch.object(camera_state, "_get_flatbuffers_inference_data"),
        patch(
            "local_console.core.camera.mixin_streaming.get_output_from_inference_results"
        ) as mock_get_output_from_inference_results,
        patch(
            "local_console.core.camera.mixin_streaming.Path.read_bytes",
            return_value=b"boo",
        ),
        patch(
            "local_console.core.camera.mixin_streaming.Path.read_text",
            return_value="boo",
        ),
        patch.object(Path, "read_text", return_value=""),
    ):
        camera_state.vapp_type = TrackingVariable(ApplicationType.CLASSIFICATION.value)

        inference_file_in = root / "inferences/a.txt"
        inference_file_saved = inferences_dir / inference_file_in.name
        mock_save.return_value = inference_file_saved
        camera_state._process_camera_upload(b"", inference_file_in)
        mock_save.assert_called_with(inference_file_in.name, b"", inferences_dir)

        image_file_in = root / "images/a.jpg"
        image_file_saved = images_dir / image_file_in.name
        mock_save.return_value = image_file_saved
        camera_state._process_camera_upload(b"", image_file_in)
        mock_save.assert_called_with(image_file_in.name, b"", images_dir)

        mock_get_output_from_inference_results.assert_called_once_with(b"boo")
