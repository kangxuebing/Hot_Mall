from django.contrib import admin
from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['id', 'supl_name', 'supl_addr', 'supl_phone', 'wechat', 'business_license', 'level', 'create_time', 'update_time']
    search_fields = ['supl_name', 'supl_phone', 'wechat']
    list_filter = ['level', 'create_time']
    ordering = ['-create_time']
