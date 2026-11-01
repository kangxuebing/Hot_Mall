from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, models
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.contrib import messages
import hashlib
import ipaddress
import re
import uuid
import json
import logging
from urllib.parse import unquote
from decimal import Decimal
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from django.conf import settings
from goods.models import SKU
from .models import POSOrder, POSOrderItem, BarcodeScanner, SuspendedOrder, PromotionProduct, Store, StoreStock, StoreTerminal, UserStore
from users.models import User
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)


def get_terminal_id(request):
    """Validate store terminal code, client IP and mTLS certificate fingerprint."""
    try:
        requested_terminal = (
            request.META.get('HTTP_X_POS_TERMINAL_CODE') or
            request.POST.get('terminal_id') or
            request.GET.get('terminal_id') or ''
        ).strip()

        store_id = get_current_store_id(request)
        if not store_id:
            logger.warning(f"get_terminal_id: No store_id in session")
            return None

        # 开发环境：如果没有提供终端编号，使用默认终端或创建一个
        if settings.DEBUG and not requested_terminal:
            logger.info(f"get_terminal_id: DEBUG mode, no terminal_code provided, using default")
            # 尝试获取门店的第一个终端
            terminal = StoreTerminal.objects.filter(store_id=store_id, status=1).first()
            if terminal:
                logger.info(f"get_terminal_id: Using existing terminal {terminal.terminal_code}")
                return str(terminal.terminal_code)
            # 如果没有终端，创建一个默认终端
            try:
                store = Store.objects.get(id=store_id)
                terminal = StoreTerminal.objects.create(
                    store=store,
                    terminal_code='DEFAULT_TERMINAL',
                    name='默认收银终端',
                    status=1
                )
                logger.info(f"get_terminal_id: Created default terminal")
                return str(terminal.terminal_code)
            except Exception as e:
                logger.error(f"get_terminal_id: Failed to create default terminal: {e}")
                return None

        if not requested_terminal:
            logger.warning(f"get_terminal_id: No terminal_code provided")
            return None

        terminal = StoreTerminal.objects.filter(
            store_id=store_id,
            terminal_code=requested_terminal,
            status=1,
        ).first()
        if not terminal:
            logger.warning(f"get_terminal_id: Terminal not found - store_id={store_id}, terminal_code={requested_terminal}")
            # 开发环境：自动创建终端
            if settings.DEBUG:
                logger.info(f"get_terminal_id: DEBUG mode, auto-creating terminal {requested_terminal}")
                try:
                    store = Store.objects.get(id=store_id)
                    terminal = StoreTerminal.objects.create(
                        store=store,
                        terminal_code=requested_terminal,
                        name=f'自动创建终端-{requested_terminal}',
                        status=1
                    )
                    logger.info(f"get_terminal_id: Auto-created terminal {requested_terminal}")
                except Exception as e:
                    logger.error(f"get_terminal_id: Failed to auto-create terminal: {e}")
                    return None
            else:
                return None

        # 开发环境跳过严格的 mTLS 验证
        if settings.DEBUG:
            logger.info(f"get_terminal_id: DEBUG mode, skipping mTLS validation for terminal {requested_terminal}")
            return str(terminal.terminal_code)

        # 生产环境进行完整的 mTLS 验证
        if not terminal.ip_address or not terminal.certificate_fingerprint:
            logger.warning(f"get_terminal_id: Terminal missing ip_address or certificate_fingerprint")
            return None

        try:
            client_ip = ipaddress.ip_address(get_verified_client_ip(request))
            terminal_ip = ipaddress.ip_address(terminal.ip_address)
            certificate_fingerprint = get_verified_client_certificate_fingerprint(request)
        except ValueError:
            return None
        except (TypeError, UnicodeError, x509.ExtensionNotFound):
            return None
        if client_ip != terminal_ip or certificate_fingerprint != terminal.certificate_fingerprint:
            return None
        return str(terminal.terminal_code)
    except Exception as e:
        logger.error(f"get_terminal_id: Unexpected error: {type(e).__name__}: {str(e)}", exc_info=True)
        return None


def get_trusted_proxy_networks():
    """Parse proxy addresses/CIDRs allowed to assert verified mTLS metadata."""
    configured = getattr(settings, 'POS_TRUSTED_TLS_PROXY_IPS', '')
    networks = []
    try:
        for value in configured.split(','):
            value = value.strip()
            if value:
                networks.append(ipaddress.ip_network(value, strict=False))
    except ValueError:
        return []
    return networks


def is_trusted_tls_proxy(request):
    try:
        peer_ip = ipaddress.ip_address((request.META.get('REMOTE_ADDR') or '').strip())
    except ValueError:
        return False
    return any(peer_ip in network for network in get_trusted_proxy_networks())


def get_verified_client_ip(request):
    if not is_trusted_tls_proxy(request):
        raise ValueError('请求不是来自可信TLS代理')
    client_ip = (request.META.get('HTTP_X_VERIFIED_CLIENT_IP') or '').strip()
    return str(ipaddress.ip_address(client_ip))


def get_verified_client_certificate_fingerprint(request):
    if not is_trusted_tls_proxy(request):
        raise ValueError('请求不是来自可信TLS代理')
    if request.META.get('HTTP_X_CLIENT_CERT_VERIFY') != 'SUCCESS':
        raise ValueError('客户端证书未通过代理验证')

    escaped_certificate = request.META.get('HTTP_X_VERIFIED_CLIENT_CERT', '')
    certificate_pem = unquote(escaped_certificate).replace('\\n', '\n').strip()
    if not certificate_pem:
        raise ValueError('缺少客户端证书')

    certificate = x509.load_pem_x509_certificate(certificate_pem.encode('ascii'))
    certificate_der = certificate.public_bytes(serialization.Encoding.DER)
    return hashlib.sha256(certificate_der).hexdigest()


def get_current_store_id(request):
    """返回用户当前可访问的启用门店，失效的选择会从会话中清除。"""
    store_id = request.session.get('current_store_id')
    if not store_id:
        return None

    stores = Store.objects.filter(id=store_id, status=1)
    if not request.user.is_superuser:
        stores = stores.filter(userstore__user=request.user)

    store = stores.first()
    if not store:
        request.session.pop('current_store_id', None)
        request.session.pop('current_store_name', None)
        return None
    return store.id


def check_product_expiration(sku):
    """
    检查商品保质期状态
    现在只用于信息显示，不阻止销售
    返回: (is_valid, message)
    is_valid: 始终返回True（不阻止销售）
    message: 保质期状态信息
    """
    if not sku.expiration_date:
        # 没有过期日期
        return True, None
    
    today = date.today()
    days_until_expiry = (sku.expiration_date - today).days
    
    if days_until_expiry < 0:
        # 已过期（但允许销售）
        return True, f"商品已过期（过期日期：{sku.expiration_date}）"
    elif days_until_expiry <= 3:
        # 临保质期（但允许销售）
        return True, f"商品临保质期（剩余{days_until_expiry}天，过期日期：{sku.expiration_date}）"
    
    # 正常
    return True, None


class BasePosView(LoginRequiredMixin, View):
    """POS系统基础视图，统一注入登录验证与公共上下文"""
    left_menu_active = ""  # 子类重写以指定当前激活菜单

    def get_context_data(self, **kwargs):
        """统一添加侧边栏激活标识和管理员权限状态"""
        context = {}
        context.update(kwargs)
        context['left_menu_active'] = self.left_menu_active
        context['is_superuser'] = self.request.user.is_superuser
        return context


