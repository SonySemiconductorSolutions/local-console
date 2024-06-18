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
# This file incorporates material from the original trio-paho-mqtt project and
# a fork of it, both of which are licensed under the Apache License, Version 2.0:
#
#     Apache License
#     Version 2.0, January 2004
#     http://www.apache.org/licenses/
#
# Original Project (https://github.com/bkanuka/trio-paho-mqtt):
#     Copyright [2020] Bennett Kanuka
#
# Forked Project (https://github.com/lexknuther/trio-paho-mqtt):
#     Copyright [2021] Lex Knuther
#
# The following modifications have been made to the original trio-paho-mqtt code and
# the forked code:
# - Added typing annotations
# - Added methods for publish and wait
#
# SPDX-License-Identifier: Apache-2.0
import socket
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Any
from typing import Optional

import paho.mqtt.client as mqtt
import trio
from trio_util import trio_async_generator


class AsyncClient:
    def __init__(
        self,
        sync_client: mqtt.Client,
        parent_nursery: trio.Nursery,
        max_buffer: int = 100,
    ) -> None:
        self._client = sync_client
        self._nursery = parent_nursery

        self.socket = self._client.socket()

        self._cancel_scopes: list[trio.CancelScope] = []

        self._event_connect = trio.Event()
        self._event_large_write = trio.Event()
        self._event_should_read = trio.Event()
        self._event_should_read.set()
        self._published_msg: dict[int, trio.Event] = defaultdict(trio.Event)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_socket_open = self._on_socket_open  # type: ignore  # 'object' part of inferred signature is weird
        self._client.on_socket_close = self._on_socket_close  # type: ignore  # 'object' part of inferred signature is weird
        self._client.on_message = self._on_message
        self._client.on_socket_register_write = self._on_socket_register_write  # type: ignore  # 'object' part of inferred signature is weird
        self._client.on_socket_unregister_write = self._on_socket_unregister_write  # type: ignore  # 'object' part of inferred signature is weird
        self._client.on_publish = self._on_publish

        channel: tuple[
            trio.MemorySendChannel,
            trio.MemoryReceiveChannel,
        ] = trio.open_memory_channel(max_buffer)
        self._msg_send_channel: trio.MemorySendChannel = channel[0]
        self._msg_receive_channel: trio.MemoryReceiveChannel = channel[1]

        self.subscribe = self._client.subscribe
        self.publish = self._client.publish
        self.unsubscribe = self._client.unsubscribe
        self.will_set = self._client.will_set
        self.will_clear = self._client.will_clear
        self.proxy_set = self._client.proxy_set
        self.tls_set = self._client.tls_set
        self.tls_insecure_set = self._client.tls_insecure_set
        self.tls_set_context = self._client.tls_set_context
        self.user_data_set = self._client.user_data_set
        self.username_pw_set = self._client.username_pw_set
        self.ws_set_options = self._client.ws_set_options

    def _start_all_loop(self) -> None:
        self._nursery.start_soon(self._loop_read)
        self._nursery.start_soon(self._loop_write)
        self._nursery.start_soon(self._loop_misc)

    def _stop_all_loop(self) -> None:
        for cs in self._cancel_scopes:
            cs.cancel()

    async def _loop_misc(self) -> None:
        cs = trio.CancelScope()
        self._cancel_scopes.append(cs)
        await self._event_connect.wait()
        with cs:
            while self._client.loop_misc() == mqtt.MQTT_ERR_SUCCESS:
                await trio.sleep(1)

    async def _loop_read(self) -> None:
        cs = trio.CancelScope()
        self._cancel_scopes.append(cs)
        with cs:
            while True:
                await self._event_should_read.wait()
                await trio.lowlevel.wait_readable(self.socket)  # type: ignore  # silence useless type check
                self._client.loop_read()

    async def _loop_write(self) -> None:
        cs = trio.CancelScope()
        self._cancel_scopes.append(cs)
        with cs:
            while True:
                await self._event_large_write.wait()
                await trio.lowlevel.wait_writable(self.socket)  # type: ignore  # silence useless type check
                self._client.loop_write()

    def connect(
        self,
        host: str,
        port: int = 1883,
        keepalive: int = 60,
        bind_address: str = "",
        bind_port: int = 0,
        clean_start: int = mqtt.MQTT_CLEAN_START_FIRST_ONLY,
        properties: Optional[mqtt.Properties] = None,
    ) -> None:
        self._start_all_loop()
        self._client.connect(
            host,
            port,
            keepalive,
            bind_address,
            bind_port,
            clean_start,
            properties,
        )

    def _on_connect(
        self, client: mqtt.Client, userdata: Any, flags: dict[str, int], rc: int
    ) -> None:
        self._event_connect.set()

    @trio_async_generator
    async def messages(self) -> AsyncIterator[mqtt.MQTTMessage]:
        self._event_should_read.set()
        while True:
            msg = await self._msg_receive_channel.receive()
            yield msg
            self._event_should_read.set()

    def _on_message(
        self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage
    ) -> None:
        try:
            self._msg_send_channel.send_nowait(msg)
        except trio.WouldBlock:
            print("Buffer full. Discarding an old msg!")
            # Take the old msg off the channel, discard it, and put the new msg on
            _ = self._msg_receive_channel.receive_nowait()
            # TODO: Store this old msg?
            self._msg_send_channel.send_nowait(msg)
            # Stop reading until the messages are read off the mem channel
            self._event_should_read = trio.Event()

    def disconnect(
        self, reasoncode: Optional[mqtt.ReasonCodes] = None, properties: Any = None
    ) -> None:
        self._client.disconnect(reasoncode, properties)
        self._stop_all_loop()

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int) -> None:
        self._event_connect = trio.Event()
        self._stop_all_loop()

    def _on_socket_open(
        self, client: mqtt.Client, userdata: Any, sock: socket.socket
    ) -> None:
        self.socket = sock
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2048)

    def _on_socket_close(
        self, client: mqtt.Client, userdata: Any, sock: socket.socket
    ) -> None:
        """
        Empty implementation. Added to be consistent with the rest of the defined functions.
        """
        pass

    def _on_socket_register_write(
        self, client: mqtt.Client, userdata: Any, sock: socket.socket
    ) -> None:
        # large write request - start write loop
        self._event_large_write.set()

    def _on_socket_unregister_write(
        self, client: mqtt.Client, userdata: Any, sock: socket.socket
    ) -> None:
        # finished large write - stop write loop
        self._event_large_write = trio.Event()

    def _on_publish(self, client: mqtt.Client, userdata: Any, mid: int) -> None:
        self._published_msg[mid].set()

    async def publish_and_wait(
        self,
        topic: str,
        payload: Optional[str] = None,
        qos: int = 0,
        retain: bool = False,
        properties: Optional[mqtt.Properties] = None,
    ) -> mqtt.MQTTMessageInfo:
        msg_info = self._client.publish(topic, payload, qos, retain, properties)
        await self.wait_until_published(msg_info)
        return msg_info

    async def wait_until_published(self, msg_info: mqtt.MQTTMessageInfo) -> None:
        await self._published_msg[msg_info.mid].wait()
        self._published_msg.pop(msg_info.mid)
