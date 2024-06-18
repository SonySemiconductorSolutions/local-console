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
from base64 import b64encode
from pathlib import Path
from pathlib import PurePosixPath

from cryptography.hazmat.primitives import hashes
from local_console.core.schemas.edge_cloud_if_v1 import DnnModelVersion
from local_console.core.schemas.edge_cloud_if_v1 import DnnOta
from local_console.core.schemas.edge_cloud_if_v1 import DnnOtaBody


def get_package_hash(package_file: Path) -> str:
    digest = hashes.Hash(hashes.SHA256())
    digest.update(package_file.read_bytes())
    return b64encode(digest.finalize()).decode()


def get_package_version(package_file: Path) -> str:
    ver_bytes = package_file.read_bytes()[0x30:0x40]
    return ver_bytes.decode()


def get_network_id(package_file: Path) -> str:
    ver_bytes = get_package_version(package_file)
    return ver_bytes[6 : 6 + 6]


def configuration_spec(
    package_file: Path, webserver_root: Path, webserver_port: int, webserver_host: str
) -> DnnOta:
    file_hash = get_package_hash(package_file)
    version_str = get_package_version(package_file)
    rel_path = PurePosixPath(package_file.relative_to(webserver_root))
    url = f"http://{webserver_host}:{webserver_port}/{rel_path}"
    return DnnOta(
        OTA=DnnOtaBody(DesiredVersion=version_str, PackageUri=url, HashValue=file_hash)
    )


def get_network_ids(dnn_model_version: DnnModelVersion) -> list[str]:
    return [desired_version[6 : 6 + 6] for desired_version in dnn_model_version]


def get_apfw_version_string(fw_binary: bytes) -> str:
    # See: https://github.com/SonySemiconductorSolutions/EdgeAIPF.smartcamera.type3.mirror/blob/aa66e6ec772a9bd3577061d1767870b906751e94/src/imx_app/adapter/app_desc_nx_adp.c#L19
    # Note that the following only holds if the binary is UNENCRYPTED
    offset = fw_binary.index(b"PROJECT_NAME")
    if offset < 0:
        raise ValueError("Cannot find esp_app_desc_nx_adp_t struct in firmware")
    # Now, look the version string up, as it is located
    # contiguously before the `PROJECT_NAME` string,
    # with some surrounding zero padding.
    while offset > 0 and fw_binary[offset - 1] == 0:
        offset -= 1
    if fw_binary[offset - 1] == 0:
        raise ValueError("Could not locate the end of version string")
    end = offset

    while offset > 0 and fw_binary[offset - 1] != 0:
        offset -= 1
    if fw_binary[offset - 1] != 0:
        raise ValueError("Could not locate the start of version string")
    start = offset

    return fw_binary[start:end].decode()
