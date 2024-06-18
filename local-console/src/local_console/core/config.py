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
import configparser
import json
import logging
from pathlib import Path
from typing import Any
from typing import get_args
from typing import get_type_hints
from typing import Optional

from local_console.core.enums import config_paths
from local_console.core.schemas.schemas import AgentConfiguration
from local_console.core.schemas.schemas import DeploymentManifest
from local_console.core.schemas.schemas import EVPParams
from local_console.core.schemas.schemas import IPAddress
from local_console.core.schemas.schemas import MQTTParams
from local_console.core.schemas.schemas import TLSConfiguration
from local_console.core.schemas.schemas import WebserverParams
from pydantic import BaseModel
from pydantic import ValidationError

logger = logging.getLogger(__name__)


def get_default_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config["evp"] = {
        "iot_platform": "EVP1",
    }
    config["mqtt"] = {"host": "localhost", "port": "1883"}
    config["webserver"] = {"host": "localhost", "port": "8000"}
    return config


def setup_default_config() -> None:
    config_file = config_paths.config_path
    if not config_file.is_file():
        logger.info("Generating default config_paths")
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_paths.config_path, "w") as f:
                get_default_config().write(f)
        except OSError as e:
            logger.error(f"Error while generating folder {config_file.parent}: {e}")
            raise SystemExit()


def parse_ini(config_parser: configparser.ConfigParser) -> str:
    parsed_config = ["\n"]
    for section in config_parser.sections():
        parsed_config.append(f"[{section}]")
        for key, value in config_parser.items(section):
            parsed_config.append(f"{key} = {value}")
    return "\n".join(parsed_config)


def config_to_schema(config: configparser.ConfigParser) -> AgentConfiguration:
    try:
        return AgentConfiguration(
            evp=EVPParams(
                iot_platform=config["evp"]["iot_platform"],
            ),
            mqtt=MQTTParams(
                host=IPAddress(ip_value=config["mqtt"]["host"]),
                port=int(config["mqtt"]["port"]),
                device_id=config["mqtt"].get("device_id", None),
            ),
            webserver=WebserverParams(
                host=IPAddress(ip_value=config["webserver"]["host"]),
                port=int(config["webserver"]["port"]),
            ),
            tls=TLSConfiguration(
                ca_certificate=optional_path(
                    config.get("tls", "ca_certificate", fallback=None)
                ),
                ca_key=optional_path(config.get("tls", "ca_key", fallback=None)),
            ),
        )
    except KeyError as e:
        logger.error(
            f"Config file not correct. Section or parameter missing is {e}. \n The file should have the following sections and parameters {parse_ini(get_default_config())}"
        )
        raise SystemExit()


def optional_path(path: Optional[str]) -> Optional[Path]:
    return Path(path) if path else None


def get_config(config_file: Optional[Path] = None) -> AgentConfiguration:
    config_parser: configparser.ConfigParser = configparser.ConfigParser()
    try:
        config_parser.read(config_paths.config_path if not config_file else config_file)
    except FileNotFoundError:
        logger.error("Config file not found")
        exit(1)
    except configparser.MissingSectionHeaderError:
        logger.error("No header found in the specified file")
        exit(1)
    return config_to_schema(config_parser)


def get_deployment_schema() -> DeploymentManifest:
    try:
        with open(config_paths.deployment_json) as f:
            deployment_data = json.load(f)
    except Exception:
        logger.error("deployment.json does not exist or is not well formed")
        exit(1)
    try:
        return DeploymentManifest(**deployment_data)
    except ValidationError as e:
        missing_field = list(e.errors()[0]["loc"])[1:]
        logger.warning(f"Missing field in the deployment manifest: {missing_field}")
        exit(1)


def check_section_and_params(
    agent_config: AgentConfiguration, section: str, parameter: Optional[str] = None
) -> None:
    if section not in agent_config.model_fields:
        logger.error(f"Invalid section. Valid ones are: {agent_config.__dict__.keys()}")
        raise ValueError

    section_from_agent_spec = AgentConfiguration.model_fields[section]
    section_model = unwrap_class(section_from_agent_spec.annotation)
    if parameter and parameter not in section_model.model_fields:
        logger.error(
            f"Invalid parameter of the {section} section. Valid ones are: {list(section_model.model_fields.keys())}"
        )
        raise ValueError


def parse_section_to_ini(
    section_model: BaseModel, section_name: str, parameter: Optional[str] = None
) -> str:
    ini_lines = [f"[{section_name}]"]
    if parameter:
        ini_lines.append(parameter_render(parameter, section_model))
    else:
        for parameter in section_model.model_fields.keys():
            ini_lines.append(parameter_render(parameter, section_model))

    return "\n".join(ini_lines)


def parameter_render(parameter: str, section_model: BaseModel) -> str:
    param_value = getattr(section_model, parameter)
    return f"{parameter} = {param_value}"


def unwrap_class(cls: Any) -> Any:
    """
    This function will strip the Optional in an Optional[T]
    type annotation, if the provided class object has been
    annotated that way.
    """
    args = get_args(cls)
    if args:
        return args[0]
    else:
        return cls


def cast_rawvalue_as_field(raw_value: Optional[str], field_class: Any) -> Any:
    """
    This function will cast a raw value (e.g. just read from a config file)
    into a target field type.
    """
    if raw_value is None:
        return None
    if not issubclass(field_class, BaseModel):
        value = field_class(raw_value)
    else:
        fields = field_class.model_fields
        if len(fields) == 1:
            field = next(iter(fields.keys()))
            value = field_class(**{field: raw_value})
        else:
            raise ValueError
    return value


def schema_to_parser(
    agent_config: AgentConfiguration, section: str, parameter: str, new: Optional[str]
) -> configparser.ConfigParser:
    try:
        sec_obj = getattr(agent_config, section)
        field_types = get_type_hints(sec_obj, include_extras=False)
        field_class = unwrap_class(field_types[parameter])
        value = cast_rawvalue_as_field(new, field_class)
        setattr(sec_obj, parameter, value)
    except ValidationError as e:
        err = e.errors()[0]
        if new is None:
            # This happens when unsetting a value
            msg = f"Parameter '{parameter}' in section '{section}' cannot be unset"
        else:
            # The most usual case: the input cannot be cast into the expected data type
            msg = f"Setting parameter '{parameter}' in section '{section}': {err['msg']} (was '{new}')"
        logger.error(msg)
        raise e
    except ValueError as e:
        raise ValueError(f"Unable to validate value for '{section}.{parameter}'") from e

    config_dict = agent_config.model_dump(exclude_none=True)
    config_parser = configparser.ConfigParser()
    for section_names, values in config_dict.items():
        config_parser[section_names] = values
    return config_parser
