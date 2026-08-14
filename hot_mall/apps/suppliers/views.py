from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView,View
from django.urls import reverse_lazy
from .models import Supplier, SupplierPurchaseRecord, SupplierImage
from django.http import JsonResponse
from hot_mall.utils.views import LoginRequiredJSONMixin
from django.core.files import File
from django.core.files.storage import default_storage
from django.db.models import Q
import logging
import os
import uuid
import json
import datetime

logger = logging.getLogger('django')

# 临时图片存储目录（和商品保持一致）
TEMP_UPLOAD_PREFIX = 'tmp/supplier_uploads/'


def _save_temp_image(uploaded_file):
    """保存临时供应商图片，返回存储路径与可访问URL。"""
    unique_name = f'{uuid.uuid4().hex}_{uploaded_file.name}'
    temp_path = default_storage.save(f'{TEMP_UPLOAD_PREFIX}{unique_name}', uploaded_file)
    temp_url = default_storage.url(temp_path)
    return temp_path, temp_url


def _consume_temp_images(supplier, temp_paths):
    """将临时图片转存为 SupplierImage 并删除临时文件。"""
    for temp_path in temp_paths:
        if not temp_path or not str(temp_path).startswith(TEMP_UPLOAD_PREFIX):
            continue
        if not default_storage.exists(temp_path):
            continue
        with default_storage.open(temp_path, 'rb') as fp:
            file_name = os.path.basename(temp_path)
            supplier_image = SupplierImage()
            supplier_image.supplier = supplier
            supplier_image.image.save(file_name, File(fp), save=True)
        default_storage.delete(temp_path)

class SupplierListView(LoginRequiredMixin, ListView):
    """供应商列表"""
    model = Supplier
    template_name = 'supplier_list.html'
    context_object_name = 'suppliers'
    ordering = ['-create_time']
    paginate_by = 10

    def get_queryset(self):
        return Supplier.objects.all().order_by("-create_time")

    def get_context_data(self,** kwargs):
        context = super().get_context_data(** kwargs)
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'supplier-update'

        # 组装前端需要的结构化数据
        data_list = []
        for supplier in context["suppliers"]:
            if supplier.create_time:
                create_time_str = supplier.create_time.strftime("%Y-%m-%d %H:%M")
            else:
                create_time_str = ""
            data_list.append({
                "id": supplier.id,
                "supl_name": supplier.supl_name or "",
                "supl_phone": supplier.supl_phone or "",
                "wechat": supplier.wechat or "",
                "supl_addr": supplier.supl_addr or "",
                "level": supplier.level or "",
                "business_license": supplier.business_license or "",
                "create_time": create_time_str
            })

        # 转为JSON字符串，传给模板（解决特殊字符问题）
        context["supplier_json"] = json.dumps(data_list, ensure_ascii=False)
        return context




class SupplierCreateView(LoginRequiredMixin, CreateView):
    """创建供应商"""
    model = Supplier
    fields = ['supl_name', 'supl_addr', 'supl_phone', 'wechat', 'business_license', 'level']
    template_name = 'supplier_add.html'
    success_url = reverse_lazy('suppliers:supplier_list')


    def get_context_data(self,** kwargs):
        context = super().get_context_data(** kwargs)
        context['title'] = '新增供应商'
        context['supplier_images'] = []
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'supplier-add'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        supplier = self.object

        # 处理图片上传
        images = self.request.FILES.getlist('images')
        temp_images = self.request.POST.getlist('temp_uploaded_images')

        created_images = []
        if images:
            for img in images:
                sup_img = SupplierImage.objects.create(supplier=supplier, image=img)
                created_images.append(sup_img)

        if temp_images:
            _consume_temp_images(supplier, temp_images)
            new_images = SupplierImage.objects.filter(supplier=supplier).order_by('-id')[:len(temp_images)]
            created_images.extend(new_images)

        # 设置第一张为默认图片
        if not supplier.default_image and created_images:
            supplier.default_image = created_images[0].image
            supplier.save()

        messages.success(self.request, f'供应商 "{supplier.supl_name}" 创建成功！')
        return response



