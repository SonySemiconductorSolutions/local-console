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
import logging
from collections import defaultdict
from typing import Annotated
from typing import Callable
from typing import Optional

import trio
import typer
from local_console.clients.agent import Agent
from local_console.commands.rpc import rpc_task
from local_console.commands.utils import find_device_config
from local_console.core.camera.enums import MQTTTopics
from local_console.core.helpers import read_only_loop
from local_console.core.schemas.schemas import DeviceConnection
from local_console.plugin import PluginBase

logger = logging.getLogger(__name__)

app = typer.Typer()


@app.command(help="Command for getting logs reported by a specific edge app instance")
def logs(
    instance_id: Annotated[
        str,
        typer.Argument(help="ID of the instance to get the logs from"),
    ],
    timeout: Annotated[
        int,
        typer.Option(
            "-t",
            "--timeout",
            help="Max seconds to wait for a module instance log to be reported",
        ),
    ] = 10,
    device: Annotated[
        Optional[str],
        typer.Option(
            "--device",
            "-d",
            help="The name of the device from which to retrieve the logs.",
        ),
    ] = None,
    port: Annotated[
        Optional[int],
        typer.Option(
            help="An alternative to --device, using the port to identify the device instead of its name. Ignored if the --device option is specified."
        ),
    ] = None,
) -> None:
    config_device = find_device_config(device, port)
    agent = Agent(config_device.mqtt.port)
    try:
        trio.run(request_instance_logs, instance_id, config_device)
        read_only_loop(
            agent,
            subs_topics=[MQTTTopics.TELEMETRY.value],
            message_task=on_message_logs(instance_id, timeout),
        )
    except ConnectionError:
        raise SystemExit(
            f"Could not send command for enabling logs to device {instance_id}"
        )


async def request_instance_logs(
    instance_id: str,
    config: DeviceConnection,
) -> None:
    await rpc_task(instance_id, "$agent/set", '{"log_enable": true}', config)


def on_message_logs(instance_id: str, timeout: int) -> Callable:
    async def __task(cs: trio.CancelScope, agent: Agent) -> None:
        assert agent.client is not None
        with trio.move_on_after(timeout) as time_cs:
            async with agent.client.messages() as mgen:
                async for msg in mgen:
                    payload = json.loads(msg.payload.decode())
                    logs = defaultdict(list)
                    if "values" in payload:
                        payload = payload["values"]
                    if "device/log" not in payload.keys():
                        continue

                    for log in payload["device/log"]:
                        logs[log["app"]].append(log)
                    if instance_id in logs.keys():
                        time_cs.deadline += timeout
                        for instance_log in logs[instance_id]:
                            print(instance_log)

        if time_cs.cancelled_caught:
            logger.error(
                f"No logs received for {instance_id} within {timeout} seconds. Please check the instance id is correct"
            )
            cs.cancel()

    return __task


class LogsCommand(PluginBase):
    implementer = app