class CashierInterfaceView(BasePosView):
    """收银台界面"""
    left_menu_active = "cashier"

    def get(self, request):
        store_id = get_current_store_id(request)
        if not store_id:
            return redirect(reverse_lazy('pos:select_store'))
        context = self.get_context_data()
        context['is_superuser'] = request.user.is_superuser
        terminals = list(
            StoreTerminal.objects.filter(store_id=store_id, status=1).values(
                'terminal_code', 'name', 'ip_address'
            )
        )
        context['pos_terminals'] = terminals
        context['current_store_name'] = request.session.get('current_store_name', '')
        context['current_store_name'] = request.session.get('current_store_name', '')
        return render(request, 'pos/cashier.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class ScanBarcodeView(LoginRequiredMixin, View):
    """扫描条码"""

    @method_decorator(require_http_methods(["POST"]))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        barcode = request.POST.get('barcode', '').strip()
        if not barcode:
            return JsonResponse({'success': False, 'message': '条码不能为空'})

        try:
            sku = SKU.objects.get(barcode=barcode, is_launched=True)

            # 获取当前门店ID
            store_id = get_current_store_id(request)
            if not store_id:
                return JsonResponse({'success': False, 'message': '请先选择门店'})

            # 查询门店库存
            store_stock = StoreStock.objects.filter(store_id=store_id, sku=sku).first()
            if not store_stock:
                # 未初始化的SKU在该门店库存为0，不从全局库存隐式分配。
                store_stock = StoreStock.objects.create(
                    store_id=store_id,
                    sku=sku,
                    stock=0,
                    near_expiry_num=0,
                    expired_num=0
                )

            # 检查商品保质期状态（仅用于信息显示，不阻止销售）
            is_valid, expiration_message = check_product_expiration(sku)

            return JsonResponse({
                'success': True,
                'sku': {
                    'id': sku.id,
                    'name': sku.name,
                    'caption': sku.caption,
                    'price': str(sku.price),
                    'stock': store_stock.stock,  # 使用门店库存
                    'barcode': sku.barcode,
                    'default_image': sku.default_image.url if sku.default_image else '',
                    'expiration_date': str(sku.expiration_date) if sku.expiration_date else None,
                    'near_expiry_num': store_stock.near_expiry_num,  # 使用门店临保质期数量
                    'expired_num': store_stock.expired_num,  # 使用门店过期数量
                    'expiration_message': expiration_message  # 添加保质期状态信息
                }
            })
        except SKU.DoesNotExist:
            return JsonResponse({'success': False, 'message': '未找到该条码对应的商品'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'查询商品失败: {str(e)}'})


@method_decorator(csrf_exempt, name='dispatch')
class QueryMemberView(LoginRequiredMixin, View):
    """查询会员信息"""

    @method_decorator(require_http_methods(["POST"]))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        identifier = request.POST.get('identifier', '').strip()
        if not identifier:
            return JsonResponse({'success': False, 'message': '会员标识不能为空'})

        try:
            # 支持通过手机号或用户名查询会员
            member = User.objects.filter(
                models.Q(mobile=identifier) | models.Q(username=identifier)
            ).first()

            if not member:
                return JsonResponse({'success': False, 'message': '未找到该会员'})

            return JsonResponse({
                'success': True,
                'member': {
                    'id': member.id,
                    'username': member.username,
                    'mobile': member.mobile,
                    'member_level': member.member_level,
                    'member_level_display': member.get_member_level_display(),
                    'points': member.points,
                    'discount_rate': str(member.discount_rate),
                    'total_consume': str(member.total_consume),
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'查询会员失败: {str(e)}'})


@method_decorator(csrf_exempt, name='dispatch')
class CreateOrderView(LoginRequiredMixin, View):
    """创建订单"""

    @method_decorator(require_http_methods(["POST"]))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        items_json = request.POST.get('items', '[]')
        terminal_id = get_terminal_id(request)
        client_request_id = request.POST.get('client_request_id', '').strip()
        payment_method = request.POST.get('payment_method', 1)
        paid_amount = request.POST.get('paid_amount', 0)
        remark = request.POST.get('remark', '')
        member_id = request.POST.get('member_id', '')

        try:
            items = json.loads(items_json)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': '购物车数据格式错误'})

        if not items:
            return JsonResponse({'success': False, 'message': '购物车为空'})
        if not terminal_id or not client_request_id:
            return JsonResponse({'success': False, 'message': '收银终端未配置或终端标识不匹配'})

        try:
            with transaction.atomic():
                existing_order = POSOrder.objects.filter(client_request_id=client_request_id).first()
                if existing_order:
                    if (existing_order.cashier_id != request.user.id or
                            existing_order.terminal_id != terminal_id):
                        return JsonResponse({'success': False, 'message': '请求标识已被其他收银终端使用'})
                    return JsonResponse({
                        'success': True, 'order_id': existing_order.order_id,
                        'total_amount': str(existing_order.total_amount),
                        'discount_amount': str(existing_order.discount_amount),
                        'paid_amount': str(existing_order.paid_amount),
                        'change_amount': str(existing_order.change_amount),
                        'member': None, 'idempotent': True,
                    })
                # 生成订单号
                order_id = f"POS{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

                cashier = request.user

                # 获取当前门店ID
                store_id = get_current_store_id(request)
                if not store_id:
                    return JsonResponse({'success': False, 'message': '请先选择门店'})

                # 获取门店信息
                try:
                    store = Store.objects.get(id=store_id)
                except Store.DoesNotExist:
                    return JsonResponse({'success': False, 'message': '门店不存在'})

                # 获取会员信息
                member = None
                member_discount_rate = Decimal('1.00')
                if member_id:
                    try:
                        member = User.objects.select_for_update().get(id=member_id)
                        member_discount_rate = member.discount_rate
                    except User.DoesNotExist:
                        return JsonResponse({'success': False, 'message': '会员不存在'})

                # 计算总金额和折扣
                total_amount = Decimal('0')
                order_items = []

                # 检查每个商品的促销信息
                for item_data in items:
                    sku_id = item_data.get('sku_id')
                    quantity = item_data.get('quantity', 1)

                    sku = SKU.objects.select_for_update().get(id=sku_id)
                    original_price = sku.price

                    # 查询门店库存
                    store_stock = StoreStock.objects.select_for_update().filter(store_id=store_id, sku=sku).first()
                    if not store_stock:
                        # 未初始化的SKU在该门店库存为0，不从全局库存隐式分配。
                        store_stock = StoreStock.objects.create(
                            store_id=store_id,
                            sku=sku,
                            stock=0,
                            near_expiry_num=0,
                            expired_num=0
                        )

                    # 检查库存是否充足（考虑过期和临保质期商品）
                    available_stock = store_stock.stock - store_stock.expired_num - store_stock.near_expiry_num
                    if quantity > available_stock:
                        return JsonResponse({
                            'success': False,
                            'message': f'商品 {sku.name} 库存不足。需要：{quantity}，可用库存：{available_stock}（总库存：{store_stock.stock}，过期商品：{store_stock.expired_num}，临保质期商品：{store_stock.near_expiry_num}）'
                        })

                    # 检查商品促销（优先查询门店级促销，再查询全局促销）
                    promotion = PromotionProduct.objects.filter(
                        sku=sku,
                        store_id=store_id,
                        is_active=True
                    ).first()
                    if not promotion:
                        # 如果没有门店级促销，查询全局促销
                        promotion = PromotionProduct.objects.filter(
                            sku=sku,
                            store__isnull=True,
                            is_active=True
                        ).first()
                    
                    # 确定最终价格和折扣类型
                    if not member:
                        # 非会员：所有商品都按原价，不享受任何折扣
                        final_price = original_price
                        used_discount_type = 'none'
                    else:
                        # 会员：只有促销商品可以使用折扣，非促销商品按原价
                        if promotion and promotion.is_valid():
                            # 促销商品：比较促销价和会员折扣价，取较小值
                            if promotion.discount_type == 1:  # 固定折扣率
                                promotion_price = original_price * promotion.discount_rate
                            else:  # 固定金额优惠
                                promotion_price = max(Decimal('0.01'), original_price - promotion.discount_amount)
                            
                            member_price = original_price * member_discount_rate
                            
                            # 取较小值
                            if promotion_price < member_price:
                                final_price = promotion_price
                                used_discount_type = 'promotion'
                            else:
                                final_price = member_price
                                used_discount_type = 'member'
                        else:
                            # 非促销商品：按原价，不使用会员折扣
                            final_price = original_price
                            used_discount_type = 'none'
                    
                    final_subtotal = final_price * quantity
                    total_amount += final_subtotal
                    
                    order_items.append({
                        'sku': sku,
                        'quantity': quantity,
                        'original_price': original_price,
                        'price': final_price,
                        'subtotal': final_subtotal,
                        'used_discount_type': used_discount_type,
                        'promotion': promotion
                    })

                # 计算原始总金额（不含折扣）
                original_amount = sum(item['original_price'] * item['quantity'] for item in order_items)
                discount_amount = original_amount - total_amount
                
                # 确定订单使用的折扣类型（基于商品中的折扣类型）
                has_promotion_discount = any(item['used_discount_type'] == 'promotion' for item in order_items)
                has_member_discount = any(item['used_discount_type'] == 'member' for item in order_items)
                
                if has_promotion_discount:
                    order_discount_type = 'promotion'
                elif has_member_discount:
                    order_discount_type = 'member'
                else:
                    order_discount_type = 'none'

                # 创建订单
                total_count = sum(item['quantity'] for item in order_items)
                order = POSOrder.objects.create(
                    order_id=order_id,
                    store=store,  # 添加门店字段
                    cashier=cashier,
                    terminal_id=terminal_id,
                    client_request_id=client_request_id,
                    member=member,
                    total_count=total_count,
                    total_amount=total_amount,
                    original_amount=original_amount,
                    discount_amount=discount_amount,
                    discount_type=order_discount_type,
                    paid_amount=Decimal(str(paid_amount)),
                    change_amount=Decimal(str(paid_amount)) - total_amount,
                    payment_method=int(payment_method),
                    status=2,  # 已支付
                    remark=remark
                )

                # 更新会员积分和累计消费
                if member:
                    # 增加积分（按消费金额的1%计算）
                    points_to_add = int(total_amount)
                    member.points += points_to_add
                    member.total_consume += total_amount
                    member.save()

                # 创建订单商品并扣减库存
                for item in order_items:
                    sku = item['sku']
                    quantity = item['quantity']

                    # 扣减门店库存（使用乐观锁防止超卖）
                    while True:
                        store_stock_obj = StoreStock.objects.select_for_update().get(store_id=store_id, sku=sku)
                        origin_stock = store_stock_obj.stock
                        origin_near_expiry = store_stock_obj.near_expiry_num
                        origin_expired = store_stock_obj.expired_num
                        new_stock = origin_stock - quantity

                        if new_stock < 0:
                            raise Exception(f'商品 {sku.name} 库存不足')

                        # 根据商品保质期状态更新临保质期或过期商品数量
                        today = date.today()
                        days_until_expiry = None
                        if sku.expiration_date:
                            days_until_expiry = (sku.expiration_date - today).days
                        elif sku.production_date and sku.shelf_life:
                            expiry_date = sku.production_date + timedelta(days=sku.shelf_life)
                            days_until_expiry = (expiry_date - today).days

                        new_near_expiry = origin_near_expiry
                        new_expired = origin_expired

                        if days_until_expiry is not None:
                            if days_until_expiry < 0:
                                # 已过期商品，增加过期数量
                                new_expired = origin_expired + quantity
                            elif days_until_expiry <= 3:
                                # 临保质期商品，增加临保质期数量
                                new_near_expiry = origin_near_expiry + quantity

                        # 乐观锁更新门店库存和临保质期/过期数量
                        ret = StoreStock.objects.filter(
                            id=store_stock_obj.id,
                            stock=origin_stock,
                            near_expiry_num=origin_near_expiry,
                            expired_num=origin_expired
                        ).update(
                            stock=new_stock,
                            near_expiry_num=new_near_expiry,
                            expired_num=new_expired
                        )

                        if ret > 0:
                            break  # 更新成功

                    # 同时更新SKU表的销量（用于全局统计）
                    SKU.objects.filter(id=sku.id).update(sales=models.F('sales') + quantity)

                    # 计算商品折扣率
                    original_price = item['sku'].price
                    if original_price > 0:
                        item_discount_rate = item['price'] / original_price
                    else:
                        item_discount_rate = Decimal('1.00')
                    
                    POSOrderItem.objects.create(
                        order=order,
                        sku=sku,
                        quantity=quantity,
                        original_price=original_price,
                        price=item['price'],
                        subtotal=item['subtotal'],
                        discount_rate=item_discount_rate,
                        discount_type=item['used_discount_type']
                    )

                return JsonResponse({
                    'success': True,
                    'order_id': order_id,
                    'total_amount': str(total_amount),
                    'discount_amount': str(discount_amount),
                    'paid_amount': str(Decimal(str(paid_amount))),
                    'change_amount': str(order.change_amount),
                    'member': {
                        'id': member.id,
                        'username': member.username,
                        'points': member.points
                    } if member else None
                })

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'创建订单失败: {str(e)}'})


