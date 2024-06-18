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
from collections.abc import Iterable

from Crypto.Hash import SHA256  # type: ignore
from Crypto.PublicKey import ECC  # type: ignore
from Crypto.Signature import DSS  # type: ignore

_SWAF_ECDSA_SIGN_PADDED_SIZE = 80
_SWAF_FOOTER_META_SIZE = 16
_SWAF_FOOTER_META_VERSION = (0x00, 0x00)
_SWAF_FOOTER_META_IDENTIFIER = (0x3A, 0x53, 0xF0, 0x07)


def make_swaf_bytes(input_aot_ba: bytes, priv_key_ba: bytes) -> Iterable[bytes]:
    #
    # Check WASM AoT file bytes
    #

    input_aot_len = len(input_aot_ba)
    aot_hash = SHA256.new(input_aot_ba)

    if input_aot_len <= 0:
        raise ValueError("Input file size is 0 bytes")

    #
    # Import private key
    #
    priv_key = ECC.import_key(priv_key_ba)

    #
    # Calculate signature (deterministic ECDSA P-256 and SHA-256)
    #
    signer = DSS.new(priv_key, "deterministic-rfc6979", encoding="der")
    sig_ba = signer.sign(aot_hash)

    sig_len = len(sig_ba)
    assert sig_len <= _SWAF_ECDSA_SIGN_PADDED_SIZE
    padding_len = _SWAF_ECDSA_SIGN_PADDED_SIZE - sig_len
    padding_ba = bytes([0] * padding_len)

    #
    # Calculate SHA-256 of AoT file and signature (+padding)
    #
    aot_and_sig_hash = SHA256.new(input_aot_ba + sig_ba + padding_ba)

    #
    # Calculate SHA-256 of public key
    #
    pub_key = priv_key.public_key()
    pub_key_ba = pub_key.export_key(format="DER")
    pub_key_hash = SHA256.new(pub_key_ba)

    #
    # Make footer meta information
    #
    footer_meta_array = [0] * _SWAF_FOOTER_META_SIZE
    footer_meta_array[3] = padding_len & 0xFF
    footer_meta_array[4] = (input_aot_len >> 0) & 0xFF
    footer_meta_array[5] = (input_aot_len >> 8) & 0xFF
    footer_meta_array[6] = (input_aot_len >> 16) & 0xFF
    footer_meta_array[7] = (input_aot_len >> 24) & 0xFF
    footer_meta_array[8] = (sig_len >> 0) & 0xFF
    footer_meta_array[9] = (sig_len >> 8) & 0xFF
    footer_meta_array[10] = _SWAF_FOOTER_META_VERSION[0]
    footer_meta_array[11] = _SWAF_FOOTER_META_VERSION[1]
    footer_meta_array[12] = _SWAF_FOOTER_META_IDENTIFIER[0]
    footer_meta_array[13] = _SWAF_FOOTER_META_IDENTIFIER[1]
    footer_meta_array[14] = _SWAF_FOOTER_META_IDENTIFIER[2]
    footer_meta_array[15] = _SWAF_FOOTER_META_IDENTIFIER[3]
    footer_meta_ba = bytes(footer_meta_array)

    #
    # Make SWAF bytes
    #
    return (
        input_aot_ba,
        sig_ba,
        padding_ba,
        aot_and_sig_hash.digest(),
        pub_key_hash.digest(),
        footer_meta_ba,
    )


def sign(content: bytes, ecdsa_private_key: bytes) -> bytes:
    return b"".join(make_swaf_bytes(content, ecdsa_private_key))
