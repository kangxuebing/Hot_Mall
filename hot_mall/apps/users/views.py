import re, json

# from django.contrib.auth.models import User

from django.conf import settings
from .face_utils import decode_base64_image, encode_face_from_image, save_face_encoding, find_user_by_face
from django.db import DatabaseError
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django_redis import get_redis_connection
from .models import User, Address
from django.http import HttpResponseForbidden,JsonResponse, HttpResponseBadRequest, HttpResponseServerError,HttpResponseNotFound
from hot_mall.utils.response_code import RETCODE
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from hot_mall.utils.views import LoginRequiredJSONMixin
from celery_tasks.email.tasks import send_verify_email
from users.utils import generate_verify_email_url, check_verify_email_token
from . import constants
from carts.utils import merge_carts_cookies_redis
from datetime import datetime
from goods.utils import get_breadcrumb
from contents.utils import get_categories
from django.utils import timezone  # 处理时间
from orders.models import OrderGoods
from goods.models import SKU, GoodsVisitCount, SKUImage, GoodsCategory
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from orders.models import OrderInfo
from django.core.paginator import Paginator, EmptyPage



import logging
logger = logging.getLogger('django')



class UserOrderInfoView(LoginRequiredMixin, View):
    def get(self, request, page_num):
        """提供我的订单页面"""
        user = request.user
        # 查询订单
        orders = user.orderinfo_set.all().order_by("-create_time")
        # 遍历所有订单
        for order in orders:
            # 绑定订单状态
            order.status_name = OrderInfo.ORDER_STATUS_CHOICES[order.status - 1][1]
            # 绑定支付方式
            order.pay_method_name = OrderInfo.PAY_METHOD_CHOICES[order.pay_method - 1][1]
            order.sku_list = []
            # 查询订单商品
            order_goods = order.skus.all()
            # 遍历订单商品
            for order_good in order_goods:
                sku = order_good.sku
                sku.count = order_good.count
                sku.amount = sku.price * sku.count
                order.sku_list.append(sku)

        # 分页
        page_num = int(page_num)
        try:
            paginator = Paginator(orders, constants.ORDERS_LIST_LIMIT)
            page_orders = paginator.page(page_num)
            total_page = paginator.num_pages
        except EmptyPage:
            return HttpResponseNotFound('订单不存在')

        context = {
            "page_orders": page_orders,
            'total_page': total_page,
            'page_num': page_num,
            'is_superuser': request.user.is_superuser,
            'left_menu_active': 'order'  # 高亮
        }
        return render(request, "user_center_order.html", context)


