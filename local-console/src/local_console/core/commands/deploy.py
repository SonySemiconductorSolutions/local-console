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
import enum
import hashlib
import json
import logging
import shutil
import uuid
from abc import ABC
from abc import abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from pathlib import PurePosixPath
from tempfile import TemporaryDirectory
from typing import Any
from typing import Callable
from typing import Optional

import trio
import typer
from local_console.clients.agent import Agent
from local_console.core.camera import MQTTTopics
from local_console.core.enums import ModuleExtension
from local_console.core.enums import Target
from local_console.core.schemas.schemas import Deployment
from local_console.core.schemas.schemas import DeploymentManifest
from local_console.core.schemas.schemas import OnWireProtocol
from local_console.servers.webserver import AsyncWebserver
from local_console.utils.local_network import get_my_ip_by_routing

logger = logging.getLogger(__name__)


class DeployStage(enum.IntEnum):
    WaitFirstStatus = enum.auto()
    WaitAppliedConfirmation = enum.auto()
    Done = enum.auto()
    Error = enum.auto()


async def exec_deployment(
    agent: Agent,
    deploy_manifest: DeploymentManifest,
    deploy_webserver: bool,
    webserver_path: Path,
    webserver_port: int,
    timeout_secs: int,
    stage_callback: Optional[Callable[[DeployStage], None]] = None,
) -> bool:
    deploy_fsm = DeployFSM.instantiate(agent, deploy_manifest, stage_callback)

    # GUI mode starts responding to requests in the background, but not the CLI
    # NOTE: revisit GUI - CLI interaction
    await agent.initialize_handshake()

    success = False
    with trio.move_on_after(timeout_secs) as timeout_scope:
        assert agent.onwire_schema  # make mypy happy
        logger.debug(f"Opening webserver at {webserver_path}")
        async with (
            agent.mqtt_scope([MQTTTopics.ATTRIBUTES.value]),
            AsyncWebserver(webserver_path, webserver_port, None, deploy_webserver),
        ):
            assert agent.nursery is not None  # make mypy happy
            agent.nursery.start_soon(deploy_fsm.message_task)
            await deploy_fsm.done.wait()
            success = not deploy_fsm.errored

    if timeout_scope.cancelled_caught:
        logger.error("Timeout when sending modules.")
        if stage_callback:
            stage_callback(DeployStage.Error)

    return success


class DeployFSM(ABC):
    def __init__(
        self,
        agent: Agent,
        to_deploy: DeploymentManifest,
        stage_callback: Optional[Callable[[DeployStage], None]] = None,
    ) -> None:
        self.agent = agent
        self.to_deploy = to_deploy
        self.stage_callback = stage_callback

        self.done = trio.Event()
        self.errored: Optional[bool] = None

        # This redundant declaration appeases the static checker
        self.stage = DeployStage.WaitFirstStatus
        self._set_new_stage(DeployStage.WaitFirstStatus)

    def _set_new_stage(self, new_stage: DeployStage) -> None:
        self.stage = new_stage
        if self.stage_callback:
            self.stage_callback(self.stage)

    @abstractmethod
    async def update(self, deploy_status: dict[str, Any]) -> None:
        """
        Updates the FSM as it progresses through its states.
        """

    @abstractmethod
    async def message_task(self) -> None:
        """
        Receives messages from the agent and reacts
        accordingly, calling update() with the latest
        deployment status report.
        """

    @staticmethod
    def verify_report(
        deployment_id: str, deploy_status: dict[str, Any]
    ) -> tuple[bool, bool, bool]:
        matches = deploy_status.get("deploymentId") == deployment_id
        is_finished = deploy_status.get("reconcileStatus") == "ok"

        error_in_modules = any(
            n["status"] == "error" for n in deploy_status.get("modules", {}).values()
        )
        error_in_modinsts = any(
            n["status"] == "error" for n in deploy_status.get("instances", {}).values()
        )
        is_errored = error_in_modinsts or error_in_modules

        return is_finished, matches, is_errored

    def check_termination(
        self, is_finished: bool, matches: bool, is_errored: bool
    ) -> bool:
        should_terminate = False
        if matches:
            if is_finished:
                should_terminate = True
                self._set_new_stage(DeployStage.Done)
                self.errored = False
                logger.info("Deployment complete")

            elif is_errored:
                should_terminate = True
                self._set_new_stage(DeployStage.Error)
                self.errored = True
                logger.info("Deployment errored")

        if should_terminate:
            self.done.set()

        return should_terminate

    @staticmethod
    def instantiate(
        agent: Agent,
        deploy_manifest: DeploymentManifest,
        stage_callback: Optional[Callable[[DeployStage], None]] = None,
    ) -> "DeployFSM":
        if agent.onwire_schema == OnWireProtocol.EVP1:
            return EVP1DeployFSM(agent, deploy_manifest, stage_callback)
        elif agent.onwire_schema == OnWireProtocol.EVP2:
            return EVP2DeployFSM(agent, deploy_manifest, stage_callback)


