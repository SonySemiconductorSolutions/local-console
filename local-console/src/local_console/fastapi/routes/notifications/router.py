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
from fastapi import APIRouter
from fastapi import WebSocket
from local_console.fastapi.dependencies.notifications import websockets_from_app

router = APIRouter(
    # prefix="/ws", Cannot use this for websockets. Read test suite doc.
    tags=["Notifications"],
)


@router.websocket_route("/")
async def notifications(websocket: WebSocket) -> None:
    # Websocket endpoints cannot use Depends()-based injection of
    # dependencies. See:
    # https://github.com/fastapi/fastapi/issues/4957
    app = websocket.app
    controller = websockets_from_app(app)
    await controller.loop_for(websocket)
