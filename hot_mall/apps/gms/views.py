# from django.contrib.auth.models import User

from contents.utils import get_categories
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files import File
from django.core.files.storage import default_storage
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from goods.models import SKU, GoodsVisitCount, SKUImage, GoodsCategory
from goods.utils import get_breadcrumb
from orders.models import OrderGoods
from orders.models import OrderInfo
from users import constants
from users.utils import generate_verify_email_url, check_verify_email_token
from hot_mall.utils.views import LoginRequiredJSONMixin

import logging
import os
import uuid

logger = logging.getLogger('django')

TEMP_UPLOAD_PREFIX = 'tmp/sku_uploads/'


def _save_temp_image(uploaded_file):
    """保存临时图片，返回存储路径与可访问URL。"""
    unique_name = f'{uuid.uuid4().hex}_{uploaded_file.name}'
    temp_path = default_storage.save(f'{TEMP_UPLOAD_PREFIX}{unique_name}', uploaded_file)
    temp_url = default_storage.url(temp_path)
    return temp_path, temp_url


def _consume_temp_images(sku, temp_paths):
    """将临时图片转存为SKUImage并删除临时文件。"""
    for temp_path in temp_paths:
        if not temp_path or not str(temp_path).startswith(TEMP_UPLOAD_PREFIX):
            continue
        if not default_storage.exists(temp_path):
            continue
        with default_storage.open(temp_path, 'rb') as fp:
            file_name = os.path.basename(temp_path)
            sku_image = SKUImage()
            sku_image.sku = sku
            sku_image.image.save(file_name, File(fp), save=True)
        default_storage.delete(temp_path)


class SKUListView(LoginRequiredMixin, ListView):
    """返回纯前端页面"""
    model = SKU
    template_name = 'user_center_gms.html'

    def get(self, request):
        return render(request, self.template_name, {
            'left_menu_active': 'gms',
            'is_superuser': request.user.is_superuser
        })


class SKUListAPIView(LoginRequiredMixin, ListView):
    """返回JSON数据接口（优化版）"""
    model = SKU
    paginate_by = 10  # 每页数量
    # 关闭默认的模板渲染（因为是接口）
    template_name = None

    def get_queryset(self):
        """优化查询逻辑：1. 关键词过滤 2. 关联查询优化（减少数据库查询）"""
        queryset = super().get_queryset()
        # 预加载category，避免N+1查询问题
        queryset = queryset.select_related('category').order_by('id')

        # 关键词过滤（条码/名称）
        # keyword = self.request.GET.get('keyword', '').strip()
        keyword = self.request.GET.get('Q', self.request.GET.get('keyword', '')).strip()
        if keyword:
            queryset = queryset.filter(
                Q(barcode__icontains=keyword) | Q(name__icontains=keyword)
            )
        return queryset

    def get_paginated_response(self, page_obj):
        """重构数据构造逻辑：更简洁、健壮"""

        # 构造单条SKU数据
        def serialize_sku(sku):
            # 处理图片URL：兼容开发/生产环境
            image_url = None
            if sku.default_image:
                image_url = sku.default_image.url

            return {
                'id': sku.id,
                'name': sku.name,
                'category__name': sku.category.name,
                'price': sku.price,
                'cost_price': sku.cost_price,
                'market_price': sku.market_price,
                'stock': sku.stock,
                'sales': sku.sales,
                'comments': sku.comments,
                'is_launched': sku.is_launched,
                'production_date': sku.production_date.isoformat() if sku.production_date else None,
                'shelf_life': sku.shelf_life,
                'expiration_date': sku.expiration_date.isoformat() if sku.expiration_date else None,
                'barcode': sku.barcode,
                'near_expiry_num': sku.near_expiry_num,
                'expired_num': sku.expired_num,
                'default_image_url': image_url
            }

        # 构造分页数据
        return {
            'results': [serialize_sku(sku) for sku in page_obj.object_list],
            'current_page': page_obj.number,
            'total_pages': page_obj.paginator.num_pages,
            'count': page_obj.paginator.count,
            'page_size': self.paginate_by
        }

    def get(self, request, *args, **kwargs):
        """简化get方法：复用ListView内置的分页逻辑"""
        # 1. 获取查询集
        queryset = self.get_queryset()

        # 2. 使用ListView内置的分页处理（无需手动实例化Paginator）
        context = self.get_context_data(object_list=queryset)

        # 3. 提取分页对象
        page_obj = context.get('page_obj')

        # 4. 构造并返回JSON数据
        data = self.get_paginated_response(page_obj)
        return JsonResponse(data, safe=True)


