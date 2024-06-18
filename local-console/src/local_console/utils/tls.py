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
import socket
import ssl
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Optional

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509 import Name
from cryptography.x509.oid import NameOID
from local_console.core.schemas.schemas import IPAddress
from local_console.core.schemas.schemas import TLSConfiguration
from retry import retry

logger = logging.getLogger(__name__)


def generate_signed_certificate_pair(
    identifier: str,
    ca_certificate: x509.Certificate,
    ca_private_key: rsa.RSAPrivateKey,
    key_size: int = 2048,
    is_server: bool = False,
) -> tuple[x509.Certificate, rsa.RSAPrivateKey]:
    client_private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )
    client_public_key = client_private_key.public_key()

    # Builder for client certificate
    client_cert_builder = x509.CertificateBuilder()

    client_cert_builder = client_cert_builder.subject_name(
        Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, identifier),
                # Add attributes from the CA certificate's subject, except its CN
                *(
                    x509.NameAttribute(attr.oid, attr.value)
                    for attr in ca_certificate.subject
                    if attr.oid != NameOID.COMMON_NAME
                ),
            ]
        )
    )
    client_cert_builder = client_cert_builder.issuer_name(ca_certificate.subject)
    client_cert_builder = client_cert_builder.not_valid_before(
        datetime.today() - timedelta(days=1)
    )
    client_cert_builder = client_cert_builder.not_valid_after(
        datetime.today() + timedelta(days=365)
    )
    client_cert_builder = client_cert_builder.serial_number(x509.random_serial_number())
    client_cert_builder = client_cert_builder.public_key(client_public_key)
    client_cert_builder = client_cert_builder.add_extension(
        x509.BasicConstraints(ca=False, path_length=None),
        critical=True,
    )

    # If used as a server certificate, add the identifier as its SAN.
    if is_server:
        client_cert_builder = client_cert_builder.add_extension(
            x509.SubjectAlternativeName([x509.DNSName(identifier)]), critical=False
        )

    # Sign the client certificate with the CA's private key
    client_certificate = client_cert_builder.sign(
        private_key=ca_private_key,
        algorithm=hashes.SHA256(),
    )

    return client_certificate, client_private_key


def ensure_certificate_pair_exists(
    identifier: str,
    certificate_path: Path,
    key_path: Path,
    tls_configuration: TLSConfiguration,
    is_server: bool = False,
) -> None:
    if not (certificate_path.is_file() and key_path.is_file()):
        assert tls_configuration.ca_certificate
        assert tls_configuration.ca_key
        ca_cert, ca_key = load_certificate_pair(
            tls_configuration.ca_certificate, tls_configuration.ca_key
        )
        certificate, key = generate_signed_certificate_pair(
            identifier, ca_cert, ca_key, is_server=is_server
        )
        if not certificate_path.parent.is_dir():
            certificate_path.parent.mkdir()
        if not key_path.parent.is_dir():
            key_path.parent.mkdir()
        export_cert_pair_as_pem(certificate, key, certificate_path, key_path)


def load_certificate_pair(
    ca_certificate_path: Path, ca_key_path: Path
) -> tuple[x509.Certificate, rsa.RSAPrivateKey]:
    ca_cert = x509.load_pem_x509_certificate(ca_certificate_path.read_bytes())
    ca_key = load_pem_private_key(ca_key_path.read_bytes(), password=None)
    return ca_cert, ca_key


def export_cert_pair_as_pem(
    certificate: x509.Certificate,
    client_private_key: rsa.RSAPrivateKey,
    certificate_file: Path,
    key_file: Path,
) -> None:
    logger.info(f"Writing private key {key_file}")
    with key_file.open("wb") as f:
        f.write(
            client_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Write the client's certificate to a file
    logger.info(f"Writing certificate {certificate_file}")
    with certificate_file.open("wb") as f:
        f.write(certificate.public_bytes(serialization.Encoding.PEM))


def get_random_identifier(prefix: str = "", max_length: int = 36) -> str:
    full = prefix + str(x509.random_serial_number())
    return full[:max_length]


@retry(tries=5, delay=0.3, exceptions=(ConnectionError, ssl.SSLError))
def get_remote_server_certificate(hostname: IPAddress, port: int) -> x509.Certificate:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((hostname.ip_value, port)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname.ip_value) as sslsock:
            # Get the server's certificate
            der_cert = sslsock.getpeercert(binary_form=True)
            # Parse DER form into x509 Certificate
            return x509.load_der_x509_certificate(der_cert)


def get_certificate_cn(certificate: x509.Certificate) -> Optional[str]:
    # Get the CN (Common Name) from the subject
    cn: Optional[str] = None
    for attribute in certificate.subject:
        if attribute.oid == NameOID.COMMON_NAME:
            cn = attribute.value
            break
    if cn is not None:
        return cn
    else:
        raise AttributeError("Certificate does not hold a Common Name")


def generate_self_signed_ca(
    ca_directory: Path,
    ca_name: str = "Your Own CA",
    validity_days: int = 365,
    key_size: int = 2048,
) -> tuple[Path, Path, x509.Certificate, rsa.RSAPrivateKey]:
    ca_private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )

    ca_cert_path = ca_directory / "ca.crt"
    ca_key_path = ca_directory / "ca.key"

    if ca_cert_path.is_file() and ca_key_path.is_file():
        ca_certificate, ca_private_key = load_certificate_pair(
            ca_cert_path, ca_key_path
        )
    else:
        # CA details are for a simple self-signed certificate, valid only in a local setting.
        ca_subject = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "ES"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "LocalDeploy"),
                x509.NameAttribute(NameOID.COMMON_NAME, ca_name),
            ]
        )
        ca_cert_builder = x509.CertificateBuilder()
        ca_cert_builder = ca_cert_builder.subject_name(ca_subject)
        ca_cert_builder = ca_cert_builder.issuer_name(
            ca_subject
        )  # Self-signed, so issuer is subject
        ca_cert_builder = ca_cert_builder.public_key(ca_private_key.public_key())
        ca_cert_builder = ca_cert_builder.serial_number(x509.random_serial_number())
        ca_cert_builder = ca_cert_builder.not_valid_before(
            datetime.today() - timedelta(days=1)
        )
        ca_cert_builder = ca_cert_builder.not_valid_after(
            datetime.today() + timedelta(days=validity_days)
        )
        ca_cert_builder = ca_cert_builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )

        # Sign CA certificate with its own private key
        ca_certificate = ca_cert_builder.sign(
            private_key=ca_private_key,
            algorithm=hashes.SHA256(),
        )

        export_cert_pair_as_pem(
            ca_certificate, ca_private_key, ca_cert_path, ca_key_path
        )
        logger.info("Created self-signed CA at %s", str(ca_cert_path))

    return ca_cert_path, ca_key_path, ca_certificate, ca_private_key


def verify_certificate_against_ca(
    certificate: x509.Certificate, ca_certificate: x509.Certificate
) -> None:
    # Get the public key from the CA certificate
    ca_public_key = ca_certificate.public_key()

    # Verify the signature on the certificate to be verified
    ca_public_key.verify(
        certificate.signature,
        certificate.tbs_certificate_bytes,
        padding.PKCS1v15(),
        certificate.signature_hash_algorithm,
    )
