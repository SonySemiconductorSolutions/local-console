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
from mocked_device.mqtt.connection import create_connection
from mocked_device.mqtt.connection import MqttConnection
from mocked_device.mqtt.event import TopicListener
from mocked_device.mqtt.values import MqttConfig
from mocked_device.mqtt.values import MqttMessage
from mocked_device.retry.retrier import Retry


class MockDevice:
    def __init__(self, conn: MqttConnection):
        self._conn = conn

    def send_mqtt(self, message: MqttMessage) -> None:
        myself = self._conn.config
        self._conn.publish(message.target_to(myself))

    def add_listener(self, listener: TopicListener) -> None:
        self._conn.add_listener(listener)


def create_device(config: MqttConfig) -> MockDevice:
    conn = Retry(lambda: create_connection(config)).get()
    assert conn
    return MockDevice(conn)
