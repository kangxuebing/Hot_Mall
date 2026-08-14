from django.shortcuts import render, get_object_or_404
import os
from django.views import View
from orders.models import OrderInfo
from alipay import AliPay
from hot_mall.utils.views import LoginRequiredJSONMixin
from hot_mall.utils.response_code import RETCODE
from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
from .models import Payment
import json
from hot_mall.utils.views import LoginRequiredMixin
from orders.models import OrderInfo, OrderGoods
from django.http import HttpResponseNotFound, HttpResponseServerError
from goods.models import SKU
from django.urls import reverse
import logging
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .wechat_pay import create_native_pay_code_url, decrypt_notify_resource, is_wechat_pay_configured

logger = logging.getLogger('django')


# Create your views here.
class OrderCommentView(LoginRequiredMixin, View):
    """订单商品评价"""

    def get(self, request):
        """展示商品评价页面"""
        # 接收参数
        order_id = request.GET.get('order_id')
        # 校验参数
        try:
            OrderInfo.objects.get(order_id=order_id, user=request.user)
        except OrderInfo.DoesNotExist:
            return HttpResponseNotFound('订单不存在')

        # 查询订单中未被评价的商品信息
        try:
            uncomment_goods = OrderGoods.objects.filter(order_id=order_id, is_commented=False)
        except Exception:
            return HttpResponseServerError('订单商品信息出错')

        # 构造待评价商品数据
        uncomment_goods_list = []
        for goods in uncomment_goods:
            uncomment_goods_list.append({
                # 订单号
                'order_id': goods.order.order_id,
                # 商品sku_id
                'sku_id': goods.sku.id,
                # 商品名称
                'name': goods.sku.name,
                # 商品价格
                'price': str(goods.price),
                # 商品图片
                'default_image_url': settings.STATIC_URL + 'images/goods/' + goods.sku.default_image.url + '.jpg',
                # 商品评价内容
                'comment': goods.comment,
                # 商品评分
                'score': goods.score,
                # 匿名用户
                'is_anonymous': str(goods.is_anonymous),
            })

        # 渲染模板
        context = {
            'uncomment_goods_list': uncomment_goods_list
        }
        return render(request, 'goods_judge.html', context)

    def post(self, request):
        """评价订单商品"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        order_id = json_dict.get('order_id')
        sku_id = json_dict.get('sku_id')
        score = json_dict.get('score')
        comment = json_dict.get('comment')
        is_anonymous = json_dict.get('is_anonymous')
        # 校验参数
        if not all([order_id, sku_id, score, comment]):
            return HttpResponseForbidden('缺少必传参数')
        try:
            OrderInfo.objects.filter(order_id=order_id, user=request.user,
                                     status=OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT'])
        except OrderInfo.DoesNotExist:
            return HttpResponseForbidden('参数order_id错误')
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return HttpResponseForbidden('参数sku_id错误')
        if is_anonymous:
            if not isinstance(is_anonymous, bool):
                return HttpResponseForbidden('参数is_anonymous错误')

        # 保存订单商品评价数据
        OrderGoods.objects.filter(order_id=order_id, sku_id=sku_id, is_commented=False).update(
            comment=comment,
            score=score,
            is_anonymous=is_anonymous,
            is_commented=True
        )

        # 累计评论数据
        sku.comments += 1
        sku.save()
        sku.spu.comments += 1
        sku.spu.save()

        # 如果所有订单商品都已评价，则修改订单状态为已完成
        if OrderGoods.objects.filter(order_id=order_id, is_commented=False).count() == 0:
            OrderInfo.objects.filter(order_id=order_id).update(status=OrderInfo.ORDER_STATUS_ENUM['FINISHED'])

        return JsonResponse({'code': RETCODE.OK, 'errmsg': '评价成功'})


class PaymentStatusView(View):
    """保存订单支付结果"""

    def get(self, request):
        query_dict = request.GET  # 获取前端传入的请求参数
        data = query_dict.dict()
        signature = data.pop('sign')  # 从请求参数中剔除signature

        # 创建支付宝支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_string=open(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem")).read(),
            alipay_public_key_string=open(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/alipay_public_key.pem")).read(),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )
        # 校验这个重定向是否是alipay重定向过来的
        success = alipay.verify(data, signature)
        if success:
            order_id = data.get('out_trade_no')  # 读取order_id
            trade_id = data.get('trade_no')  # 读取支付宝流水号
            # 保存Payment模型类数据
            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_id
            )
            # 修改订单状态为待评价
            OrderInfo.objects.filter(order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(
                status=OrderInfo.ORDER_STATUS_ENUM["UNCOMMENT"])
            # 响应trade_id
            context = {
                'trade_id': trade_id
            }

            return render(request, 'pay_success.html', context)
        else:
            # 订单支付失败，重定向到我的订单
            return HttpResponseForbidden('非法请求')


class PaymentView(LoginRequiredJSONMixin, View):
    """订单支付功能"""

    def get(self, request, order_id):
        user = request.user
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return HttpResponseForbidden('订单信息错误')

        if order.pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY']:
            alipay = AliPay(
                appid=settings.ALIPAY_APPID,
                app_notify_url=None,
                app_private_key_string=open(
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem")).read(),
                alipay_public_key_string=open(
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/alipay_public_key.pem")).read(),
                sign_type="RSA2",
                debug=settings.ALIPAY_DEBUG
            )
            order_string = alipay.api_alipay_trade_page_pay(
                out_trade_no=order_id,
                total_amount=str(order.total_amount),
                subject="肥猫商城%s" % order_id,
                return_url=settings.ALIPAY_RETURN_URL
            )
            alipay_url = settings.ALIPAY_URL + "?" + order_string
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'alipay_url': alipay_url})

        if order.pay_method == OrderInfo.PAY_METHODS_ENUM['WECHAT']:
            checkout_path = reverse('payment:wechat_checkout', kwargs={'order_id': order.order_id})
            wechat_pay_url = request.build_absolute_uri(checkout_path)
            return JsonResponse({
                'code': RETCODE.OK,
                'errmsg': 'OK',
                'pay_channel': 'wechat',
                'wechat_pay_url': wechat_pay_url,
            })

        return HttpResponseForbidden('该订单支付方式不支持在线支付')


class WeChatCheckoutView(LoginRequiredMixin, View):
    """微信支付收银台：演示模式或展示 Native 二维码。"""

    def get(self, request, order_id):
        order = get_object_or_404(
            OrderInfo,
            order_id=order_id,
            user=request.user,
            pay_method=OrderInfo.PAY_METHODS_ENUM['WECHAT'],
            status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'],
        )

        use_demo = getattr(settings, 'WECHAT_PAY_USE_DEMO', True)
        code_url = None
        wechat_error = None
        demo_mode = False

        if use_demo:
            demo_mode = True
        elif not is_wechat_pay_configured():
            wechat_error = '未配置微信商户参数，请在 settings 中填写 WECHAT_PAY_* 或开启 WECHAT_PAY_USE_DEMO'
        else:
            code_url, err = create_native_pay_code_url(order)
            if not code_url:
                wechat_error = err or '微信下单失败'

        qr_img_url = None
        if code_url:
            from urllib.parse import quote
            qr_img_url = (
                'https://api.qrserver.com/v1/create-qr-code/?size=220x220&data='
                + quote(code_url, safe='')
            )

        context = {
            'order_id': order.order_id,
            'payment_amount': order.total_amount,
            'demo_mode': demo_mode,
            'code_url': code_url,
            'qr_img_url': qr_img_url,
            'wechat_error': wechat_error,
        }
        return render(request, 'wechat_pay_checkout.html', context)


class WeChatDemoConfirmView(LoginRequiredMixin, View):
    """演示环境：模拟微信支付成功（仅 WECHAT_PAY_USE_DEMO=True 时可用）。"""

    @method_decorator(require_http_methods(['POST']))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, order_id):
        if not getattr(settings, 'WECHAT_PAY_USE_DEMO', True):
            return HttpResponseForbidden('演示支付已关闭，请使用真实微信回调完成支付')

        order = get_object_or_404(
            OrderInfo,
            order_id=order_id,
            user=request.user,
            pay_method=OrderInfo.PAY_METHODS_ENUM['WECHAT'],
        )
        if order.status != OrderInfo.ORDER_STATUS_ENUM['UNPAID']:
            pay = Payment.objects.filter(order=order).first()
            tid = pay.trade_id if pay else 'WECHAT_OK'
            return render(request, 'pay_success.html', {'trade_id': tid})

        trade_id = 'WECHAT_DEMO_' + order.order_id
        Payment.objects.get_or_create(
            order=order,
            defaults={'trade_id': trade_id},
        )
        OrderInfo.objects.filter(
            order_id=order.order_id,
            status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'],
        ).update(status=OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT'])

        context = {'trade_id': trade_id}
        return render(request, 'pay_success.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class WeChatNotifyView(View):
    """微信支付 APIv3 异步通知。"""

    def post(self, request):
        if not is_wechat_pay_configured():
            return JsonResponse({'code': 'FAIL', 'message': 'not configured'}, status=503)

        try:
            body = json.loads(request.body.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({'code': 'FAIL', 'message': 'bad json'}, status=400)

        if body.get('event_type') != 'TRANSACTION.SUCCESS':
            return JsonResponse({'code': 'SUCCESS', 'message': '成功'})

        resource = body.get('resource') or {}
        try:
            plain = decrypt_notify_resource(
                resource['ciphertext'],
                resource['nonce'],
                resource.get('associated_data') or '',
                settings.WECHAT_PAY_API_V3_KEY,
            )
        except Exception as e:
            logger.exception('微信通知解密失败: %s', e)
            return JsonResponse({'code': 'FAIL', 'message': 'decrypt error'}, status=400)

        if plain.get('trade_state') and plain.get('trade_state') != 'SUCCESS':
            return JsonResponse({'code': 'SUCCESS', 'message': '成功'})

        out_trade_no = plain.get('out_trade_no')
        transaction_id = plain.get('transaction_id')
        if not out_trade_no or not transaction_id:
            return JsonResponse({'code': 'FAIL', 'message': 'missing fields'}, status=400)

        updated = OrderInfo.objects.filter(
            order_id=out_trade_no,
            status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'],
        ).update(status=OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT'])
        if updated:
            try:
                order = OrderInfo.objects.get(order_id=out_trade_no)
            except OrderInfo.DoesNotExist:
                return JsonResponse({'code': 'FAIL', 'message': 'order missing'}, status=400)
            Payment.objects.get_or_create(
                order=order,
                defaults={'trade_id': transaction_id},
            )
        return JsonResponse({'code': 'SUCCESS', 'message': '成功'})
