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
from random import random
from unittest.mock import AsyncMock

import pytest
import trio
from local_console.utils.timing import TimeoutBehavior


@pytest.mark.trio
async def test_timeout_expires_once(autojump_clock, nursery):
    timeout = 3
    callable_mock = AsyncMock()
    timeout_obj = TimeoutBehavior(timeout, callable_mock)
    timeout_obj.spawn_in(nursery)

    await trio.sleep(timeout + 0.1)
    callable_mock.assert_called_once()


@pytest.mark.trio
async def test_timeout_expires_multiple_times(autojump_clock, nursery):
    timeout = 3
    expirations = 4
    callable_mock = AsyncMock()
    timeout_obj = TimeoutBehavior(timeout, callable_mock)
    timeout_obj.spawn_in(nursery)

    await trio.sleep(expirations * timeout + 0.1)
    assert callable_mock.call_count == expirations


@pytest.mark.trio
async def test_timeout_avoided_once(autojump_clock, nursery):
    timeout = 3
    callable_mock = AsyncMock()
    timeout_obj = TimeoutBehavior(timeout, callable_mock)
    timeout_obj.spawn_in(nursery)

    await trio.sleep(0.5 * timeout)
    timeout_obj.tap()
    await trio.sleep(0.5 * timeout)
    assert callable_mock.call_count == 0


@pytest.mark.trio
async def test_timeout_avoided_once_then_expired(autojump_clock, nursery):
    timeout = 3
    callable_mock = AsyncMock()
    timeout_obj = TimeoutBehavior(timeout, callable_mock)
    timeout_obj.spawn_in(nursery)

    await trio.sleep(0.5 * timeout)
    timeout_obj.tap()
    await trio.sleep(0.5 * timeout)
    assert callable_mock.call_count == 0

    await trio.sleep(timeout + 0.1)
    assert callable_mock.call_count == 1


@pytest.mark.trio
async def test_timeout_avoided_repeatedly(autojump_clock, nursery):
    timeout = 3
    callable_mock = AsyncMock()
    timeout_obj = TimeoutBehavior(timeout, callable_mock)
    timeout_obj.spawn_in(nursery)

    await trio.sleep(0.5 * timeout)
    timeout_obj.tap()
    await trio.sleep(0.5 * timeout)
    assert callable_mock.call_count == 0
    timeout_obj.tap()

    for _ in range(20):
        await trio.sleep(random() * timeout)
        timeout_obj.tap()
        assert callable_mock.call_count == 0
