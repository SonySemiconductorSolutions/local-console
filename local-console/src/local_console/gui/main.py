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
# This file incorporates material from the KivyMD project, which is licensed
# under the MIT License:
#
#     MIT License
#
#     Copyright (c) 2024 KivyMD contributors
#
#     Permission is hereby granted, free of charge, to any person obtaining a copy
#     of this software and associated documentation files (the "Software"), to deal
#     in the Software without restriction, including without limitation the rights
#     to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#     copies of the Software, and to permit persons to whom the Software is
#     furnished to do so, subject to the following conditions:
#
#     The above copyright notice and this permission notice shall be included in all
#     copies or substantial portions of the Software.
#
#     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#     IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#     FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#     AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#     LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#     OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#     SOFTWARE.
#
# The following modifications have been made to the original KivyMD code:
#
# - This file started from the project template provided by KivyMD at
#   https://kivymd.readthedocs.io/en/latest/api/kivymd/tools/patterns/create_project/#project-creation
#
# SPDX-License-Identifier: Apache-2.0
import logging
from typing import Any

from kivy.base import ExceptionHandler
from kivy.base import ExceptionManager
from kivy.properties import BooleanProperty
from kivy.properties import StringProperty
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from local_console.gui.config import configure
from local_console.gui.driver import Driver
from local_console.gui.view.screens import screen_dict
from local_console.gui.view.screens import start_screen

logger = logging.getLogger(__name__)


class LocalConsoleGUIAPP(MDApp):
    nursery = None
    driver = None

    # Proxy objects leveraged for using Kivy's event dispatching
    is_ready = BooleanProperty(False)
    is_streaming = BooleanProperty(False)
    image_dir_path = StringProperty("")
    inference_dir_path = StringProperty("")

    async def app_main(self) -> None:
        self.driver = Driver(self)
        await self.driver.main()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.load_all_kv_files(self.directory)
        self.manager_screens = MDScreenManager()
        self.views: dict[str, type[MDScreen]] = {}
        configure()

    def build(self) -> MDScreenManager:
        self.title = "Local Console"
        self.generate_application_screens()
        return self.manager_screens

    def generate_application_screens(self) -> None:
        for name, entry in screen_dict.items():
            # TODO:FIXME: as a consequence of decouple viewer and controller
            model = entry["model_class"]()  # type: ignore
            controller = entry["controller_class"](model, self.driver)  # type: ignore
            view = controller.get_view()
            view.manager_screens = self.manager_screens
            view.name = name

            view.theme_cls.theme_style = "Light"
            view.theme_cls.primary_palette = (
                "Green"  # Pick one from kivymd.theming.ThemeManager.primary_palette
            )

            self.manager_screens.add_widget(view)
            self.views[name] = view

        self.manager_screens.current = start_screen


class GUIExceptionHandler(ExceptionHandler):
    def handle_exception(self, inst: BaseException) -> Any:
        if isinstance(inst, KeyboardInterrupt):
            # The user requested cancellation, so this is handled.
            return ExceptionManager.RAISE

        logger.exception("Uncaught Kivy exception ocurred:", exc_info=inst)
        cause = inst.__traceback__
        assert cause  # appease mypy
        while cause.tb_next:
            cause = cause.tb_next
        """
        TODO Decide whether to return .RAISE or .PASS depending
             on the 'cause'. If .PASS, maybe we can show it on
             the GUI itself!
        """
        return ExceptionManager.RAISE


ExceptionManager.add_handler(GUIExceptionHandler())
