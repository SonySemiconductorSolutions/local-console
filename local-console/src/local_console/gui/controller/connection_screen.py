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
from local_console.core.camera import get_qr_object
from local_console.gui.driver import Driver
from local_console.gui.model.connection_screen import ConnectionScreenModel
from local_console.gui.utils.qr import Color
from local_console.gui.utils.qr import qr_object_as_texture
from local_console.gui.view.connection_screen.connection_screen import (
    ConnectionScreenView,
)
from local_console.utils.local_network import get_my_ip_by_routing
from local_console.utils.local_network import replace_local_address


class ConnectionScreenController:
    """
    The `ConnectionScreenController` class represents a controller implementation.
    Coordinates work of the view with the model.
    The controller implements the strategy pattern. The controller connects to
    the view to control its actions.
    """

    def __init__(self, model: ConnectionScreenModel, driver: Driver):
        self.model = model
        self.driver = driver
        self.view = ConnectionScreenView(controller=self, model=self.model)

    def get_view(self) -> ConnectionScreenView:
        return self.view

    def toggle_password_visibile(self) -> None:
        if self.model.wifi_password_hidden:
            self.model.wifi_password_hidden = False
            self.model.wifi_icon_eye = "eye"
        else:
            self.model.wifi_password_hidden = True
            self.model.wifi_icon_eye = "eye-off"

    def qr_generate(self) -> None:
        # Get the local IP since it might be updated.
        self.model.local_ip = get_my_ip_by_routing()
        mqtt_port = int(self.model.mqtt_port) if self.model.mqtt_port != "" else None
        tls_enabled = False
        qr = get_qr_object(
            replace_local_address(self.model.mqtt_host),
            mqtt_port,
            tls_enabled,
            replace_local_address(self.model.ntp_host),
            self.model.ip_address,
            self.model.subnet_mask,
            self.model.gateway,
            self.model.dns_server,
            self.model.wifi_ssid,
            self.model.wifi_password,
            border=4,
        )
        background: Color = tuple(
            int(255 * (val * 1.1)) for val in self.view.theme_cls.backgroundColor[:3]
        )
        fill: Color = (0, 0, 0)
        self.view.ids.img_qr_display.texture = qr_object_as_texture(
            qr, background, fill
        )