class EVP2DeployFSM(DeployFSM):
    async def update(self, deploy_status: Optional[dict[str, Any]]) -> None:
        assert isinstance(deploy_status, dict)

        next_stage = self.stage

        is_finished, matches, is_errored = self.verify_report(
            self.to_deploy.deployment.deploymentId, deploy_status
        )
        if self.check_termination(is_finished, matches, is_errored):
            return

        if self.stage == DeployStage.WaitFirstStatus:
            logger.debug("Agent can receive deployments. Pushing manifest now.")
            await self.agent.deploy(self.to_deploy)
            next_stage = DeployStage.WaitAppliedConfirmation

        elif self.stage == DeployStage.WaitAppliedConfirmation:
            if matches:
                logger.debug(
                    "Deployment received, reconcile=%s",
                    deploy_status.get("reconcileStatus", "<null>"),
                )
                logger.info("Deployment received, waiting for reconcile completion")

        elif self.stage in (DeployStage.Done, DeployStage.Error):
            logger.warning(
                "Should not reach here! (status is %s)",
                json.dumps(deploy_status),
            )

        self._set_new_stage(next_stage)

    async def message_task(self) -> None:
        """
        Notes:
        - Assumes report interval is short to perform the handshake.
        """
        assert self.agent.client is not None
        async with self.agent.client.messages() as mgen:
            async for msg in mgen:
                payload = json.loads(msg.payload)
                logger.debug("Incoming on %s: %s", msg.topic, str(payload))

                if payload and msg.topic == MQTTTopics.ATTRIBUTES.value:
                    if "deploymentStatus" in payload:
                        deploy_status = payload.get("deploymentStatus")
                        await self.update(deploy_status)


class EVP1DeployFSM(DeployFSM):
    async def update(self, deploy_status: dict[str, Any]) -> None:
        """
        Sending deployment is done in message_task.
        This method waits until current deployment in agent matches deployed.
        """
        is_finished, matches, is_errored = self.verify_report(
            self.to_deploy.deployment.deploymentId, deploy_status
        )
        if self.check_termination(is_finished, matches, is_errored):
            return

    async def message_task(self) -> None:
        """
        Simplified handshake compared to EVP2:
        - Sends deployment at beginning.
        - Check current is the one applied.
        """
        assert self.agent.client is not None

        # Deploy without comparing with current to speed-up the process
        await self.agent.deploy(self.to_deploy)
        async with self.agent.client.messages() as mgen:
            async for msg in mgen:
                payload = json.loads(msg.payload)
                logger.debug("Incoming on %s: %s", msg.topic, str(payload))

                if payload and msg.topic == MQTTTopics.ATTRIBUTES.value:
                    if "deploymentStatus" in payload:
                        deploy_status = json.loads(payload.get("deploymentStatus"))
                        await self.update(deploy_status)


