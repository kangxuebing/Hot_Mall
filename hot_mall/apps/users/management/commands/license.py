import os
from datetime import datetime, timezone

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from django.core.management.base import BaseCommand, CommandError

from hot_mall.license import LicenseError, get_server_fingerprint, issue_license


class Command(BaseCommand):
    help = '生成授权密钥、查看服务器指纹或签发业务授权证书'

    def add_arguments(self, parser):
        parser.add_argument('action', choices=('fingerprint', 'generate-keys', 'issue'))
        parser.add_argument('--private-key', default='license-private-key.pem')
        parser.add_argument('--public-key', default='license-public-key.pem')
        parser.add_argument('--output', default='license.json')
        parser.add_argument('--customer')
        parser.add_argument('--server-fingerprint', help='客户服务器指纹；不填写时使用当前机器指纹')
        parser.add_argument('--expires-at', help='UTC时间，格式：2027-08-22T00:00:00+00:00')
        parser.add_argument('--license-id')
        parser.add_argument('--feature', action='append', dest='features', default=[])

    def handle(self, *args, **options):
        action = options['action']
        if action == 'fingerprint':
            self.stdout.write(get_server_fingerprint())
            return
        if action == 'generate-keys':
            self._generate_keys(options['private_key'], options['public_key'])
            return
        if not options['customer'] or not options['expires_at']:
            raise CommandError('issue 需要 --customer 和 --expires-at')
        try:
            expires_at = datetime.fromisoformat(options['expires_at'].replace('Z', '+00:00'))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            payload = issue_license(
                options['private_key'], options['output'], options['customer'],
                options['server_fingerprint'] or get_server_fingerprint(), expires_at,
                options['license_id'], features=options['features'],
            )
        except (ValueError, LicenseError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(self.style.SUCCESS('授权证书已生成：%s（有效期至 %s）' % (
            options['output'], payload['expires_at'])))

    def _generate_keys(self, private_path, public_path):
        if os.path.exists(private_path) or os.path.exists(public_path):
            raise CommandError('密钥文件已存在，请更换路径或先由管理员安全处理旧密钥')
        private_key = Ed25519PrivateKey.generate()
        with open(private_path, 'wb') as key_file:
            key_file.write(private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            ))
        os.chmod(private_path, 0o600)
        with open(public_path, 'wb') as key_file:
            key_file.write(private_key.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            ))
        self.stdout.write(self.style.SUCCESS('已生成签发私钥和验证公钥，请勿将私钥部署到客户服务器'))
