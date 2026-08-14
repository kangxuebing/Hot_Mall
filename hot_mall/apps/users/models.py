from django.db import models
from hot_mall.utils.models import BaseModel
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """自定义用户模型类"""
    # 手机号
    mobile = models.CharField(max_length=11, unique=True, verbose_name="手机号")
    email_active = models.BooleanField(default=False, verbose_name="邮箱验证状态")
    default_address = models.ForeignKey('Address', related_name='users', null=True, blank=True,
                                        on_delete=models.SET_NULL, verbose_name='默认地址')
    # 人脸特征编码（存储为JSON字符串）
    face_encoding = models.TextField(null=True, blank=True, verbose_name="人脸特征编码")
    
    # 会员相关字段
    MEMBER_LEVEL_CHOICES = (
        (0, "普通会员"),
        (1, "银卡会员"),
        (2, "金卡会员"),
        (3, "钻石会员"),
    )
    member_level = models.SmallIntegerField(choices=MEMBER_LEVEL_CHOICES, default=0, verbose_name="会员等级")
    points = models.IntegerField(default=0, verbose_name="积分")
    discount_rate = models.DecimalField(max_digits=3, decimal_places=2, default=1.00, verbose_name="折扣率")
    total_consume = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="累计消费")
    
    class Meta:
        db_table = 'tb_users'  # 自定义数据表名
        verbose_name = '用户'
        verbose_name_plural = verbose_name
    def __str__(self):
        return self.username

class Address(BaseModel):
    """用户地址"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='用户')
    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    province = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='province_addresses',
                                 verbose_name='省')
    city = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='city_addresses', verbose_name='市')
    district = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='district_addresses',
                                 verbose_name='区')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')
    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']  # 根据更新时间倒序