class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    """更新供应商"""
    model = Supplier
    fields = ['supl_name', 'supl_addr', 'supl_phone', 'wechat', 'business_license', 'level']
    template_name = 'supplier_add.html'
    success_url = reverse_lazy('suppliers:supplier_list')


    def get_context_data(self,** kwargs):
        context = super().get_context_data(** kwargs)
        context['title'] = '修改供应商'
        context['supplier'] = self.object
        context['is_superuser'] = self.request.user.is_superuser
        context['supplier_images'] = SupplierImage.objects.filter(supplier=self.object)
        context['left_menu_active'] = 'supplier-update'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        supplier = self.object

        # 处理图片上传
        images = self.request.FILES.getlist('images')
        temp_images = self.request.POST.getlist('temp_uploaded_images')

        created_images = []
        if images:
            for img in images:
                sup_img = SupplierImage.objects.create(supplier=supplier, image=img)
                created_images.append(sup_img)

        if temp_images:
            _consume_temp_images(supplier, temp_images)
            new_images = SupplierImage.objects.filter(supplier=supplier).order_by('-id')[:len(temp_images)]
            created_images.extend(new_images)

        # 设置第一张为默认图片
        if not supplier.default_image and created_images:
            supplier.default_image = created_images[0].image
            supplier.save()

        messages.success(self.request, f'供应商 "{supplier.supl_name}" 更新成功！')
        return response

    def form_invalid(self, form):
        """补充：表单验证失败时的提示（可选）"""
        messages.error(self.request, '表单填写有误，请检查后重新提交！')
        return super().form_invalid(form)

class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    """删除供应商"""
    model = Supplier
    success_url = reverse_lazy('suppliers:supplier_list')

    # 关键：禁用默认的删除确认页面
    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        # 获取对象并删除
        supplier = get_object_or_404(Supplier, pk=kwargs.get('pk'))
        SupplierImage.objects.filter(supplier=supplier).delete()
        supplier.delete()

        # AJAX 请求 → 返回 JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"status": "success", "msg": "删除成功"})

        # 普通请求 → 跳回列表
        return redirect(self.success_url)

# ------------------------------------------------------------------------------
# 供应商图片核心功能（完全仿照 SKU 写法）
# ------------------------------------------------------------------------------

class SetSupplierDefaultImageView(LoginRequiredJSONMixin, UpdateView):
    """设置供应商默认图片"""
    model = Supplier

    def post(self, request, supplier_id, image_id):
        # 检查是否是 AJAX 请求
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            supplier = get_object_or_404(Supplier, pk=supplier_id)
            image = get_object_or_404(SupplierImage, pk=image_id, supplier=supplier)

            supplier.default_image = image.image
            supplier.save()

            return JsonResponse({
                'status': 'success',
                'message': '默认图片已更新'
            })
        return JsonResponse({
            'status': 'error',
            'message': '无效的请求'
        }, status=400)