@method_decorator(csrf_exempt, name='dispatch')
class CheckStockView(LoginRequiredMixin, View):
    """检查库存"""

    @method_decorator(require_http_methods(["POST"]))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        sku_id = request.POST.get('sku_id')
        quantity = request.POST.get('quantity', 1)

        try:
            # 获取当前门店ID
            store_id = get_current_store_id(request)
            if not store_id:
                return JsonResponse({'success': False, 'message': '请先选择门店'})

            sku = SKU.objects.get(id=sku_id)

            # 查询门店库存
            store_stock = StoreStock.objects.filter(store_id=store_id, sku=sku).first()
            if not store_stock:
                return JsonResponse({'success': False, 'message': '该商品尚未初始化到此门店，当前库存: 0', 'stock': 0})

            if store_stock.stock < int(quantity):
                return JsonResponse({
                    'success': False,
                    'message': f'库存不足，当前库存: {store_stock.stock}'
                })

            return JsonResponse({'success': True, 'stock': store_stock.stock})
        except SKU.DoesNotExist:
            return JsonResponse({'success': False, 'message': '商品不存在'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'检查库存失败: {str(e)}'})


class UsbScannerStatusView(LoginRequiredMixin, View):
    """USB扫描器状态"""

    def get(self, request):
        scanners = BarcodeScanner.objects.all()

        scanner_list = []
        for scanner in scanners:
            scanner_list.append({
                'id': scanner.id,
                'name': scanner.name,
                'device_id': scanner.device_id,
                'port': scanner.port,
                'status': scanner.get_status_display(),
                'last_active': scanner.last_active.strftime('%Y-%m-%d %H:%M:%S') if scanner.last_active else ''
            })

        return JsonResponse({'success': True, 'scanners': scanner_list})


class ReceiptPreviewView(BasePosView):
    """小票预览"""
    left_menu_active = "receipt"

    def get(self, request, order_id):
        try:
            order = POSOrder.objects.select_related('store', 'cashier', 'member').get(order_id=order_id)
            order_items = order.items.all()
            context = self.get_context_data(order=order, order_items=order_items)
            return render(request, 'pos/receipt.html', context)
        except POSOrder.DoesNotExist:
            return JsonResponse({'success': False, 'message': '订单不存在'})


@method_decorator(csrf_exempt, name='dispatch')
class PrintReceiptView(LoginRequiredMixin, View):
    """打印小票"""

    @method_decorator(require_http_methods(["POST"]))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        order_id = request.POST.get('order_id')

        try:
            order = POSOrder.objects.select_related('store', 'cashier', 'member').get(order_id=order_id)
            order_items = order.items.all()

            # 生成小票内容
            store_label = (
                f'{order.store.store_code} - {order.store.store_name}'
                if order.store else '未关联门店'
            )
            receipt_content = f"""
================================
           HOT MALL 收银小票
================================
订单号: {order.order_id}
门店: {store_label}
终端编号: {order.terminal_id}
时间: {order.create_time.strftime('%Y-%m-%d %H:%M:%S')}
收银员: {order.cashier.username}
"""
            if order.member:
                receipt_content += f"会员: {order.member.username}\n"
                receipt_content += f"会员等级: {order.member.get_member_level_display()}\n"
            
            receipt_content += f"支付方式: {order.get_payment_method_display()}\n"
            receipt_content += "--------------------------------\n"
            receipt_content += "商品明细:\n"

            for item in order_items:
                receipt_content += f"{item.sku.name}\n"
                receipt_content += f"  原价: ¥{item.original_price} x {item.quantity}\n"
                if item.discount_rate < Decimal('1.00'):
                    receipt_content += f"  折扣率: {item.discount_rate}\n"
                receipt_content += f"  应付: ¥{item.price} x {item.quantity} = ¥{item.subtotal}\n"

            receipt_content += f"""
--------------------------------
商品数量: {order.total_count}
折扣前总金额: ¥{order.original_amount}
"""
            if order.discount_amount > 0:
                receipt_content += f"优惠金额: -¥{order.discount_amount}\n"
                receipt_content += f"折扣后金额: ¥{order.total_amount}\n"
            
            receipt_content += f"应付金额: ¥{order.total_amount}\n"
            
            if order.member or order.discount_type != 'none':
                receipt_content += "--------------------------------\n"
                receipt_content += "折扣信息:\n"
                if order.member:
                    receipt_content += f"会员折扣率: {order.member.discount_rate}\n"
                discount_type_display = {
                    'member': '会员折扣',
                    'promotion': '商品促销',
                    'none': '无折扣'
                }
                receipt_content += f"订单折扣方式: {discount_type_display.get(order.discount_type, '无折扣')}\n"
            
            receipt_content += "================================\n"
            receipt_content += "          谢谢惠顾！\n"
            receipt_content += "================================\n"

            return JsonResponse({
                'success': True,
                'receipt_content': receipt_content,
                'order_id': order_id
            })

        except POSOrder.DoesNotExist:
            return JsonResponse({'success': False, 'message': '订单不存在'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'打印小票失败: {str(e)}'})


