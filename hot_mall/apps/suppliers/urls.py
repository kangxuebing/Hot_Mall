from django.urls import path
from . import views


app_name = 'suppliers'
urlpatterns = [
    path('suplcrt/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('listsupplier/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suplupd/<int:pk>/', views.SupplierUpdateView.as_view(), name='supplier_update'),
    path('supldel/<int:pk>/', views.SupplierDeleteView.as_view(), name='supplier_delete'),
    path('purchadd/', views.PurchaseRecordCreateView.as_view(), name='purchase_add'),
    path('listpurchase/', views.PurchaseRecordListView.as_view(), name='purchase_list'),
    path('purchupd/<int:pk>/', views.PurchaseRecordUpdateView.as_view(), name='purchase_update'),
    path('purchdel/<int:pk>/', views.PurchaseRecordDeleteView.as_view(), name='purchase_delete'),
    path('setsupldefimage/<int:supplier_id>/<int:image_id>/', views.SetSupplierDefaultImageView.as_view(), name='set_default_image'),
    # 上传图片（编辑页即时入库，添加页临时存储）
    path('upload-image/', views.SupplierImageUploadView.as_view(), name='image_upload'),
    # 删除单张图片
    path('delsuplimage/<int:pk>/', views.SupplierImageDeleteView.as_view(), name='image_delete'),
    # 通过条码搜索SKU
    path('search-sku/', views.SearchSKUByBarcodeView.as_view(), name='search_sku'),
    # 通过商品名称搜索SKU
    path('search-sku-by-name/', views.SearchSKUByNameView.as_view(), name='search_sku_by_name'),
]