class SupplierImageUploadView(LoginRequiredJSONMixin, View):
    """供应商图片上传：临时存储 / 直接保存"""
    def post(self, request):
        if request.headers.get('x-requested-with') != 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': '无效的请求'}, status=400)

        images = request.FILES.getlist('images')
        if not images:
            return JsonResponse({'status': 'error', 'message': '未选择图片'}, status=400)

        supplier_id = request.POST.get('supplier_id')
        uploaded_items = []

        if supplier_id:
            supplier = get_object_or_404(Supplier, pk=supplier_id)
            for img in images:
                sup_img = SupplierImage.objects.create(supplier=supplier, image=img)
                uploaded_items.append({
                    'type': 'saved',
                    'id': sup_img.id,
                    'name': sup_img.image.name,
                    'url': sup_img.image.url,
                    'supplier_id': supplier.id,
                    'is_default': bool(supplier.default_image and supplier.default_image.name == sup_img.image.name),
                    'delete_url': reverse('suppliers:image_delete', kwargs={'pk': sup_img.id})
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


class SupplierImageDeleteView(LoginRequiredMixin, View):
    """删除单张供应商图片（完全仿照 SKU 图片删除逻辑）"""

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
        logger.info(f'用户 {request.user.id} 尝试删除供应商图片，图片ID: {pk}')

        # 1. 查询图片（不存在则返回404）
        try:
            image = SupplierImage.objects.select_related('supplier').get(pk=pk)
        except SupplierImage.DoesNotExist:
            logger.warning(f'删除图片失败：图片ID {pk} 不存在')
            return JsonResponse(
                {'status': 'error', 'message': '图片不存在'},
                status=404
            )

        supplier = image.supplier
        # 3. 若删除的是默认图片，清空默认图片设置
        default_image_updated = False
        if supplier.default_image and supplier.default_image.name == image.image.name:
            supplier.default_image = None
            supplier.save(update_fields=['default_image'])
            default_image_updated = True
            logger.info(f'供应商 {supplier.id} 默认图片已清空（因删除图片ID {pk}）')

        # 4. 安全删除图片
        try:
            # 删除文件
            if image.image and default_storage.exists(image.image.name):
                default_storage.delete(image.image.name)
            # 删除数据库记录
            image.delete()
            logger.info(f'图片ID {pk} 删除成功（供应商 ID: {supplier.id}）')

        except Exception as e:
            logger.error(f'删除图片ID {pk} 失败：{str(e)}', exc_info=True)
            return JsonResponse(
                {'status': 'error', 'message': '图片删除失败，请重试'},
                status=500
            )

        return JsonResponse({
            'status': 'success',
            'message': '图片已删除',
            'data': {'supplier_id': supplier.id, 'cleared_default_image': default_image_updated}
        })

    # 兼容表单POST提交
    post = delete

# ---------------------
# 进货记录列表
# ---------------------
class PurchaseRecordListView(LoginRequiredMixin, ListView):
    model = SupplierPurchaseRecord
    template_name = 'purchase_record_upd.html'
    context_object_name = 'records'
    paginate_by = 10

    def get_queryset(self):
        return SupplierPurchaseRecord.objects.select_related('supplier')

    def get_context_data(self,** kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '进货记录管理'
        context['left_menu_active'] = 'purchase-update'
        context['is_superuser'] = self.request.user.is_superuser
        return context

# ---------------------
# 添加进货记录
# ---------------------
class PurchaseRecordCreateView(LoginRequiredMixin, CreateView):
    model = SupplierPurchaseRecord
    fields = ['supplier', 'product_name', 'product_spec', 'barcode', 'production_date', 'shelf_life', 'expiration_date', 'purchase_num', 'qualified_num', 'near_expiry_num', 'damaged_num', 'purchase_price', 'total_price', 'purchase_time', 'operator', 'remark']
    template_name = 'purchase_record_add.html'
    success_url = reverse_lazy('suppliers:purchase_list')

    def get_context_data(self,** kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '添加进货记录'
        context['purchase'] = None
        context['suppliers'] = Supplier.objects.all()
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'purchase-add'
        return context

    def form_valid(self, form):
        messages.success(self.request, '进货记录添加成功！')
        return super().form_valid(form)


class PurchaseRecordUpdateView(LoginRequiredMixin, UpdateView):
    """修改进货记录"""
    model = SupplierPurchaseRecord
    fields = [
        'supplier', 'product_name', 'product_spec', 'barcode', 'production_date', 'shelf_life', 'expiration_date',
        'purchase_num', 'qualified_num', 'near_expiry_num', 'damaged_num', 'purchase_price', 'total_price',
        'purchase_time', 'operator', 'remark'
    ]
    template_name = 'purchase_record_add.html'
    success_url = reverse_lazy('suppliers:purchase_list')

    def get_context_data(self,** kwargs):
        context = super().get_context_data(** kwargs)
        context['title'] = '修改进货记录'
        context['suppliers'] = Supplier.objects.all()
        context['purchase'] = self.object
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'purchase-update'
        return context

    def form_valid(self, form):
        record = form.save()
        messages.success(self.request, f'进货记录已更新！')
        return super().form_valid(form)


class PurchaseRecordDeleteView(LoginRequiredMixin, DeleteView):
    """删除进货记录"""
    model = SupplierPurchaseRecord
    success_url = reverse_lazy('suppliers:purchase_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        record = get_object_or_404(SupplierPurchaseRecord, pk=kwargs.get('pk'))
        record.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"status": "success", "msg": "删除成功"})

        return redirect(self.success_url)


class SearchSKUByBarcodeView(View):
    """通过条码搜索SKU商品"""
    def get(self, request):
        barcode = request.GET.get('barcode', '').strip()
        if not barcode:
            return JsonResponse({'success': False, 'message': '条码不能为空'})

        try:
            from goods.models import SKU
            sku = SKU.objects.get(barcode=barcode)
            return JsonResponse({
                'success': True,
                'sku': {
                    'id': sku.id,
                    'name': sku.name,
                    'barcode': sku.barcode,
                    'caption': sku.caption if sku.caption else '',
                }
            })
        except SKU.DoesNotExist:
            return JsonResponse({'success': False, 'message': '未找到该条码对应的商品'})
        except Exception as e:
            logger.error(f'SKU search error: {str(e)}')
            return JsonResponse({'success': False, 'message': f'查询失败: {str(e)}'})


class SearchSKUByNameView(View):
    """通过商品名称搜索SKU商品"""
    def get(self, request):
        name = request.GET.get('name', '').strip()
        if not name or len(name) < 2:
            return JsonResponse({'success': False, 'message': '商品名称至少需要2个字符'})

        try:
            from goods.models import SKU
            # 尝试精确匹配
            sku = SKU.objects.filter(name__icontains=name).first()
            if sku:
                return JsonResponse({
                    'success': True,
                    'sku': {
                        'id': sku.id,
                        'name': sku.name,
                        'barcode': sku.barcode,
                        'caption': sku.caption if sku.caption else '',
                    }
                })
            else:
                return JsonResponse({'success': False, 'message': '未找到匹配的商品'})
        except Exception as e:
            logger.error(f'SKU name search error: {str(e)}')
            return JsonResponse({'success': False, 'message': f'查询失败: {str(e)}'})