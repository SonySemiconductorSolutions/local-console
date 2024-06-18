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

from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.snackbar import MDSnackbarButtonContainer
from kivymd.uix.snackbar import MDSnackbarCloseButton
from kivymd.uix.snackbar import MDSnackbarSupportingText
from local_console.gui.view.base_screen import BaseScreenView
from local_console.gui.view.common.components import (
    FocusText,
)  # nopycln: import # Required by the screen's KV spec file
from local_console.gui.view.common.components import (
    GUITooltip,
)  # nopycln: import # Required by the screen's KV spec file

logger = logging.getLogger(__name__)


class LocalIPInput(GUITooltip, FocusText):
    pass


class ConnectionScreenView(BaseScreenView):
    INPUTBOX_HEIGHT = "32dp"

    def entry_actions(self) -> None:
        self.model_is_changed()

    def validate_mqtt_host(self, widget: Widget, text: str) -> None:
        self.model.mqtt_host = text

    def validate_mqtt_port(self, widget: Widget, text: str) -> None:
        self.model.mqtt_port = text

    def validate_ntp_host(self, widget: Widget, text: str) -> None:
        self.model.ntp_host = text

    def validate_ip_address(self, widget: Widget, text: str) -> None:
        self.model.ip_address = text

    def validate_subnet_mask(self, widget: Widget, text: str) -> None:
        self.model.subnet_mask = text

    def validate_gateway(self, widget: Widget, text: str) -> None:
        self.model.gateway = text

    def validate_dns_server(self, widget: Widget, text: str) -> None:
        self.model.dns_server = text

    def validate_wifi_ssid(self, widget: Widget, text: str) -> None:
        self.model.wifi_ssid = text

    def validate_wifi_password(self, widget: Widget, text: str) -> None:
        self.model.wifi_password = text

    def model_is_changed(self) -> None:
        self.ids.lbl_conn_status.text = (
            "Connected [No TLS]" if self.model.connected else "Disconnected"
        )
        self.ids.txt_local_ip.text = self.model.local_ip
        self.ids.txt_mqtt_host.text = self.model.mqtt_host
        self.ids.txt_mqtt_port.text = self.model.mqtt_port
        self.ids.txt_ntp_host.text = self.model.ntp_host
        self.ids.txt_ip_address.text = self.model.ip_address
        self.ids.txt_subnet_mask.text = self.model.subnet_mask
        self.ids.txt_gateway.text = self.model.gateway
        self.ids.txt_dns_server.text = self.model.dns_server
        self.ids.txt_wifi_ssid.text = self.model.wifi_ssid
        self.ids.txt_wifi_password.text = self.model.wifi_password

        self.ids.txt_wifi_password.password = self.model.wifi_password_hidden
        self.ids.btn_icon_eye.icon = self.model.wifi_icon_eye

        if self.model.warning_message != "":
            self.show_message_at_bottom(self.model.warning_message)
            self.model.warning_message = ""

        self.ids.txt_mqtt_host.error = self.model.mqtt_host_error
        self.ids.txt_mqtt_port.error = self.model.mqtt_port_error
        self.ids.txt_ntp_host.error = self.model.ntp_host_error
        self.ids.txt_ip_address.error = self.model.ip_address_error
        self.ids.txt_subnet_mask.error = self.model.subnet_mask_error
        self.ids.txt_gateway.error = self.model.gateway_error
        self.ids.txt_dns_server.error = self.model.dns_server_error

    def show_message_at_bottom(self, message: str) -> None:
        MDSnackbar(
            MDSnackbarSupportingText(text=message),
            MDSnackbarButtonContainer(
                MDSnackbarCloseButton(
                    icon="close",
                ),
                pos_hint={"center_y": 0.5},
            ),
            y=dp(24),
            orientation="horizontal",
            pos_hint={"center_x": 0.5},
            size_hint_x=0.5,
            duration=5,
        ).open()
