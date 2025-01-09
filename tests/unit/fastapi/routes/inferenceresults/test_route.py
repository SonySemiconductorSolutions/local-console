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
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

from fastapi import status
from fastapi.testclient import TestClient
from local_console.core.camera.state import CameraState
from local_console.core.files.inference import InferenceWithSource
from local_console.fastapi.routes.inferenceresults.dependencies import (
    inference_manager,
)

from tests.fixtures.fastapi import fa_client
from tests.strategies.samplers.files import InferenceWithSourceSampler
from tests.unit.core.files.test_inference import INFERENCE_CONTENT_SAMPLE


def test_get_inferences(fa_client: TestClient) -> None:
    with TemporaryDirectory(
        prefix="dropthis", ignore_cleanup_errors=True
    ) as temporary_dir:
        base_path = Path(temporary_dir)
        files = [
            base_path / "20241003093439234.txt",
            base_path / "20241003093439235.txt",
        ]
        for file in files:
            file.write_text(INFERENCE_CONTENT_SAMPLE)
        device_id = 1883
        fa_client.app.state.device_service.states[device_id] = CameraState(
            MagicMock(), MagicMock()
        )
        fa_client.app.state.device_service.states[
            device_id
        ].inference_dir_path.value = Path(temporary_dir)

        result = fa_client.get(f"/inferenceresults/devices/{device_id}/")

        assert result.status_code == status.HTTP_200_OK
        images = result.json()["data"]
        assert sorted(images, key=lambda e: e["id"]) == sorted(
            [
                {
                    "id": "20241003093439234.txt",
                    "model_id": "0308000000000100",
                    "model_version_id": "",
                    "inference_result": {
                        "DeviceID": "sid-100A50500A2010072664012000000000",
                        "ModelID": "0308000000000100",
                        "Image": True,
                        "Inferences": [
                            {
                                "T": "20241003093439234",
                                "O": "AMBdPQAALrwAgAA9AFAcPgBgJz4AAAI8AAA3PADgCz4AoIU9AABKPADAyD0AQAG9AADEOwAAJDwAoA0+ALBUPgAARDwAsIM+ABAGPgAAcLwA2Ms+AAC8OwDgAz4AgMO8AHACPgDwyj4AsB4+ACBHPgAg0D0AAO47AAC4uwDQBz4AAI48AIApPQAAHLsAcCY+AABcuwCAAT0AAFw8AABQOgCg1D0AMD4+AAAgOgDAoD0AAK67AHAUPgBAjj4AIOU9AACJPQDAzT0AwL09AACEOwCANj0AcHo+ACBQPgCARr0AILY+AIBaPgAAgLgAwBc9AAAwOgAAaTwAABO8AMChPgAUAz8A8Ek+AACsOwBgWD8AFBA/AGg8PwAAQLoAMEk+AIgGPwD0YD8AjBE/ANBlPwAo7j4AePA+AEg1PwAAyDoAgAs/AAwdPwBAwD0AqFI/ACxMPwAgID4AAFA7AGjlPgAAXDsAAPw7AFjzPgBARz4AAMA5AFAEPwAAsjsAtA8/ALwrPwD8CT8AgCE+AJxZPwAMHT8AAKs+APgEPwBomT4AIJw+APChPgDEDD8AAJ8+ANiSPgCwlD4AsIg+AFj2PgBARj4A4B4+AABpPgA4pj4AAE0+ALDbPgDwZD4AwJ0+AIR8PwAQmj4AMIY+AFjgPgDIgz4AMBM/ANiaPgAQsz4ACNE+APAdPgAgFz4AMGM+ACAOPgDgXj4AkCI+ANiZPgBgkz0A4I8+AHDtPgBAdj0AkDU+AEibPgAAyD0AIEg+AODwPQDYnT4AwBE/AFA4PgAAST4AIF0+ABhwPwCAoz4A4Bw/ANijPgBQjD4AOCA/AKB3PwCArD4AsCk+AIjpPgBAVj0AKN4+AJBvPgCgwT4A1Bo/AJiNPgBA9z0AQH4/AGwoPwBQeT8AuFI/APjfPgCIMj8APH4/ANQ/PwDYfz8A9CU/AMwkPwA4fD8AQHY9APhkPwB0ND8AQC4+APBzPwDMez8AYGw+AMCTPQB8Jz8AcCA+AADBPQDEIT8AEJk+AIB0PQCoFj8AYOM9AKxBPwDGgD8ATC0/AIBlPgBsbD8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcj8AAJY+AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQA==",
                                "unexpected_field": "with value",
                            }
                        ],
                        "additional_field": "some value",
                    },
                },
                {
                    "id": "20241003093439235.txt",
                    "model_id": "0308000000000100",
                    "model_version_id": "",
                    "inference_result": {
                        "DeviceID": "sid-100A50500A2010072664012000000000",
                        "ModelID": "0308000000000100",
                        "Image": True,
                        "Inferences": [
                            {
                                "T": "20241003093439234",
                                "O": "AMBdPQAALrwAgAA9AFAcPgBgJz4AAAI8AAA3PADgCz4AoIU9AABKPADAyD0AQAG9AADEOwAAJDwAoA0+ALBUPgAARDwAsIM+ABAGPgAAcLwA2Ms+AAC8OwDgAz4AgMO8AHACPgDwyj4AsB4+ACBHPgAg0D0AAO47AAC4uwDQBz4AAI48AIApPQAAHLsAcCY+AABcuwCAAT0AAFw8AABQOgCg1D0AMD4+AAAgOgDAoD0AAK67AHAUPgBAjj4AIOU9AACJPQDAzT0AwL09AACEOwCANj0AcHo+ACBQPgCARr0AILY+AIBaPgAAgLgAwBc9AAAwOgAAaTwAABO8AMChPgAUAz8A8Ek+AACsOwBgWD8AFBA/AGg8PwAAQLoAMEk+AIgGPwD0YD8AjBE/ANBlPwAo7j4AePA+AEg1PwAAyDoAgAs/AAwdPwBAwD0AqFI/ACxMPwAgID4AAFA7AGjlPgAAXDsAAPw7AFjzPgBARz4AAMA5AFAEPwAAsjsAtA8/ALwrPwD8CT8AgCE+AJxZPwAMHT8AAKs+APgEPwBomT4AIJw+APChPgDEDD8AAJ8+ANiSPgCwlD4AsIg+AFj2PgBARj4A4B4+AABpPgA4pj4AAE0+ALDbPgDwZD4AwJ0+AIR8PwAQmj4AMIY+AFjgPgDIgz4AMBM/ANiaPgAQsz4ACNE+APAdPgAgFz4AMGM+ACAOPgDgXj4AkCI+ANiZPgBgkz0A4I8+AHDtPgBAdj0AkDU+AEibPgAAyD0AIEg+AODwPQDYnT4AwBE/AFA4PgAAST4AIF0+ABhwPwCAoz4A4Bw/ANijPgBQjD4AOCA/AKB3PwCArD4AsCk+AIjpPgBAVj0AKN4+AJBvPgCgwT4A1Bo/AJiNPgBA9z0AQH4/AGwoPwBQeT8AuFI/APjfPgCIMj8APH4/ANQ/PwDYfz8A9CU/AMwkPwA4fD8AQHY9APhkPwB0ND8AQC4+APBzPwDMez8AYGw+AMCTPQB8Jz8AcCA+AADBPQDEIT8AEJk+AIB0PQCoFj8AYOM9AKxBPwDGgD8ATC0/AIBlPgBsbD8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcj8AAJY+AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQA==",
                                "unexpected_field": "with value",
                            }
                        ],
                        "additional_field": "some value",
                    },
                },
            ],
            key=lambda e: e["id"],
        )

        for id in [e["id"] for e in result.json()["data"]]:
            result = fa_client.get(f"/inferenceresults/devices/{device_id}/{id}")
            assert result.status_code == status.HTTP_200_OK
            assert result.json() == {
                "DeviceID": "sid-100A50500A2010072664012000000000",
                "ModelID": "0308000000000100",
                "Image": True,
                "Inferences": [
                    {
                        "T": "20241003093439234",
                        "O": "AMBdPQAALrwAgAA9AFAcPgBgJz4AAAI8AAA3PADgCz4AoIU9AABKPADAyD0AQAG9AADEOwAAJDwAoA0+ALBUPgAARDwAsIM+ABAGPgAAcLwA2Ms+AAC8OwDgAz4AgMO8AHACPgDwyj4AsB4+ACBHPgAg0D0AAO47AAC4uwDQBz4AAI48AIApPQAAHLsAcCY+AABcuwCAAT0AAFw8AABQOgCg1D0AMD4+AAAgOgDAoD0AAK67AHAUPgBAjj4AIOU9AACJPQDAzT0AwL09AACEOwCANj0AcHo+ACBQPgCARr0AILY+AIBaPgAAgLgAwBc9AAAwOgAAaTwAABO8AMChPgAUAz8A8Ek+AACsOwBgWD8AFBA/AGg8PwAAQLoAMEk+AIgGPwD0YD8AjBE/ANBlPwAo7j4AePA+AEg1PwAAyDoAgAs/AAwdPwBAwD0AqFI/ACxMPwAgID4AAFA7AGjlPgAAXDsAAPw7AFjzPgBARz4AAMA5AFAEPwAAsjsAtA8/ALwrPwD8CT8AgCE+AJxZPwAMHT8AAKs+APgEPwBomT4AIJw+APChPgDEDD8AAJ8+ANiSPgCwlD4AsIg+AFj2PgBARj4A4B4+AABpPgA4pj4AAE0+ALDbPgDwZD4AwJ0+AIR8PwAQmj4AMIY+AFjgPgDIgz4AMBM/ANiaPgAQsz4ACNE+APAdPgAgFz4AMGM+ACAOPgDgXj4AkCI+ANiZPgBgkz0A4I8+AHDtPgBAdj0AkDU+AEibPgAAyD0AIEg+AODwPQDYnT4AwBE/AFA4PgAAST4AIF0+ABhwPwCAoz4A4Bw/ANijPgBQjD4AOCA/AKB3PwCArD4AsCk+AIjpPgBAVj0AKN4+AJBvPgCgwT4A1Bo/AJiNPgBA9z0AQH4/AGwoPwBQeT8AuFI/APjfPgCIMj8APH4/ANQ/PwDYfz8A9CU/AMwkPwA4fD8AQHY9APhkPwB0ND8AQC4+APBzPwDMez8AYGw+AMCTPQB8Jz8AcCA+AADBPQDEIT8AEJk+AIB0PQCoFj8AYOM9AKxBPwDGgD8ATC0/AIBlPgBsbD8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcj8AAJY+AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQA==",
                        "unexpected_field": "with value",
                    }
                ],
                "additional_field": "some value",
            }


