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
from typing import Any
from typing import Callable
from typing import Optional

import paho.mqtt.client as paho
import trio
from exceptiongroup import catch
from local_console.clients.trio_paho_mqtt import AsyncClient
from local_console.core.camera import MQTTTopics
from local_console.core.config import config_paths
from local_console.core.config import get_config
from local_console.core.schemas.schemas import AgentConfiguration
from local_console.core.schemas.schemas import DeploymentManifest
from local_console.core.schemas.schemas import DesiredDeviceConfig
from local_console.core.schemas.schemas import OnWireProtocol
from local_console.utils.local_network import is_localhost
from local_console.utils.tls import ensure_certificate_pair_exists
from local_console.utils.tls import get_random_identifier
from paho.mqtt.client import MQTT_ERR_SUCCESS

logger = logging.getLogger(__name__)


class Agent:
    def __init__(self) -> None:
        self.client: Optional[AsyncClient] = None
        self.nursery: Optional[trio.Nursery] = None

        config_parse: AgentConfiguration = get_config()
        self._host = config_parse.mqtt.host.ip_value
        self._port = config_parse.mqtt.port
        # For initializing the camera, capturing the on-wire protocol
        self.onwire_schema = OnWireProtocol.from_iot_spec(config_parse.evp.iot_platform)

        client_id = f"cli-client-{random.randint(0, 10**7)}"
        self.mqttc = paho.Client(clean_session=True, client_id=client_id)

        self.configure_tls(config_parse)

    def configure_tls(self, agent_config: AgentConfiguration) -> None:
        tls_conf = agent_config.tls
        if not (tls_conf.ca_certificate and tls_conf.ca_key):
            return

        cli_cert_path, cli_key_path = config_paths.cli_cert_pair
        ensure_certificate_pair_exists(
            get_random_identifier("local-console-"),
            cli_cert_path,
            cli_key_path,
            tls_conf,
        )

        self.mqttc.tls_set(
            ca_certs=str(tls_conf.ca_certificate),
            certfile=str(cli_cert_path),
            keyfile=str(cli_key_path),
        )

        # No server validation is necessary if the server is localhost
        # This spares us from needing to setup custom name resolution for
        # complying with TLS' Subject Common Name matching.
        self.mqttc.tls_insecure_set(is_localhost(agent_config.mqtt.host.ip_value))

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

    async def rpc(self, instance_id: str, method: str, params: str) -> None:
        # TODO Schematize this across the on-wire schema versions

        reqid = str(random.randint(0, 10**8))
        RPC_TOPIC = f"v1/devices/me/rpc/request/{reqid}"
        if self.onwire_schema == OnWireProtocol.EVP2:
            # Following the implementation at:
            # https://github.com/midokura/wedge-agent/blob/fa3d4840c37978938084cbc70612fdb8ea8dbf9f/src/libwedge-agent/hub/tb/tb.c#L218
            # https://github.com/midokura/wedge-agent/blob/fa3d4840c37978938084cbc70612fdb8ea8dbf9f/src/libwedge-agent/direct_command.c#L206
            # https://github.com/midokura/evp-onwire-schema/blob/9a0a861a6518681ceda5749890d4322a56dfbc3e/schema/direct-command-request.example.json#L2
            evp2_body = {
                "direct-command-request": {
                    "reqid": reqid,
                    "method": method,
                    "instance": instance_id,
                    "params": params,
                }
            }
            payload = json.dumps(
                {
                    "method": "ModuleMethodCall",
                    "params": evp2_body,
                }
            )
        elif self.onwire_schema == OnWireProtocol.EVP1:
            # Following the implementation at:
            # https://github.com/midokura/wedge-agent/blob/fa3d4840c37978938084cbc70612fdb8ea8dbf9f/src/libwedge-agent/hub/tb/tb.c#L179
            # https://github.com/midokura/wedge-agent/blob/fa3d4840c37978938084cbc70612fdb8ea8dbf9f/src/libwedge-agent/direct_command.c#L158
            # https://github.com/midokura/evp-onwire-schema/blob/1164987a620f34e142869f3979ca63b186c0a061/schema/directcommandrequest/direct-command-request.example.json#L2
            evp1_body = {
                "moduleMethod": method,
                "moduleInstance": instance_id,
                "params": json.loads(params),
            }
            payload = json.dumps(
                {
                    "method": "ModuleMethodCall",
                    "params": evp1_body,
                }
            )
        logger.debug(f"payload: {payload}")
        await self.publish(RPC_TOPIC, payload=payload)

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
        async with guarded_nursery() as nursery:
            self.nursery = nursery
            self.client = AsyncClient(self.mqttc, self.nursery)

            try:
                self.client.connect(self._host, self._port)
                for topic in subs_topics:
                    self.client.subscribe(topic)
                yield
            finally:
                self.client.disconnect()
                self.nursery.cancel_scope.cancel()

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


@asynccontextmanager
async def guarded_nursery() -> AsyncIterator[trio.Nursery]:
    with catch(
        {
            Exception: handle_task_exceptions,
        }
    ):
        async with trio.open_nursery() as nursery:
            yield nursery


def handle_task_exceptions(excgroup: Any) -> None:
    # The 'Any' annotation is used to silence mypy,
    # as it is not raising a helpful error.
    num_exceptions = len(excgroup.exceptions)
    logger.error(
        "%d Exception%s occurred, listed below:",
        num_exceptions,
        "s" if num_exceptions else "",
    )
    for e in excgroup.exceptions:
        logger.exception(
            "Exception occurred within MQTT client processing:", exc_info=e
        )


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
