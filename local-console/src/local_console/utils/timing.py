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
from typing import Callable

import trio


class TimeoutBehavior:
    def __init__(self, timeout: float, callback: Callable):
        self.timeout_secs = timeout
        self.callback = callback

        self._event_flag = trio.Event()

    def tap(self) -> None:
        """
        Avoid timer expiration
        """
        self._event_flag.set()

    def spawn_in(self, nursery: trio.Nursery) -> None:
        nursery.start_soon(self.timeout_behavior_task)

    async def timeout_behavior_task(self) -> None:
        """
        This task will call the given callable if the
        event flag has not been refreshed within the timeout period,
        specified in seconds as per trio.move_on_after().
        """
        while True:
            with trio.move_on_after(self.timeout_secs) as time_cs:
                await self._event_flag.wait()
                time_cs.deadline += self.timeout_secs
                self._event_flag = trio.Event()

            if time_cs.cancelled_caught:
                await self.callback()
