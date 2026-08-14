from django.conf import settings
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from datetime import datetime
from goods.utils import get_breadcrumb
from hot_mall.utils.views import LoginRequiredJSONMixin
from hot_mall.utils.response_code import RETCODE
from contents.utils import get_categories
from django.http import HttpResponseForbidden, HttpResponseNotFound, JsonResponse, HttpResponseServerError
from django.utils import timezone  # 处理时间
from orders.models import OrderGoods
from .models import SKU, GoodsVisitCount, SKUImage, GoodsCategory, Brand, SPU, SPUSpecification, SpecificationOption, SKUSpecification, GoodsChannel, GoodsChannelGroup
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.core.files import File
from django.core.files.storage import default_storage
import logging
import os
import uuid

logger = logging.getLogger('django')

# 临时图片存储目录（和SKU保持一致）
TEMP_UPLOAD_PREFIX = 'tmp/brand_uploads/'


def _save_temp_image(uploaded_file):
    """保存临时品牌图片，返回存储路径与可访问URL。"""
    unique_name = f'{uuid.uuid4().hex}_{uploaded_file.name}'
    temp_path = default_storage.save(f'{TEMP_UPLOAD_PREFIX}{unique_name}', uploaded_file)
    temp_url = default_storage.url(temp_path)
    return temp_path, temp_url
# Create your views here.
class GoodsCommentView(View):
    """订单商品评价信息"""

    def get(self, request, sku_id):
        # 获取被评价的订单商品信息
        order_goods_list = OrderGoods.objects.filter(sku_id=sku_id, is_commented=True).order_by('-create_time')[:30]
        # 序列化
        comment_list = []
        for order_goods in order_goods_list:
            username = order_goods.order.user.username
            comment_list.append({
                'username': username[0] + '***' + username[-1]
                if order_goods.is_anonymous else username,
                'comment': order_goods.comment,
                'score': order_goods.score,
            })
            # print('评价信息')
            # print(comment_list)
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'comment_list': comment_list})


class DetailVisitView(View):
    """统计分类商品访问量"""

    def post(self, request, category_id):
        """记录分类商品访问量"""
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return HttpResponseForbidden('缺少必传参数')

        # 获取今天的日期
        t = timezone.localtime()
        today_str = '%d-%02d-%02d' % (t.year, t.month, t.day)
        today_date = datetime.strptime(today_str, '%Y-%m-%d')
        try:
            # 查询今天该类别的商品的访问量
            counts_data = category.goodsvisitcount_set.get(date=today_date)
        except GoodsVisitCount.DoesNotExist:
            # 如果该类别的商品在今天没有过访问记录，就新建一个访问记录
            counts_data = GoodsVisitCount()

        try:
            counts_data.category = category
            counts_data.count += 1
            counts_data.save()
        except Exception as e:
            logger.error(e)
            return HttpResponseServerError('服务器异常')

        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class DetailView(View):
    """商品详情页"""

    def get(self, request, sku_id):
        """提供商品详情页"""
        # 获取当前sku的信息
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request, '404.html')

        # 查询商品频道分类
        categories = get_categories()
        # 查询面包屑导航
        breadcrumb = get_breadcrumb(sku.category)

        # 构建当前商品的规格键
        sku_specs = sku.specs.order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option.id)
        # 获取当前商品的所有SKU
        skus = sku.spu.sku_set.all()
        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')
            # 用于形成规格参数-sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数-sku字典添加记录
            spec_sku_map[tuple(key)] = s.id
        # 获取当前商品的规格信息
        goods_specs = sku.spu.specs.order_by('id')
        # 若当前sku的规格信息不完整，则不再继续
        if len(sku_key) < len(goods_specs):
            return render(request, '404.html')
        for index, spec in enumerate(goods_specs):
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options

        # 渲染页面
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'specs': goods_specs,

            # 商品数量
            'stock': sku.stock
        }
        return render(request, 'detail.html', context)


