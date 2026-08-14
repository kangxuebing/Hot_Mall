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
]