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
import os
import platform
from pathlib import Path

from local_console.utils.enums import StrEnum


class Config:
    def __init__(self) -> None:
        self.home = get_default_home()
        self._config_file = "config.ini"
        self.deployment_json = "deployment.json"
        self.bin = "bin"

    @property
    def config_path(self) -> Path:
        return self.home / self._config_file

    @property
    def tls_cert_root(self) -> Path:
        return self.home / "tls_client_certs"

    @property
    def cli_cert_pair(self) -> tuple[Path, Path]:
        return self.tls_cert_root / "cli.crt.pem", self.tls_cert_root / "cli.key.pem"

    @property
    def broker_cert_pair(self) -> tuple[Path, Path]:
        return (
            self.tls_cert_root / "broker.crt.pem",
            self.tls_cert_root / "broker.key.pem",
        )

    @property
    def agent_cert_pair(self) -> tuple[Path, Path]:
        return (
            self.tls_cert_root / "agent.crt.pem",
            self.tls_cert_root / "agent.key.pem",
        )

    @property
    def home(self) -> Path:
        return self._home

    @home.setter
    def home(self, value: str) -> None:
        self._home = Path(value).expanduser().resolve()


def get_default_home() -> Path:
    app_subdir = Path("local-console")
    os_name = platform.system()
    if os_name == "Linux":
        # https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
        return Path.home() / ".config" / app_subdir
    elif os_name == "Windows":
        # https://learn.microsoft.com/en-us/dotnet/api/system.environment.specialfolder?view=netframework-4.8
        app_data_root = os.getenv("APPDATA")
        if not app_data_root:
            raise OSError("Could not resolve this machine's %APPDATA% folder!")
        return Path(app_data_root) / app_subdir
    elif os_name == "Darwin":
        # https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPFileSystem/Articles/WhereToPutFiles.html
        return Path.home() / "Library/Application Support" / app_subdir
    else:
        raise OSError(f"Unsupported runtime: {os_name}")


config_paths = Config()


class GetObjects(StrEnum):
    INSTANCE = "instance"
    DEPLOYMENT = "deployment"
    TELEMETRY = "telemetry"


class GetCommands(StrEnum):
    GET = "get"
    SET = "set"
    UNSET = "unset"
    SEND = "send"


class Target(StrEnum):
    AMD64 = "amd64"
    ARM64 = "arm64"
    XTENSA = "xtensa"


class ModuleExtension(StrEnum):
    WASM = "wasm"
    AOT = "aot"
    SIGNED = "signed"