class GoodsListView(View):
    """商品列表页"""

    def get(self, request, category_id, page_num):
        """查询并渲染商品列表页"""
        # 校验参数
        try:
            # 三级类别
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return HttpResponseForbidden("参数category_id不存在")
        # 获取sort（排序规则）  如果sort没有值，取default
        sort = request.GET.get('sort', 'default')
        # 根据sort选择排排序字段, 排序字段必须是模型类的属性
        if sort == 'price':  # 按照价格由低到高排序
            sort_field = 'price'
        elif sort == 'hot':
            sort_field = '-sales'  # 按照销量由高到低排序
        else:  # 只要不是price和-sales其他的所有情况都归为default
            sort = 'default'
            sort_field = 'create_time'
        # 查询商品分类
        categories = get_categories()
        # 查询面包屑导航：一级 ==>二级==>一级
        breadcrumb = get_breadcrumb(category)

        # 分页和排序查询 category查询sku 一查多
        skus = category.sku_set.filter(is_launched=True).order_by(sort_field)
        # 创建分页器
        # Paginator('要分页的记录','每页记录的条数')
        paginator = Paginator(skus, 5)  # 把skus进行分页，每页5条记录
        # 需要获取用户当前要看的那一页
        try:
            page_skus = paginator.page(page_num)  # 获取到page_num页中的5条记录
        except EmptyPage:
            return HttpResponseNotFound('Empty Page')
        # 获取总页数: 前端的分页插件需要使用
        total_page = paginator.num_pages
        # 构造上下文
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'page_skus': page_skus,
            'total_page': total_page,
            'page_num': page_num,
            'sort': sort,
            'category_id': category_id,
        }
        return render(request, 'list.html', context)


class HotGoodsView(View):
    """热销排行"""

    def get(self, request, category_id):
        # 要查询指定分类的sku信息，而且必须是一个上架转态，然后按照由高到低排序，最后切片取出前两位
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]
        # 将模型列表转字典构造json数据
        hot_skus = []

        for sku in skus:
            sku_dict = {
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url if sku.default_image else ''
            }
            hot_skus.append(sku_dict)
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_skus': hot_skus})


class SKUBarcodeSearchView(View):
    """按条码精确搜索商品"""

    def get(self, request):
        """按条码搜索商品，返回单个商品或空"""
        barcode = request.GET.get('q', '').strip()
        if not barcode:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '请输入条码'})

        try:
            sku = SKU.objects.get(barcode=barcode, is_launched=True)
            sku_dict = {
                'id': sku.id,
                'name': sku.name,
                'price': str(sku.price),
                'default_image_url': sku.default_image.url if sku.default_image else '',
                'stock': sku.stock,
            }
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sku': sku_dict})
        except SKU.DoesNotExist:
            return JsonResponse({'code': RETCODE.NODATA, 'errmsg': '未找到该条码对应的商品'})
        except SKU.MultipleObjectsReturned:
            # 条码不唯一时返回第一个匹配的商品
            sku = SKU.objects.filter(barcode=barcode, is_launched=True).first()
            sku_dict = {
                'id': sku.id,
                'name': sku.name,
                'price': str(sku.price),
                'default_image_url': sku.default_image.url if sku.default_image else '',
                'stock': sku.stock,
            }
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sku': sku_dict})


class BarcodeSearchView(View):
    """按条码搜索商品页面"""

    def get(self, request):
        barcode = request.GET.get('q', '').strip()

        if not barcode:
            return render(request, 'search/barcode_search.html', {
                'sku': None,
                'barcode': '',
                'error': '请输入条码',
            })

        # 精确查找商品
        try:
            sku = SKU.objects.get(barcode=barcode, is_launched=True)
            return render(request, 'search/barcode_search.html', {
                'sku': sku,
                'barcode': barcode,
            })
        except SKU.DoesNotExist:
            # 条码不唯一时返回第一个匹配的商品
            sku = SKU.objects.filter(barcode=barcode, is_launched=True).first()
            if sku:
                return render(request, 'search/barcode_search.html', {
                    'sku': sku,
                    'barcode': barcode,
                })
            # 未找到商品
            return render(request, 'search/barcode_search.html', {
                'sku': None,
                'barcode': barcode,
                'error': '未找到该条码对应的商品',
            })


class AutoSearchView(View):
    """自动判断搜索类型：条码模糊匹配 或 名称全文搜索"""

    def get(self, request):
        q = request.GET.get('q', '').strip()
        if not q:
            # 空搜索使用 Haystack 搜索页面
            from haystack.views import SearchView
            return SearchView()(request)

        # 判断是否为纯数字（可能是条码）
        if q.isdigit():
            # 尝试按条码模糊匹配（包含查询）
            sku = SKU.objects.filter(barcode__contains=q, is_launched=True).first()
            if sku:
                # 找到商品，跳转到详情页
                return redirect('goods:detail', sku.id)

        # 默认使用 Haystack 名称搜索
        from haystack.views import SearchView
        return SearchView()(request)


# ============ Brand Management Views ============
class BrandListView(LoginRequiredMixin, ListView):
    """品牌列表"""
    model = Brand
    template_name = 'brand_update.html'
    context_object_name = 'brands'
    ordering = ['-create_time']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'brand-update'
        return context


