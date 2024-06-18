#!/usr/bin/env python
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
"""
Downloads source code of tools.
"""
import json
import pathlib
import subprocess

root_path = pathlib.Path(__file__).parent.absolute()
target_folder = pathlib.Path() / "tools"


def main() -> None:
    with open(root_path / "manual-application-tools-sbom.json") as f:
        data = json.loads(f.read())

    for component in data["components"]:
        branch, url = None, None
        for ref in component["externalReferences"]:
            if ref["type"] == "code":
                url = ref["url"]
            elif ref["type"] == "branch":
                branch = ref["url"]
        if url and branch:
            name = component["bom-ref"]
            folder = str(target_folder / name)
            subprocess.run(
                ["git", "clone", "--branch", branch, "--depth", "1", url, folder]
            )
        else:
            print(f"{component['bom-ref']} is missing.")
            exit(1)


if __name__ == "__main__":
    main()