class UserBrowseHistory(LoginRequiredJSONMixin, View):
    """用户浏览记录"""

    def post(self, request):
        """保存用户商品浏览记录"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        # 校验参数
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return HttpResponseForbidden('sku不存在')
        # 保存sku_id到redis
        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()
        user_id = request.user.id
        # 先去重
        pl.lrem('history_%s' % user_id, 0, sku_id)
        # 再存储
        pl.lpush('history_%s' % user_id, sku_id)
        # 最后截取
        pl.ltrim('history_%s' % user_id, 0, 4)
        # 执行管道
        pl.execute()
        # 响应结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

    """用户浏览记录"""

    def get(self, request):
        """获取用户浏览记录"""
        # 获取Redis存储的sku_id列表信息
        redis_conn = get_redis_connection('history')
        sku_ids = redis_conn.lrange('history_%s' % request.user.id, 0, -1)
        # 根据sku_ids列表数据，查询出商品sku信息
        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url if sku.default_image else '',
                'price': sku.price
            })
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'skus': skus})


class ChangePasswordView(LoginRequiredMixin, View):
    """修改密码"""

    def get(self, request):
        """展示修改密码界面"""
        context = {'is_superuser': request.user.is_superuser,
            'left_menu_active': 'pass'  # 高亮
                   }
        return render(request, 'user_center_pass.html', context)

    def post(self, request):
        """实现修改密码逻辑"""
        # 接收参数
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        new_password2 = request.POST.get('new_password2')
        # 校验参数
        if not all([old_password, new_password, new_password2]):
            return render(request, 'user_center_pass.html', {
                'change_password_errmsg': '请填写当前密码、新密码与确认新密码',
                'is_superuser': request.user.is_superuser,
                'left_menu_active': 'pass',
            })
        try:
            if not request.user.check_password(old_password):
                return render(request, 'user_center_pass.html', {
                    'origin_password_errmsg': '原始密码错误',
                    'is_superuser': request.user.is_superuser,
                    'left_menu_active': 'pass',
                })
        except Exception as e:
            logger.error(e)
            return render(request, 'user_center_pass.html', {
                'origin_password_errmsg': '查询密码失败',
                'is_superuser': request.user.is_superuser,
                'left_menu_active': 'pass',
            })
        if not constants.USER_PASSWORD_REGEX.match(new_password):
            return render(request, 'user_center_pass.html', {
                'change_password_errmsg': '密码须为8-20位可打印字符，且含数字、小写、大写及特殊符号（如@、_）',
                'is_superuser': request.user.is_superuser,
                'left_menu_active': 'pass',
            })
        if new_password != new_password2:
            return render(request, 'user_center_pass.html', {
                'change_password_errmsg': '两次输入的新密码不一致',
                'is_superuser': request.user.is_superuser,
                'left_menu_active': 'pass',
            })
        # 修改密码
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:
            logger.error(e)
            return render(request, 'user_center_pass.html', {
                'change_password_errmsg': '修改密码失败',
                'is_superuser': request.user.is_superuser,
                'left_menu_active': 'pass',
            })
        # 清理状态保持信息
        logout(request)
        response = redirect(reverse('users:login'))
        response.delete_cookie('username')
        # 响应密码修改结果：重定向到登录界面
        return response


class UpdateTitleAddressView(LoginRequiredJSONMixin, View):
    """设置地址标题"""

    def put(self, request, address_id):
        """设置地址标题"""
        json_dict = json.loads(request.body.decode())  # 接收参数：地址标题
        title = json_dict.get('title')
        try:
            address = Address.objects.get(id=address_id)  # 查询地址
            address.title = title  # 设置新的地址标题
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置地址标题失败'})
        # 响应删除地址结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '设置地址标题成功'})


class DefaultAddressView(LoginRequiredJSONMixin, View):
    """设置默认地址"""

    def put(self, request, address_id):
        """设置默认地址"""
        try:
            address = Address.objects.get(id=address_id)  # 接收参数,查询地址
            request.user.default_address = address  # 设置地址为默认地址
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})
        # 响应设置默认地址结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})


class UpdateDestroyAddressView(LoginRequiredJSONMixin, View):
    def put(self, request, address_id):
        """修改地址"""
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return HttpResponseForbidden('参数email有误')
        # 判断地址是否存在,并更新地址信息
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user, title=receiver, receiver=receiver,
                province_id=province_id, city_id=city_id, place=place,
                district_id=district_id, mobile=mobile, tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '更新地址失败'})
        # 构造响应数据
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id, "title": address.title,
            "receiver": address.receiver, "province": address.province.name,
            "city": address.city.name, "district": address.district.name,
            "place": address.place, "mobile": address.mobile,
            "tel": address.tel, "email": address.email
        }
        # 响应更新地址结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '更新地址成功', 'address': address_dict})

    def delete(self, request, address_id):
        """删除地址"""
        default_address_id = request.user.default_address_id
        try:
            address = Address.objects.get(id=address_id)
            if default_address_id == address.id:
                request.user.default_address_id = None
                request.user.save()
            address.is_deleted = True
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '删除地址失败'})
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})


class AddressView(LoginRequiredMixin, View):
    """展示地址"""

    def get(self, request):
        """提供收货地址界面"""
        login_user = request.user  # 获取当前登录用户对象
        addresses = Address.objects.filter(user=login_user, is_deleted=False)
        address_list = []  # 将用户地址模型列表转字典列表
        for address in addresses:
            address_dict = {
                "id": address.id, "title": address.title,
                "receiver": address.receiver, "city": address.city.name,
                "province": address.province.name, "place": address.place,
                "district": address.district.name, "tel": address.tel,
                "mobile": address.mobile, "email": address.email
            }
            address_list.append(address_dict)
        context = {
            'default_address_id': login_user.default_address_id or '0',
            'addresses': address_list,
            'is_superuser': request.user.is_superuser,
            'left_menu_active': 'address'  # 高亮
        }
        return render(request, 'user_center_site.html', context)


class AddressCreateView(LoginRequiredJSONMixin, View):
    """新增地址"""

    def post(self, request):
        count = request.user.addresses.filter(is_deleted__exact=False).count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return JsonResponse({"code": RETCODE.THROTTLINGERR, 'errmsg': "超出用户地址上限"})
        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return HttpResponseForbidden('参数email有误')
        # 保存用户传入的地址信息
        try:
            address = Address.objects.create(
                user=request.user, title=receiver, receiver=receiver,
                province_id=province_id, place=place, tel=tel,
                city_id=city_id, district_id=district_id,
                mobile=mobile, email=email
            )
            # 设置默认地址
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '新增地址失败'})
        # 新增地址成功，将新增的地址响应给前端实现局部刷新 构造新增地址字典数据
        address_dict = {
            "id": address.id, "title": address.title,
            "receiver": address.receiver, "province": address.province.name,
            "city": address.city.name, "district": address.district.name,
            "place": address.place, "mobile": address.mobile,
            "tel": address.tel, "email": address.email
        }
        # 响应新增地址结果：需要将新增的地址返回给前端渲染
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '新增地址成功', 'address': address_dict})


class VerifyEmailView(View):
    """验证邮箱"""

    def get(self, request):
        token = request.GET.get('token')  # 接收参数
        if not token:  # 校验参数
            return HttpResponseForbidden('缺少token')
        user = check_verify_email_token(token)  # 从token中提取用户信息
        if not user:
            return HttpResponseBadRequest('无效的token')
        try:
            user.email_active = True  # 将用户的email_active 设置为true
            user.save()
        except Exception as e:
            logger.error(e)
            return HttpResponseServerError('激活邮箱失败')
        # 响应结果：重定向到用户中心
        return redirect(reverse('users:info'))


class EmailView(LoginRequiredJSONMixin, View):
    """添加邮箱"""

    def put(self, request):
        """实现添加邮箱逻辑"""
        # 接收参数 body 类型是bytes类型
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        email = json_dict.get('email')
        if not email:  # 2.校验参数
            return HttpResponseForbidden('缺少email参数')
        if not re.match(r'^[a-z0-9][\w\\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return HttpResponseForbidden('参数email有误')
            # 赋值email字段
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '添加邮箱失败'})
        # 异步发送验证邮件
        # verify_url = '邮件验证链接'
        verify_url = generate_verify_email_url(request.user)
        send_verify_email.delay(email, verify_url)

        # 响应添加邮箱结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})


class UserInfoView(LoginRequiredMixin, View):
    """用户中心"""

    def get(self, request):
        """提供用户中心页面"""
        context = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active,
            'is_superuser': request.user.is_superuser,
            'left_menu_active': 'info'  # 高亮
        }
        return render(request, 'user_center_info.html', context=context)


class LogoutView(View):
    """用户退出登录"""

    def get(self, request):
        # 清除状态保持信息
        logout(request)
        # 响应结果 重定向到首页
        response = redirect(reverse('contents:index'))
        # 删除cookie中的用户名
        response.delete_cookie('username')
        return response


class LoginView(View):
    """用户名登录"""

    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        # 接收参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')
        # 校验参数
        if not all([username, password]):
            return HttpResponseForbidden('缺少必传参数')
        # 判断用户名是否是5-20个字符
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return HttpResponseForbidden('请输入正确的用户名或手机号')
        # 登录密码仅做长度限制（与注册/修改密码允许的符号一致，如 @、_ 等）
        if len(password) < 8 or len(password) > 128:
            return HttpResponseForbidden('密码长度应在 8～128 位之间')
        # 认证登录用户
        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '账号或密码错误'})
        login(request, user)  # 实现状态保持
        if remembered != 'on':  # 设置状态保持的周期
            request.session.set_expiry(0)  # 没有记住用户：浏览器会话结束就过期
        else:
            request.session.set_expiry(None)  # 记住用户：None表示两周后过期
        # return redirect(reverse('contents:index')) # 响应登录结果
        # 响应登录结果
        # 先取出next
        next = request.GET.get('next')
        if next:
            # 重定向到next
            response = redirect(next)
        else:
            response = redirect(reverse('contents:index'))
        # 登录时用户名写入到cookie，有效期15天
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
        response = merge_carts_cookies_redis(request=request, user=user, response=response)
        return response


class MoblieCountView(View):
    def get(self, request, mobile):
        """
        :param mobile: 手机号码
        :return:json
        """
        # 接收输入的手机号码
        count = User.objects.filter(mobile=mobile).count()
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', "count": count})


class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        """
        :param request: 请求对象
        :param username: 用户名
        :return: JSON
        """
        count = User.objects.filter(username=username).count()
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """提供用户注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        """实现用户注册业务逻辑"""
        username = request.POST.get("username")  # 用户名
        password = request.POST.get("password")  # 密码
        password2 = request.POST.get("password2")  # 确认密码
        mobile = request.POST.get("mobile")  # 手机号
        sms_code_client = request.POST.get('sms_code')  # 短信验证码
        allow = request.POST.get("allow")  # 是否同意协议
        if not all([username, password, password2, mobile, sms_code_client, allow]):
            # if not all([username, password, password2, mobile, allow]):
            # 返回403  禁止请求
            return HttpResponseForbidden("缺少必传参数")
        # 判断用户名是否是5-20个字符
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return HttpResponseForbidden("请输入5-20个字符的用户名")
        if not constants.USER_PASSWORD_REGEX.match(password):
            return HttpResponseForbidden(
                "密码须为8-20位可打印字符，且含数字、小写、大写及特殊符号（如@、_）"
            )
        # 判断两次输入的密码是否相同
        if password != password2:
            return HttpResponseForbidden("两次输入的密码不一致")
        # 判断手机号码是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden("您输入的手机号格式不正确")

        # 判断短信验证码是否输入正确
        redis_conn = get_redis_connection("verify_code")
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        if sms_code_server is None:
            return render(request, 'register.html', {"sms_code_errmsg": "短信验证码已失效"})
        if sms_code_client != sms_code_server.decode():
            return render(request, 'register.html', {"sms_code_errmsg": "输入短信验证码有误"})

        # 判断用户是否勾选协议
        if allow != 'on':
            return HttpResponseForbidden("请勾选用户协议")
        # 保存注册数据：是注册业务的核心
        try:
            #  注册成功的用户对象
            user = User.objects.create_user(username=username, mobile=mobile, password=password, )
        except DatabaseError:
            return render(request, 'register.html', {'register_errmsg': '注册失败'})
        login(request, user)  # 登入用户，实现状态保持
        # 响应登录结果:重定向到首页
        response = redirect(reverse('contents:index'))
        # 为了实现在首页右上角展示用户信息，我们需要将用户名缓存到cookie中
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)
        return response


