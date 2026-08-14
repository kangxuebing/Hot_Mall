from django.urls import path,re_path
from . import views
# 设置应用程序命名空间
app_name = 'contents'
urlpatterns = [
    # 首页
    path("", views.IndexView.as_view(), name='index'),
    
    # ContentCategory Management
    path('content-category/list/', views.ContentCategoryListView.as_view(), name='content_category_list'),
    path('content-category/add/', views.ContentCategoryCreateView.as_view(), name='content_category_add'),
    path('content-category/edit/<int:pk>/', views.ContentCategoryUpdateView.as_view(), name='content_category_edit'),
    path('content-category/delete/<int:pk>/', views.ContentCategoryDeleteView.as_view(), name='content_category_delete'),
    
    # Content Management
    path('content/list/', views.ContentListView.as_view(), name='content_list'),
    path('content/add/', views.ContentCreateView.as_view(), name='content_add'),
    path('content/edit/<int:pk>/', views.ContentUpdateView.as_view(), name='content_edit'),
    path('content/delete/<int:pk>/', views.ContentDeleteView.as_view(), name='content_delete'),
]