class BrandCreateView(LoginRequiredMixin, CreateView):
    """创建品牌"""
    model = Brand
    fields = ['name', 'logo', 'first_letter']
    template_name = 'brand_add.html'
    success_url = reverse_lazy('goods:brand_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '新增品牌'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'brand-add'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'品牌 "{self.object.name}" 创建成功！')
        return response


class BrandUpdateView(LoginRequiredMixin, UpdateView):
    """更新品牌"""
    model = Brand
    fields = ['name', 'logo', 'first_letter']
    template_name = 'brand_add.html'
    success_url = reverse_lazy('goods:brand_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '编辑品牌'
        context['brand'] = self.object
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'brand-update'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'品牌 "{self.object.name}" 更新成功！')
        return response

    def form_invalid(self, form):
        messages.error(self.request, '表单填写有误，请检查后重新提交！')
        return super().form_invalid(form)


class BrandDeleteView(LoginRequiredMixin, DeleteView):
    """删除品牌"""
    model = Brand
    success_url = reverse_lazy('goods:brand_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        brand = get_object_or_404(Brand, pk=kwargs.get('pk'))
        brand.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"status": "success", "msg": "删除成功"})

        return redirect(self.success_url)


# ============ GoodsCategory Management Views ============
class GoodsCategoryListView(LoginRequiredMixin, ListView):
    """商品类别列表"""
    model = GoodsCategory
    template_name = 'goods_category_update.html'
    context_object_name = 'categories'
    ordering = ['-create_time']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'goods_category'
        return context


class GoodsCategoryCreateView(LoginRequiredMixin, CreateView):
    """创建商品类别"""
    model = GoodsCategory
    fields = ['name', 'parent']
    template_name = 'goods_category_add.html'
    success_url = reverse_lazy('goods:goods_category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '新增商品类别'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'goods_category-add'
        context['all_categories'] = GoodsCategory.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'商品类别 "{self.object.name}" 创建成功！')
        return response


class GoodsCategoryUpdateView(LoginRequiredMixin, UpdateView):
    """更新商品类别"""
    model = GoodsCategory
    fields = ['name', 'parent']
    template_name = 'goods_category_add.html'
    success_url = reverse_lazy('goods:goods_category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '编辑商品类别'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'goods_category'
        context['all_categories'] = GoodsCategory.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'商品类别 "{self.object.name}" 更新成功！')
        return response

    def form_invalid(self, form):
        messages.error(self.request, '表单填写有误，请检查后重新提交！')
        return super().form_invalid(form)


class GoodsCategoryDeleteView(LoginRequiredMixin, DeleteView):
    """删除商品类别"""
    model = GoodsCategory
    success_url = reverse_lazy('goods:goods_category_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        category = get_object_or_404(GoodsCategory, pk=kwargs.get('pk'))
        category.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"status": "success", "msg": "删除成功"})

        return redirect(self.success_url)


# ============ GoodsChannelGroup Management Views ============
class GoodsChannelGroupListView(LoginRequiredMixin, ListView):
    """商品频道组列表"""
    model = GoodsChannelGroup
    template_name = 'channel_group_update.html'
    context_object_name = 'channel_groups'
    ordering = ['-create_time']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'channel_group'
        return context


