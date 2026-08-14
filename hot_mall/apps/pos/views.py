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
import uuid
import json
from decimal import Decimal
from goods.models import SKU
from .models import POSOrder, POSOrderItem, BarcodeScanner, SuspendedOrder, PromotionProduct
from users.models import User
from datetime import datetime, date, timedelta


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
        context = self.get_context_data()
        context['is_superuser'] = request.user.is_superuser
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
            
            # 检查商品保质期状态（仅用于信息显示，不阻止销售）
            is_valid, expiration_message = check_product_expiration(sku)
            
            return JsonResponse({
                'success': True,
                'sku': {
                    'id': sku.id,
                    'name': sku.name,
                    'caption': sku.caption,
                    'price': str(sku.price),
                    'stock': sku.stock,
                    'barcode': sku.barcode,
                    'default_image': sku.default_image.url if sku.default_image else '',
                    'expiration_date': str(sku.expiration_date) if sku.expiration_date else None,
                    'near_expiry_num': sku.near_expiry_num,
                    'expired_num': sku.expired_num,
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

        try:
            with transaction.atomic():
                # 生成订单号
                order_id = f"POS{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

                # 获取收银员（暂时使用第一个用户）
                cashier = User.objects.first()

                # 获取会员信息
                member = None
                member_discount_rate = Decimal('1.00')
                if member_id:
                    try:
                        member = User.objects.get(id=member_id)
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

                    sku = SKU.objects.get(id=sku_id)
                    original_price = sku.price
                    
                    # 检查库存是否充足（考虑过期和临保质期商品）
                    available_stock = sku.stock - sku.expired_num - sku.near_expiry_num
                    if quantity > available_stock:
                        return JsonResponse({
                            'success': False, 
                            'message': f'商品 {sku.name} 库存不足。需要：{quantity}，可用库存：{available_stock}（总库存：{sku.stock}，过期商品：{sku.expired_num}，临保质期商品：{sku.near_expiry_num}）'
                        })
                    
                    # 检查商品促销
                    promotion = PromotionProduct.objects.filter(
                        sku=sku, 
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
                    cashier=cashier,
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

                    # 扣减库存（使用乐观锁防止超卖）
                    while True:
                        origin_stock = sku.stock
                        origin_near_expiry = sku.near_expiry_num
                        origin_expired = sku.expired_num
                        new_stock = origin_stock - quantity
                        new_sales = sku.sales + quantity

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

                        # 乐观锁更新库存、销量和临保质期/过期数量
                        ret = SKU.objects.filter(
                            id=sku.id, 
                            stock=origin_stock,
                            near_expiry_num=origin_near_expiry,
                            expired_num=origin_expired
                        ).update(
                            stock=new_stock,
                            sales=new_sales,
                            near_expiry_num=new_near_expiry,
                            expired_num=new_expired
                        )

                        if ret > 0:
                            break  # 更新成功

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
            sku = SKU.objects.get(id=sku_id)
            if sku.stock < int(quantity):
                return JsonResponse({
                    'success': False,
                    'message': f'库存不足，当前库存: {sku.stock}'
                })

            return JsonResponse({'success': True, 'stock': sku.stock})
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
            order = POSOrder.objects.get(order_id=order_id)
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
            order = POSOrder.objects.get(order_id=order_id)
            order_items = order.items.all()

            # 生成小票内容
            receipt_content = f"""
================================
           HOT MALL 收银小票
================================
订单号: {order.order_id}
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
        cart_data = request.POST.get('cart_data', '[]')
        remark = request.POST.get('remark', '')
        member_id = request.POST.get('member_id', '')

        try:
            cart = json.loads(cart_data)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': '购物车数据格式错误'})

        if not cart:
            return JsonResponse({'success': False, 'message': '购物车为空'})

        try:
            # 获取收银员（暂时使用第一个用户）
            cashier = User.objects.first()

            # 计算总金额和商品数量
            total_amount = Decimal('0')
            total_count = 0

            for item in cart:
                quantity = item.get('quantity', 1)
                price = Decimal(str(item.get('price', 0)))
                total_amount += price * quantity
                total_count += quantity

            member = None
            if member_id:
                member = User.objects.filter(id=member_id).first()

            # 创建挂单
            suspended_order = SuspendedOrder.objects.create(
                cashier=cashier,
                member=member,
                total_count=total_count,
                total_amount=total_amount,
                cart_data=cart_data,
                remark=remark
            )

            return JsonResponse({
                'success': True,
                'suspended_order_id': suspended_order.id,
                'message': '挂单成功'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'挂单失败: {str(e)}'})


@method_decorator(csrf_exempt, name='dispatch')
class GetSuspendedOrdersView(LoginRequiredMixin, View):
    """获取挂单列表"""

    @method_decorator(require_http_methods(["GET"]))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        try:
            # 获取收银员（暂时使用第一个用户）
            cashier = User.objects.first()

            # 获取该收银员的挂单列表
            suspended_orders = SuspendedOrder.objects.filter(cashier=cashier).order_by('-create_time')

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

        try:
            suspended_order = SuspendedOrder.objects.get(id=suspended_order_id)

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

        try:
            suspended_order = SuspendedOrder.objects.get(id=suspended_order_id)
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
            # 构建查询条件（已修复排序问题）
            order_items = POSOrderItem.objects.select_related('order', 'sku').order_by('-order__create_time')

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
            # 构建查询条件（已修复排序问题）
            orders = POSOrder.objects.order_by('-create_time')

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
class UpdateOrderStatusView(View):
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
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'message': f'促销商品“{sku_name}”已删除。'})
