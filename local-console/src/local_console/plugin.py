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
from abc import ABC
from importlib.metadata import entry_points

from local_console.core.enums import Config
from typer import Typer


class PluginBase(ABC):
    """
    This member should be assigned by implementations
    of this class. It should hold one or more registered
    commands to expose in the main CLI.
    """

    implementer: Typer | None = None

    @classmethod
    def register_me(cls, main_handle: Typer, name: str) -> None:
        assert cls.implementer

        if len(cls.implementer.registered_commands) > 1:
            main_handle.add_typer(cls.implementer, name=name)
        else:
            main_handle.registered_commands += cls.implementer.registered_commands

    @classmethod
    def pre_setup_callback(cls, config_paths: Config) -> None:
        pass


def populate_commands(main_handle: Typer) -> dict[str, type[PluginBase]]:
    """
    Load all entry points defined by packages at the "local_console.plugin"
    group in pyproject.toml, which shall inherit from PluginBase, and
    invoke register_me on each of them, so as to populate the CLI

    Args:
        main_handle: the Typer object that provides the main CLI

    Returns:
        A dictionary with all resolved command classes
    """
    plugin_entry_points = entry_points(group="local_console.plugin")
    command_classes = {
        p.name: p.load()
        for p in plugin_entry_points
        if p.name != "base"  # ignore the PluginBase class
    }
    for name, command_class in command_classes.items():
        command_class.register_me(main_handle, name)

    return command_classes
