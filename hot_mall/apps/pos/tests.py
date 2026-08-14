import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from pos.models import SuspendedOrder


class SuspendOrderMemberPersistenceTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.cashier = self.User.objects.create_user(
            username='cashier',
            password='123456',
            mobile='13800000001',
        )
        self.member = self.User.objects.create_user(
            username='member_user',
            password='123456',
            mobile='13800000002',
            discount_rate='0.90',
            points=100,
            total_consume='100.00',
        )

    def test_suspend_and_resume_order_keep_member_info(self):
        self.client.force_login(self.cashier)

        response = self.client.post(
            reverse('pos:suspend_order'),
            {
                'cart_data': json.dumps([{'id': 1, 'name': '商品A', 'price': '10.00', 'quantity': 1}]),
                'remark': '测试挂单',
                'member_id': self.member.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])

        suspended_order = SuspendedOrder.objects.get(id=payload['suspended_order_id'])
        self.assertEqual(suspended_order.member_id, self.member.id)

        resume_response = self.client.post(
            reverse('pos:resume_order'),
            {'suspended_order_id': suspended_order.id},
        )

        self.assertEqual(resume_response.status_code, 200)
        resume_payload = resume_response.json()
        self.assertTrue(resume_payload['success'])
        self.assertEqual(resume_payload['member']['id'], self.member.id)
        self.assertEqual(resume_payload['member']['username'], self.member.username)