@method_decorator(csrf_exempt, name='dispatch')
class SuspendOrderView(LoginRequiredMixin, View):
    """挂单"""

    @method_decorator(require_http_methods(["POST"]))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            cart_data = request.POST.get('cart_data', '[]')
            remark = request.POST.get('remark', '')
            member_id = request.POST.get('member_id', '')
            terminal_id = get_terminal_id(request)

            logger.info(f"SuspendOrder - terminal_id: {terminal_id}, member_id: {member_id}")

            try:
                cart = json.loads(cart_data)
            except json.JSONDecodeError as e:
                logger.error(f"SuspendOrder - JSON decode error: {e}")
                return JsonResponse({'success': False, 'message': '购物车数据格式错误'})

            if not cart:
                return JsonResponse({'success': False, 'message': '购物车为空'})
            if not terminal_id:
                return JsonResponse({'success': False, 'message': '收银终端未配置或终端标识不匹配'})

            # 获取当前门店ID
            store_id = get_current_store_id(request)
            if not store_id:
                return JsonResponse({'success': False, 'message': '请先选择门店'})

            # 获取门店信息
            try:
                store = Store.objects.get(id=store_id)
            except Store.DoesNotExist:
                return JsonResponse({'success': False, 'message': '门店不存在'})

            cashier = request.user

            # 计算总金额和商品数量
            total_amount = Decimal('0')
            total_count = 0

            for item in cart:
                quantity = item.get('quantity', 1)
                price_str = str(item.get('price', 0))
                try:
                    price = Decimal(price_str)
                except Exception as e:
                    logger.error(f"SuspendOrder - Invalid price format: {price_str}, error: {e}")
                    return JsonResponse({'success': False, 'message': f'商品价格格式错误: {price_str}'})
                total_amount += price * quantity
                total_count += quantity

            member = None
            if member_id:
                try:
                    # 确保 member_id 是整数
                    member_id_int = int(member_id)
                    member = User.objects.get(id=member_id_int)
                except (ValueError, TypeError) as e:
                    logger.warning(f"SuspendOrder - Invalid member_id format: {member_id}, error: {e}")
                    # 继续执行，不绑定会员
                except User.DoesNotExist as e:
                    logger.warning(f"SuspendOrder - Member not found: {member_id}, error: {e}")
                    # 继续执行，不绑定会员

            logger.info(f"SuspendOrder - Creating order - store: {store.id}, cashier: {cashier.id}, terminal: {terminal_id}, member: {member.id if member else None}")

            # 创建挂单
            try:
                suspended_order = SuspendedOrder.objects.create(
                    store=store,  # 添加门店字段
                    cashier=cashier,
                    terminal_id=str(terminal_id) if terminal_id else '',  # 确保是字符串
                    member=member,
                    total_count=total_count,
                    total_amount=total_amount,
                    cart_data=cart_data,
                    remark=remark
                )
            except Exception as create_error:
                logger.error(f"SuspendOrder - Failed to create SuspendedOrder: {type(create_error).__name__}: {str(create_error)}", exc_info=True)
                # 尝试获取详细的验证错误信息
                if hasattr(create_error, 'message_dict'):
                    logger.error(f"SuspendOrder - Validation errors: {create_error.message_dict}")
                    # 返回更友好的错误信息
                    error_details = []
                    for field, errors in create_error.message_dict.items():
                        error_details.append(f"{field}: {', '.join(errors)}")
                    return JsonResponse({'success': False, 'message': f'创建挂单失败: {"; ".join(error_details)}'})
                return JsonResponse({'success': False, 'message': f'创建挂单失败: {str(create_error)}'})

            return JsonResponse({
                'success': True,
                'suspended_order_id': suspended_order.id,
                'message': '挂单成功'
            })

        except Exception as e:
            logger.error(f"SuspendOrder - Outer Exception: {type(e).__name__}: {str(e)}", exc_info=True)
            logger.error(f"SuspendOrder - Request data: POST={dict(request.POST)}, GET={dict(request.GET)}")
            return JsonResponse({'success': False, 'message': f'挂单失败: {str(e)}'})


@method_decorator(csrf_exempt, name='dispatch')
class GetSuspendedOrdersView(LoginRequiredMixin, View):
    """获取挂单列表"""

    @method_decorator(require_http_methods(["GET"]))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        try:
            terminal_id = get_terminal_id(request)
            if not terminal_id:
                return JsonResponse({'success': False, 'message': '收银终端未配置或终端标识不匹配'})

            # 获取当前门店ID
            store_id = get_current_store_id(request)
            if not store_id:
                return JsonResponse({'success': False, 'message': '请先选择门店'})

            suspended_orders = SuspendedOrder.objects.filter(
                cashier=request.user, terminal_id=terminal_id, store_id=store_id
            ).order_by('-create_time')

            order_list = []
            for order in suspended_orders:
                member_data = None
                if order.member:
                    member_data = {
                        'id': order.member.id,
                        'username': order.member.username,
                        'member_level_display': order.member.get_member_level_display(),
                    }
                order_list.append({
                    'id': order.id,
                    'total_count': order.total_count,
                    'total_amount': str(order.total_amount),
                    'create_time': order.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'remark': order.remark,
                    'member': member_data
                })

            return JsonResponse({'success': True, 'orders': order_list})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'获取挂单列表失败: {str(e)}'})


@method_decorator(csrf_exempt, name='dispatch')
class ResumeOrderView(LoginRequiredMixin, View):
    """取单"""

    @method_decorator(require_http_methods(["POST"]))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        suspended_order_id = request.POST.get('suspended_order_id')
        terminal_id = get_terminal_id(request)
        if not terminal_id:
            return JsonResponse({'success': False, 'message': '收银终端未配置或终端标识不匹配'})

        # 获取当前门店ID
        store_id = get_current_store_id(request)
        if not store_id:
            return JsonResponse({'success': False, 'message': '请先选择门店'})

        try:
            suspended_order = SuspendedOrder.objects.get(
                id=suspended_order_id, cashier=request.user, terminal_id=terminal_id, store_id=store_id
            )

            # 获取购物车数据
            cart_data = json.loads(suspended_order.cart_data)

            # 不立即删除挂单，返回挂单ID供前端使用
            member_data = None
            if suspended_order.member:
                member_data = {
                    'id': suspended_order.member.id,
                    'username': suspended_order.member.username,
                    'member_level_display': suspended_order.member.get_member_level_display(),
                    'points': suspended_order.member.points,
                    'discount_rate': str(suspended_order.member.discount_rate),
                    'total_consume': str(suspended_order.member.total_consume),
                }

            return JsonResponse({
                'success': True,
                'cart_data': cart_data,
                'remark': suspended_order.remark,
                'member': member_data,
                'suspended_order_id': suspended_order.id,
                'message': '取单成功'
            })

        except SuspendedOrder.DoesNotExist:
            return JsonResponse({'success': False, 'message': '挂单不存在'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'取单失败: {str(e)}'})


@method_decorator(csrf_exempt, name='dispatch')
class DeleteSuspendedOrderView(LoginRequiredMixin, View):
    """删除挂单"""

    @method_decorator(require_http_methods(["POST"]))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        suspended_order_id = request.POST.get('suspended_order_id')
        terminal_id = get_terminal_id(request)
        if not terminal_id:
            return JsonResponse({'success': False, 'message': '收银终端未配置或终端标识不匹配'})

        # 获取当前门店ID
        store_id = get_current_store_id(request)
        if not store_id:
            return JsonResponse({'success': False, 'message': '请先选择门店'})

        try:
            with transaction.atomic():
                suspended_order = SuspendedOrder.objects.select_for_update().get(
                    id=suspended_order_id, cashier=request.user, terminal_id=terminal_id, store_id=store_id
                )
                suspended_order.delete()

            return JsonResponse({'success': True, 'message': '删除挂单成功'})

        except SuspendedOrder.DoesNotExist:
            return JsonResponse({'success': False, 'message': '挂单不存在'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'删除挂单失败: {str(e)}'})


class TransactionRecordsPageView(BasePosView):
    """交易记录查询页面"""
    left_menu_active = "transaction-records"

    def get(self, request):
        context = self.get_context_data()
        return render(request, 'pos/transaction_records.html', context)


