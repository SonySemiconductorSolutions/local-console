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
import logging
from enum import IntEnum
from pathlib import Path
from typing import Annotated
from typing import Any

from local_console.core.files.device import InferenceFileManager
from local_console.core.files.exceptions import FileNotFound
from local_console.core.schemas.schemas import DeviceID
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class InferenceType(IntEnum):
    FLATBUFFER = 0
    JSON = 1


class InferenceDetail(BaseModel):
    t: Annotated[str, Field(..., alias="T")]
    o: Annotated[Any, Field(..., alias="O")]
    f: Annotated[InferenceType | None, Field(alias="F")] = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Inference(BaseModel):
    device_id: str = Field(..., alias="DeviceID")
    model_id: str = Field(..., alias="ModelID")
    image: bool = Field(..., alias="Image")
    inferences: list[InferenceDetail] = Field(..., alias="Inferences")

    model_config = ConfigDict(
        extra="allow", populate_by_name=True, protected_namespaces=()
    )


class InferenceDetailOut(BaseModel):
    time: Annotated[str, Field(..., serialization_alias="T")]
    data: Annotated[Any, Field(..., serialization_alias="O")]
    ftype: Annotated[InferenceType | None, Field(serialization_alias="F")] = None


class InferenceOut(BaseModel):
    device_id: str = Field(..., alias="DeviceID")
    model_id: str = Field(..., alias="ModelID")
    image: bool = Field(..., alias="Image")
    inferences: list[InferenceDetailOut] = Field(..., alias="Inferences")

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())


class InferenceWithSource(BaseModel):
    path: Path
    inference: Inference


class InferenceManager:
    def __init__(self, files: InferenceFileManager) -> None:
        self.files = files

    def _inference_or_none(self, inference_path: Path) -> InferenceWithSource | None:
        try:
            inf = Inference.model_validate_json(inference_path.read_text())
            return InferenceWithSource(path=inference_path, inference=inf)
        except ValidationError as e:
            logger.error(f"Could not parse inference from {inference_path}", exc_info=e)
        except Exception as e:
            logger.error(f"Unknown error from {inference_path}", exc_info=e)
        return None

    def list(self, device_id: DeviceID) -> list[InferenceWithSource]:
        files = self.files.list_for(device_id)
        return [inf for f in files if (inf := self._inference_or_none(f))]

    def get(self, device_id: DeviceID, inference_id: str) -> InferenceWithSource:
        inferences = [
            inf for inf in self.list(device_id) if inf.path.name == inference_id
        ]
        if len(inferences) < 1:
            raise FileNotFound(
                filename=inference_id,
                message=f"Inference file '{inference_id}' not found",
            )
        elif len(inferences) > 1:
            raise AssertionError(
                f"Multiple inference files with id '{inference_id}' exist"
            )
        return inferences[0]
