import json
import hashlib
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from goods.models import SKU
from pos.models import POSOrder, Store, StoreStock, StoreTerminal, SuspendedOrder, UserStore


@override_settings(MIDDLEWARE=[
    middleware for middleware in settings.MIDDLEWARE
    if middleware != 'hot_mall.license_middleware.LicenseMiddleware'
])
class SuspendOrderMemberPersistenceTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.cashier = self.User.objects.create_user(
            username='cashier',
            password='123456',
            mobile='13800000001',
        )
        self.store = Store.objects.create(
            store_code='SUSPEND-STORE', store_name='挂单测试门店', address='测试地址'
        )
        UserStore.objects.create(user=self.cashier, store=self.store, role=2)
        StoreTerminal.objects.create(
            store=self.store, name='挂单测试终端', terminal_code='terminal-a',
            ip_address='127.0.0.1', status=1,
        )
        self.member = self.User.objects.create_user(
            username='member_user',
            password='123456',
            mobile='13800000002',
            discount_rate='0.90',
            points=100,
            total_consume='100.00',
        )

    def select_store_for(self, user):
        session = self.client.session
        session['current_store_id'] = self.store.id
        session['current_store_name'] = self.store.store_name
        session.save()

    @patch('pos.views.get_terminal_id', return_value='terminal-a')
    def test_suspend_and_resume_order_keep_member_info(self, mocked_terminal_id):
        self.client.force_login(self.cashier)
        self.select_store_for(self.cashier)

        response = self.client.post(
            reverse('pos:suspend_order'),
            {
                'cart_data': json.dumps([{'id': 1, 'name': '商品A', 'price': '10.00', 'quantity': 1}]),
                'remark': '测试挂单',
                'member_id': self.member.id,
                'terminal_id': 'terminal-a',
            }, REMOTE_ADDR='127.0.0.1',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])

        suspended_order = SuspendedOrder.objects.get(id=payload['suspended_order_id'])
        self.assertEqual(suspended_order.member_id, self.member.id)

        resume_response = self.client.post(
            reverse('pos:resume_order'),
            {'suspended_order_id': suspended_order.id, 'terminal_id': 'terminal-a'},
            REMOTE_ADDR='127.0.0.1',
        )

        self.assertEqual(resume_response.status_code, 200)
        resume_payload = resume_response.json()
        self.assertTrue(resume_payload['success'])
        self.assertEqual(resume_payload['member']['id'], self.member.id)
        self.assertEqual(resume_payload['member']['username'], self.member.username)

    @patch('pos.views.get_terminal_id', side_effect=lambda request: request.GET.get('terminal_id') or request.POST.get('terminal_id'))
    def test_suspended_orders_are_isolated_by_cashier_and_terminal(self, mocked_terminal_id):
        other_cashier = self.User.objects.create_user(
            username='other_cashier', password='123456', mobile='13800000003'
        )
        self.client.force_login(self.cashier)
        self.select_store_for(self.cashier)
        response = self.client.post(
            reverse('pos:suspend_order'),
            {
                'cart_data': json.dumps([{'id': 1, 'price': '10.00', 'quantity': 1}]),
                'terminal_id': 'terminal-a', 'member_id': self.member.id,
            },
            REMOTE_ADDR='127.0.0.1',
        )
        suspended_order_id = response.json()['suspended_order_id']

        other_terminal_response = self.client.get(
            reverse('pos:get_suspended_orders'), {'terminal_id': 'terminal-b'}
        )
        self.assertEqual(other_terminal_response.json()['orders'], [])

        self.client.force_login(other_cashier)
        UserStore.objects.create(user=other_cashier, store=self.store, role=2)
        self.select_store_for(other_cashier)
        other_cashier_response = self.client.post(
            reverse('pos:resume_order'),
            {'suspended_order_id': suspended_order_id, 'terminal_id': 'terminal-a'},
            REMOTE_ADDR='127.0.0.1',
        )
        self.assertFalse(other_cashier_response.json()['success'])


