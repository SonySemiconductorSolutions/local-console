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
import re
import subprocess
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path
from shutil import which
from string import Template
from tempfile import TemporaryDirectory

import trio
from local_console.core.enums import config_paths
from local_console.core.schemas.schemas import AgentConfiguration
from local_console.utils.tls import ensure_certificate_pair_exists

logger = logging.getLogger(__name__)

broker_assets = Path(__file__).parents[1] / "assets" / "broker"


@asynccontextmanager
async def spawn_broker(
    config: AgentConfiguration, nursery: trio.Nursery, verbose: bool, server_name: str
) -> AsyncIterator[trio.Process]:
    if config.is_tls_enabled:
        broker_cert_path, broker_key_path = config_paths.broker_cert_pair
        ensure_certificate_pair_exists(
            server_name, broker_cert_path, broker_key_path, config.tls, is_server=True
        )

    broker_bin = which("mosquitto")
    if not broker_bin:
        raise ValueError(
            "Could not find mosquitto in the PATH. Please add it and try again"
        )

    with TemporaryDirectory() as tmp_dir:
        config_file = Path(tmp_dir) / "broker.toml"
        populate_broker_conf(config, config_file)

        cmd = [broker_bin, "-v", "-c", str(config_file)]
        invocation = partial(
            trio.run_process,
            command=cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        broker_proc = await nursery.start(invocation)
        # This is to check the broker start up.
        # A (minor) enhancement would be to poll the broker.
        pattern = re.compile(r"mosquitto version (\d+\.\d+\.\d+) running")
        while True:
            data = await broker_proc.stdout.receive_some()
            if data:
                data = data.decode("utf-8")
                for line in data.splitlines():
                    logger.debug(line)
                if "Error" in data:
                    logger.error("Mosquitto already initialized")
                    sys.exit(1)
                elif pattern.search(data):
                    break

        nursery.start_soon(get_broker_logs, broker_proc.stdout)
        yield broker_proc
        broker_proc.kill()


def populate_broker_conf(config: AgentConfiguration, config_file: Path) -> None:
    data = {"mqtt_port": str(config.mqtt.port)}

    if config.is_tls_enabled:
        broker_cert_path, broker_key_path = config_paths.broker_cert_pair
        variant = "tls"
        data.update(
            {
                "ca_crt": str(config.tls.ca_certificate),
                "server_crt": str(broker_cert_path),
                "server_key": str(broker_key_path),
            }
        )
    else:
        variant = "no-tls"

    logger.info(f"MQTT broker in {variant} mode")
    template_file = broker_assets / f"config.{variant}.toml.tpl"
    template = Template(template_file.read_text())
    rendered = template.substitute(data)
    config_file.write_text(rendered)


async def get_broker_logs(proc_stdout: trio.abc.ReceiveStream) -> None:
    async for chunk in proc_stdout:
        for line in chunk.decode().splitlines():
            logger.debug(line)
