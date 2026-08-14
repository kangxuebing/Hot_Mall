from django.urls import re_path, path
from . import views
app_name = 'payment'
urlpatterns = [
    # 支付
    re_path(r'payment/(?P<order_id>\d+)/', views.PaymentView.as_view()),
    path('payment/status/', views.PaymentStatusView.as_view()),
    path('payment/wechat/checkout/<str:order_id>/', views.WeChatCheckoutView.as_view(), name='wechat_checkout'),
    path('payment/wechat/demo-confirm/<str:order_id>/', views.WeChatDemoConfirmView.as_view(), name='wechat_demo_confirm'),
    path('payment/wechat/notify/', views.WeChatNotifyView.as_view(), name='wechat_notify'),
    path('orders/comment/', views.OrderCommentView.as_view()),
]