class TransactionDetailsPageView(BasePosView):
    """交易记录明细查询页面"""
    left_menu_active = "transaction-details"

    def get(self, request):
        context = self.get_context_data()
        return render(request, 'pos/transaction_details.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class GetTransactionDetailsView(LoginRequiredMixin, View):
    """获取订单明细"""

    @method_decorator(require_http_methods(["GET"]))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        page = request.GET.get('page', 1)
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        order_id = request.GET.get('order_id', '')

        try:
            # 获取当前门店ID
            store_id = get_current_store_id(request)
            if not store_id:
                return JsonResponse({'success': False, 'message': '请先选择门店'})

            # 构建查询条件（已修复排序问题）
            order_items = POSOrderItem.objects.select_related('order', 'sku').filter(
                order__store_id=store_id
            ).order_by('-order__create_time')

            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    start_dt = timezone.make_aware(start_dt, timezone.get_current_timezone())
                    order_items = order_items.filter(order__create_time__gte=start_dt)
                except (ValueError, Exception):
                    pass
            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                    end_dt = end_dt.replace(hour=23, minute=59, second=59)
                    end_dt = timezone.make_aware(end_dt, timezone.get_current_timezone())
                    order_items = order_items.filter(order__create_time__lte=end_dt)
                except (ValueError, Exception):
                    pass
            if order_id:
                order_items = order_items.filter(order__order_id__icontains=order_id)

            # 分页
            paginator = Paginator(order_items, 10)

            try:
                items_page = paginator.page(page)
            except PageNotAnInteger:
                items_page = paginator.page(1)
            except EmptyPage:
                items_page = paginator.page(paginator.num_pages)

            # 构建返回数据
            item_list = []
            for item in items_page:
                item_list.append({
                    'id': item.id,
                    'order_id': item.order.order_id,
                    'sku_name': item.sku.name,
                    'sku_caption': item.sku.caption,
                    'price': str(item.price),
                    'quantity': item.quantity,
                    'subtotal': str(item.subtotal),
                    'create_time': item.order.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'cashier': item.order.cashier.username,
                    'payment_method': item.order.get_payment_method_display(),
                    'status': item.order.get_status_display()
                })

            return JsonResponse({
                'success': True,
                'items': item_list,
                'total_pages': paginator.num_pages,
                'current_page': items_page.number
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'获取订单明细失败: {str(e)}'})


@method_decorator(csrf_exempt, name='dispatch')
class GetTransactionRecordsView(LoginRequiredMixin, View):
    """获取交易记录"""

    @method_decorator(require_http_methods(["GET"]))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        page = request.GET.get('page', 1)
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        order_id = request.GET.get('order_id', '')

        try:
            # 获取当前门店ID
            store_id = get_current_store_id(request)
            if not store_id:
                return JsonResponse({'success': False, 'message': '请先选择门店'})

            # 构建查询条件（已修复排序问题）
            orders = POSOrder.objects.filter(store_id=store_id).order_by('-create_time')

            # 时区兼容日期筛选 核心修复
            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    start_dt = timezone.make_aware(start_dt, timezone.get_current_timezone())
                    orders = orders.filter(create_time__gte=start_dt)
                except:
                    pass
            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                    end_dt = end_dt.replace(hour=23, minute=59, second=59)
                    end_dt = timezone.make_aware(end_dt, timezone.get_current_timezone())
                    orders = orders.filter(create_time__lte=end_dt)
                except:
                    pass

            if order_id:
                orders = orders.filter(order_id__icontains=order_id)

            # 分页
            paginator = Paginator(orders, 10)

            try:
                orders_page = paginator.page(page)
            except PageNotAnInteger:
                orders_page = paginator.page(1)
            except EmptyPage:
                orders_page = paginator.page(paginator.num_pages)

            # 构建返回数据
            order_list = []
            for order in orders_page:
                order_list.append({
                    'order_id': order.order_id,
                    'cashier': order.cashier.username,
                    'total_count': order.total_count,
                    'total_amount': str(order.total_amount),
                    'paid_amount': str(order.paid_amount),
                    'payment_method': order.get_payment_method_display(),
                    'status': order.get_status_display(),
                    'status_code': order.status,
                    'create_time': order.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'remark': order.remark
                })

            return JsonResponse({
                'success': True,
                'orders': order_list,
                'total_pages': paginator.num_pages,
                'current_page': orders_page.number
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'获取交易记录失败: {str(e)}'})


@method_decorator(csrf_exempt, name='dispatch')
class UpdateOrderStatusView(LoginRequiredMixin, View):
    """更新订单状态"""

    @method_decorator(require_http_methods(["POST"]))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        order_id = request.POST.get('order_id')
        status = request.POST.get('status')

        if not order_id or not status:
            return JsonResponse({'success': False, 'message': '订单号和状态不能为空'})

        try:
            status = int(status)
            if status not in [3, 9]:
                return JsonResponse({'success': False, 'message': '无效的状态值'})

            order = POSOrder.objects.get(order_id=order_id)
            order.status = status
            order.save()

            return JsonResponse({
                'success': True,
                'message': f'订单状态已更新为{order.get_status_display()}'
            })

        except POSOrder.DoesNotExist:
            return JsonResponse({'success': False, 'message': '订单不存在'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'更新订单状态失败: {str(e)}'})


class PromotionListView(BasePosView):
    """促销商品列表页面"""
    left_menu_active = "promotion"
    template_name = 'user_center_promotion.html'

    def get(self, request):
        if not request.user.is_superuser:
            return redirect(reverse_lazy('contents:index'))
        
        context = self.get_context_data()
        context['is_superuser'] = request.user.is_superuser
        return render(request, self.template_name, context)


class PromotionListAPIView(LoginRequiredMixin, ListView):
    """促销商品列表API"""
    model = PromotionProduct
    paginate_by = 10
    template_name = None

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('sku').order_by('-create_time')
        
        keyword = self.request.GET.get('keyword', '').strip()
        if keyword:
            queryset = queryset.filter(sku__name__icontains=keyword)
        
        return queryset

    def get_paginated_response(self, page_obj):
        promotions = []
        for promotion in page_obj.object_list:
            promotions.append({
                'id': promotion.id,
                'sku_id': promotion.sku.id,
                'sku_name': promotion.sku.name,
                'discount_type': promotion.discount_type,
                'discount_type_display': promotion.get_discount_type_display(),
                'discount_rate': str(promotion.discount_rate),
                'discount_amount': str(promotion.discount_amount),
                'start_time': promotion.start_time.isoformat(),
                'end_time': promotion.end_time.isoformat(),
                'is_active': promotion.is_active,
                'description': promotion.description
            })
        
        return {
            'code': 0,
            'errmsg': 'OK',
            'promotions': promotions,
            'total_pages': page_obj.paginator.num_pages,
            'current_page': page_obj.number
        }

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        
        page = request.GET.get('page', 1)
        paginator = Paginator(self.object_list, self.paginate_by)
        
        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        
        return JsonResponse(self.get_paginated_response(page_obj))


class PromotionAddView(BasePosView, View):
    """添加促销商品"""
    left_menu_active = "promotion-add"
    template_name = 'user_center_promotion_manage.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect(reverse_lazy('contents:index'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        from goods.models import SKU
        skus = SKU.objects.filter(is_launched=True)
        context = self.get_context_data()
        context['title'] = '添加促销商品'
        context['is_superuser'] = request.user.is_superuser
        context['skus'] = skus
        return render(request, self.template_name, context)

    def post(self, request):
        if not request.user.is_superuser:
            return JsonResponse({'success': False, 'message': '权限不足'})

        try:
            sku_id = request.POST.get('sku_id')
            discount_type = int(request.POST.get('discount_type', 1))
            discount_rate = Decimal(request.POST.get('discount_rate', '1.00'))
            discount_amount = Decimal(request.POST.get('discount_amount', '0'))
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            is_active = request.POST.get('is_active') == 'True'
            description = request.POST.get('description', '')

            if not sku_id:
                from goods.models import SKU
                skus = SKU.objects.filter(is_launched=True)
                context = self.get_context_data()
                context['title'] = '添加促销商品'
                context['is_superuser'] = request.user.is_superuser
                context['skus'] = skus
                context['error'] = '请选择商品'
                return render(request, self.template_name, context)

            if not start_time or not end_time:
                from goods.models import SKU
                skus = SKU.objects.filter(is_launched=True)
                context = self.get_context_data()
                context['title'] = '添加促销商品'
                context['is_superuser'] = request.user.is_superuser
                context['skus'] = skus
                context['error'] = '请设置促销时间'
                return render(request, self.template_name, context)

            from goods.models import SKU
            sku = SKU.objects.get(id=sku_id)
            
            PromotionProduct.objects.create(
                sku=sku,
                discount_type=discount_type,
                discount_rate=discount_rate,
                discount_amount=discount_amount,
                start_time=start_time,
                end_time=end_time,
                is_active=is_active,
                description=description
            )

            messages.success(request, f"促销商品“{sku.name}”已添加。")
            return redirect(reverse_lazy('pos:promotion_list'))

        except Exception as e:
            from goods.models import SKU
            skus = SKU.objects.filter(is_launched=True)
            context = self.get_context_data()
            context['title'] = '添加促销商品'
            context['is_superuser'] = request.user.is_superuser
            context['skus'] = skus
            context['error'] = f'添加失败: {str(e)}'
            return render(request, self.template_name, context)


class PromotionEditView(BasePosView, View):
    """编辑促销商品"""
    left_menu_active = "promotion-edit"
    template_name = 'user_center_promotion_manage.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect(reverse_lazy('contents:index'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        from goods.models import SKU
        try:
            promotion = PromotionProduct.objects.get(id=pk)
            skus = SKU.objects.filter(is_launched=True)
            context = self.get_context_data()
            context['title'] = '编辑促销商品'
            context['is_superuser'] = request.user.is_superuser
            context['skus'] = skus
            context['promotion'] = promotion
            return render(request, self.template_name, context)
        except PromotionProduct.DoesNotExist:
            return redirect(reverse_lazy('pos:promotion_list'))

    def post(self, request, pk):
        if not request.user.is_superuser:
            return JsonResponse({'success': False, 'message': '权限不足'})

        try:
            promotion = PromotionProduct.objects.get(id=pk)
            
            sku_id = request.POST.get('sku_id')
            discount_type = int(request.POST.get('discount_type', 1))
            discount_rate = Decimal(request.POST.get('discount_rate', '1.00'))
            discount_amount = Decimal(request.POST.get('discount_amount', '0'))
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            is_active = request.POST.get('is_active') == 'True'
            description = request.POST.get('description', '')

            if sku_id:
                from goods.models import SKU
                promotion.sku = SKU.objects.get(id=sku_id)
            
            promotion.discount_type = discount_type
            promotion.discount_rate = discount_rate
            promotion.discount_amount = discount_amount
            promotion.start_time = start_time
            promotion.end_time = end_time
            promotion.is_active = is_active
            promotion.description = description
            promotion.save()

            messages.success(request, f"促销商品“{promotion.sku.name}”已更新。")
            return redirect(reverse_lazy('pos:promotion_list'))

        except Exception as e:
            from goods.models import SKU
            skus = SKU.objects.filter(is_launched=True)
            context = self.get_context_data()
            context['title'] = '编辑促销商品'
            context['is_superuser'] = request.user.is_superuser
            context['skus'] = skus
            context['promotion'] = promotion
            context['error'] = f'更新失败: {str(e)}'
            return render(request, self.template_name, context)


class PromotionDeleteView(LoginRequiredMixin, DeleteView):
    """删除促销商品"""
    model = PromotionProduct
    success_url = reverse_lazy('pos:promotion_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return JsonResponse({'code': 1, 'errmsg': '权限不足'}, status=403)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        sku_name = self.object.sku.name
        self.object.delete()
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'message': f'促销商品"{sku_name}"已删除。'})


