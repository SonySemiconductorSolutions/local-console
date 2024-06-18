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
import random
from collections import OrderedDict
from itertools import cycle
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from local_console.utils.fswatch import StorageSizeWatcher


@pytest.fixture
def dir_layout(tmpdir):
    entries = [
        tmpdir.join("fileA"),
        tmpdir.join("fileB"),
        tmpdir.mkdir("sub").join("file0"),
        tmpdir.join("sub").mkdir("subsub").join("file0"),
    ]
    # Make all entries, files of size 1
    for e in entries:
        e.write_binary(b"0")

    return [Path(tmpdir), len(entries)]


class walk_entry_mock:
    def __init__(self) -> None:
        self.age = 0
        self.cache: dict[Path, int] = {}

    def __call__(self, path: Path) -> tuple[tuple[int, Path], int]:
        size = 1
        if path in self.cache:
            age = self.cache[path]
        else:
            age = self.age
            self.cache[path] = age
            self.age += 1
        return (age, path), size


def create_new(root: Path) -> Path:
    new_file = root / f"{random.randint(1, 1e6)}"
    new_file.write_bytes(b"0")
    return new_file


def test_regular_sequence(dir_layout):
    dir_base, size = dir_layout
    with patch("local_console.utils.fswatch.walk_entry", walk_entry_mock()):
        w = StorageSizeWatcher(check_frequency=10)
        assert w.state == StorageSizeWatcher.State.Start

        w.set_path(dir_base)
        assert w.state == StorageSizeWatcher.State.Accumulating
        assert w.storage_usage == size

        w.incoming(create_new(dir_base))
        assert w.state == StorageSizeWatcher.State.Accumulating
        assert w.storage_usage == size + 1
        size += 1

        oldest_age, _ = w.get_oldest()
        assert oldest_age == 0

        st_limit = 4
        w.set_storage_limit(st_limit)
        oldest_age, _ = w.get_oldest()
        assert oldest_age == 1
        assert w.storage_usage == st_limit
        assert w._consistency_check()

        # Test creating and registering new files
        # in lockstep
        num_new_files = random.randint(5, 20)
        for _ in range(num_new_files):
            w.incoming(create_new(dir_base))
        assert w._consistency_check()
        assert w.storage_usage == st_limit
        expected_oldest_age = oldest_age + num_new_files
        oldest_age, _ = w.get_oldest()
        # This is due to the timestamp mocking, as each new file
        # is timestamped one time unit later than the previous.
        assert oldest_age == expected_oldest_age

        # Test creating and registering new files
        # not in lockstep
        num_new_files = random.randint(5, 20)
        for _ in range(num_new_files):
            create_new(dir_base)
        # although consistency_check restores consistency,
        # it returns whether state was consistent before
        assert not w._consistency_check()
        # hence, a further call should indicate consistency.
        assert w._consistency_check()
        expected_oldest_age = oldest_age + num_new_files

        # However, pruning is still necessary:
        oldest_age, _ = w.get_oldest()
        assert oldest_age != expected_oldest_age
        assert w.storage_usage != st_limit
        w._prune()
        oldest_age, _ = w.get_oldest()
        assert oldest_age == expected_oldest_age
        assert w.storage_usage == st_limit


def test_incoming_always_prunes(dir_layout):
    dir_base, size = dir_layout
    mock_prune = Mock()
    with patch(
        "local_console.utils.fswatch.walk_entry", walk_entry_mock()
    ), patch.object(StorageSizeWatcher, "_prune", mock_prune):
        w = StorageSizeWatcher(check_frequency=10)
        w.set_path(dir_base)
        st_limit = 4
        assert mock_prune.call_count == 0
        w.set_storage_limit(st_limit)
        assert mock_prune.call_count == 1

        num_new_files = random.randint(5, 20)
        for _ in range(num_new_files):
            w.incoming(create_new(dir_base))
        assert mock_prune.call_count == num_new_files + 1


def test_remaining_before_consistency_check(dir_layout):
    check_frequency = 10
    storage_limit = 4

    dir_base, size = dir_layout
    mock_prune = Mock()
    with patch(
        "local_console.utils.fswatch.walk_entry", walk_entry_mock()
    ), patch.object(StorageSizeWatcher, "_prune", mock_prune):
        w = StorageSizeWatcher(check_frequency=check_frequency)
        w.set_path(dir_base)
        w.set_storage_limit(storage_limit)
        assert w._remaining_before_check == check_frequency

        for i in range(check_frequency):
            assert w._remaining_before_check == check_frequency - i
            w.incoming(create_new(dir_base))
        assert w._remaining_before_check == check_frequency