def test_device_is_int(fa_client: TestClient) -> None:
    result = fa_client.get("/inferenceresults/devices/not_an_int/")

    assert result.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert (
        result.json()["message"]
        == "device_id: Input should be a valid integer, unable to parse string as an integer"
    )


def test_inference_pagination(fa_client: TestClient) -> None:
    manager = MagicMock()
    fa_client.app.dependency_overrides[inference_manager] = lambda: manager
    sampler = InferenceWithSourceSampler()
    mocked_inferences: list[InferenceWithSource] = []
    for i in range(10):
        sampler.path = Path(f"some/path/202410011618320{i}.txt")
        sampler.inference.device_id = f"device_{i}"
        mocked_inferences.append(sampler.sample())

    manager.list.return_value = mocked_inferences

    result = fa_client.get("/inferenceresults/devices/1?limit=2")

    assert result.status_code == status.HTTP_200_OK
    ids = [d["id"] for d in result.json()["data"]]
    assert sorted(ids) == ["2024100116183200.txt", "2024100116183201.txt"]
    assert result.json()["continuation_token"] == "2024100116183201.txt"

    result = fa_client.get(
        "/inferenceresults/devices/1?limit=2&starting_after=2024100116183201.txt"
    )

    assert result.status_code == status.HTTP_200_OK
    ids = [d["id"] for d in result.json()["data"]]
    assert sorted(ids) == ["2024100116183202.txt", "2024100116183203.txt"]
    assert result.json()["continuation_token"] == "2024100116183203.txt"


def test_inference_device_not_int(fa_client: TestClient) -> None:
    result = fa_client.get("/inferenceresults/devices/not_an_int/inf.txt")

    assert result.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert (
        result.json()["message"]
        == "device_id: Input should be a valid integer, unable to parse string as an integer"
    )


def test_inference_not_found(fa_client: TestClient) -> None:
    result = fa_client.get("/inferenceresults/devices/1/inf.txt")

    assert result.status_code == status.HTTP_404_NOT_FOUND
    assert result.json()["message"] == "Device for port 1 not found"


def test_download_image_not_found(fa_client: TestClient) -> None:
    with TemporaryDirectory(
        prefix="dropthis", ignore_cleanup_errors=True
    ) as temporary_dir:
        device_id = 1883
        fa_client.app.state.device_service.states[device_id] = CameraState(
            MagicMock(), MagicMock()
        )
        fa_client.app.state.device_service.states[
            device_id
        ].inference_dir_path.value = Path(temporary_dir)
        result = fa_client.get(f"/inferenceresults/devices/{device_id}/inf.txt")

        assert result.status_code == status.HTTP_404_NOT_FOUND
        assert result.json()["message"] == "Inference file 'inf.txt' not found"
