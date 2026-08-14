from django.db import models
from hot_mall.utils.models import BaseModel
from goods.models import SKU
from users.models import User


class PromotionProduct(BaseModel):
    """促销商品"""
    DISCOUNT_TYPE_CHOICES = (
        (1, "固定折扣率"),
        (2, "固定金额优惠"),
    )
    
    sku = models.ForeignKey(SKU, on_delete=models.CASCADE, verbose_name="商品SKU")
    discount_type = models.SmallIntegerField(choices=DISCOUNT_TYPE_CHOICES, default=1, verbose_name="折扣类型")
    discount_rate = models.DecimalField(max_digits=3, decimal_places=2, default=1.00, verbose_name="折扣率")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="优惠金额")
    start_time = models.DateTimeField(verbose_name="促销开始时间")
    end_time = models.DateTimeField(verbose_name="促销结束时间")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    description = models.TextField(default="", verbose_name="促销说明")
    
    class Meta:
        db_table = "tb_promotion_product"
        verbose_name = '促销商品'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']
    
    def __str__(self):
        return f"{self.sku.name} - {self.get_discount_type_display()}"
    
    def is_valid(self):
        """检查促销是否有效"""
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and self.start_time <= now <= self.end_time


class POSOrder(BaseModel):
    """收银台订单"""
    ORDER_STATUS_CHOICES = (
        (1, "待支付"),
        (2, "已支付"),
        (3, "已取消"),
        (9, "已删除"),
    )
    PAYMENT_METHOD_CHOICES = (
        (1, "现金"),
        (2, "支付宝"),
        (3, "微信支付"),
        (4, "银行卡"),
    )
    
    order_id = models.CharField(max_length=64, primary_key=True, verbose_name="订单号")
    cashier = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="收银员", related_name="cashier_orders")
    member = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="会员", related_name="member_orders")
    total_count = models.IntegerField(default=0, verbose_name="商品总数")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="总金额")
    original_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="原始总金额")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="优惠金额")
    discount_type = models.CharField(max_length=20, default='member', verbose_name="折扣类型")  # member:会员折扣, promotion:商品促销
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="实付金额")
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="找零")
    payment_method = models.SmallIntegerField(choices=PAYMENT_METHOD_CHOICES, default=1, verbose_name="支付方式")
    status = models.SmallIntegerField(choices=ORDER_STATUS_CHOICES, default=1, verbose_name="订单状态")
    remark = models.TextField(default="", verbose_name="备注")
    
    class Meta:
        db_table = "tb_pos_order"
        verbose_name = '收银台订单'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']
    
    def __str__(self):
        return self.order_id


class POSOrderItem(BaseModel):
    """收银台订单商品"""
    order = models.ForeignKey(POSOrder, related_name='items', on_delete=models.CASCADE, verbose_name="订单")
    sku = models.ForeignKey(SKU, on_delete=models.PROTECT, verbose_name="商品SKU")
    quantity = models.IntegerField(default=1, verbose_name="数量")
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="原始单价")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="单价")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="小计")
    discount_rate = models.DecimalField(max_digits=3, decimal_places=2, default=1.00, verbose_name="折扣率")
    discount_type = models.CharField(max_length=20, default='none', verbose_name="折扣类型")
    
    class Meta:
        db_table = "tb_pos_order_item"
        verbose_name = '收银台订单商品'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return f"{self.sku.name} x {self.quantity}"


class BarcodeScanner(BaseModel):
    """条码扫描器设备"""
    DEVICE_STATUS_CHOICES = (
        (1, "在线"),
        (2, "离线"),
        (3, "故障"),
    )
    
    name = models.CharField(max_length=50, verbose_name="设备名称")
    device_id = models.CharField(max_length=100, unique=True, verbose_name="设备ID")
    port = models.CharField(max_length=50, verbose_name="串口端口")
    baud_rate = models.IntegerField(default=9600, verbose_name="波特率")
    status = models.SmallIntegerField(choices=DEVICE_STATUS_CHOICES, default=2, verbose_name="设备状态")
    last_active = models.DateTimeField(null=True, blank=True, verbose_name="最后活跃时间")
    
    class Meta:
        db_table = "tb_barcode_scanner"
        verbose_name = '条码扫描器'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return self.name


class SuspendedOrder(BaseModel):
    """挂单"""
    cashier = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="收银员")
    member = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="会员", related_name="suspended_orders")
    total_count = models.IntegerField(default=0, verbose_name="商品总数")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="总金额")
    cart_data = models.TextField(verbose_name="购物车数据JSON")
    remark = models.TextField(default="", verbose_name="备注")
    
    class Meta:
        db_table = "tb_suspended_order"
        verbose_name = '挂单'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']
    
    def __str__(self):
        return f"挂单 {self.id} - {self.cashier.username}"
