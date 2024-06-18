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
import signal
from importlib.metadata import version as version_info
from pathlib import Path
from types import FrameType
from typing import Annotated
from typing import Optional

import typer
from local_console.core.config import setup_default_config
from local_console.core.enums import config_paths
from local_console.plugin import populate_commands
from local_console.utils.logger import configure_logger

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="local_console",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)
cmds = populate_commands(app)


def handle_exit(signal: int, frame: Optional[FrameType]) -> None:
    raise SystemExit


signal.signal(signal.SIGTERM, handle_exit)


@app.callback(invoke_without_command=True, context_settings={"obj": cmds})
def main(
    ctx: typer.Context,
    config_dir: Annotated[
        Path,
        typer.Option(help="Path for the file configs of the CLI and agent"),
    ] = config_paths.home,
    silent: Annotated[
        bool,
        typer.Option(
            "--silent",
            "-s",
            help="Decrease log verbosity (only show warnings and errors)",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose", "-v", help="Increase log verbosity (show debug messages too)"
        ),
    ] = False,
    version: Annotated[
        bool,
        typer.Option("--version", "-V", help="Display this program's version"),
    ] = False,
) -> None:
    if not ctx.invoked_subcommand and not version:
        print(ctx.get_help())
        return

    config_paths.home = config_dir
    configure_logger(silent, verbose)
    setup_default_config()

    if version:
        try:
            print(f"Version: {version_info('local-console')}")
        except Exception as e:
            logger.warning(f"Error while getting version from Python package: {e}")

    loaded_commands = ctx.obj
    for name, command_class in loaded_commands.items():
        logger.debug(f"Invoking pre-setup callback for command {name}")
        command_class.pre_setup_callback(config_paths)

    ctx.obj = config_paths.config_path


if __name__ == "__main__":
    logger.debug(f"Loaded commands: {cmds}")
    app()
