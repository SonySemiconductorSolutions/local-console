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
import logging
from collections import OrderedDict
from collections.abc import Iterator
from os import walk
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


class WatchException(Exception):
    pass


class StorageSizeWatcher:
    class State(enum.Enum):
        Start = enum.auto()
        Accumulating = enum.auto()
        Checking = enum.auto()

    def __init__(self, check_frequency: int = 50) -> None:
        """
        Class for watching a directory for incoming files while maintaining
        the total storage usage within the directory under a given limit size,
        pruning the oldest files when necessary.

        Bookkeeping is made in-memory for it to remain fast, however consistency
        is checked against the filesystem once every given number of incoming
        files.

        Args:
                check_frequency (int, optional): check consistency after this many new files. Defaults to 50.
        """
        self.check_frequency = check_frequency
        self._paths: set[Path] = set()
        self.state = self.State.Start
        self._size_limit: Optional[int] = None
        self.content: OrderedDict[tuple[int, Path], int] = OrderedDict()
        self.storage_usage = 0
        self._remaining_before_check = self.check_frequency

    def set_path(self, path: Path) -> None:
        assert path.is_dir()

        p = path.resolve()
        if p in self._paths:
            return
        self._paths.add(p)

        # Execute regardless of current state
        self._build_content_dict()

    def unwatch_path(self, path: Path) -> None:
        assert path.is_dir()
        self._paths.discard(path.resolve())

    def set_storage_limit(self, limit: int) -> None:
        assert limit >= 0

        self._size_limit = limit
        if self.state == self.State.Accumulating:
            self._prune()

    def incoming(self, path: Path) -> None:
        assert path.is_file()

        if not self._paths:
            return

        if not any(path.resolve().is_relative_to(root) for root in self._paths):
            raise WatchException(
                f"Incoming file {path} does not belong to either of {self._paths}"
            )

        if self.state == self.State.Accumulating:
            self._register_file(path)

            self._remaining_before_check -= 1
            if self._remaining_before_check == 0:
                self._consistency_check()
                self._remaining_before_check = self.check_frequency

            self._prune()
        else:
            logger.warning(
                f"Deferring update of size statistic for incoming file {path} during state {self.state}"
            )

    def get_oldest(self) -> Optional[tuple[int, Path]]:
        if self.content:
            key = next(iter(self.content.keys()))
            assert key
            return key
        else:
            return None

    def _register_file(self, path: Path) -> None:
        key, val = walk_entry(path)
        self.content[key] = val
        self.storage_usage += val

    def _unregister_file(self, path: Path) -> None:
        key, val = walk_entry(path)
        self.storage_usage -= val
        try:
            self.content.pop(key)
        except KeyError:
            stale_keys = [sk for sk in self.content if sk[1] == path]
            for sk in stale_keys:
                self.content.pop(sk)

    def _build_content_dict(self) -> None:
        """
        Generate a dictionary ordered first by file age, then by file name
        for disambiguation, with the value being the file size.
        """
        assert self._paths
        self.state = self.State.Accumulating

        sorted_e = sorted(
            (walk_entry(p) for root in self._paths for p in walk_files(root)),
            key=lambda e: e[0],
        )
        self.content = OrderedDict(sorted_e)
        self.storage_usage = sum(e[1] for e in sorted_e)

    def _prune(self) -> None:
        if self._size_limit is None:
            return

        # In order to make this class thread-safe,
        # the following would be required:
        # self.state == self.State.Checking

        while self.storage_usage > self._size_limit:
            try:
                (_, path), size = self.content.popitem(last=False)
                path.unlink()
                self.storage_usage -= size
            except FileNotFoundError:
                logger.warning(f"File {path} was already removed")
            except KeyError:
                break

        # In order to make this class thread-safe,
        # the following would be required:
        # self.state == self.State.Accumulating

    def _consistency_check(self) -> bool:
        assert self._paths
        in_memory = {k[1] for k in self.content.keys()}
        in_storage = {p for root in self._paths for p in walk_files(root)}

        difference = in_storage - in_memory
        if difference:
            logger.warning(
                f"File bookkeeping inconsistency: new files on disk are: {difference}"
            )
            for path in difference:
                self._register_file(path)
            return False

        difference = in_memory - in_storage
        if difference:
            logger.warning(
                f"File bookkeeping inconsistency: files unexpectedly removed: {difference}"
            )
            for path in difference:
                self._unregister_file(path)
            return False

        return True


def walk_entry(path: Path) -> tuple[tuple[int, Path], int]:
    st = path.stat()
    file_age = st.st_mtime_ns
    file_size = st.st_size
    return (file_age, path), file_size


def walk_files(root: Path) -> Iterator[Path]:
    # os.walk to be replaced with:
    # https://docs.python.org/3.12/library/pathlib.html#pathlib.Path.walk
    for dir_path, dir_names, file_names in walk(root):
        for fname in file_names:
            yield Path(dir_path).joinpath(fname)
