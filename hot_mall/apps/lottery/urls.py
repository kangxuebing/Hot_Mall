from django.urls import path
from . import views

app_name = 'lottery'

urlpatterns = [
    # ========== 后台页面路由 ==========
    # 奖项管理
    path('prize-level/', views.PrizeLevelListView.as_view(), name='prize_level_list'),
    path('prize-level/add/', views.PrizeLevelAddView.as_view(), name='prize_level_add'),
    path('prize-level/edit/<int:pk>/', views.PrizeLevelEditView.as_view(), name='prize_level_edit'),

    # 奖品管理
    path('prize/', views.PrizeListView.as_view(), name='prize_list'),
    path('prize/add/', views.PrizeAddView.as_view(), name='prize_add'),
    path('prize/edit/<int:pk>/', views.PrizeEditView.as_view(), name='prize_edit'),

    # 用户转盘页面
    path('wheel/', views.LotteryWheelView.as_view(), name='lottery_wheel'),

    # 中奖历史记录
    path('records/', views.LotteryRecordListView.as_view(), name='lottery_record_list'),
    path('api/records/', views.LotteryRecordAPIView.as_view(), name='lottery_record_api'),

    # ========== AJAX 接口路由（前端JS调用） ==========
    path('api/prize-level/delete/', views.PrizeLevelDeleteAjaxView.as_view(), name='prize_level_delete_ajax'),
    path('api/prize/delete/', views.PrizeDeleteAjaxView.as_view(), name='prize_delete_ajax'),
    path('draw/', views.LotteryDrawView.as_view(), name='lottery_draw'),
]