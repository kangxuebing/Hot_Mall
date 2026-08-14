from django.db import models
from hot_mall.utils.models import BaseModel
from goods.models import SKU
from django.conf import settings


class PrizeLevel(BaseModel):
    """奖项"""
    name = models.CharField(max_length=50, verbose_name="等级名称")
    level = models.IntegerField(unique=True, verbose_name="等级序号")
    probability = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="中奖概率(%)")
    color = models.CharField(max_length=20, default="#FF6B6B", verbose_name="转盘颜色")
    
    class Meta:
        db_table = "tb_prize_level"
        verbose_name = '奖项'
        verbose_name_plural = verbose_name
        ordering = ['level']
    
    def __str__(self):
        return f"{self.level}等奖 - {self.name}"


class Prize(BaseModel):
    """奖品"""
    prize_level = models.ForeignKey(PrizeLevel, on_delete=models.CASCADE, verbose_name="中奖等级")
    sku = models.ForeignKey(SKU, on_delete=models.CASCADE, verbose_name="商品")
    quantity = models.IntegerField(default=1, verbose_name="奖品数量")
    
    class Meta:
        db_table = "tb_prize"
        verbose_name = '奖品'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return f"{self.prize_level.name} - {self.sku.name} x{self.quantity}"


class LotteryRecord(BaseModel):
    """中奖历史记录"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="用户")
    prize_level = models.ForeignKey(PrizeLevel, on_delete=models.CASCADE, verbose_name="中奖等级")
    prize = models.ForeignKey(Prize, on_delete=models.CASCADE, null=True, blank=True, verbose_name="奖品")
    is_won = models.BooleanField(default=False, verbose_name="是否中奖")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP地址")
    
    class Meta:
        db_table = "tb_lottery_record"
        verbose_name = '中奖记录'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.prize_level.name}"
