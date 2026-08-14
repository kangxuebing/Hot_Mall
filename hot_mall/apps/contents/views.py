from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse

from contents.utils import get_categories
from collections import OrderedDict
from contents.models import ContentCategory, Content


class IndexView(View):
    def get(self, request):
        """提供首页广告页面"""
        categories = get_categories()
        # 查询首页广告数据
        # 查询所有的广告类别
        content_categories = ContentCategory.objects.all()
        # 使用广告类别查询出该类别对应的所有的广告内容
        contents = OrderedDict()
        for content_categorie in content_categories:
            contents[content_categorie.key] = content_categorie.content_set.filter(status=True).order_by(
                'sequence')  # 查询出未下架的广告并排序
        # 渲染模板的上下文
        context = {
            'categories': categories,
            'contents': contents,
        }
        return render(request, 'index.html', context)


# ============ ContentCategory Management Views ============
class ContentCategoryListView(LoginRequiredMixin, ListView):
    """广告内容类别列表"""
    model = ContentCategory
    template_name = 'content_category_update.html'
    context_object_name = 'content_categories'
    ordering = ['-create_time']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'content_category'
        return context


class ContentCategoryCreateView(LoginRequiredMixin, CreateView):
    """创建广告内容类别"""
    model = ContentCategory
    fields = ['name', 'key']
    template_name = 'content_category_add.html'
    success_url = reverse_lazy('contents:content_category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '新增广告内容类别'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'content_category-add'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'广告内容类别 "{self.object.name}" 创建成功！')
        return response


class ContentCategoryUpdateView(LoginRequiredMixin, UpdateView):
    """更新广告内容类别"""
    model = ContentCategory
    fields = ['name', 'key']
    template_name = 'content_category_add.html'
    success_url = reverse_lazy('contents:content_category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '编辑广告内容类别'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'content_category'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'广告内容类别 "{self.object.name}" 更新成功！')
        return response

    def form_invalid(self, form):
        messages.error(self.request, '表单填写有误，请检查后重新提交！')
        return super().form_invalid(form)


class ContentCategoryDeleteView(LoginRequiredMixin, DeleteView):
    """删除广告内容类别"""
    model = ContentCategory
    success_url = reverse_lazy('contents:content_category_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        category = get_object_or_404(ContentCategory, pk=kwargs.get('pk'))
        category.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"status": "success", "msg": "删除成功"})

        return redirect(self.success_url)


# ============ Content Management Views ============
class ContentListView(LoginRequiredMixin, ListView):
    """广告内容列表"""
    model = Content
    template_name = 'content_update.html'
    context_object_name = 'contents'
    ordering = ['-create_time']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'content'
        return context


class ContentCreateView(LoginRequiredMixin, CreateView):
    """创建广告内容"""
    model = Content
    fields = ['category', 'title', 'url', 'image', 'text', 'sequence', 'status']
    template_name = 'content_add.html'
    success_url = reverse_lazy('contents:content_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '新增广告内容'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'content-add'
        context['content_categories'] = ContentCategory.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'广告内容 "{self.object.title}" 创建成功！')
        return response


class ContentUpdateView(LoginRequiredMixin, UpdateView):
    """更新广告内容"""
    model = Content
    fields = ['category', 'title', 'url', 'image', 'text', 'sequence', 'status']
    template_name = 'content_add.html'
    success_url = reverse_lazy('contents:content_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '编辑广告内容'
        context['is_superuser'] = self.request.user.is_superuser
        context['left_menu_active'] = 'content'
        context['content_categories'] = ContentCategory.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'广告内容 "{self.object.title}" 更新成功！')
        return response

    def form_invalid(self, form):
        messages.error(self.request, '表单填写有误，请检查后重新提交！')
        return super().form_invalid(form)


class ContentDeleteView(LoginRequiredMixin, DeleteView):
    """删除广告内容"""
    model = Content
    success_url = reverse_lazy('contents:content_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        content = get_object_or_404(Content, pk=kwargs.get('pk'))
        content.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"status": "success", "msg": "删除成功"})

        return redirect(self.success_url)
