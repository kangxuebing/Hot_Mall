"""
剔除重复的SKU数据
对于 name, caption, is_launched, default_image, category_id, spu_id, barcode 
这些字段值相同的SKU只保留ID最小的一个
"""
import os
import sys
import django

# 添加项目根目录到Python路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hot_mall.settings.dev')
django.setup()

from goods.models import SKU
from django.db.models import Count, Min


def remove_duplicate_skus():
    """剔除重复的SKU"""
    print("开始查找重复的SKU...")
    
    # 查找重复的SKU（基于指定字段）
    duplicate_skus = SKU.objects.values(
        'name', 'caption', 'is_launched', 'default_image', 
        'category_id', 'spu_id', 'barcode'
    ).annotate(
        count=Count('id'),
        min_id=Min('id')
    ).filter(count__gt=1)
    
    total_duplicates = duplicate_skus.count()
    print(f"发现 {total_duplicates} 组重复的SKU")
    
    if total_duplicates == 0:
        print("没有发现重复的SKU，无需处理")
        return
    
    total_to_delete = 0
    
    for duplicate in duplicate_skus:
        # 获取该组所有SKU
        skus = SKU.objects.filter(
            name=duplicate['name'],
            caption=duplicate['caption'],
            is_launched=duplicate['is_launched'],
            default_image=duplicate['default_image'],
            category_id=duplicate['category_id'],
            spu_id=duplicate['spu_id'],
            barcode=duplicate['barcode']
        ).order_by('id')
        
        # 保留ID最小的，删除其他的
        keep_sku = skus.first()
        delete_skus = skus.exclude(id=keep_sku.id)
        
        delete_count = delete_skus.count()
        total_to_delete += delete_count
        
        print(f"\n重复组: {keep_sku.name}")
        print(f"  保留SKU ID: {keep_sku.id}")
        print(f"  删除 {delete_count} 个重复SKU: {[s.id for s in delete_skus]}")
        
        # 删除重复的SKU
        delete_skus.delete()
    
    print(f"\n删除完成！共删除 {total_to_delete} 个重复SKU")
    print(f"保留了 {total_duplicates} 个唯一SKU")


if __name__ == '__main__':
    # 确认操作
    print("警告：此操作将删除数据库中的重复SKU数据！")
    print("只保留每组重复SKU中ID最小的一个。")
    
    confirm = input("确认继续？(yes/no): ")
    if confirm.lower() in ['yes', 'y']:
        remove_duplicate_skus()
    else:
        print("操作已取消")