class PaymentConfigView(BasePosView):
    """收银设置页面"""
    left_menu_active = "payment-config"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect(reverse_lazy('contents:index'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        from .models import PaymentAccount
        payment_accounts = PaymentAccount.objects.all()
        context = self.get_context_data()
        context['payment_accounts'] = payment_accounts
        context['is_superuser'] = request.user.is_superuser
        return render(request, 'pos/payment_config.html', context)


class PaymentAccountAddView(BasePosView):
    """添加收款账户"""
    left_menu_active = "payment-config"
    template_name = 'pos/payment_account_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect(reverse_lazy('contents:index'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        context = self.get_context_data()
        context['title'] = '添加收款账户'
        context['is_superuser'] = request.user.is_superuser
        return render(request, self.template_name, context)

    def post(self, request):
        if not request.user.is_superuser:
            return JsonResponse({'success': False, 'message': '权限不足'})

        try:
            from .models import PaymentAccount
            payment_type = int(request.POST.get('payment_type'))
            account_name = request.POST.get('account_name')
            account_number = request.POST.get('account_number')
            merchant_id = request.POST.get('merchant_id', '')
            api_key = request.POST.get('api_key', '')
            app_id = request.POST.get('app_id', '')
            is_active = request.POST.get('is_active') == '1'
            remark = request.POST.get('remark', '')

            PaymentAccount.objects.create(
                payment_type=payment_type,
                account_name=account_name,
                account_number=account_number,
                merchant_id=merchant_id,
                api_key=api_key,
                app_id=app_id,
                is_active=is_active,
                remark=remark
            )

            messages.success(request, f"收款账户「{account_name}」已添加。")
            return redirect(reverse_lazy('pos:payment_config'))

        except Exception as e:
            context = self.get_context_data()
            context['title'] = '添加收款账户'
            context['is_superuser'] = request.user.is_superuser
            context['error'] = f'添加失败: {str(e)}'
            return render(request, self.template_name, context)


class PaymentAccountEditView(BasePosView):
    """编辑收款账户"""
    left_menu_active = "payment-config"
    template_name = 'pos/payment_account_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect(reverse_lazy('contents:index'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        from .models import PaymentAccount
        try:
            account = PaymentAccount.objects.get(id=pk)
            context = self.get_context_data()
            context['title'] = '编辑收款账户'
            context['is_superuser'] = request.user.is_superuser
            context['account'] = account
            return render(request, self.template_name, context)
        except PaymentAccount.DoesNotExist:
            return redirect(reverse_lazy('pos:payment_config'))

    def post(self, request, pk):
        if not request.user.is_superuser:
            return JsonResponse({'success': False, 'message': '权限不足'})

        try:
            from .models import PaymentAccount
            account = PaymentAccount.objects.get(id=pk)
            
            account_name = request.POST.get('account_name')
            account_number = request.POST.get('account_number')
            merchant_id = request.POST.get('merchant_id', '')
            api_key = request.POST.get('api_key', '')
            app_id = request.POST.get('app_id', '')
            is_active = request.POST.get('is_active') == '1'
            remark = request.POST.get('remark', '')

            account.account_name = account_name
            account.account_number = account_number
            account.merchant_id = merchant_id
            account.api_key = api_key
            account.app_id = app_id
            account.is_active = is_active
            account.remark = remark
            account.save()

            messages.success(request, f"收款账户「{account_name}」已更新。")
            return redirect(reverse_lazy('pos:payment_config'))

        except PaymentAccount.DoesNotExist:
            return redirect(reverse_lazy('pos:payment_config'))
        except Exception as e:
            context = self.get_context_data()
            context['title'] = '编辑收款账户'
            context['is_superuser'] = request.user.is_superuser
            context['account'] = None
            context['error'] = f'更新失败: {str(e)}'
            return render(request, self.template_name, context)


class PaymentAccountDeleteView(LoginRequiredMixin, DeleteView):
    """删除收款账户"""
    from .models import PaymentAccount
    model = PaymentAccount
    success_url = reverse_lazy('pos:payment_config')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return JsonResponse({'code': 1, 'errmsg': '权限不足'}, status=403)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        account_name = self.object.account_name
        self.object.delete()
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'message': f'收款账户「{account_name}」已删除。'})


# ==================== 门店管理 ====================

class StoreListView(BasePosView):
    """门店列表页面"""
    left_menu_active = "store"
    template_name = 'pos/store_list.html'

    def get(self, request):
        if not request.user.is_superuser:
            return redirect(reverse_lazy('contents:index'))

        stores = Store.objects.all().order_by('store_code')
        context = self.get_context_data()
        context['is_superuser'] = request.user.is_superuser
        context['stores'] = stores
        return render(request, self.template_name, context)


class StoreAddView(BasePosView, View):
    """添加门店"""
    left_menu_active = "store-add"
    template_name = 'pos/store_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect(reverse_lazy('contents:index'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        context = self.get_context_data()
        context['title'] = '添加门店'
        context['is_superuser'] = request.user.is_superuser
        context['store'] = None
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            store_code = request.POST.get('store_code')
            store_name = request.POST.get('store_name')
            address = request.POST.get('address')
            phone = request.POST.get('phone', '')
            manager = request.POST.get('manager', '')
            status = request.POST.get('status', '1')
            business_hours = request.POST.get('business_hours', '')

            if not store_code or not store_name or not address:
                context = self.get_context_data()
                context['title'] = '添加门店'
                context['is_superuser'] = request.user.is_superuser
                context['error'] = '门店编号、名称和地址不能为空'
                return render(request, self.template_name, context)

            # 检查门店编号是否已存在
            if Store.objects.filter(store_code=store_code).exists():
                context = self.get_context_data()
                context['title'] = '添加门店'
                context['is_superuser'] = request.user.is_superuser
                context['error'] = '门店编号已存在'
                return render(request, self.template_name, context)

            Store.objects.create(
                store_code=store_code,
                store_name=store_name,
                address=address,
                phone=phone,
                manager=manager,
                status=int(status),
                business_hours=business_hours
            )

            messages.success(request, f"门店「{store_name}」已添加。")
            return redirect(reverse_lazy('pos:store_list'))

        except Exception as e:
            context = self.get_context_data()
            context['title'] = '添加门店'
            context['is_superuser'] = request.user.is_superuser
            context['error'] = f'添加失败: {str(e)}'
            return render(request, self.template_name, context)


