from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    path('cashier/', views.CashierInterfaceView.as_view(), name='cashier'),
    path('scan/', views.ScanBarcodeView.as_view(), name='scan_barcode'),
    path('query-member/', views.QueryMemberView.as_view(), name='query_member'),
    path('create-order/', views.CreateOrderView.as_view(), name='create_order'),
    path('check-stock/', views.CheckStockView.as_view(), name='check_stock'),
    path('scanner-status/', views.UsbScannerStatusView.as_view(), name='scanner_status'),
    path('receipt/<str:order_id>/', views.ReceiptPreviewView.as_view(), name='receipt_preview'),
    path('print-receipt/', views.PrintReceiptView.as_view(), name='print_receipt'),
    path('suspend-order/', views.SuspendOrderView.as_view(), name='suspend_order'),
    path('suspended-orders/', views.GetSuspendedOrdersView.as_view(), name='get_suspended_orders'),
    path('resume-order/', views.ResumeOrderView.as_view(), name='resume_order'),
    path('delete-suspended-order/', views.DeleteSuspendedOrderView.as_view(), name='delete_suspended_order'),
    path('transaction-records/', views.TransactionRecordsPageView.as_view(), name='transaction_records'),
    path('get-transaction-records/', views.GetTransactionRecordsView.as_view(), name='get_transaction_records'),
    path('transaction-details/', views.TransactionDetailsPageView.as_view(), name='transaction_details'),
    path('get-transaction-details/', views.GetTransactionDetailsView.as_view(), name='get_transaction_details'),
    path('update-order-status/', views.UpdateOrderStatusView.as_view(), name='update_order_status'),
    path('promotion/', views.PromotionListView.as_view(), name='promotion_list'),
    path('promotion/add/', views.PromotionAddView.as_view(), name='promotion_add'),
    path('promotion/edit/<int:pk>/', views.PromotionEditView.as_view(), name='promotion_edit'),
    path('promotion/delete/<int:pk>/', views.PromotionDeleteView.as_view(), name='promotion_delete'),
    path('promotion/api/list/', views.PromotionListAPIView.as_view(), name='promotion_api_list'),
    path('payment-config/', views.PaymentConfigView.as_view(), name='payment_config'),
    path('payment-account/add/', views.PaymentAccountAddView.as_view(), name='payment_account_add'),
    path('payment-account/edit/<int:pk>/', views.PaymentAccountEditView.as_view(), name='payment_account_edit'),
    path('payment-account/delete/<int:pk>/', views.PaymentAccountDeleteView.as_view(), name='payment_account_delete'),
    # 门店管理
    path('store/', views.StoreListView.as_view(), name='store_list'),
    path('store/add/', views.StoreAddView.as_view(), name='store_add'),
    path('store/edit/<int:pk>/', views.StoreEditView.as_view(), name='store_edit'),
    path('store/delete/<int:pk>/', views.StoreDeleteView.as_view(), name='store_delete'),
    path('store/<int:store_pk>/terminals/', views.StoreTerminalListView.as_view(), name='store_terminal_list'),
    path('store/<int:store_pk>/terminals/add/', views.StoreTerminalFormView.as_view(), name='store_terminal_add'),
    path('store/<int:store_pk>/terminals/<int:pk>/edit/', views.StoreTerminalFormView.as_view(), name='store_terminal_edit'),
    path('store/<int:store_pk>/terminals/<int:pk>/delete/', views.StoreTerminalDeleteView.as_view(), name='store_terminal_delete'),
    # 用户-门店关联管理
    path('user-store/', views.UserStoreListView.as_view(), name='user_store_list'),
    path('user-store/add/', views.UserStoreAddView.as_view(), name='user_store_add'),
    path('user-store/edit/<int:pk>/', views.UserStoreEditView.as_view(), name='user_store_edit'),
    path('user-store/delete/<int:pk>/', views.UserStoreDeleteView.as_view(), name='user_store_delete'),
    # 门店选择
    path('select-store/', views.SelectStoreView.as_view(), name='select_store'),
    # 门店库存初始化
    path('init-stock/', views.InitStoreStockView.as_view(), name='init_store_stock'),
    # 证书管理API
    path('api/certificate/bind/', views.BindCertificateView.as_view(), name='bind_certificate'),
    path('api/certificate/unbind/<int:pk>/', views.UnbindCertificateView.as_view(), name='unbind_certificate'),
    path('api/certificate/verify/', views.VerifyCertificateView.as_view(), name='verify_certificate'),
]