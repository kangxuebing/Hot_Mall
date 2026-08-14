from django.db import models
from hot_mall.utils.models import BaseModel
from django.utils import timezone

class Supplier(BaseModel):
    """供应商模型"""
    supl_name = models.CharField(max_length=100, verbose_name='供应商名称', help_text='供应商的名称')
    supl_addr = models.CharField(max_length=200, blank=True, verbose_name='供应商地址', help_text='供应商的地址')
    supl_phone = models.CharField(max_length=20, blank=True, verbose_name='供应商联系电话', help_text='供应商的联系电话')
    wechat = models.CharField(max_length=50, blank=True, verbose_name='供应商微信', help_text='供应商的微信号')
    business_license = models.CharField(max_length=100, blank=True, verbose_name='供应商营业执照', help_text='供应商的营业执照号')
    level = models.CharField(max_length=20, blank=True, verbose_name='供应商等级', help_text='供应商的等级')
    # 新增：供应商图片/Logo 字段
    default_image = models.ImageField(max_length=200, default='', null=True, blank=True, upload_to='suppliers/licenses/',verbose_name='营业执照')

    class Meta:
        db_table = 'tb_supplier'
        verbose_name = '供应商'
        verbose_name_plural = '供应商'
        app_label = 'suppliers'

    def __str__(self):
        return self.supl_name


class SupplierImage(BaseModel):
    """供应商图片表（支持多图）"""
    # 外键关联供应商
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='供应商'
    )

    # 图片字段
    image = models.ImageField(
        upload_to='supplier/licenses/',  # 上传目录：media/supplier/licenses/
        verbose_name='营业执照/资质图片'
    )

    class Meta:
        db_table = 'tb_supplier_image'
        verbose_name = '供应商营业执照'
        verbose_name_plural = verbose_name
        app_label = 'suppliers'

    def __str__(self):
        # 正确获取供应商名称
        return f'{self.supplier.supl_name} - 图片{self.id}'


class SupplierPurchaseRecord(models.Model):
    """供应商进货记录"""
    supplier = models.ForeignKey(
        'Supplier', on_delete=models.CASCADE, related_name='purchases',
        verbose_name='供应商'
    )
    product_name = models.CharField(max_length=200, verbose_name='商品名称')
    product_spec = models.CharField(max_length=200, blank=True, verbose_name='规格型号')
    barcode = models.CharField(max_length=50, blank=True, verbose_name='商品条码', help_text='商品的条形码')
    production_date = models.DateField(null=True, blank=True, verbose_name='生产日期')
    shelf_life = models.IntegerField(default=0, verbose_name='保质期(天)', help_text='保质期，单位为天')
    expiration_date = models.DateField(null=True, blank=True, verbose_name='过期日期', help_text='商品的过期日期')
    purchase_num = models.IntegerField(verbose_name='进货数量')
    qualified_num = models.IntegerField(default=0, verbose_name='合格数量', help_text='合格商品数量')
    near_expiry_num = models.IntegerField(default=0, verbose_name='临保质期数量', help_text='临保质期商品数量')
    damaged_num = models.IntegerField(default=0, verbose_name='破损数量', help_text='破损商品数量')
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='进货单价')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='总金额')
    purchase_time = models.DateTimeField(default=timezone.now, verbose_name='进货时间')
    operator = models.CharField(max_length=50, blank=True, verbose_name='操作人')
    remark = models.TextField(blank=True, verbose_name='备注')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return f"{self.supplier.supl_name} - {self.product_name}"

    class Meta:
        db_table = 'tb_supplier_purchase'
        verbose_name = '供应商进货记录'
        verbose_name_plural = verbose_name
        ordering = ['-purchase_time']