class StoreEditView(BasePosView, View):
    """编辑门店"""
    left_menu_active = "store-edit"
    template_name = 'pos/store_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect(reverse_lazy('contents:index'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        try:
            store = Store.objects.get(pk=pk)
            context = self.get_context_data()
            context['title'] = '编辑门店'
            context['is_superuser'] = request.user.is_superuser
            context['store'] = store
            return render(request, self.template_name, context)
        except Store.DoesNotExist:
            return redirect(reverse_lazy('pos:store_list'))

    def post(self, request, pk):
        try:
            store = Store.objects.get(pk=pk)

            store_code = request.POST.get('store_code')
            store_name = request.POST.get('store_name')
            address = request.POST.get('address')
            phone = request.POST.get('phone', '')
            manager = request.POST.get('manager', '')
            status = request.POST.get('status', '1')
            business_hours = request.POST.get('business_hours', '')

            if not store_code or not store_name or not address:
                context = self.get_context_data()
                context['title'] = '编辑门店'
                context['is_superuser'] = request.user.is_superuser
                context['store'] = store
                context['error'] = '门店编号、名称和地址不能为空'
                return render(request, self.template_name, context)

            # 检查门店编号是否被其他门店使用
            if Store.objects.filter(store_code=store_code).exclude(pk=pk).exists():
                context = self.get_context_data()
                context['title'] = '编辑门店'
                context['is_superuser'] = request.user.is_superuser
                context['store'] = store
                context['error'] = '门店编号已被其他门店使用'
                return render(request, self.template_name, context)

            store.store_code = store_code
            store.store_name = store_name
            store.address = address
            store.phone = phone
            store.manager = manager
            store.status = int(status)
            store.business_hours = business_hours
            store.save()

            messages.success(request, f"门店「{store_name}」已更新。")
            return redirect(reverse_lazy('pos:store_list'))

        except Store.DoesNotExist:
            return redirect(reverse_lazy('pos:store_list'))
        except Exception as e:
            context = self.get_context_data()
            context['title'] = '编辑门店'
            context['is_superuser'] = request.user.is_superuser
            context['store'] = store
            context['error'] = f'更新失败: {str(e)}'
            return render(request, self.template_name, context)


class StoreTerminalListView(BasePosView):
    """门店收银终端列表。"""
    left_menu_active = 'store'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect(reverse_lazy('contents:index'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, store_pk):
        store = get_object_or_404(Store, pk=store_pk)
        terminals = StoreTerminal.objects.filter(store=store)
        return render(request, 'pos/store_terminal_list.html', self.get_context_data(
            store=store, terminals=terminals, is_superuser=True,
        ))


class StoreTerminalFormView(BasePosView, View):
    """新增或编辑门店收银终端。"""
    left_menu_active = 'store'
    template_name = 'pos/store_terminal_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect(reverse_lazy('contents:index'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, store_pk, pk=None):
        store = get_object_or_404(Store, pk=store_pk)
        terminal = get_object_or_404(StoreTerminal, pk=pk, store=store) if pk else None
        title = '编辑收银终端' if terminal else '添加收银终端'
        return render(request, self.template_name, self.get_context_data(
            store=store, terminal=terminal, title=title, is_superuser=True,
        ))

    def post(self, request, store_pk, pk=None):
        store = get_object_or_404(Store, pk=store_pk)
        terminal = get_object_or_404(StoreTerminal, pk=pk, store=store) if pk else None
        terminal_code = request.POST.get('terminal_code', '').strip()
        name = request.POST.get('name', '').strip()
        ip_address = request.POST.get('ip_address', '').strip()
        certificate_fingerprint = request.POST.get('certificate_fingerprint', '').strip().lower()
        status = request.POST.get('status', '1')
        title = '编辑收银终端' if terminal else '添加收银终端'

        duplicate = StoreTerminal.objects.filter(terminal_code=terminal_code)
        duplicate_fingerprint = StoreTerminal.objects.filter(
            certificate_fingerprint=certificate_fingerprint
        ) if certificate_fingerprint else StoreTerminal.objects.none()
        if terminal:
            duplicate = duplicate.exclude(pk=terminal.pk)
            duplicate_fingerprint = duplicate_fingerprint.exclude(pk=terminal.pk)
        error = ''
        if not terminal_code or not name:
            error = '终端编号和名称不能为空'
        elif not ip_address:
            error = '终端IP地址不能为空'
        elif len(terminal_code) > 100 or len(name) > 100:
            error = '终端编号和名称不能超过100个字符'
        elif len(ip_address) > 45:
            error = '终端IP地址长度无效'
        else:
            try:
                ip_address = ipaddress.ip_address(ip_address).compressed
            except ValueError:
                error = '请输入有效的IPv4或IPv6地址'

        if not error and status not in ('0', '1'):
            error = '终端状态无效'
        elif not error and status == '1' and not re.fullmatch(r'[0-9a-f]{64}', certificate_fingerprint):
            error = '启用终端必须填写有效的SHA-256客户端证书指纹'
        elif not error and duplicate_fingerprint.exists():
            error = '客户端证书指纹已绑定其他终端'
        elif not error and duplicate.exists():
            error = '终端编号已被使用'

        if error:
            return render(request, self.template_name, self.get_context_data(
                store=store, terminal=terminal, title=title, error=error, is_superuser=True,
            ))

        if terminal is None:
            StoreTerminal.objects.create(
                store=store, terminal_code=terminal_code, name=name,
                ip_address=ip_address, certificate_fingerprint=certificate_fingerprint,
                status=int(status),
            )
        else:
            terminal.terminal_code = terminal_code
            terminal.name = name
            terminal.ip_address = ip_address
            terminal.certificate_fingerprint = certificate_fingerprint
            terminal.status = int(status)
            terminal.save()
        messages.success(request, f'收银终端「{name}」已保存。')
        return redirect(reverse_lazy('pos:store_terminal_list', kwargs={'store_pk': store.pk}))


class StoreTerminalDeleteView(LoginRequiredMixin, View):
    """删除门店收银终端。"""

    def post(self, request, store_pk, pk):
        if not request.user.is_superuser:
            return JsonResponse({'code': 1, 'errmsg': '权限不足'}, status=403)
        terminal = get_object_or_404(StoreTerminal, pk=pk, store_id=store_pk)
        name = terminal.name
        terminal.delete()
        return JsonResponse({'code': 0, 'message': f'收银终端「{name}」已删除。'})


class StoreDeleteView(LoginRequiredMixin, DeleteView):
    """删除门店"""
    model = Store
    success_url = reverse_lazy('pos:store_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return JsonResponse({'code': 1, 'errmsg': '权限不足'}, status=403)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        store_name = self.object.store_name
        self.object.delete()
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'message': f'门店「{store_name}」已删除。'})


# ==================== 用户-门店关联管理 ====================

class UserStoreListView(BasePosView):
    """用户-门店关联列表页面"""
    left_menu_active = "user-store"
    template_name = 'pos/user_store_list.html'

    def get(self, request):
        if not request.user.is_superuser:
            return redirect(reverse_lazy('contents:index'))

        user_stores = UserStore.objects.select_related('user', 'store').all().order_by('user', 'store')
        context = self.get_context_data()
        context['is_superuser'] = request.user.is_superuser
        context['user_stores'] = user_stores
        return render(request, self.template_name, context)


class UserStoreAddView(BasePosView, View):
    """添加用户-门店关联"""
    left_menu_active = "user-store-add"
    template_name = 'pos/user_store_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect(reverse_lazy('contents:index'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        users = User.objects.all()
        stores = Store.objects.filter(status=1)
        context = self.get_context_data()
        context['title'] = '添加用户-门店关联'
        context['is_superuser'] = request.user.is_superuser
        context['users'] = users
        context['stores'] = stores
        context['user_store'] = None
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            user_id = request.POST.get('user_id')
            store_id = request.POST.get('store_id')
            role = request.POST.get('role', '2')

            if not user_id or not store_id:
                context = self.get_context_data()
                context['title'] = '添加用户-门店关联'
                context['is_superuser'] = request.user.is_superuser
                context['users'] = User.objects.all()
                context['stores'] = Store.objects.filter(status=1)
                context['error'] = '用户和门店不能为空'
                return render(request, self.template_name, context)

            # 检查关联是否已存在
            if UserStore.objects.filter(user_id=user_id, store_id=store_id).exists():
                context = self.get_context_data()
                context['title'] = '添加用户-门店关联'
                context['is_superuser'] = request.user.is_superuser
                context['users'] = User.objects.all()
                context['stores'] = Store.objects.filter(status=1)
                context['error'] = '该用户已关联此门店'
                return render(request, self.template_name, context)

            UserStore.objects.create(
                user_id=user_id,
                store_id=store_id,
                role=int(role)
            )

            messages.success(request, "用户-门店关联已添加。")
            return redirect(reverse_lazy('pos:user_store_list'))

        except Exception as e:
            context = self.get_context_data()
            context['title'] = '添加用户-门店关联'
            context['is_superuser'] = request.user.is_superuser
            context['users'] = User.objects.all()
            context['stores'] = Store.objects.filter(status=1)
            context['error'] = f'添加失败: {str(e)}'
            return render(request, self.template_name, context)


