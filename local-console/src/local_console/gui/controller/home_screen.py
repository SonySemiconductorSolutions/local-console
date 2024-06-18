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
from local_console.gui.driver import Driver
from local_console.gui.model.base_model import BaseScreenModel
from local_console.gui.view.home_screen.home_screen import HomeScreenView


class HomeScreenController:
    """
    The `HomeScreenController` class represents a controller implementation.
    Coordinates work of the view with the model.
    The controller implements the strategy pattern. The controller connects to
    the view to control its actions.
    """

    def __init__(self, model: BaseScreenModel, driver: Driver):
        self.model = model  # Model.home_screen.HomeScreenModel
        self.driver = driver
        self.view = HomeScreenView(controller=self, model=self.model)

    def get_view(self) -> HomeScreenView:
        return self.view
