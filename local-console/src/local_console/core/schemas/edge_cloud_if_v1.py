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
Edge Cloud IF v1 schemas. Properties not included here are ignored. For example, PQ settings.
"""
from local_console.utils.schemas import ListModel
from pydantic import BaseModel
from pydantic import Field


class Hardware(BaseModel):
    Sensor: str
    SensorId: str
    KG: str
    ApplicationProcessor: str
    LedOn: bool


class DnnModelVersion(ListModel):
    root: list[str]


class Version(BaseModel):
    SensorFwVersion: str
    SensorLoaderVersion: str
    DnnModelVersion: DnnModelVersion
    ApFwVersion: str
    ApLoaderVersion: str


class Status(BaseModel):
    Sensor: str
    ApplicationProcessor: str


class OTA(BaseModel):
    SensorFwLastUpdatedDate: str
    SensorLoaderLastUpdatedDate: str
    DnnModelLastUpdatedDate: list[str]
    ApFwLastUpdatedDate: str
    UpdateProgress: int
    UpdateStatus: str


class Permission(BaseModel):
    FactoryReset: bool


class DeviceConfiguration(BaseModel):
    Hardware: Hardware
    Version: Version
    Status: Status
    OTA: OTA
    Permission: Permission


class DnnOtaBody(BaseModel):
    UpdateModule: str = Field(default="DnnModel")
    DesiredVersion: str
    PackageUri: str
    HashValue: str


class DnnOta(BaseModel):
    OTA: DnnOtaBody


class DnnDeleteBody(BaseModel):
    UpdateModule: str = Field(default="DnnModel")
    DeleteNetworkID: str


class DnnDelete(BaseModel):
    OTA: DnnDeleteBody


class SetFactoryReset(BaseModel):
    Permission: Permission


class StartUploadInferenceData(BaseModel):
    Mode: int = 1
    UploadMethod: str = "HttpStorage"
    StorageName: str
    StorageSubDirectoryPath: str
    UploadMethodIR: str = "HttpStorage"
    StorageNameIR: str
    UploadInterval: int = 30
    StorageSubDirectoryPathIR: str
    CropHOffset: int
    CropVOffset: int
    CropHSize: int
    CropVSize: int