class UserStoreDeleteView(LoginRequiredMixin, DeleteView):
    """删除用户-门店关联"""
    model = UserStore
    success_url = reverse_lazy('pos:user_store_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return JsonResponse({'code': 1, 'errmsg': '权限不足'}, status=403)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'message': '用户-门店关联已删除。'})


class UserStoreEditView(BasePosView, View):
    """修改用户在门店中的角色。"""
    left_menu_active = "user-store"
    template_name = 'pos/user_store_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect(reverse_lazy('contents:index'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        user_store = get_object_or_404(UserStore.objects.select_related('user', 'store'), pk=pk)
        return render(request, self.template_name, self.get_context_data(
            title='编辑用户-门店关联', is_superuser=True,
            users=User.objects.all(), stores=Store.objects.filter(status=1),
            user_store=user_store,
        ))

    def post(self, request, pk):
        user_store = get_object_or_404(UserStore, pk=pk)
        role = request.POST.get('role', '')
        valid_roles = {str(value) for value, _ in UserStore.ROLE_CHOICES}
        if role not in valid_roles:
            return render(request, self.template_name, self.get_context_data(
                title='编辑用户-门店关联', is_superuser=True,
                users=User.objects.all(), stores=Store.objects.filter(status=1),
                user_store=user_store, error='请选择有效角色',
            ))

        user_store.role = int(role)
        user_store.save(update_fields=['role', 'update_time'])
        messages.success(request, '用户门店角色已更新。')
        return redirect(reverse_lazy('pos:user_store_list'))


# ==================== 门店选择 ====================

class SelectStoreView(LoginRequiredMixin, View):
    """选择门店"""

    def get(self, request):
        # 获取用户可访问的门店
        if request.user.is_superuser:
            # 超级管理员可以访问所有门店
            stores = Store.objects.filter(status=1)
        else:
            # 普通用户只能访问关联的门店
            stores = Store.objects.filter(userstore__user=request.user, status=1).distinct()

        current_store_id = get_current_store_id(request)

        context = {
            'stores': stores,
            'current_store_id': current_store_id,
            'current_store_name': request.session.get('current_store_name', ''),
        }
        return render(request, 'pos/select_store.html', context)

    def post(self, request):
        store_id = request.POST.get('store_id')
        if not store_id:
            return JsonResponse({'success': False, 'message': '请选择门店'})

        try:
            # 验证用户是否有权限访问该门店
            if request.user.is_superuser:
                store = Store.objects.get(id=store_id, status=1)
            else:
                user_store = UserStore.objects.get(user=request.user, store_id=store_id)
                store = user_store.store
                if store.status != 1:
                    return JsonResponse({'success': False, 'message': '该门店已停用'})

            # 设置当前门店到Session
            request.session['current_store_id'] = store.id
            request.session['current_store_name'] = store.store_name

            return JsonResponse({'success': True, 'message': f'已切换到门店：{store.store_name}'})

        except Store.DoesNotExist:
            return JsonResponse({'success': False, 'message': '门店不存在'})
        except UserStore.DoesNotExist:
            return JsonResponse({'success': False, 'message': '您没有权限访问该门店'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'切换门店失败: {str(e)}'})


# ==================== 门店库存初始化 ====================

class InitStoreStockView(BasePosView, View):
    """门店库存初始化"""
    left_menu_active = "init-stock"
    template_name = 'pos/init_store_stock.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect(reverse_lazy('contents:index'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        stores = Store.objects.filter(status=1)
        context = self.get_context_data()
        context['title'] = '门店库存初始化'
        context['is_superuser'] = request.user.is_superuser
        context['stores'] = stores
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            store_id = request.POST.get('store_id')
            if not store_id:
                context = self.get_context_data()
                context['title'] = '门店库存初始化'
                context['is_superuser'] = request.user.is_superuser
                context['stores'] = Store.objects.filter(status=1)
                context['error'] = '请选择门店'
                return render(request, self.template_name, context)

            store = Store.objects.get(id=store_id, status=1)

            # 获取所有SKU
            skus = SKU.objects.all()
            created_count = 0
            updated_count = 0

            with transaction.atomic():
                for sku in skus:
                    _, created = StoreStock.objects.get_or_create(
                        store=store,
                        sku=sku,
                        defaults={
                            'stock': sku.stock,
                            'near_expiry_num': sku.near_expiry_num,
                            'expired_num': sku.expired_num
                        }
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

            messages.success(request, f"门店「{store.store_name}」库存初始化完成。新增：{created_count}，已存在：{updated_count}。")
            return redirect(reverse_lazy('pos:init_store_stock'))

        except Store.DoesNotExist:
            context = self.get_context_data()
            context['title'] = '门店库存初始化'
            context['is_superuser'] = request.user.is_superuser
            context['stores'] = Store.objects.filter(status=1)
            context['error'] = '门店不存在'
            return render(request, self.template_name, context)
        except Exception as e:
            context = self.get_context_data()
            context['title'] = '门店库存初始化'
            context['is_superuser'] = request.user.is_superuser
            context['stores'] = Store.objects.filter(status=1)
            context['error'] = f'初始化失败: {str(e)}'
            return render(request, self.template_name, context)


class BindCertificateView(LoginRequiredMixin, View):
    """绑定客户端证书到收银终端"""

    def post(self, request):
        terminal_id = request.POST.get('terminal_id')
        certificate_pem = request.POST.get('certificate_pem')

        if not terminal_id or not certificate_pem:
            return JsonResponse({'success': False, 'message': '缺少必要参数'}, status=400)

        try:
            from hot_mall.utils.mtls_utils import get_certificate_fingerprint_from_pem

            # Calculate certificate fingerprint
            fingerprint = get_certificate_fingerprint_from_pem(certificate_pem)

            # Get terminal
            terminal = get_object_or_404(StoreTerminal, id=terminal_id)

            # Update terminal with certificate fingerprint
            terminal.certificate_fingerprint = fingerprint
            terminal.save()

            return JsonResponse({
                'success': True,
                'message': '证书绑定成功',
                'fingerprint': fingerprint
            })
        except ValueError as e:
            return JsonResponse({'success': False, 'message': f'证书解析失败: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'绑定失败: {str(e)}'}, status=500)


class UnbindCertificateView(LoginRequiredMixin, View):
    """解绑收银终端的客户端证书"""

    def post(self, request, pk):
        try:
            terminal = get_object_or_404(StoreTerminal, id=pk)
            terminal.certificate_fingerprint = ''
            terminal.save()

            return JsonResponse({'success': True, 'message': '证书解绑成功'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'解绑失败: {str(e)}'}, status=500)


class VerifyCertificateView(View):
    """验证客户端证书（用于测试）"""

    def post(self, request):
        certificate_pem = request.POST.get('certificate_pem')
        terminal_code = request.POST.get('terminal_code')

        if not certificate_pem or not terminal_code:
            return JsonResponse({'success': False, 'message': '缺少必要参数'}, status=400)

        try:
            from hot_mall.utils.mtls_utils import (
                get_certificate_fingerprint_from_pem,
                verify_certificate_binding
            )

            # Calculate certificate fingerprint
            fingerprint = get_certificate_fingerprint_from_pem(certificate_pem)

            # Verify binding
            result = verify_certificate_binding(fingerprint, terminal_code)

            # Map reason codes to user-friendly messages
            error_messages = {
                'TERMINAL_NOT_FOUND': '收银终端不存在或终端标识不匹配',
                'TERMINAL_DISABLED': '收银终端已停用',
                'CERTIFICATE_NOT_CONFIGURED': '收银终端未配置客户端证书',
                'CERTIFICATE_MISMATCH': '客户端证书与终端不匹配'
            }

            return JsonResponse({
                'success': True,
                'valid': result['valid'],
                'fingerprint': fingerprint,
                'reason': result.get('reason'),
                'terminal_id': result.get('terminal_id'),
                'message': '证书验证通过' if result['valid'] else error_messages.get(result.get('reason'), '证书验证失败')
            })
        except ValueError as e:
            return JsonResponse({'success': False, 'message': f'证书解析失败: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'验证失败: {str(e)}'}, status=500)
