from django.urls import path
from . import views

# 设置应用程序命名空间
app_name = 'goods'
urlpatterns = [
    # 商品列表页
    path('list/<int:category_id>/<int:page_num>/', views.GoodsListView.as_view(), name='list'),
    # 热销排行
    path('hot/<int:category_id>/', views.HotGoodsView.as_view()),
    # 商品详情
    path('detail/<int:sku_id>/', views.DetailView.as_view(), name='detail'),
    # 统计商品分类的访问量
    path('detail/visit/<int:category_id>/', views.DetailVisitView.as_view()),
    # 商品评价
    path('comments/<int:sku_id>/', views.GoodsCommentView.as_view()),
    # 按条码搜索商品页面
    path('barcode/search/', views.BarcodeSearchView.as_view(), name='barcode_search'),
    
    # Brand Management
    path('brand/list/', views.BrandListView.as_view(), name='brand_list'),
    path('brand/add/', views.BrandCreateView.as_view(), name='brand_add'),
    path('brand/edit/<int:pk>/', views.BrandUpdateView.as_view(), name='brand_edit'),
    path('brand/delete/<int:pk>/', views.BrandDeleteView.as_view(), name='brand_delete'),
    
    # GoodsCategory Management
    path('category/list/', views.GoodsCategoryListView.as_view(), name='goods_category_list'),
    path('category/add/', views.GoodsCategoryCreateView.as_view(), name='goods_category_add'),
    path('category/edit/<int:pk>/', views.GoodsCategoryUpdateView.as_view(), name='goods_category_edit'),
    path('category/delete/<int:pk>/', views.GoodsCategoryDeleteView.as_view(), name='goods_category_delete'),
    
    # GoodsChannelGroup Management
    path('channel-group/list/', views.GoodsChannelGroupListView.as_view(), name='channel_group_list'),
    path('channel-group/add/', views.GoodsChannelGroupCreateView.as_view(), name='channel_group_add'),
    path('channel-group/edit/<int:pk>/', views.GoodsChannelGroupUpdateView.as_view(), name='channel_group_edit'),
    path('channel-group/delete/<int:pk>/', views.GoodsChannelGroupDeleteView.as_view(), name='channel_group_delete'),
    
    # GoodsChannel Management
    path('channel/list/', views.GoodsChannelListView.as_view(), name='channel_list'),
    path('channel/add/', views.GoodsChannelCreateView.as_view(), name='channel_add'),
    path('channel/edit/<int:pk>/', views.GoodsChannelUpdateView.as_view(), name='channel_edit'),
    path('channel/delete/<int:pk>/', views.GoodsChannelDeleteView.as_view(), name='channel_delete'),
    
    # SPU Management
    path('spu/list/', views.SPUListView.as_view(), name='spu_list'),
    path('spu/add/', views.SPUCreateView.as_view(), name='spu_add'),
    path('spu/edit/<int:pk>/', views.SPUUpdateView.as_view(), name='spu_edit'),
    path('spu/detail/<int:pk>/', views.SPUDetailView.as_view(), name='spu_detail'),
    path('spu/delete/<int:pk>/', views.SPUDeleteView.as_view(), name='spu_delete'),
    
    # SPUSpecification Management
    path('spu-spec/list/', views.SPUSpecificationListView.as_view(), name='spu_specification_list'),
    path('spu-spec/add/', views.SPUSpecificationCreateView.as_view(), name='spu_specification_add'),
    path('spu-spec/edit/<int:pk>/', views.SPUSpecificationUpdateView.as_view(), name='spu_specification_edit'),
    path('spu-spec/delete/<int:pk>/', views.SPUSpecificationDeleteView.as_view(), name='spu_specification_delete'),
    
    # SpecificationOption Management
    path('spec-option/list/', views.SpecificationOptionListView.as_view(), name='specification_option_list'),
    path('spec-option/add/', views.SpecificationOptionCreateView.as_view(), name='specification_option_add'),
    path('spec-option/edit/<int:pk>/', views.SpecificationOptionUpdateView.as_view(), name='specification_option_edit'),
    path('spec-option/delete/<int:pk>/', views.SpecificationOptionDeleteView.as_view(), name='specification_option_delete'),
    
    # SKUSpecification Management
    path('sku-spec/list/', views.SKUSpecificationListView.as_view(), name='sku_specification_list'),
    path('sku-spec/add/', views.SKUSpecificationCreateView.as_view(), name='sku_specification_add'),
    path('sku-spec/edit/<int:pk>/', views.SKUSpecificationUpdateView.as_view(), name='sku_specification_edit'),
    path('sku-spec/delete/<int:pk>/', views.SKUSpecificationDeleteView.as_view(), name='sku_specification_delete'),
]