def test_age_bookkeeping():
    names = "abcdefghijklmn"
    timestamps = list(range(len(names)))
    random.shuffle(timestamps)

    # helper dict for building assertions
    min_timestamp = min(timestamps)
    max_timestamp = max(timestamps)
    helper = {
        timestamp: name
        for timestamp, name in zip(timestamps, names)
        if timestamp in (min_timestamp, max_timestamp)
    }
    name_of_min_timestamp = helper[min_timestamp]
    name_of_max_timestamp = helper[max_timestamp]

    odd = OrderedDict(
        sorted(
            ((((timestamp, name), None)) for timestamp, name in zip(timestamps, names)),
            key=lambda e: e[0],
        )
    )
    first_key = next(iter(odd.keys()))
    assert first_key == (min_timestamp, name_of_min_timestamp)

    last_key, _ = odd.popitem()
    assert last_key == (max_timestamp, name_of_max_timestamp)

    popped_first, _ = odd.popitem(last=False)
    assert first_key == popped_first


@pytest.fixture
def multi_dir_layout(tmpdir):
    bases = [tmpdir.mkdir("sub_X"), tmpdir.mkdir("sub_Y")]
    entries = [
        bases[0].join("file0"),
        bases[0].mkdir("internal").join("file1"),
        bases[1].join("fileA"),
        bases[1].join("fileB"),
    ]
    # Make all entries, files of size 1
    for e in entries:
        e.write_binary(b"0")

    return [Path(b) for b in bases], len(entries)


def create_new_agename(root: Path, age_name: int) -> Path:
    new_file = root / f"age_{age_name}"
    new_file.write_bytes(b"0")
    return new_file


def test_regular_sequence_multiple_dirs(multi_dir_layout):
    dir_bases, initial_size = multi_dir_layout
    expected_curr_size = initial_size
    walk_entry_fn = walk_entry_mock()
    with patch("local_console.utils.fswatch.walk_entry", walk_entry_fn):
        w = StorageSizeWatcher(check_frequency=10)
        assert w.state == StorageSizeWatcher.State.Start

        w.set_path(dir_bases[0])
        assert w.state == StorageSizeWatcher.State.Accumulating
        assert w.storage_usage < expected_curr_size
        oldest_age, _ = w.get_oldest()
        assert oldest_age == 0

        w.set_path(dir_bases[1])
        assert w.storage_usage == expected_curr_size
        assert w.state == StorageSizeWatcher.State.Accumulating
        oldest_age, _ = w.get_oldest()
        assert oldest_age == 0

        # Test that adding a new file while no limit has been set yet,
        # does not invoke pruning, so the previous oldest file remains.
        w.incoming(create_new_agename(dir_bases[0], walk_entry_fn.age))
        expected_curr_size += 1
        assert w.storage_usage == expected_curr_size
        assert w.state == StorageSizeWatcher.State.Accumulating
        oldest_age, _ = w.get_oldest()
        assert oldest_age == 0

        # Test that setting the size limit, invokes pruning, making
        # the oldest file, a more recent one.
        st_limit = 4
        w.set_storage_limit(st_limit)
        expected_curr_size = st_limit
        assert w.storage_usage == expected_curr_size
        oldest_age, _ = w.get_oldest()
        assert oldest_age == 1

        # Test creating and registering new files in lockstep
        num_new_files = random.randint(5, 20)
        for _, base in zip(range(num_new_files), cycle(dir_bases)):
            w.incoming(create_new_agename(base, walk_entry_fn.age))
            assert w._consistency_check()
            assert w.storage_usage <= st_limit

        files_created_up_to_now = initial_size + 1 + num_new_files
        expected_newest_age = files_created_up_to_now - 1
        expected_oldest_age = expected_newest_age - st_limit + 1
        oldest_age, _ = w.get_oldest()
        assert oldest_age == expected_oldest_age

        # Test setting a limit larger than current usage
        st_limit = 7
        w.set_storage_limit(st_limit)
        # expected_curr_size is unchanged as the limit
        # is greater than the current size.
        assert w.storage_usage == expected_curr_size
