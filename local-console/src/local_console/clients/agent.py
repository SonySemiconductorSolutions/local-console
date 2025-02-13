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
import base64
import json
import logging
import random
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Callable
from typing import Optional

import paho.mqtt.client as paho
import trio
from local_console.clients.command.base_command import CommandClient
from local_console.clients.command.rpc import RPC
from local_console.clients.command.rpc import RPCArgument
from local_console.clients.command.rpc_injector import empty_injector
from local_console.clients.trio_paho_mqtt import AsyncClient
from local_console.core.camera.enums import MQTTTopics
from local_console.core.schemas.schemas import DeploymentManifest
from local_console.core.schemas.schemas import DesiredDeviceConfig
from local_console.core.schemas.schemas import OnWireProtocol
from paho.mqtt.client import MQTT_ERR_SUCCESS

logger = logging.getLogger(__name__)


class Agent(CommandClient):
    def __init__(self, host: str, port: int, onwire_schema: OnWireProtocol) -> None:
        self.host = host
        self.port = port
        self.onwire_schema = onwire_schema

        self.client: Optional[AsyncClient] = None
        self.nursery: Optional[trio.Nursery] = None

        client_id = f"cli-client-{random.randint(0, 10**7)}"
        self.mqttc = paho.Client(clean_session=True, client_id=client_id)

    async def initialize_handshake(self, timeout: int = 5) -> None:
        async with self.mqtt_scope(
            [
                MQTTTopics.ATTRIBUTES_REQ.value,
            ]
        ):
            assert self.nursery
            assert self.client  # appease mypy

            with trio.move_on_after(timeout):
                async with self.client.messages() as mgen:
                    async for msg in mgen:
                        await check_attributes_request(
                            self, msg.topic, msg.payload.decode()
                        )
            logger.debug("Exiting initialized handshake")

    async def set_periodic_reports(self, report_interval: int) -> None:
        await self.device_configure(
            DesiredDeviceConfig(
                reportStatusIntervalMax=report_interval,
                reportStatusIntervalMin=min(report_interval, 1),
            )
        )

    async def deploy(self, to_deploy: DeploymentManifest) -> None:
        if self.onwire_schema == OnWireProtocol.EVP2:
            deployment = to_deploy.render_for_evp2()
        elif self.onwire_schema == OnWireProtocol.EVP1:
            deployment = to_deploy.render_for_evp1()

        await self.publish(MQTTTopics.ATTRIBUTES.value, payload=deployment)

    async def rpc(self, instance_id: str, method: str, params: str) -> str:
        rpc_input = RPCArgument(
            onwire_schema=self.onwire_schema,
            instance_id=instance_id,
            method=method,
            params=json.loads(params),
        )
        response = await RPC(self, empty_injector()).run(rpc_input)
        return response.response_id

    async def configure(self, instance_id: str, topic: str, config: str) -> None:
        # TODO Schematize this across the on-wire schema versions
        # FIXME EVP2 does not enforce base64 encoding. Decide how to handle it here
        #       see:
        #       https://github.com/SonySemiconductorSolutions/EdgeAIPF.smartcamera.type3.system-test/blob/a66d25ed6a4efbf0bffb593bc7013b098dd35786/src/interface.py#L82
        #       https://github.com/midokura/wedge-agent/blob/ee08d254658177ddfa3f75b7d1f09922104a2427/src/libwedge-agent/instance_config.c#L339

        # The following stanza matches the implementation at:
        # https://github.com/midokura/wedge-agent/blob/ee08d254658177ddfa3f75b7d1f09922104a2427/src/libwedge-agent/instance_config.c#L324
        config = base64.b64encode(config.encode("utf-8")).decode("utf-8")

        message: dict = {f"configuration/{instance_id}/{topic}": config}
        payload = json.dumps(message)
        logger.debug(f"payload: {payload}")
        await self.publish(MQTTTopics.ATTRIBUTES.value, payload=payload)

    async def device_configure(
        self, desired_device_config: DesiredDeviceConfig
    ) -> None:
        """
        :param config: Configuration of the module instance.
        """
        message: dict = {
            "desiredDeviceConfig": {
                "desiredDeviceConfig": {
                    "configuration/$agent/report-status-interval-max": desired_device_config.reportStatusIntervalMax,
                    "configuration/$agent/report-status-interval-min": desired_device_config.reportStatusIntervalMin,
                    "configuration/$agent/configuration-id": "",
                    "configuration/$agent/registry-auth": {},
                }
            }
        }
        payload = json.dumps(message)
        await self.publish(MQTTTopics.ATTRIBUTES.value, payload=payload)

    async def loop_client(
        self, subs_topics: list[str], driver_task: Callable, message_task: Callable
    ) -> None:
        async with self.mqtt_scope(subs_topics):
            assert self.nursery is not None
            cs = self.nursery.cancel_scope
            self.nursery.start_soon(message_task, cs, self)
            await driver_task(cs, self)

    @asynccontextmanager
    async def mqtt_scope(self, subs_topics: list[str]) -> AsyncIterator[None]:
        is_os_error = False  # Determines if an OSError occurred within the context

        try:
            async with trio.open_nursery() as nursery:

                self.nursery = nursery
                self.client = AsyncClient(self.mqttc, self.nursery)
                try:
                    self.client.connect(self.host, self.port)
                    for topic in subs_topics:
                        self.client.subscribe(topic)
                    yield
                except OSError:
                    logger.error(
                        f"Error while connecting to MQTT broker {self.host}:{self.port}"
                    )
                    is_os_error = True
                finally:
                    self.client.disconnect()
                    self.nursery.cancel_scope.cancel()

        except* Exception as excgroup:
            for e in excgroup.exceptions:
                logger.exception(
                    "Exception occurred within MQTT client processing:", exc_info=e
                )
            is_os_error = True

        if is_os_error:
            raise SystemExit

    async def publish(self, topic: str, payload: str) -> None:
        assert self.client is not None
        msg_info = await self.client.publish_and_wait(topic, payload=payload)
        if msg_info[0] != MQTT_ERR_SUCCESS:
            logger.error("Error on MQTT publish agent logs")
            raise ConnectionError

    def read_only_loop(self, subs_topics: list[str], message_task: Callable) -> None:
        async def _driver_task(_cs: trio.CancelScope, _agent: "Agent") -> None:
            await trio.sleep_forever()

        trio.run(self.loop_client, subs_topics, _driver_task, message_task)

    async def request_instance_logs(self, instance_id: str) -> None:
        async with self.mqtt_scope([]):
            await self.rpc(instance_id, "$agent/set", '{"log_enable": true}')


async def check_attributes_request(agent: Agent, topic: str, payload: str) -> bool:
    """
    Checks that a given MQTT message (as provided by its topic and payload)
    conveys a request from the device's agent for data attributes set in the
    MQTT broker.
    """
    got_request = False
    result = re.search(r"^v1/devices/me/attributes/request/(\d+)$", topic)
    if result:
        got_request = True
        req_id = result.group(1)
        logger.debug(
            "Got attribute request (id=%s) with payload: '%s'",
            req_id,
            payload,
        )
        await agent.publish(
            f"v1/devices/me/attributes/response/{req_id}",
            "{}",
        )
    return got_request