class FaceRegisterView(LoginRequiredMixin, View):
    """人脸注册"""
    
    def get(self, request):
        """提供人脸注册页面"""
        context = {
            'username': request.user.username,
            'is_superuser': request.user.is_superuser,
            'left_menu_active': 'face-register'
        }
        return render(request, 'face_register.html', context)
    
    def post(self, request):
        """实现人脸注册逻辑"""
        user = request.user
        
        # 接收base64编码的图片数据
        image_data = request.POST.get('image_data')
        
        if not image_data:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '未接收到图片数据'})
        
        # 解码图片
        image = decode_base64_image(image_data)
        if image is None:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '图片解码失败'})
        
        # 提取人脸特征
        face_encoding = encode_face_from_image(image)
        if face_encoding is None:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '未检测到人脸或人脸特征提取失败'})
        
        # 保存人脸特征
        if save_face_encoding(user, face_encoding):
            return JsonResponse({'code': RETCODE.OK, 'errmsg': '人脸注册成功'})
        else:
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '人脸注册失败'})


class FaceLoginView(View):
    """人脸登录"""
    
    def get(self, request):
        """提供人脸登录页面"""
        return render(request, 'face_login.html')
    
    def post(self, request):
        """实现人脸登录逻辑"""
        # 接收base64编码的图片数据
        image_data = request.POST.get('image_data')
        
        if not image_data:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '未接收到图片数据'})
        
        # 解码图片
        image = decode_base64_image(image_data)
        if image is None:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '图片解码失败'})
        
        # 提取人脸特征
        face_encoding = encode_face_from_image(image)
        if face_encoding is None:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '未检测到人脸或人脸特征提取失败'})
        
        # 查找匹配的用户
        user = find_user_by_face(face_encoding)
        
        if user is None:
            return JsonResponse({'code': RETCODE.USERERR, 'errmsg': '未找到匹配的用户'})
        
        # 登录用户
        login(request, user)
        
        # 合并购物车
        from carts.utils import merge_carts_cookies_redis
        response = JsonResponse({'code': RETCODE.OK, 'errmsg': '登录成功', 'username': user.username})
        response = merge_carts_cookies_redis(request=request, user=user, response=response)
        
        # 设置cookie
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
        
        return response


