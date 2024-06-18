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
import sys
from functools import partial
from pathlib import Path
from typing import Annotated
from typing import Optional

import trio
import typer
from local_console.clients.agent import Agent
from local_console.core.commands.deploy import exec_deployment
from local_console.core.commands.deploy import get_empty_deployment
from local_console.core.commands.deploy import make_unique_module_ids
from local_console.core.commands.deploy import update_deployment_manifest
from local_console.core.config import get_config
from local_console.core.config import get_deployment_schema
from local_console.core.enums import config_paths
from local_console.core.enums import Target
from local_console.plugin import PluginBase
from local_console.utils.local_network import get_my_ip_by_routing
from local_console.utils.local_network import is_localhost

logger = logging.getLogger(__name__)

app = typer.Typer()


@app.command(help="Command for deploying application to the agent")
def deploy(
    empty: Annotated[
        bool,
        typer.Option(
            "-e",
            "--empty",
            help="Option to remove previous deployment with an empty one",
        ),
    ] = False,
    signed: Annotated[
        bool,
        typer.Option(
            "-s",
            "--signed",
            help="Option to deploy signed files(already built with the 'build' command)",
        ),
    ] = False,
    timeout: Annotated[
        int,
        typer.Option(
            "-t",
            "--timeout",
            help="Set timeout to wait for the modules to be downloaded by the agent",
        ),
    ] = 15,
    target: Annotated[
        Optional[Target],
        typer.Argument(
            help="Optional argument to specify which AoT compilation to deploy. If not defined it will deploy the plain WASM"
        ),
    ] = None,
    force_webserver: Annotated[
        bool,
        typer.Option(
            "-f",
            "--force-webserver",
            help=(
                "If passed, the command will deploy the webserver locally, even if the "
                "configured webserver host does not resolve to localhost"
            ),
        ),
    ] = False,
) -> None:
    agent = Agent()
    config: AgentConfiguration = get_config()  # type: ignore
    port = config.webserver.port
    host = config.webserver.host.ip_value
    deploy_webserver = force_webserver

    local_ip = get_my_ip_by_routing()
    if is_localhost(host) or host == local_ip:
        host = local_ip
        deploy_webserver = True

    if empty:
        deployment_manifest = get_empty_deployment()
    else:
        bin_fp = Path(config_paths.bin)
        if not bin_fp.is_dir():
            raise SystemExit(f"'bin' folder does not exist at {bin_fp.parent}")

        deployment_manifest = get_deployment_schema()
        update_deployment_manifest(deployment_manifest, host, port, bin_fp, target, signed)  # type: ignore
        with open(config_paths.deployment_json, "w") as f:
            json.dump(deployment_manifest.model_dump(), f, indent=2)

        make_unique_module_ids(deployment_manifest)

    success = False
    deployment_fn = partial(
        exec_deployment,
        agent,
        deployment_manifest,
        deploy_webserver,
        Path.cwd(),
        port,
        timeout,
    )
    try:
        success = trio.run(deployment_fn)

    except Exception as e:
        logger.exception("Deployment error", exc_info=e)
    except KeyboardInterrupt:
        logger.info("Cancelled by the user")
    finally:
        sys.exit(0 if success else 1)


class DeployCommand(PluginBase):
    implementer = app