class GoodsChannelGroupCreateView(LoginRequiredMixin, CreateView):
    """创建商品频道组"""
    model = GoodsChannelGroup
    fields = ['name']
    template_name = 'channel_group_add.html'
    success_url = reverse_lazy('goods:channel_group_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '新增频道组'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'channel_group-add'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'频道组 "{self.object.name}" 创建成功！')
        return response


class GoodsChannelGroupUpdateView(LoginRequiredMixin, UpdateView):
    """更新商品频道组"""
    model = GoodsChannelGroup
    fields = ['name']
    template_name = 'channel_group_add.html'
    success_url = reverse_lazy('goods:channel_group_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '编辑频道组'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'channel_group'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'频道组 "{self.object.name}" 更新成功！')
        return response

    def form_invalid(self, form):
        messages.error(self.request, '表单填写有误，请检查后重新提交！')
        return super().form_invalid(form)


class GoodsChannelGroupDeleteView(LoginRequiredMixin, DeleteView):
    """删除商品频道组"""
    model = GoodsChannelGroup
    success_url = reverse_lazy('goods:channel_group_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        group = get_object_or_404(GoodsChannelGroup, pk=kwargs.get('pk'))
        group.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"status": "success", "msg": "删除成功"})

        return redirect(self.success_url)


# ============ GoodsChannel Management Views ============
class GoodsChannelListView(LoginRequiredMixin, ListView):
    """商品频道列表"""
    model = GoodsChannel
    template_name = 'channel_update.html'
    context_object_name = 'channels'
    ordering = ['-create_time']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'channel'
        return context


class GoodsChannelCreateView(LoginRequiredMixin, CreateView):
    """创建商品频道"""
    model = GoodsChannel
    fields = ['group', 'category', 'url', 'sequence']
    template_name = 'channel_add.html'
    success_url = reverse_lazy('goods:channel_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '新增频道'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'channel-add'
        context['groups'] = GoodsChannelGroup.objects.all()
        context['categories'] = GoodsCategory.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'频道 "{self.object.category.name}" 创建成功！')
        return response


class GoodsChannelUpdateView(LoginRequiredMixin, UpdateView):
    """更新商品频道"""
    model = GoodsChannel
    fields = ['group', 'category', 'url', 'sequence']
    template_name = 'channel_add.html'
    success_url = reverse_lazy('goods:channel_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '编辑频道'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'channel'
        context['groups'] = GoodsChannelGroup.objects.all()
        context['categories'] = GoodsCategory.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'频道 "{self.object.category.name}" 更新成功！')
        return response

    def form_invalid(self, form):
        messages.error(self.request, '表单填写有误，请检查后重新提交！')
        return super().form_invalid(form)


class GoodsChannelDeleteView(LoginRequiredMixin, DeleteView):
    """删除商品频道"""
    model = GoodsChannel
    success_url = reverse_lazy('goods:channel_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        channel = get_object_or_404(GoodsChannel, pk=kwargs.get('pk'))
        channel.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"status": "success", "msg": "删除成功"})

        return redirect(self.success_url)


# ============ SPU Management Views ============
class SPUListView(LoginRequiredMixin, ListView):
    """SPU列表"""
    model = SPU
    template_name = 'spu_update.html'
    context_object_name = 'spus'
    ordering = ['-create_time']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'spu'
        return context


class SPUCreateView(LoginRequiredMixin, CreateView):
    """创建SPU"""
    model = SPU
    fields = ['name', 'brand', 'category1', 'category2', 'category3', 'sales', 'comments', 'desc_detail', 'desc_pack', 'desc_service']
    template_name = 'spu_add.html'
    success_url = reverse_lazy('goods:spu_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '新增SPU'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'spu-add'
        context['brands'] = Brand.objects.all()
        context['categories'] = GoodsCategory.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'SPU "{self.object.name}" 创建成功！')
        return response


class SPUUpdateView(LoginRequiredMixin, UpdateView):
    """更新SPU"""
    model = SPU
    fields = ['name', 'brand', 'category1', 'category2', 'category3', 'sales', 'comments', 'desc_detail', 'desc_pack', 'desc_service']
    template_name = 'spu_add.html'
    success_url = reverse_lazy('goods:spu_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '编辑SPU'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'spu'
        context['brands'] = Brand.objects.all()
        context['categories'] = GoodsCategory.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'SPU "{self.object.name}" 更新成功！')
        return response

    def form_invalid(self, form):
        messages.error(self.request, '表单填写有误，请检查后重新提交！')
        return super().form_invalid(form)


class SPUDetailView(LoginRequiredMixin, UpdateView):
    """SPU详情（用于查看和编辑）"""
    model = SPU
    fields = ['name', 'brand', 'category1', 'category2', 'category3', 'sales', 'comments', 'desc_detail', 'desc_pack', 'desc_service']
    template_name = 'spu_detail.html'
    success_url = reverse_lazy('goods:spu_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = Brand.objects.all()
        context['categories'] = GoodsCategory.objects.all()
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'spu'
        return context


class SPUDeleteView(LoginRequiredMixin, DeleteView):
    """删除SPU"""
    model = SPU
    success_url = reverse_lazy('goods:spu_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        spu = get_object_or_404(SPU, pk=kwargs.get('pk'))
        spu.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"status": "success", "msg": "删除成功"})

        return redirect(self.success_url)


# ============ SPUSpecification Management Views ============
class SPUSpecificationListView(LoginRequiredMixin, ListView):
    """SPU规格列表"""
    model = SPUSpecification
    template_name = 'spu_specification_update.html'
    context_object_name = 'specs'
    ordering = ['-create_time']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'spu_specification'
        return context


class SPUSpecificationCreateView(LoginRequiredMixin, CreateView):
    """创建SPU规格"""
    model = SPUSpecification
    fields = ['spu', 'name']
    template_name = 'spu_specification_add.html'
    success_url = reverse_lazy('goods:spu_specification_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '新增SPU规格'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'spu_specification-add'
        context['spus'] = SPU.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'SPU规格 "{self.object.name}" 创建成功！')
        return response