class MemberListView(LoginRequiredMixin, ListView):
    """会员管理列表页面"""
    model = User
    template_name = 'user_center_member.html'

    def get(self, request):
        if not request.user.is_superuser:
            return HttpResponseForbidden('权限不足')
        return render(request, self.template_name, {
            'left_menu_active': 'member-list',
            'is_superuser': request.user.is_superuser
        })


class MemberListAPIView(LoginRequiredMixin, ListView):
    """会员管理列表API"""
    model = User
    paginate_by = 10
    template_name = None

    def get_queryset(self):
        """查询逻辑：支持关键词过滤"""
        queryset = super().get_queryset()
        # 关键词过滤（用户名/手机号）
        keyword = self.request.GET.get('keyword', '').strip()
        if keyword:
            queryset = queryset.filter(
                Q(username__icontains=keyword) | Q(mobile__icontains=keyword)
            )
        return queryset.order_by('-date_joined')

    def get_paginated_response(self, page_obj):
        """构造分页数据"""
        users = []
        for user in page_obj.object_list:
            users.append({
                'id': user.id,
                'username': user.username,
                'mobile': user.mobile,
                'email': user.email,
                'email_active': user.email_active,
                'member_level': user.member_level,
                'member_level_display': user.get_member_level_display(),
                'points': user.points,
                'discount_rate': str(user.discount_rate),
                'total_consume': str(user.total_consume),
                'is_active': user.is_active,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
            })

        return {
            'results': users,
            'current_page': page_obj.number,
            'total_pages': page_obj.paginator.num_pages,
            'count': page_obj.paginator.count,
            'page_size': self.paginate_by
        }

    def get(self, request, *args, **kwargs):
        """返回JSON数据"""
        queryset = self.get_queryset()
        context = self.get_context_data(object_list=queryset)
        page_obj = context.get('page_obj')
        data = self.get_paginated_response(page_obj)
        return JsonResponse(data, safe=True)


class MemberUpdateView(LoginRequiredMixin, UpdateView):
    """会员编辑页面"""
    model = User
    template_name = 'user_center_member_edit.html'
    fields = ['member_level', 'points', 'discount_rate']
    success_url = reverse_lazy('users:member_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden('权限不足')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '编辑会员信息'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'member-edit'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"会员“{self.object.username}”信息已更新。")
        return super().form_valid(form)


class MemberResetPasswordView(LoginRequiredMixin, View):
    """重置会员密码"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden('权限不足')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        
        # 支持JSON和表单数据两种格式
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            new_password = data.get('new_password')
        else:
            new_password = request.POST.get('new_password')
        
        if not new_password:
            return JsonResponse({'success': False, 'message': '请输入新密码'})
        
        if len(new_password) < 6:
            return JsonResponse({'success': False, 'message': '密码长度不能少于6位'})
        
        user.set_password(new_password)
        user.save()
        
        return JsonResponse({'success': True, 'message': f'用户{user.username}密码已重置'})





