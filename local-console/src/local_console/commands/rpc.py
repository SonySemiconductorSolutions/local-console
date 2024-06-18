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
from local_console.clients.agent import Agent
from local_console.plugin import PluginBase

app = typer.Typer()

logger = logging.getLogger(__name__)


@app.command(help="Command to send RPC to a module instance")
def rpc(
    instance_id: Annotated[
        str,
        typer.Argument(help="Target instance of the RPC"),
    ],
    method: Annotated[
        str,
        typer.Argument(help="Method of the RPC"),
    ],
    params: Annotated[
        str,
        typer.Argument(help="JSON representing the parameters"),
    ],
) -> None:
    try:
        trio.run(rpc_task, instance_id, method, params)
    except ConnectionError:
        raise SystemExit(f"Could not send command {method} to device {instance_id}")


async def rpc_task(instance_id: str, method: str, params: str) -> None:
    agent = Agent()  # type: ignore
    await agent.initialize_handshake()
    async with agent.mqtt_scope([]):
        await agent.rpc(instance_id, method, params)


class RPCCommand(PluginBase):
    implementer = app