@override_settings(MIDDLEWARE=[
    middleware for middleware in settings.MIDDLEWARE
    if middleware != 'hot_mall.license_middleware.LicenseMiddleware'
])
class StoreWorkflowTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.cashier = self.User.objects.create_user(
            username='store_cashier', password='12345678', mobile='13800000011'
        )
        self.store = Store.objects.create(
            store_code='S001', store_name='测试门店', address='测试地址'
        )
        self.client_certificate, self.client_certificate_fingerprint = self.create_test_client_certificate()

    @staticmethod
    def create_test_client_certificate():
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, 'pos-test-terminal'),
        ])
        certificate = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow() - timedelta(minutes=1))
            .not_valid_after(datetime.utcnow() + timedelta(days=1))
            .sign(private_key, hashes.SHA256())
        )
        certificate_pem = certificate.public_bytes(serialization.Encoding.PEM).decode('ascii')
        fingerprint = hashlib.sha256(
            certificate.public_bytes(serialization.Encoding.DER)
        ).hexdigest()
        return certificate_pem, fingerprint

    def test_select_store_requires_user_store_assignment(self):
        self.client.force_login(self.cashier)

        denied = self.client.post(reverse('pos:select_store'), {'store_id': self.store.id})
        self.assertFalse(denied.json()['success'])

        UserStore.objects.create(user=self.cashier, store=self.store, role=2)
        allowed = self.client.post(reverse('pos:select_store'), {'store_id': self.store.id})
        self.assertTrue(allowed.json()['success'], allowed.json())
        self.assertEqual(self.client.session['current_store_id'], self.store.id)

    def test_admin_can_change_user_store_role(self):
        admin = self.User.objects.create_superuser(
            username='role_admin', password='12345678', mobile='13800000013'
        )
        user_store = UserStore.objects.create(user=self.cashier, store=self.store, role=2)
        self.client.force_login(admin)

        response = self.client.post(
            reverse('pos:user_store_edit', args=[user_store.pk]), {'role': '3'}
        )

        self.assertRedirects(response, reverse('pos:user_store_list'))
        user_store.refresh_from_db()
        self.assertEqual(user_store.role, 3)

    def test_cashier_redirects_when_store_is_not_selected_or_assignment_was_removed(self):
        self.client.force_login(self.cashier)
        response = self.client.get(reverse('pos:cashier'))
        self.assertRedirects(response, reverse('pos:select_store'))

        UserStore.objects.create(user=self.cashier, store=self.store, role=2)
        session = self.client.session
        session['current_store_id'] = self.store.id
        session['current_store_name'] = self.store.store_name
        session.save()
        UserStore.objects.filter(user=self.cashier, store=self.store).delete()

        response = self.client.get(reverse('pos:cashier'))
        self.assertRedirects(response, reverse('pos:select_store'))
        self.assertNotIn('current_store_id', self.client.session)

    def test_cashier_lists_only_enabled_terminals_from_current_store(self):
        UserStore.objects.create(user=self.cashier, store=self.store, role=2)
        StoreTerminal.objects.create(
            store=self.store, name='前台收银机', terminal_code='S001-POS01',
            ip_address='127.0.0.1', status=1,
        )
        StoreTerminal.objects.create(
            store=self.store, name='备用收银机', terminal_code='S001-POS02',
            ip_address='127.0.0.2', status=0,
        )
        self.client.force_login(self.cashier)
        session = self.client.session
        session['current_store_id'] = self.store.id
        session['current_store_name'] = self.store.store_name
        session.save()

        response = self.client.get(reverse('pos:cashier'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual([terminal['terminal_code'] for terminal in response.context['pos_terminals']], ['S001-POS01'])
        self.assertContains(response, 'S001-POS01')
        self.assertNotContains(response, 'S001-POS02')

    def test_cashier_has_no_terminal_fallback_when_store_is_unconfigured(self):
        UserStore.objects.create(user=self.cashier, store=self.store, role=2)
        self.client.force_login(self.cashier)
        session = self.client.session
        session['current_store_id'] = self.store.id
        session.save()

        response = self.client.get(reverse('pos:cashier'))

        self.assertEqual(response.context['pos_terminals'], [])
        self.assertContains(response, '未配置可用收银终端')

    def test_admin_can_add_terminal_for_store(self):
        admin = self.User.objects.create_superuser(
            username='terminal_admin', password='12345678', mobile='13800000014'
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse('pos:store_terminal_add', args=[self.store.pk]),
            {
                'name': '前台收银机', 'terminal_code': 'S001-POS01',
                'ip_address': '192.168.1.101', 'status': '1',
                'certificate_fingerprint': self.client_certificate_fingerprint,
            },
        )

        self.assertRedirects(response, reverse('pos:store_terminal_list', args=[self.store.pk]))
        terminal = StoreTerminal.objects.get(terminal_code='S001-POS01')
        self.assertEqual(terminal.store, self.store)
        self.assertEqual(terminal.status, 1)
        self.assertEqual(terminal.ip_address, '192.168.1.101')
        self.assertEqual(terminal.certificate_fingerprint, self.client_certificate_fingerprint)

    def test_admin_cannot_save_terminal_with_invalid_ip(self):
        admin = self.User.objects.create_superuser(
            username='invalid_ip_admin', password='12345678', mobile='13800000015'
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse('pos:store_terminal_add', args=[self.store.pk]),
            {
                'name': '无效终端', 'terminal_code': 'S001-BAD',
                'ip_address': 'not-an-ip', 'status': '1',
                'certificate_fingerprint': self.client_certificate_fingerprint,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '请输入有效的IPv4或IPv6地址')
        self.assertFalse(StoreTerminal.objects.filter(terminal_code='S001-BAD').exists())

    def test_enabled_terminal_requires_a_valid_certificate_fingerprint(self):
        admin = self.User.objects.create_superuser(
            username='missing_cert_admin', password='12345678', mobile='13800000016'
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse('pos:store_terminal_add', args=[self.store.pk]),
            {
                'name': '未绑定设备', 'terminal_code': 'S001-NOCERT',
                'ip_address': '192.168.1.102', 'status': '1',
            },
        )

        self.assertContains(response, '启用终端必须填写有效的SHA-256客户端证书指纹')
        self.assertFalse(StoreTerminal.objects.filter(terminal_code='S001-NOCERT').exists())

    def test_client_certificate_fingerprint_cannot_be_reused(self):
        admin = self.User.objects.create_superuser(
            username='duplicate_cert_admin', password='12345678', mobile='13800000017'
        )
        StoreTerminal.objects.create(
            store=self.store, name='已有设备', terminal_code='S001-EXISTING',
            ip_address='192.168.1.10',
            certificate_fingerprint=self.client_certificate_fingerprint,
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse('pos:store_terminal_add', args=[self.store.pk]),
            {
                'name': '重复证书设备', 'terminal_code': 'S001-DUPLICATE',
                'ip_address': '192.168.1.11',
                'certificate_fingerprint': self.client_certificate_fingerprint,
                'status': '1',
            },
        )

        self.assertContains(response, '客户端证书指纹已绑定其他终端')
        self.assertFalse(StoreTerminal.objects.filter(terminal_code='S001-DUPLICATE').exists())

    def test_store_terminal_is_selected_and_enforced_for_cashier_requests(self):
        UserStore.objects.create(user=self.cashier, store=self.store, role=2)
        StoreTerminal.objects.create(
            store=self.store, name='前台收银机', terminal_code='S001-POS01',
            ip_address='127.0.0.1', certificate_fingerprint=self.client_certificate_fingerprint,
            status=1,
        )
        self.client.force_login(self.cashier)
        session = self.client.session
        session['current_store_id'] = self.store.id
        session['current_store_name'] = self.store.store_name
        session.save()

        cashier_page = self.client.get(reverse('pos:cashier'))
        self.assertContains(cashier_page, 'S001-POS01')

        proxy_headers = {
            'REMOTE_ADDR': '127.0.0.2',
            'HTTP_X_VERIFIED_CLIENT_IP': '127.0.0.1',
            'HTTP_X_CLIENT_CERT_VERIFY': 'SUCCESS',
            'HTTP_X_VERIFIED_CLIENT_CERT': self.client_certificate.replace('\n', '%0A'),
        }
        with override_settings(POS_TRUSTED_TLS_PROXY_IPS='127.0.0.2'):
            allowed = self.client.post(reverse('pos:suspend_order'), {
            'cart_data': '[{"id": 1, "price": "5.00", "quantity": 1}]',
            'terminal_id': 'S001-POS01',
            'member_id': self.cashier.id,
            }, **proxy_headers)
        self.assertTrue(allowed.json()['success'], allowed.json())

        with override_settings(POS_TRUSTED_TLS_PROXY_IPS='127.0.0.2'):
            rejected = self.client.post(reverse('pos:suspend_order'), {
            'cart_data': '[{"id": 1, "price": "5.00", "quantity": 1}]',
            'terminal_id': 'S001-POS01',
            'member_id': self.cashier.id,
            }, **dict(proxy_headers, HTTP_X_VERIFIED_CLIENT_IP='127.0.0.9'))
        self.assertFalse(rejected.json()['success'])
        self.assertIn('终端', rejected.json()['message'])

        with override_settings(POS_TRUSTED_TLS_PROXY_IPS='127.0.0.2'):
            wrong_terminal = self.client.post(reverse('pos:suspend_order'), {
            'cart_data': '[{"id": 1, "price": "5.00", "quantity": 1}]',
            'terminal_id': 'OTHER-POS01',
            'member_id': self.cashier.id,
            }, **proxy_headers)
        self.assertFalse(wrong_terminal.json()['success'])

        with override_settings(POS_TRUSTED_TLS_PROXY_IPS='127.0.0.2'):
            unverified_certificate = self.client.post(reverse('pos:suspend_order'), {
                'cart_data': '[{"id": 1, "price": "5.00", "quantity": 1}]',
                'terminal_id': 'S001-POS01',
                'member_id': self.cashier.id,
            }, **dict(proxy_headers, HTTP_X_CLIENT_CERT_VERIFY='FAILED'))
            forged_fingerprint = self.client.post(reverse('pos:suspend_order'), {
                'cart_data': '[{"id": 1, "price": "5.00", "quantity": 1}]',
                'terminal_id': 'S001-POS01',
                'member_id': self.cashier.id,
            }, **dict(proxy_headers, HTTP_X_VERIFIED_CLIENT_CERT='not-a-certificate'))
        self.assertFalse(unverified_certificate.json()['success'])
        self.assertFalse(forged_fingerprint.json()['success'])

        StoreTerminal.objects.filter(store=self.store).update(status=0)
        with override_settings(POS_TRUSTED_TLS_PROXY_IPS='127.0.0.2'):
            disabled = self.client.post(reverse('pos:suspend_order'), {
            'cart_data': '[{"id": 1, "price": "5.00", "quantity": 1}]',
            'terminal_id': 'S001-POS01',
            'member_id': self.cashier.id,
            }, **proxy_headers)
        self.assertFalse(disabled.json()['success'])
        self.assertIn('终端', disabled.json()['message'])

        with override_settings(POS_TRUSTED_TLS_PROXY_IPS=''):
            untrusted_proxy = self.client.post(reverse('pos:suspend_order'), {
                'cart_data': '[{"id": 1, "price": "5.00", "quantity": 1}]',
                'terminal_id': 'S001-POS01',
                'member_id': self.cashier.id,
            }, **proxy_headers)
        self.assertFalse(untrusted_proxy.json()['success'])

    def test_receipt_shows_order_store_separately_from_terminal_code(self):
        store = Store.objects.create(
            store_code='STORE002', store_name='二号门店', address='测试地址'
        )
        order = POSOrder.objects.create(
            order_id='POS-STORE-RECEIPT-1', store=store, cashier=self.cashier,
            terminal_id='STORE001-POS01', member=self.cashier, total_amount='12.00',
        )
        self.client.force_login(self.cashier)

        preview = self.client.get(reverse('pos:receipt_preview', args=[order.order_id]))
        self.assertEqual(preview.status_code, 200)
        self.assertContains(preview, 'STORE002 - 二号门店')
        self.assertContains(preview, 'STORE001-POS01')

        printed = self.client.post(reverse('pos:print_receipt'), {'order_id': order.order_id})
        self.assertEqual(printed.status_code, 200)
        self.assertIn('门店: STORE002 - 二号门店', printed.json()['receipt_content'])
        self.assertIn('终端编号: STORE001-POS01', printed.json()['receipt_content'])

    def test_inventory_initialization_copies_once_without_overwriting_existing_stock(self):
        admin = self.User.objects.create_superuser(
            username='store_admin', password='12345678', mobile='13800000012'
        )
        sku = SimpleNamespace(stock=8, near_expiry_num=1, expired_num=0)
        self.client.force_login(admin)

        with patch.object(SKU.objects, 'all', return_value=[sku]), patch(
            'pos.views.StoreStock.objects.get_or_create',
            side_effect=[(object(), True), (object(), False)],
        ) as get_or_create:
            response = self.client.post(reverse('pos:init_store_stock'), {'store_id': self.store.id})
            self.assertRedirects(response, reverse('pos:init_store_stock'))
            response = self.client.post(reverse('pos:init_store_stock'), {'store_id': self.store.id})
            self.assertRedirects(response, reverse('pos:init_store_stock'))

        self.assertEqual(get_or_create.call_count, 2)
        self.assertEqual(get_or_create.call_args_list[1][1]['defaults']['stock'], 8)
