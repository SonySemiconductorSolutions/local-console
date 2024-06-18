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
from typing import Optional

import trio
import typer
from local_console.clients.agent import Agent
from local_console.core.config import check_section_and_params
from local_console.core.config import get_config
from local_console.core.config import parse_section_to_ini
from local_console.core.config import schema_to_parser
from local_console.core.enums import config_paths
from local_console.core.schemas.schemas import AgentConfiguration
from local_console.core.schemas.schemas import DesiredDeviceConfig
from local_console.core.schemas.schemas import OnWireProtocol
from local_console.plugin import PluginBase

logger = logging.getLogger(__name__)
app = typer.Typer(
    help="Command to get or set configuration parameters of a camera or a module instance"
)


@app.command(
    "get", help="Gets the values for the requested config key, or the whole config"
)
def config_get(
    section: Annotated[
        Optional[str],
        typer.Argument(
            help="Section to be retrieved. If none specified, returns the whole config"
        ),
    ] = None,
    parameter: Annotated[
        Optional[str],
        typer.Argument(
            help="Parameter from a specific section to be retrieved. If none specified, returns the whole section"
        ),
    ] = None,
) -> None:
    agent_config: AgentConfiguration = get_config()  # type: ignore
    if section is None:
        for section_name, section_value in agent_config.__dict__.items():
            parsed_section = parse_section_to_ini(section_value, section_name)
            print(parsed_section, "\n")
    else:
        try:
            check_section_and_params(agent_config, section, parameter)
        except ValueError:
            raise SystemExit(
                f"Error getting config param '{parameter}' at section {section}"
            )
        parsed_section = parse_section_to_ini(
            agent_config.__dict__[f"{section}"], section, parameter
        )
        print(parsed_section)


@app.command("set", help="Sets the config key values to the specified value")
def config_set(
    section: Annotated[
        str,
        typer.Argument(help="Section of the configuration to be set"),
    ],
    parameter: Annotated[
        str,
        typer.Argument(help="Parameter of the section of the configuration to be set"),
    ],
    new: Annotated[
        str,
        typer.Argument(
            help="New value to be used in the specified parameter of the section"
        ),
    ],
) -> None:
    agent_config: AgentConfiguration = get_config()  # type:ignore

    try:
        check_section_and_params(agent_config, section, parameter)
        config_parser = schema_to_parser(agent_config, section, parameter, new)
    except ValueError:
        raise SystemExit(
            f"Error setting config param '{parameter}' at section '{section}'"
        )

    with open(
        config_paths.config_path, "w"  # type:ignore
    ) as f:
        config_parser.write(f)


@app.command("unset", help="Removes the value of a nullable configuration key")
def config_unset(
    section: Annotated[
        str,
        typer.Argument(help="Section of the configuration to be set"),
    ],
    parameter: Annotated[
        str,
        typer.Argument(help="Parameter of the section of the configuration to be set"),
    ],
) -> None:
    agent_config: AgentConfiguration = get_config()  # type:ignore

    try:
        check_section_and_params(agent_config, section, parameter)
        config_parser = schema_to_parser(agent_config, section, parameter, None)
    except ValueError as e:
        raise SystemExit(
            f"Error unsetting config param '{parameter}' at section '{section}'. It is probably not a nullable parameter."
        ) from e

    with config_paths.config_path.open("w") as f:
        config_parser.write(f)


@app.command("instance", help="Configure an application module instance")
def config_instance(
    instance_id: Annotated[
        str,
        typer.Argument(help="Target instance of the configuration"),
    ],
    topic: Annotated[
        str,
        typer.Argument(help="Topic of the configuration"),
    ],
    config: Annotated[
        str,
        typer.Argument(help="Data of the configuration"),
    ],
) -> None:
    try:
        trio.run(configure_task, instance_id, topic, config)
    except ConnectionError:
        raise SystemExit(
            f"Connection error while attempting to set configuration topic '{topic}' for instance {instance_id}"
        )


async def configure_task(instance_id: str, topic: str, config: str) -> None:
    agent = Agent()  # type: ignore
    await agent.initialize_handshake()
    async with agent.mqtt_scope([]):
        await agent.configure(instance_id, topic, config)


@app.command("device", help="Configure the device")
def config_device(
    interval_max: Annotated[
        int,
        typer.Argument(help="Max interval to report"),
    ],
    interval_min: Annotated[
        int,
        typer.Argument(help="Min interval to report"),
    ],
) -> None:
    retcode = 1
    try:
        desired_device_config = DesiredDeviceConfig(
            reportStatusIntervalMax=interval_max, reportStatusIntervalMin=interval_min
        )
        retcode = trio.run(config_device_task, desired_device_config)
    except ValueError:
        logger.warning("Report status interval out of range.")
    except ConnectionError:
        raise SystemExit(
            "Connection error while attempting to set device configuration"
        )
    raise typer.Exit(code=retcode)


async def config_device_task(desired_device_config: DesiredDeviceConfig) -> int:
    retcode = 1
    agent = Agent()  # type: ignore
    if agent.onwire_schema == OnWireProtocol.EVP2:
        async with agent.mqtt_scope([]):
            await agent.device_configure(desired_device_config)
        retcode = 0
    else:
        logger.warning(
            f"Unsupported on-wire schema {agent.onwire_schema} for this command."
        )
    return retcode


class ConfigCommand(PluginBase):
    implementer = app
