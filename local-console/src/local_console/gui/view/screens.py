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
# The screen's dictionary contains the objects of the models and controllers
# of the screens of the application.
from functools import partial

from local_console.gui.controller.ai_model_screen import AIModelScreenController
from local_console.gui.controller.applications_screen import (
    ApplicationsScreenController,
)
from local_console.gui.controller.configuration_screen import (
    ConfigurationScreenController,
)
from local_console.gui.controller.connection_screen import ConnectionScreenController
from local_console.gui.controller.home_screen import HomeScreenController
from local_console.gui.controller.inference_screen import InferenceScreenController
from local_console.gui.controller.streaming_screen import StreamingScreenController
from local_console.gui.model.ai_model_screen import AIModelScreenModel
from local_console.gui.model.applications_screen import ApplicationsScreenModel
from local_console.gui.model.configuration_screen import ConfigurationScreenModel
from local_console.gui.model.connection_screen import ConnectionScreenModel
from local_console.gui.model.home_screen import HomeScreenModel
from local_console.gui.model.inference_screen import InferenceScreenModel
from local_console.gui.model.streaming_screen import StreamingScreenModel
from local_console.gui.view.ai_model_screen.ai_model_screen import AIModelScreenView

screen_dict = {
    "home screen": {
        "model_class": HomeScreenModel,
        "controller_class": HomeScreenController,
    },
    "connection screen": {
        "model_class": ConnectionScreenModel,
        "controller_class": ConnectionScreenController,
    },
    "configuration screen": {
        "model_class": ConfigurationScreenModel,
        "controller_class": ConfigurationScreenController,
    },
    "streaming screen": {
        "model_class": StreamingScreenModel,
        "controller_class": StreamingScreenController,
    },
    "inference screen": {
        "model_class": InferenceScreenModel,
        "controller_class": InferenceScreenController,
    },
    "applications screen": {
        "model_class": ApplicationsScreenModel,
        "controller_class": ApplicationsScreenController,
    },
    "ai model screen": {
        "model_class": AIModelScreenModel,
        "controller_class": partial(AIModelScreenController, view=AIModelScreenView),
    },
}

start_screen = "home screen"
assert start_screen in screen_dict
