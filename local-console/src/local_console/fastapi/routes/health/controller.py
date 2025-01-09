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
from fastapi import HTTPException
from fastapi import status
from local_console.core.device_services import DeviceServices
from local_console.fastapi.routes.health.dto import HealthDTO


class HealthController:

    def __init__(self, device_service: DeviceServices) -> None:
        self.device_service = device_service

    def health(self) -> HealthDTO:
        if self.device_service.started:
            return HealthDTO(status="OK")
        else:
            raise HTTPException(
                status_code=status.HTTP_425_TOO_EARLY,
                detail="Local Console backend still starting up",
            )
