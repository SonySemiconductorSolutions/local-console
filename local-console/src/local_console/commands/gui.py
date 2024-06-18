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
import os

import trio
import typer
from local_console.plugin import PluginBase

logger = logging.getLogger(__name__)
app = typer.Typer()


@app.command(help="Command to start the GUI mode")
def gui() -> None:
    os.environ["KIVY_LOG_MODE"] = "PYTHON"
    os.environ["KIVY_NO_ARGS"] = "1"
    os.environ["KIVY_NO_CONSOLELOG"] = "1"
    os.environ["KIVY_NO_FILELOG"] = "1"
    os.environ["KIVY_NO_CONFIG"] = "1"

    """
    This import must happen within this callback, as
    Kivy performs several initialization steps during
    imports, that override logging and input handling.
    """
    from local_console.gui.main import LocalConsoleGUIAPP

    trio.run(LocalConsoleGUIAPP().app_main)


class GUICommand(PluginBase):
    implementer = app
