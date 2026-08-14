"""
微信支付 APIv3（Native 扫码）与回调解密。
未配置商户参数时由视图层走演示支付流程。
"""
import base64
import json
import logging
import ssl
import time
import urllib.error
import urllib.request
import uuid

from django.conf import settings
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

logger = logging.getLogger('django')

WECHAT_NATIVE_PATH = '/v3/pay/transactions/native'
WECHAT_NATIVE_URL = 'https://api.mch.weixin.qq.com' + WECHAT_NATIVE_PATH


def is_wechat_pay_configured():
    mchid = getattr(settings, 'WECHAT_PAY_MCHID', '') or ''
    appid = getattr(settings, 'WECHAT_PAY_APPID', '') or ''
    key_path = getattr(settings, 'WECHAT_PAY_PRIVATE_KEY_PATH', '') or ''
    serial = getattr(settings, 'WECHAT_PAY_SERIAL_NO', '') or ''
    api_v3 = getattr(settings, 'WECHAT_PAY_API_V3_KEY', '') or ''
    return bool(mchid and appid and key_path and serial and api_v3)


def _sign_authorization(method, url_path, body, mchid, serial_no, private_key_pem):
    timestamp = str(int(time.time()))
    nonce = uuid.uuid4().hex
    message = f'{method}\n{url_path}\n{timestamp}\n{nonce}\n{body}\n'.encode('utf-8')
    key = serialization.load_pem_private_key(
        private_key_pem if isinstance(private_key_pem, bytes) else private_key_pem.encode('utf-8'),
        password=None,
    )
    signature = key.sign(message, padding.PKCS1v15(), hashes.SHA256())
    sign_b64 = base64.b64encode(signature).decode('ascii')
    return (
        f'WECHATPAY2-SHA256-RSA2048 mchid="{mchid}",nonce_str="{nonce}",'
        f'timestamp="{timestamp}",serial_no="{serial_no}",signature="{sign_b64}"'
    )


def create_native_pay_code_url(order):
    """
    调用微信 Native 下单，返回 code_url；失败返回 (None, err_msg)。
    未完整配置时返回 (None, 'not_configured')。
    """
    if not is_wechat_pay_configured():
        return None, 'not_configured'

    mchid = settings.WECHAT_PAY_MCHID
    appid = settings.WECHAT_PAY_APPID
    notify_url = getattr(settings, 'WECHAT_PAY_NOTIFY_URL', '') or ''
    if not notify_url:
        return None, 'missing_notify_url'

    total_fen = int(round(float(order.total_amount) * 100))
    if total_fen < 1:
        return None, 'invalid_amount'

    body_dict = {
        'appid': appid,
        'mchid': mchid,
        'description': f'肥猫商城订单{order.order_id}',
        'out_trade_no': order.order_id,
        'notify_url': notify_url,
        'amount': {'total': total_fen, 'currency': 'CNY'},
    }
    body = json.dumps(body_dict, separators=(',', ':'))

    key_path = settings.WECHAT_PAY_PRIVATE_KEY_PATH
    try:
        with open(key_path, 'rb') as f:
            private_pem = f.read()
    except OSError as e:
        logger.exception('读取微信商户私钥失败: %s', e)
        return None, 'private_key_read_error'

    auth = _sign_authorization(
        'POST',
        WECHAT_NATIVE_PATH,
        body,
        mchid,
        settings.WECHAT_PAY_SERIAL_NO,
        private_pem,
    )

    req = urllib.request.Request(
        WECHAT_NATIVE_URL,
        data=body.encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': auth,
            'User-Agent': 'HotMall/1.0',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=15, context=ssl.create_default_context()) as resp:
            raw = resp.read().decode('utf-8')
            data = json.loads(raw)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace')
        logger.warning('微信Native下单HTTP错误 %s: %s', e.code, err_body)
        return None, err_body
    except Exception as e:
        logger.exception('微信Native下单请求失败: %s', e)
        return None, str(e)

    code_url = data.get('code_url')
    if code_url:
        return code_url, None
    return None, json.dumps(data, ensure_ascii=False)


def decrypt_notify_resource(ciphertext_b64, nonce_b64, associated_data, api_v3_key):
    """解密微信支付 v3 通知 resource 中的 ciphertext（末尾 16 字节为认证标签）。"""
    from Cryptodome.Cipher import AES

    key = api_v3_key.encode('utf-8')
    if len(key) != 32:
        raise ValueError('WECHAT_PAY_API_V3_KEY 须为 32 字节字符串')

    nonce = base64.b64decode(nonce_b64)
    ciphertext = base64.b64decode(ciphertext_b64)
    if len(ciphertext) < 16:
        raise ValueError('密文长度无效')

    auth_tag = ciphertext[-16:]
    enc = ciphertext[:-16]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    if associated_data:
        cipher.update(associated_data.encode('utf-8'))
    plain = cipher.decrypt_and_verify(enc, auth_tag)
    return json.loads(plain.decode('utf-8'))