@contextmanager
def module_deployment_setup(
    module_name: str, module_file: Path, webserver_port: int
) -> Iterator[tuple[Path, DeploymentManifest]]:
    deployment = Deployment.model_validate(
        {
            "deploymentId": "",
            "instanceSpecs": {
                module_name: {"moduleId": module_name, "subscribe": {}, "publish": {}}
            },
            "modules": {
                module_name: {
                    "entryPoint": "main",
                    "moduleImpl": "wasm",
                    "downloadUrl": "",
                    "hash": "",
                }
            },
            "publishTopics": {},
            "subscribeTopics": {},
        }
    )

    with TemporaryDirectory(prefix="lc_deploy_") as temporary_dir:
        tmpdir = Path(temporary_dir)
        named_module = tmpdir / "".join([module_name] + module_file.suffixes)
        shutil.copy(module_file, named_module)
        deployment.modules[module_name].downloadUrl = str(named_module)
        deployment_manifest = DeploymentManifest(deployment=deployment)

        populate_urls_and_hashes(
            deployment_manifest, get_my_ip_by_routing(), webserver_port, tmpdir
        )
        make_unique_module_ids(deployment_manifest)

        yield tmpdir, deployment_manifest


def make_unique_module_ids(deploy_man: DeploymentManifest) -> None:
    """
    Makes module identifiers in the deployment manifest unique
    across deployments, by suffixing them with a slice of the
    module's hash.
    """
    modules = deploy_man.deployment.modules
    old_to_new = {name: f"{name}-{m.hash[:5]}" for name, m in modules.items()}

    # Update modules
    for old_id, new_id in old_to_new.items():
        module = modules.pop(old_id)
        modules[new_id] = module

    # Update instanceSpecs
    instances = deploy_man.deployment.instanceSpecs
    for instance in instances.values():
        instance.moduleId = old_to_new[instance.moduleId]


def get_empty_deployment() -> DeploymentManifest:
    deployment = {
        "deployment": {
            "deploymentId": str(uuid.uuid4()),
            "instanceSpecs": {},
            "modules": {},
            "publishTopics": {},
            "subscribeTopics": {},
        }
    }
    return DeploymentManifest.model_validate(deployment)


def update_deployment_manifest(
    deployment_manifest: DeploymentManifest,
    host: str,
    port: int,
    files_dir: Path,
    target_arch: Optional[Target],
    use_signed: bool,
) -> None:
    for module in deployment_manifest.deployment.modules.keys():
        wasm_file = files_dir / f"{module}.{ModuleExtension.WASM}"
        if not wasm_file.is_file():
            logger.error(
                f"{wasm_file} not found. Please build the modules before deployment"
            )
            raise typer.Exit(code=1)

        name_parts = [module]
        if target_arch:
            name_parts += [target_arch.value, ModuleExtension.AOT.value]
        else:
            name_parts.append(ModuleExtension.WASM.value)

        if use_signed and target_arch:
            name_parts.append(ModuleExtension.SIGNED.value)

        file = files_dir / ".".join(name_parts)

        if use_signed and not target_arch:
            logger.warning(
                f"There is no target architecture, the {file} module to be deployed is not signed"
            )

        # use the downloadUrl field as placeholder, read from the function below
        deployment_manifest.deployment.modules[module].downloadUrl = str(file)

    populate_urls_and_hashes(deployment_manifest, host, port, files_dir.parent)


def calculate_sha256(path: Path) -> str:
    sha256_hash = hashlib.sha256()
    sha256_hash.update(path.read_bytes())
    return sha256_hash.hexdigest()


def populate_urls_and_hashes(
    deployment_manifest: DeploymentManifest,
    host: str,
    port: int,
    root_path: Path,
) -> None:
    for module in deployment_manifest.deployment.modules.keys():
        file = Path(deployment_manifest.deployment.modules[module].downloadUrl)
        deployment_manifest.deployment.modules[module].hash = calculate_sha256(file)
        deployment_manifest.deployment.modules[
            module
        ].downloadUrl = (
            f"http://{host}:{port}/{PurePosixPath(file.relative_to(root_path))}"
        )

    # DeploymentId based on deployment manifest content
    deployment_manifest.deployment.deploymentId = ""
    deployment_manifest_hash = hashlib.sha256(
        str(deployment_manifest.model_dump()).encode("utf-8")
    )
    deployment_manifest.deployment.deploymentId = deployment_manifest_hash.hexdigest()
