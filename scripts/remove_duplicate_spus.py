"""
剔除重复的SPU数据
对于 name, desc_detail, desc_pack, desc_service, brand_id, category1_id, category2_id, category3_id
这些字段值相同的SPU只保留ID最小的一个
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

from goods.models import SPU, SPUSpecification, SKUSpecification
from django.db.models import Count, Min


def remove_duplicate_spus():
    """剔除重复的SPU"""
    print("开始查找重复的SPU...")
    
    # 查找重复的SPU（基于指定字段）
    duplicate_spus = SPU.objects.values(
        'name', 'desc_detail', 'desc_pack', 'desc_service',
        'brand_id', 'category1_id', 'category2_id', 'category3_id'
    ).annotate(
        count=Count('id'),
        min_id=Min('id')
    ).filter(count__gt=1)
    
    total_duplicates = duplicate_spus.count()
    print(f"发现 {total_duplicates} 组重复的SPU")
    
    if total_duplicates == 0:
        print("没有发现重复的SPU，无需处理")
        return
    
    total_to_delete = 0
    
    for duplicate in duplicate_spus:
        # 获取该组所有SPU
        spus = SPU.objects.filter(
            name=duplicate['name'],
            desc_detail=duplicate['desc_detail'],
            desc_pack=duplicate['desc_pack'],
            desc_service=duplicate['desc_service'],
            brand_id=duplicate['brand_id'],
            category1_id=duplicate['category1_id'],
            category2_id=duplicate['category2_id'],
            category3_id=duplicate['category3_id']
        ).order_by('id')
        
        # 保留ID最小的，删除其他的
        keep_spu = spus.first()
        delete_spus = spus.exclude(id=keep_spu.id)
        
        delete_count = delete_spus.count()
        total_to_delete += delete_count
        
        print(f"\n重复组: {keep_spu.name}")
        print(f"  保留SPU ID: {keep_spu.id}")
        print(f"  删除 {delete_count} 个重复SPU: {[s.id for s in delete_spus]}")
        
        # 将重复SPU的关联对象转移到保留的SPU
        for delete_spu in delete_spus:
            # 转移SPUSpecification
            SPUSpecification.objects.filter(spu=delete_spu).update(spu=keep_spu)
            
            # 转移SKU及其关联
            from goods.models import SKU
            skus = SKU.objects.filter(spu=delete_spu)
            for sku in skus:
                sku.spu = keep_spu
                sku.save()
        
        # 删除重复的SPU
        delete_spus.delete()
    
    print(f"\n删除完成！共删除 {total_to_delete} 个重复SPU")
    print(f"保留了 {total_duplicates} 个唯一SPU")


if __name__ == '__main__':
    # 确认操作
    print("警告：此操作将删除数据库中的重复SPU数据！")
    print("只保留每组重复SPU中ID最小的一个。")
    
    confirm = input("确认继续？(yes/no): ")
    if confirm.lower() in ['yes', 'y']:
        remove_duplicate_spus()
    else:
        print("操作已取消")