# 添加商品
class SKUCreateView(LoginRequiredMixin, CreateView):
    model = SKU
    template_name = 'user_center_sku.html'
    fields = ['name', 'caption', 'spu', 'category', 'price', 'cost_price', 'market_price', 'stock', 'sales', 'comments',
              'is_launched', 'production_date', 'shelf_life', 'expiration_date', 'barcode', 'near_expiry_num', 'expired_num']
    success_url = reverse_lazy('gms:sku_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '添加商品'
        context['sku_images'] = []  # 添加时没有图片
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'gms_create'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        images = self.request.FILES.getlist('images')
        temp_images = self.request.POST.getlist('temp_uploaded_images')

        # 创建SKUImage记录
        created_images = []
        if images:
            for img in images:
                sku_image = SKUImage.objects.create(sku=self.object, image=img)
                created_images.append(sku_image)

        if temp_images:
            _consume_temp_images(self.object, temp_images)
            # 获取新创建的图片
            new_images = SKUImage.objects.filter(sku=self.object).order_by('-id')[:len(temp_images)]
            created_images.extend(new_images)

        # 如果商品没有默认图片且有上传的图片，设置第一张为默认图片
        if not self.object.default_image and created_images:
            self.object.default_image = created_images[0].image
            self.object.save()

        return response


# 修改商品
class SKUDetailView(LoginRequiredMixin, UpdateView):
    model = SKU
    template_name = 'user_center_sku.html'
    fields = ['name', 'caption', 'spu', 'category', 'price', 'cost_price', 'market_price', 'stock', 'sales', 'comments',
              'is_launched', 'production_date', 'shelf_life', 'expiration_date', 'barcode', 'near_expiry_num', 'expired_num']
    success_url = reverse_lazy('gms:sku_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '修改商品'
        context['sku_images'] = self.object.skuimage_set.all()
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'gms-update'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        images = self.request.FILES.getlist('images')
        temp_images = self.request.POST.getlist('temp_uploaded_images')

        # 创建SKUImage记录
        created_images = []
        if images:
            for img in images:
                sku_image = SKUImage.objects.create(sku=self.object, image=img)
                created_images.append(sku_image)

        if temp_images:
            _consume_temp_images(self.object, temp_images)
            # 获取新创建的图片
            new_images = SKUImage.objects.filter(sku=self.object).order_by('-id')[:len(temp_images)]
            created_images.extend(new_images)

        # 如果商品没有默认图片且有上传的图片，设置第一张为默认图片
        if not self.object.default_image and created_images:
            self.object.default_image = created_images[0].image
            self.object.save()

        return response


# 删除商品
class SKUDeleteView(LoginRequiredMixin, DeleteView):
    model = SKU
    success_url = reverse_lazy('gms:sku_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.skuimage_set.all().delete()  # 删除关联图片
        messages.success(request, f"商品“{self.object.name}”已删除。")
        return super().delete(request, *args, **kwargs)


# 设置默认图片
class SetDefaultImageView(LoginRequiredJSONMixin, UpdateView):
    """设置商品默认图片"""
    model = SKU

    def post(self, request, sku_id, image_id):
        # 检查是否是 AJAX 请求
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            sku = get_object_or_404(SKU, pk=sku_id)
            image = get_object_or_404(SKUImage, pk=image_id, sku=sku)

            sku.default_image = image.image
            sku.save()

            return JsonResponse({
                'status': 'success',
                'message': '默认图片已更新'
            })
        return JsonResponse({
            'status': 'error',
            'message': '无效的请求'
        }, status=400)


class SKUImageUploadView(LoginRequiredJSONMixin, UpdateView):
    """上传图片：有sku_id时立即创建SKUImage，否则临时存储。"""
    model = SKU

    def post(self, request):
        if request.headers.get('x-requested-with') != 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': '无效的请求'}, status=400)

        images = request.FILES.getlist('images')
        if not images:
            return JsonResponse({'status': 'error', 'message': '未选择图片'}, status=400)

        sku_id = request.POST.get('sku_id')
        uploaded_items = []

        if sku_id:
            sku = get_object_or_404(SKU, pk=sku_id)
            for img in images:
                sku_img = SKUImage.objects.create(sku=sku, image=img)
                uploaded_items.append({
                    'type': 'saved',
                    'id': sku_img.id,
                    'name': sku_img.image.name,
                    'url': sku_img.image.url,
                    'sku_id': sku.id,
                    'is_default': bool(sku.default_image and sku.default_image.name == sku_img.image.name),
                    'delete_url': reverse_lazy('gms:image_delete', kwargs={'pk': sku_img.id})
                })
        else:
            for img in images:
                temp_path, temp_url = _save_temp_image(img)
                uploaded_items.append({
                    'type': 'temp',
                    'temp_path': temp_path,
                    'name': img.name,
                    'url': temp_url,
                    'is_default': False,
                })

        return JsonResponse({'status': 'success', 'items': uploaded_items})


# 删除单张图片
# 删除单张图片
class SKUImageDeleteView(LoginRequiredMixin, View):
    """删除单张图片（优化版）"""

    def dispatch(self, request, *args, **kwargs):
        """统一处理请求方法：支持 DELETE + 表单模拟 DELETE (POST + _method=DELETE)"""
        # 兼容表单提交的 DELETE 请求（通过 _method 字段）
        if request.method == 'POST' and request.POST.get('_method') == 'DELETE':
            request.method = 'DELETE'
        # 仅允许 DELETE/POST 方法（POST 仅用于表单模拟 DELETE）
        if request.method not in ['DELETE', 'POST']:
            return JsonResponse(
                {'status': 'error', 'message': '仅支持 DELETE/POST 方法'},
                status=405
            )
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, pk):
        """处理图片删除（标准 DELETE 请求 + 表单模拟 DELETE）"""
        logger.info(f'用户 {request.user.id} 尝试删除 SKU 图片，图片ID: {pk}')

        # 1. 查询图片（不存在则返回404）
        try:
            image = SKUImage.objects.select_related('sku').get(pk=pk)
        except SKUImage.DoesNotExist:
            logger.warning(f'删除图片失败：图片ID {pk} 不存在')
            return JsonResponse(
                {'status': 'error', 'message': '图片不存在'},
                status=404
            )

        sku = image.sku
        # 3. 若删除的是默认图片，清空默认图片设置
        default_image_updated = False
        if sku.default_image and sku.default_image.name == image.image.name:
            sku.default_image = None
            sku.save(update_fields=['default_image'])
            default_image_updated = True
            logger.info(f'SKU {sku.id} 默认图片已清空（因删除图片ID {pk}）')

        # 4. 安全删除图片
        try:
            # 删除文件
            if image.image and default_storage.exists(image.image.name):
                default_storage.delete(image.image.name)
            # 删除数据库记录
            image.delete()
            logger.info(f'图片ID {pk} 删除成功（SKU ID: {sku.id}）')

        except Exception as e:
            logger.error(f'删除图片ID {pk} 失败：{str(e)}', exc_info=True)
            return JsonResponse(
                {'status': 'error', 'message': '图片删除失败，请重试'},
                status=500
            )

        return JsonResponse({
            'status': 'success',
            'message': '图片已删除',
            'data': {'sku_id': sku.id, 'cleared_default_image': default_image_updated}
        })

    # 兼容表单POST提交
    post = delete


class SKUExpiryView(LoginRequiredMixin, ListView):
    """临近保质期商品页面"""
    model = SKU
    template_name = 'user_center_expiry.html'
    paginate_by = 10

    def get_queryset(self):
        """筛选临近保质期的商品：到期日期 - 当前日期 <= 15天"""
        from datetime import date, timedelta

        queryset = super().get_queryset()
        queryset = queryset.select_related('category').order_by('id')

        # 获取当前日期
        today = date.today()

        # 智能下架过期和临保质期商品：只有当库存 <= 临期数量 + 过期数量时才下架
        skus_to_delist = []
        for sku in queryset:
            days_remaining = None
            expiry_date = None

            if sku.production_date and sku.shelf_life:
                # 有生产日期和保质期的情况
                expiry_date = sku.production_date + timedelta(days=sku.shelf_life)
                days_remaining = (expiry_date - today).days
            elif sku.expiration_date:
                # 没有生产日期但有expiration_date的情况
                expiry_date = sku.expiration_date
                days_remaining = (expiry_date - today).days

            # 检查是否需要下架：已过期或临保质期（2天内）且库存不足
            if days_remaining is not None and days_remaining <= 2:
                # 检查库存是否充足：库存 > 临期数量 + 过期数量
                if sku.stock <= (sku.near_expiry_num + sku.expired_num):
                    if sku.is_launched:
                        skus_to_delist.append(sku)

        # 批量下架商品
        if skus_to_delist:
            SKU.objects.filter(id__in=[sku.id for sku in skus_to_delist]).update(is_launched=False)

        # 筛选条件：生产日期和保质期都不为空，且到期日期在15天内
        # 或者：生产日期为空但有expiration_date不为空，且当前日期 <= expiration_date + 7天
        expiry_skus = []
        for sku in queryset:
            days_remaining = None
            expiry_date = None

            if sku.production_date and sku.shelf_life:
                # 有生产日期和保质期的情况
                expiry_date = sku.production_date + timedelta(days=sku.shelf_life)
                days_remaining = (expiry_date - today).days
                # 筛选条件：剩余天数 <= 15 且 >= 0（未过期）
                if 0 <= days_remaining <= 15:
                    expiry_skus.append(sku)
            elif sku.expiration_date:
                # 没有生产日期但有expiration_date的情况
                expiry_date = sku.expiration_date
                days_remaining = (expiry_date - today).days
                # 筛选条件：当前日期 <= expiration_date + 7天 且 >= 0（未过期）
                if 0 <= days_remaining <= 7:
                    expiry_skus.append(sku)

        # 返回筛选后的商品，按到期日期升序排列
        return sorted(expiry_skus, key=lambda x: (
            x.production_date + timedelta(days=x.shelf_life) if x.production_date and x.shelf_life
            else x.expiration_date
        ))

    def get_context_data(self, **kwargs):
        """构造分页数据"""
        context = super().get_context_data(**kwargs)
        page_obj = context.get('page_obj')

        # 确保分页对象存在，即使没有数据
        if not page_obj:
            # 如果没有分页对象，创建一个空的
            from django.core.paginator import Paginator, Page
            paginator = Paginator([], self.paginate_by)
            page_obj = Page([], 1, paginator)

        def serialize_sku(sku):
            from datetime import date, timedelta

            # 处理图片URL
            image_url = None
            if sku.default_image:
                image_url = sku.default_image.url

            # 计算到期信息
            days_remaining = None
            expiry_date = None
            if sku.production_date and sku.shelf_life:
                expiry_date = sku.production_date + timedelta(days=sku.shelf_life)
                days_remaining = (expiry_date - date.today()).days
            elif sku.expiration_date:
                expiry_date = sku.expiration_date
                days_remaining = (expiry_date - date.today()).days

            return {
                'id': sku.id,
                'name': sku.name,
                'category__name': sku.category.name,
                'price': sku.price,
                'cost_price': sku.cost_price,
                'market_price': sku.market_price,
                'stock': sku.stock,
                'sales': sku.sales,
                'comments': sku.comments,
                'is_launched': sku.is_launched,
                'production_date': sku.production_date.isoformat() if sku.production_date else None,
                'shelf_life': sku.shelf_life,
                'expiration_date': sku.expiration_date.isoformat() if sku.expiration_date else None,
                'barcode': sku.barcode,
                'near_expiry_num': sku.near_expiry_num,
                'expired_num': sku.expired_num,
                'default_image_url': image_url,
                'expiry_date': expiry_date.isoformat() if expiry_date else None,
                'days_remaining': days_remaining
            }

        # 构造分页数据
        context.update({
            'skuList': [serialize_sku(sku) for sku in page_obj.object_list],
            'page_num': page_obj.number,
            'total_page': page_obj.paginator.num_pages,
            'left_menu_active': 'gms-expiry',
            'is_superuser': self.request.user.is_superuser
        })
        return context
