"""Signed business-license validation for deployed Hot_Mall installations."""

import base64
import hashlib
import hmac
import json
import os
import platform
import socket
import uuid
from datetime import datetime, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


class LicenseError(Exception):
    """Raised when a license certificate cannot authorize this installation."""


def _canonical_json(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode('utf-8')


def _decode(value):
    return base64.urlsafe_b64decode(value.encode('ascii') + b'=' * (-len(value) % 4))


def _encode(value):
    return base64.urlsafe_b64encode(value).decode('ascii').rstrip('=')


def _parse_time(value, field_name):
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (AttributeError, TypeError, ValueError) as exc:
        raise LicenseError('授权证书字段 %s 无效' % field_name) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def get_server_fingerprint():
    """Return a stable, non-secret identifier used to bind a deployment."""
    machine_id = ''
    for path in ('/etc/machine-id', '/var/lib/dbus/machine-id'):
        try:
            with open(path, 'r', encoding='ascii') as machine_file:
                machine_id = machine_file.read().strip()
                if machine_id:
                    break
        except (OSError, UnicodeError):
            continue

    parts = [machine_id, platform.system(), platform.machine(), socket.gethostname(), str(uuid.getnode())]
    return hashlib.sha256('|'.join(parts).encode('utf-8')).hexdigest()


def _load_public_key(public_key):
    try:
        key = serialization.load_pem_public_key(public_key.encode('ascii'))
    except (ValueError, TypeError) as exc:
        raise LicenseError('授权公钥配置无效') from exc
    if not isinstance(key, Ed25519PublicKey):
        raise LicenseError('授权公钥必须使用 Ed25519')
    return key


def load_license(path, public_key, now=None, server_fingerprint=None):
    """Load and verify a certificate, returning its payload on success."""
    try:
        with open(path, 'r', encoding='utf-8') as license_file:
            certificate = json.load(license_file)
    except (OSError, ValueError) as exc:
        raise LicenseError('授权证书不存在或格式无效') from exc

    if not isinstance(certificate, dict) or not isinstance(certificate.get('payload'), dict):
        raise LicenseError('授权证书结构无效')
    payload = certificate['payload']
    signature = certificate.get('signature')
    if not isinstance(signature, str):
        raise LicenseError('授权证书缺少签名')

    try:
        _load_public_key(public_key).verify(_decode(signature), _canonical_json(payload))
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise LicenseError('授权证书签名校验失败') from exc

    required_fields = ('license_id', 'customer', 'server_fingerprint', 'not_before', 'expires_at')
    if any(not payload.get(field) for field in required_fields):
        raise LicenseError('授权证书缺少必要字段')
    if server_fingerprint is None:
        server_fingerprint = get_server_fingerprint()
    if not hmac_compare(payload['server_fingerprint'], server_fingerprint):
        raise LicenseError('授权证书与当前服务器不匹配')

    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    current_time = current_time.astimezone(timezone.utc)
    if current_time < _parse_time(payload['not_before'], 'not_before'):
        raise LicenseError('授权证书尚未生效')
    if current_time >= _parse_time(payload['expires_at'], 'expires_at'):
        raise LicenseError('授权证书已过期')
    return payload


def hmac_compare(left, right):
    return hmac.compare_digest(left.encode('utf-8'), right.encode('utf-8'))


def issue_license(private_key_path, output_path, customer, server_fingerprint, expires_at,
                  license_id=None, not_before=None, features=None):
    """Create a signed certificate for the licensor's private signing key."""
    try:
        with open(private_key_path, 'rb') as key_file:
            private_key = serialization.load_pem_private_key(key_file.read(), password=None)
    except (OSError, ValueError, TypeError) as exc:
        raise LicenseError('授权私钥读取失败') from exc
    if not isinstance(private_key, Ed25519PrivateKey):
        raise LicenseError('授权私钥必须使用 Ed25519')

    payload = {
        'license_id': license_id or str(uuid.uuid4()),
        'customer': customer,
        'server_fingerprint': server_fingerprint,
        'not_before': (not_before or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(),
        'expires_at': expires_at.astimezone(timezone.utc).isoformat(),
        'features': sorted(features or []),
    }
    certificate = {
        'payload': payload,
        'signature': _encode(private_key.sign(_canonical_json(payload))),
    }
    try:
        with open(output_path, 'w', encoding='utf-8') as license_file:
            json.dump(certificate, license_file, ensure_ascii=False, indent=2)
            license_file.write('\n')
        os.chmod(output_path, 0o600)
    except OSError as exc:
        raise LicenseError('授权证书写入失败') from exc
    return payload