class SPUSpecificationUpdateView(LoginRequiredMixin, UpdateView):
    """更新SPU规格"""
    model = SPUSpecification
    fields = ['spu', 'name']
    template_name = 'spu_specification_add.html'
    success_url = reverse_lazy('goods:spu_specification_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '编辑SPU规格'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'spu_specification'
        context['spus'] = SPU.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'SPU规格 "{self.object.name}" 更新成功！')
        return response

    def form_invalid(self, form):
        messages.error(self.request, '表单填写有误，请检查后重新提交！')
        return super().form_invalid(form)


class SPUSpecificationDeleteView(LoginRequiredMixin, DeleteView):
    """删除SPU规格"""
    model = SPUSpecification
    success_url = reverse_lazy('goods:spu_specification_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        spec = get_object_or_404(SPUSpecification, pk=kwargs.get('pk'))
        spec.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"status": "success", "msg": "删除成功"})

        return redirect(self.success_url)


# ============ SpecificationOption Management Views ============
class SpecificationOptionListView(LoginRequiredMixin, ListView):
    """规格选项列表"""
    model = SpecificationOption
    template_name = 'specification_option_update.html'
    context_object_name = 'options'
    ordering = ['-create_time']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'specification_option'
        return context


class SpecificationOptionCreateView(LoginRequiredMixin, CreateView):
    """创建规格选项"""
    model = SpecificationOption
    fields = ['spec', 'value']
    template_name = 'specification_option_add.html'
    success_url = reverse_lazy('goods:specification_option_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '新增规格选项'
        context['is_superuser'] = self.request.user.is_superuser
        context['specs'] = SPUSpecification.objects.all()
        context['left_menu_active'] = 'specification_option-add'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'规格选项 "{self.object.value}" 创建成功！')
        return response


class SpecificationOptionUpdateView(LoginRequiredMixin, UpdateView):
    """更新规格选项"""
    model = SpecificationOption
    fields = ['spec', 'value']
    template_name = 'specification_option_add.html'
    success_url = reverse_lazy('goods:specification_option_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '编辑规格选项'
        context['specs'] = SPUSpecification.objects.all()
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'specification_option'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'规格选项 "{self.object.value}" 更新成功！')
        return response

    def form_invalid(self, form):
        messages.error(self.request, '表单填写有误，请检查后重新提交！')
        return super().form_invalid(form)


class SpecificationOptionDeleteView(LoginRequiredMixin, DeleteView):
    """删除规格选项"""
    model = SpecificationOption
    success_url = reverse_lazy('goods:specification_option_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        option = get_object_or_404(SpecificationOption, pk=kwargs.get('pk'))
        option.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"status": "success", "msg": "删除成功"})

        return redirect(self.success_url)


# ============ SKUSpecification Management Views ============
class SKUSpecificationListView(LoginRequiredMixin, ListView):
    """SKU规格列表"""
    model = SKUSpecification
    template_name = 'sku_specification_update.html'
    context_object_name = 'sku_specs'
    ordering = ['-create_time']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'sku_specification'
        return context


class SKUSpecificationCreateView(LoginRequiredMixin, CreateView):
    """创建SKU规格"""
    model = SKUSpecification
    fields = ['sku', 'spec', 'option']
    template_name = 'sku_specification_add.html'
    success_url = reverse_lazy('goods:sku_specification_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '新增SKU规格'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'sku_specification-add'
        context['skus'] = SKU.objects.all()
        context['specs'] = SPUSpecification.objects.all()
        context['options'] = SpecificationOption.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'SKU规格创建成功！')
        return response


class SKUSpecificationUpdateView(LoginRequiredMixin, UpdateView):
    """更新SKU规格"""
    model = SKUSpecification
    fields = ['sku', 'spec', 'option']
    template_name = 'sku_specification_add.html'
    success_url = reverse_lazy('goods:sku_specification_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skus'] = SKU.objects.all()
        context['specs'] = SPUSpecification.objects.all()
        context['options'] = SpecificationOption.objects.all()
        context['title'] = '编辑SKU规格'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'sku_specification'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'SKU规格更新成功！')
        return response

    def form_invalid(self, form):
        messages.error(self.request, '表单填写有误，请检查后重新提交！')
        return super().form_invalid(form)


class SKUSpecificationDeleteView(LoginRequiredMixin, DeleteView):
    """删除SKU规格"""
    model = SKUSpecification
    success_url = reverse_lazy('goods:sku_specification_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        sku_spec = get_object_or_404(SKUSpecification, pk=kwargs.get('pk'))
        sku_spec.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"status": "success", "msg": "删除成功"})

        return redirect(self.success_url)
