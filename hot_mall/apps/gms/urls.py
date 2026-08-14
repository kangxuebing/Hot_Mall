from django.urls import path, re_path
from . import views

# 设置应用程序命名空间
app_name = 'gms'
urlpatterns = [
     # 商品管理页面
    path('listsku/', views.SKUListView.as_view(), name='sku_list'),
    path('api/skus/', views.SKUListAPIView.as_view(), name='sku-list-api'),  # JSON接口
    # 添加商品
    path('addsku/', views.SKUCreateView.as_view(), name='sku_add'),
    # 修改商品
    path('editsku/<int:pk>/', views.SKUDetailView.as_view(), name='sku_detail'),
    # 删除商品
    path('delsku/<int:pk>/', views.SKUDeleteView.as_view(), name='sku_delete'),
    # 设置默认图片
    path('setdefimage/<int:sku_id>/<int:image_id>/', views.SetDefaultImageView.as_view(), name='set_default_image'),
    # 上传图片（编辑页即时入库，添加页临时存储）
    path('upload-image/', views.SKUImageUploadView.as_view(), name='image_upload'),
    # 删除单张图片
    path('delimage/<int:pk>/', views.SKUImageDeleteView.as_view(), name='image_delete'),

    # 临近保质期商品
    path('expirysku/', views.SKUExpiryView.as_view(), name='sku_expiry'),

]
