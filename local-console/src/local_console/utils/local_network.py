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
import ipaddress
import logging
import platform
import socket

import psutil

logger = logging.getLogger(__file__)


def get_network_ifaces() -> list[str]:
    """
    Gets network interfaces over which a local server could be
    reached in the local network.

    Returns:
        list[str]: List of network interface names
    """
    stats = psutil.net_if_stats()
    os_name = platform.system()
    if os_name == "Windows":
        chosen = list(
            k
            for k, v in stats.items()
            if v.isup and "loopback" not in k.lower() and "vethernet" not in k.lower()
        )
    else:
        chosen = list(
            k
            for k, v in stats.items()
            if v.isup
            and "running" in v.flags
            and "loopback" not in v.flags
            and "pointopoint" not in v.flags
        )
    return chosen


def get_my_ip_by_routing() -> str:
    """
    This gets the machine's IP by checking assigned IPv4
    addresses to network interfaces determined to be
    accessible by other devices in the local network.
    """
    ifaces = get_network_ifaces()
    infos = psutil.net_if_addrs()
    addr_info = {
        iface: [
            info for info in infos[iface] if info.family == socket.AddressFamily.AF_INET
        ]
        for iface in ifaces
    }
    chosen = next(addrs[0] for iface, addrs in addr_info.items() if addrs)
    return chosen.address


LOCAL_IP: str = get_my_ip_by_routing()


def is_localhost(hostname: str) -> bool:
    try:
        resolved_ip = socket.gethostbyname(hostname)
        return ipaddress.ip_address(resolved_ip).is_loopback
    except socket.gaierror:
        return False
    except UnicodeError:
        # Raised when using very long strings
        return False
    except Exception as e:
        logger.warning(f"Unknown error while getting host by name: {e}")
    return False


def replace_local_address(hostname: str) -> str:
    return LOCAL_IP if is_localhost(hostname) else hostname


def is_valid_host(hostname: str) -> bool:
    try:
        socket.gethostbyname(hostname)
    except socket.gaierror as e:
        if e.errno == socket.EAI_NONAME:
            logger.warning(f"Invalid hostname or IP address - {hostname}: {e}")
        elif e.errno == socket.EAI_AGAIN:
            logger.warning(f"DNS look up error - {hostname}: {e}")
        else:
            logger.warning(f"Socket error - {hostname}: {e}")
        return False
    except Exception as e:
        logger.warning(f"An unexpected error occurred - {hostname}: {e}")
        return False
    return True
