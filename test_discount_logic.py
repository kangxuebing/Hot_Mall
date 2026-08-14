#!/usr/bin/env python
"""
测试新的折扣逻辑
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hot_mall.settings.dev')
django.setup()

from decimal import Decimal
from users.models import User
from goods.models import SKU
from pos.models import POSOrder, POSOrderItem, PromotionProduct
from pos.views import CreateOrderView
from django.test import RequestFactory
import json

def test_discount_logic():
    print("=== 测试新的折扣逻辑 ===")
    
    # 1. 获取测试会员
    member = User.objects.get(username='testmember')
    print(f"会员: {member.username}, 折扣率: {member.discount_rate}")
    
    # 2. 获取促销商品和非促销商品
    promotion = PromotionProduct.objects.filter(is_active=True).first()
    if not promotion:
        print("错误: 没有找到有效的促销商品")
        return
    
    promotion_sku = promotion.sku
    print(f"促销商品: {promotion_sku.name}")
    print(f"商品原价: ¥{promotion_sku.price}")
    print(f"促销折扣率: {promotion.discount_rate}")
    
    # 获取一个非促销商品
    non_promotion_sku = SKU.objects.filter(is_launched=True).exclude(id=promotion_sku.id).first()
    if non_promotion_sku:
        print(f"非促销商品: {non_promotion_sku.name}")
        print(f"商品原价: ¥{non_promotion_sku.price}")
    
    # 3. 测试会员购买促销商品
    print("\n=== 测试1: 会员购买促销商品 ===")
    order_data = {
        'items': json.dumps([{
            'sku_id': promotion_sku.id,
            'quantity': 1
        }]),
        'payment_method': 1,
        'paid_amount': str(promotion_sku.price * promotion.discount_rate),
        'remark': '测试会员购买促销商品',
        'member_id': str(member.id)
    }
    
    factory = RequestFactory()
    admin = User.objects.filter(is_superuser=True).first()
    request = factory.post('/pos/create-order/', order_data)
    request.user = admin
    
    view = CreateOrderView.as_view()
    response = view(request)
    
    if response.status_code == 200:
        data = json.loads(response.content)
        if data.get('success'):
            print(f"✅ 订单创建成功!")
            print(f"订单号: {data['order_id']}")
            print(f"实付金额: ¥{data['total_amount']}")
            print(f"优惠金额: ¥{data.get('discount_amount', 0)}")
            
            order = POSOrder.objects.get(order_id=data['order_id'])
            print(f"\n订单验证:")
            print(f"  会员: {order.member.username if order.member else '无'}")
            print(f"  原始总金额: ¥{order.original_amount}")
            print(f"  折扣后金额: ¥{order.total_amount}")
            print(f"  优惠金额: ¥{order.discount_amount}")
            print(f"  折扣类型: {order.discount_type}")
            
            order_item = order.items.first()
            print(f"\n商品验证:")
            print(f"  商品名: {order_item.sku.name}")
            print(f"  原价: ¥{order_item.original_price}")
            print(f"  实付单价: ¥{order_item.price}")
            print(f"  折扣率: {order_item.discount_rate}")
            print(f"  折扣类型: {order_item.discount_type}")
            
            # 验证逻辑：促销折扣率0.75 < 会员折扣率0.90，应该使用促销折扣
            if promotion.discount_rate < member.discount_rate:
                expected_discount_type = 'promotion'
            else:
                expected_discount_type = 'member'
            
            if order.discount_type == expected_discount_type:
                print(f"  ✅ 折扣类型正确: {order.discount_type}")
            else:
                print(f"  ❌ 折扣类型错误 (预期: {expected_discount_type}, 实际: {order.discount_type})")
        else:
            print(f"❌ 订单创建失败: {data.get('message')}")
    else:
        print(f"❌ 请求失败: {response.content}")
    
    # 4. 测试会员购买非促销商品
    if non_promotion_sku:
        print("\n=== 测试2: 会员购买非促销商品 ===")
        order_data = {
            'items': json.dumps([{
                'sku_id': non_promotion_sku.id,
                'quantity': 1
            }]),
            'payment_method': 1,
            'paid_amount': str(non_promotion_sku.price),
            'remark': '测试会员购买非促销商品',
            'member_id': str(member.id)
        }
        
        request = factory.post('/pos/create-order/', order_data)
        request.user = admin
        response = view(request)
        
        if response.status_code == 200:
            data = json.loads(response.content)
            if data.get('success'):
                print(f"✅ 订单创建成功!")
                print(f"订单号: {data['order_id']}")
                print(f"实付金额: ¥{data['total_amount']}")
                print(f"优惠金额: ¥{data.get('discount_amount', 0)}")
                
                order = POSOrder.objects.get(order_id=data['order_id'])
                print(f"\n订单验证:")
                print(f"  会员: {order.member.username if order.member else '无'}")
                print(f"  原始总金额: ¥{order.original_amount}")
                print(f"  折扣后金额: ¥{order.total_amount}")
                print(f"  优惠金额: ¥{order.discount_amount}")
                print(f"  折扣类型: {order.discount_type}")
                
                order_item = order.items.first()
                print(f"\n商品验证:")
                print(f"  商品名: {order_item.sku.name}")
                print(f"  原价: ¥{order_item.original_price}")
                print(f"  实付单价: ¥{order_item.price}")
                print(f"  折扣率: {order_item.discount_rate}")
                print(f"  折扣类型: {order_item.discount_type}")
                
                # 非促销商品应该无折扣
                if order.discount_type == 'none' and order_item.discount_rate == Decimal('1.00'):
                    print(f"  ✅ 非促销商品正确无折扣")
                else:
                    print(f"  ❌ 非促销商品应该无折扣")
            else:
                print(f"❌ 订单创建失败: {data.get('message')}")
        else:
            print(f"❌ 请求失败: {response.content}")

if __name__ == '__main__':
    test_discount_logic()