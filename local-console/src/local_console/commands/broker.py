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
from typing import Annotated

import trio
import typer
from local_console.core.config import get_config
from local_console.core.schemas.schemas import AgentConfiguration
from local_console.plugin import PluginBase
from local_console.servers.broker import spawn_broker

app = typer.Typer()

logger = logging.getLogger(__name__)


@app.command(
    help="Command to start a MQTT broker. It will fail if there is already a broker listening in the port specified in config."
)
def broker(
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Starts the broker in verbose mode"),
    ] = False,
    server_name: Annotated[
        str,
        typer.Argument(
            help="Server name to assign for TLS server verification, if TLS is enabled"
        ),
    ] = "localhost",
) -> None:
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    config = get_config()
    trio.run(broker_task, config, verbose, server_name)


async def broker_task(
    config: AgentConfiguration, verbose: bool, server_name: str
) -> None:
    logger.setLevel(logging.INFO)
    async with (
        trio.open_nursery() as nursery,
        spawn_broker(config, nursery, verbose, server_name),
    ):
        try:
            logger.info(f"MQTT broker listening on port {config.mqtt.port}")
            await trio.sleep_forever()
        except KeyboardInterrupt:
            logger.warning("Cancelled by the user")


class BrokerCommand(PluginBase):
    implementer = app
