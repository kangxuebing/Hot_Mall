#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
京东风格商品数据导入脚本
支持多品类真实商品数据导入

使用方法: python manage.py shell < scripts/import_jd_goods.py
"""
import os
import random
from datetime import datetime, timedelta

from goods.models import (
    GoodsCategory, Brand, SPU, SKU, 
    SKUImage, SPUSpecification, SpecificationOption, SKUSpecification
)
from django.core.files import File
from django.db import transaction


# 京东风格商品数据
JD_GOODS_DATA = {
    "brands": [
        # 手机数码品牌
        {"name": "小米", "first_letter": "X", "logo": "xiaomi_logo.png"},
        {"name": "OPPO", "first_letter": "O", "logo": "oppo_logo.png"},
        {"name": "vivo", "first_letter": "V", "logo": "vivo_logo.png"},
        {"name": "三星", "first_letter": "S", "logo": "samsung_logo.png"},
        {"name": "索尼", "first_letter": "S", "logo": "sony_logo.png"},
        
        # 电脑办公品牌
        {"name": "联想", "first_letter": "L", "logo": "lenovo_logo.png"},
        {"name": "戴尔", "first_letter": "D", "logo": "dell_logo.png"},
        {"name": "华硕", "first_letter": "H", "logo": "asus_logo.png"},
        {"name": "惠普", "first_letter": "H", "logo": "hp_logo.png"},
        
        # 家用电器品牌
        {"name": "美的", "first_letter": "M", "logo": "midea_logo.png"},
        {"name": "格力", "first_letter": "G", "logo": "gree_logo.png"},
        {"name": "海尔", "first_letter": "H", "logo": "haier_logo.png"},
        {"name": "海信", "first_letter": "H", "logo": "hisense_logo.png"},
        
        # 服装品牌
        {"name": "耐克", "first_letter": "N", "logo": "nike_logo.png"},
        {"name": "阿迪达斯", "first_letter": "A", "logo": "adidas_logo.png"},
        {"name": "优衣库", "first_letter": "Y", "logo": "uniqlo_logo.png"},
        {"name": "李宁", "first_letter": "L", "logo": "lining_logo.png"},
        
        # 食品品牌
        {"name": "三只松鼠", "first_letter": "S", "logo": "three_squirrels_logo.png"},
        {"name": "良品铺子", "first_letter": "L", "logo": "bestore_logo.png"},
        {"name": "百草味", "first_letter": "B", "logo": "bechche_logo.png"},
        
        # 美妆品牌
        {"name": "欧莱雅", "first_letter": "O", "logo": "loreal_logo.png"},
        {"name": "雅诗兰黛", "first_letter": "Y", "logo": "estee_lauder_logo.png"},
        {"name": "兰蔻", "first_letter": "L", "logo": "lancome_logo.png"},
        
        # 食品品牌
        {"name": "旺旺", "first_letter": "W", "logo": "wangwang_logo.png"},
        {"name": "康师傅", "first_letter": "K", "logo": "kangshifu_logo.png"},
        {"name": "统一", "first_letter": "T", "logo": "tongyi_logo.png"},
        {"name": "好丽友", "first_letter": "H", "logo": "haoliyou_logo.png"},
        {"name": "奥利奥", "first_letter": "A", "logo": "oreo_logo.png"},
        {"name": "乐事", "first_letter": "L", "logo": "lays_logo.png"},
        {"name": "可口可乐", "first_letter": "K", "logo": "cocacola_logo.png"},
        {"name": "百事可乐", "first_letter": "B", "logo": "pepsi_logo.png"},
        {"name": "农夫山泉", "first_letter": "N", "logo": "nongfu_logo.png"},
        {"name": "娃哈哈", "first_letter": "W", "logo": "hahaha_logo.png"},
        {"name": "蒙牛", "first_letter": "M", "logo": "mengniu_logo.png"},
        {"name": "伊利", "first_letter": "Y", "logo": "yili_logo.png"},
        {"name": "光明", "first_letter": "G", "logo": "guangming_logo.png"},
        {"name": "汇源", "first_letter": "H", "logo": "huiyuan_logo.png"},
        {"name": "加多宝", "first_letter": "J", "logo": "jiaduobao_logo.png"},
        {"name": "王老吉", "first_letter": "W", "logo": "wanglaoji_logo.png"},
        {"name": "红牛", "first_letter": "H", "logo": "hongniu_logo.png"},
        {"name": "雀巢", "first_letter": "Q", "logo": "nestle_logo.png"},
        {"name": "星巴克", "first_letter": "X", "logo": "starbucks_logo.png"},
        {"name": "喜茶", "first_letter": "X", "logo": "heytea_logo.png"},
        
        # 日化品牌
        {"name": "宝洁", "first_letter": "B", "logo": "pg_logo.png"},
        {"name": "联合利华", "first_letter": "L", "logo": "unilever_logo.png"},
        {"name": "蓝月亮", "first_letter": "L", "logo": "bluemoon_logo.png"},
        {"name": "立白", "first_letter": "L", "logo": "libai_logo.png"},
        {"name": "威露士", "first_letter": "W", "logo": "walch_logo.png"},
        {"name": "汰渍", "first_letter": "T", "logo": "tide_logo.png"},
        {"name": "奥妙", "first_letter": "A", "logo": "omo_logo.png"},
        {"name": "舒肤佳", "first_letter": "S", "logo": "safeguard_logo.png"},
        {"name": "滴露", "first_letter": "D", "logo": "dettol_logo.png"},
        {"name": "维达", "first_letter": "W", "logo": "vinda_logo.png"},
        {"name": "清风", "first_letter": "Q", "logo": "qingfeng_logo.png"},
        {"name": "心相印", "first_letter": "X", "logo": "xinxiangyin_logo.png"},
        {"name": "洁柔", "first_letter": "J", "logo": "jierou_logo.png"},
        {"name": "海飞丝", "first_letter": "H", "logo": "headshoulders_logo.png"},
        {"name": "飘柔", "first_letter": "P", "logo": "rejoice_logo.png"},
        {"name": "潘婷", "first_letter": "P", "logo": "pantene_logo.png"},
        {"name": "沙宣", "first_letter": "S", "logo": "vs_logo.png"},
        {"name": "多芬", "first_letter": "D", "logo": "dove_logo.png"},
        {"name": "力士", "first_letter": "L", "logo": "lux_logo.png"},
        {"name": "玉兰油", "first_letter": "Y", "logo": "olay_logo.png"},
        
        # 酒水品牌
        {"name": "茅台", "first_letter": "M", "logo": "maotai_logo.png"},
        {"name": "五粮液", "first_letter": "W", "logo": "wuliangye_logo.png"},
        {"name": "剑南春", "first_letter": "J", "logo": "jiannanchun_logo.png"},
        {"name": "泸州老窖", "first_letter": "L", "logo": "luzhoulaojiao_logo.png"},
        {"name": "汾酒", "first_letter": "F", "logo": "fenjiu_logo.png"},
        {"name": "洋河", "first_letter": "Y", "logo": "yanghe_logo.png"},
        {"name": "长城", "first_letter": "C", "logo": "greatwall_logo.png"},
        {"name": "张裕", "first_letter": "Z", "logo": "changyu_logo.png"},
        {"name": "王朝", "first_letter": "W", "logo": "dynasty_logo.png"},
        {"name": "青岛啤酒", "first_letter": "Q", "logo": "tsingtao_logo.png"},
        {"name": "雪花啤酒", "first_letter": "X", "logo": "snow_logo.png"},
        {"name": "哈尔滨啤酒", "first_letter": "H", "logo": "harbin_logo.png"},
        {"name": "百威", "first_letter": "B", "logo": "budweiser_logo.png"},
        {"name": "喜力", "first_letter": "X", "logo": "heineken_logo.png"},
        {"name": "轩尼诗", "first_letter": "X", "logo": "hennessy_logo.png"},
        {"name": "马爹利", "first_letter": "M", "logo": "martell_logo.png"},
        {"name": "人头马", "first_letter": "R", "logo": "remymartin_logo.png"},
        {"name": "尊尼获加", "first_letter": "Z", "logo": "johnniewalker_logo.png"},
        {"name": "芝华士", "first_letter": "Z", "logo": "chivas_logo.png"},
        {"name": "杰克丹尼", "first_letter": "J", "logo": "jackdaniels_logo.png"},
        
        # 更多食品品牌
        {"name": "卫龙", "first_letter": "W", "logo": "weilong_logo.png"},
        {"name": "盼盼", "first_letter": "P", "logo": "panpan_logo.png"},
        {"name": "达利园", "first_letter": "D", "logo": "daliyuan_logo.png"},
        {"name": "好想你", "first_letter": "H", "logo": "haoxiangni_logo.png"},
        {"name": "盐津铺子", "first_letter": "Y", "logo": "yanjin_logo.png"},
        {"name": "来伊份", "first_letter": "L", "logo": "laiyifen_logo.png"},
        {"name": "百草味", "first_letter": "B", "logo": "bechche_logo.png"},
        {"name": "恰恰", "first_letter": "Q", "logo": "qiaqia_logo.png"},
        {"name": "真心", "first_letter": "Z", "logo": "zhenxin_logo.png"},
        {"name": "华味亨", "first_letter": "H", "logo": "huaweiheng_logo.png"},
        {"name": "姚生记", "first_letter": "Y", "logo": "yaoshengji_logo.png"},
        {"name": "新农哥", "first_letter": "X", "logo": "xinnongge_logo.png"},
        {"name": "口水娃", "first_letter": "K", "logo": "koushuiwa_logo.png"},
        {"name": "小王子", "first_letter": "X", "logo": "xiaowangzi_logo.png"},
        {"name": "稻香村", "first_letter": "D", "logo": "daoxiangcun_logo.png"},
        {"name": "好利来", "first_letter": "H", "logo": "holiland_logo.png"},
        {"name": "味多美", "first_letter": "W", "logo": "weiduomei_logo.png"},
        {"name": "巴黎贝甜", "first_letter": "B", "logo": "parisbaguette_logo.png"},
        {"name": "85度C", "first_letter": "B", "logo": "85degree_logo.png"},
        {"name": "元祖", "first_letter": "Y", "logo": "ganso_logo.png"},
        {"name": "可颂坊", "first_letter": "K", "logo": "croissant_logo.png"},
        {"name": "面包新语", "first_letter": "M", "logo": "breadtalk_logo.png"},
        
        # 粮油调味品牌
        {"name": "金龙鱼", "first_letter": "J", "logo": "jinlongyu_logo.png"},
        {"name": "福临门", "first_letter": "F", "logo": "fulinmen_logo.png"},
        {"name": "鲁花", "first_letter": "L", "logo": "luhua_logo.png"},
        {"name": "胡姬花", "first_letter": "H", "logo": "hujihua_logo.png"},
        {"name": "多力", "first_letter": "D", "logo": "duoli_logo.png"},
        {"name": "西王", "first_letter": "X", "logo": "xiwang_logo.png"},
        {"name": "海天", "first_letter": "H", "logo": "haitian_logo.png"},
        {"name": "李锦记", "first_letter": "L", "logo": "lee_kum_kee_logo.png"},
        {"name": "太太乐", "first_letter": "T", "logo": "totole_logo.png"},
        {"name": "厨邦", "first_letter": "C", "logo": "chubang_logo.png"},
        {"name": "恒顺", "first_letter": "H", "logo": "hengshun_logo.png"},
        {"name": "王致和", "first_letter": "W", "logo": "wangzhihe_logo.png"},
        {"name": "老干妈", "first_letter": "L", "logo": "lao_gan_ma_logo.png"},
        
        # 功能饮料品牌
        {"name": "东鹏特饮", "first_letter": "D", "logo": "dongpeng_logo.png"},
        {"name": "乐虎", "first_letter": "L", "logo": "lehu_logo.png"},
        {"name": "脉动", "first_letter": "M", "logo": "maidong_logo.png"},
        {"name": "尖叫", "first_letter": "J", "logo": "jianjiao_logo.png"},
        
        # 茶饮品牌
        {"name": "三得利", "first_letter": "S", "logo": "suntory_logo.png"},
        {"name": "东方树叶", "first_letter": "D", "logo": "dongfangshuye_logo.png"},
        {"name": "小茗同学", "first_letter": "X", "logo": "xiaoming_logo.png"},
        
        # 果汁品牌
        {"name": "美汁源", "first_letter": "M", "logo": "meizhiyuan_logo.png"},
        {"name": "农夫果园", "first_letter": "N", "logo": "nongguoyuan_logo.png"},
        {"name": "酷儿", "first_letter": "K", "logo": "qoo_logo.png"},
        
        # 啤酒品牌
        {"name": "燕京", "first_letter": "Y", "logo": "yanjing_logo.png"},
        {"name": "科罗娜", "first_letter": "K", "logo": "corona_logo.png"},
        {"name": "福佳白", "first_letter": "F", "logo": "hoegaarden_logo.png"},
        
        # 红酒品牌
        {"name": "奔富", "first_letter": "B", "logo": "penfolds_logo.png"},
        {"name": "拉菲", "first_letter": "L", "logo": "lafite_logo.png"},
        {"name": "黄尾袋鼠", "first_letter": "H", "logo": "yellowtail_logo.png"},
        {"name": "蒙特斯", "first_letter": "M", "logo": "montes_logo.png"},
        
        # 洗衣用品品牌
        {"name": "超能", "first_letter": "C", "logo": "chaoneng_logo.png"},
        
        # 纸品品牌
        {"name": "得宝", "first_letter": "D", "logo": "debao_logo.png"},
        
        # 乳制品品牌
        {"name": "三元", "first_letter": "S", "logo": "sanyuan_logo.png"},
        {"name": "君乐宝", "first_letter": "J", "logo": "junlebao_logo.png"},
        
        # 洗洁精品牌
        {"name": "雕牌", "first_letter": "D", "logo": "diaopai_logo.png"},
        {"name": "威猛先生", "first_letter": "W", "logo": "weimeng_logo.png"},
        {"name": "白猫", "first_letter": "B", "logo": "baimao_logo.png"},
        
        # 白酒品牌
        {"name": "古井贡", "first_letter": "G", "logo": "gujinggong_logo.png"},
        {"name": "水井坊", "first_letter": "S", "logo": "shuijingfang_logo.png"},
        {"name": "舍得", "first_letter": "S", "logo": "shede_logo.png"},
        {"name": "酒鬼", "first_letter": "J", "logo": "jiugui_logo.png"},
        
        # 口腔护理品牌
        {"name": "高露洁", "first_letter": "G", "logo": "colgate_logo.png"},
        {"name": "佳洁士", "first_letter": "J", "logo": "crest_logo.png"},
        {"name": "黑人牙膏", "first_letter": "H", "logo": "darlie_logo.png"},
        {"name": "云南白药", "first_letter": "Y", "logo": "yunnanbaiyao_logo.png"},
        {"name": "舒客", "first_letter": "S", "logo": "saky_logo.png"},
        
        # 牙刷品牌
        {"name": "欧乐B", "first_letter": "O", "logo": "oralb_logo.png"},
        {"name": "高露洁", "first_letter": "G", "logo": "colgate_logo.png"},
        {"name": "舒客", "first_letter": "S", "logo": "saky_logo.png"},
        {"name": "狮王", "first_letter": "S", "logo": "lion_logo.png"},
        {"name": "竹珍", "first_letter": "Z", "logo": "zhuzhen_logo.png"},
        
        # 洗护品牌
        {"name": "资生堂", "first_letter": "Z", "logo": "shiseido_logo.png"},
        {"name": "施华蔻", "first_letter": "S", "logo": "schwarzkopf_logo.png"},
        
        # 罐头品牌
        {"name": "梅林", "first_letter": "M", "logo": "meilin_logo.png"},
        {"name": "古龙", "first_letter": "G", "logo": "gulong_logo.png"},
        {"name": "鹰金钱", "first_letter": "Y", "logo": "yingjinqian_logo.png"},
        
        # 糖果巧克力品牌
        {"name": "阿尔卑斯", "first_letter": "A", "logo": "alpenliebe_logo.png"},
        {"name": "德芙", "first_letter": "D", "logo": "dove_logo.png"},
        {"name": "费列罗", "first_letter": "F", "logo": "ferrero_logo.png"},
        
        # 黄酒品牌
        {"name": "古越龙山", "first_letter": "G", "logo": "guyuelongshan_logo.png"},
        {"name": "会稽山", "first_letter": "H", "logo": "huijishan_logo.png"},
        
        # 肉制品品牌
        {"name": "双汇", "first_letter": "S", "logo": "shuanghui_logo.png"},
        {"name": "金锣", "first_letter": "J", "logo": "jinluo_logo.png"},
        
        # 沐浴露品牌
        {"name": "六神", "first_letter": "L", "logo": "liushen_logo.png"},
        
        # 碳酸饮料品牌
        {"name": "可口可乐", "first_letter": "K", "logo": "cocacola_logo.png"},
        {"name": "百事", "first_letter": "B", "logo": "pepsi_logo.png"},
        {"name": "雪碧", "first_letter": "X", "logo": "sprite_logo.png"},
        
        # 威士忌品牌
        {"name": "芝华士", "first_letter": "Z", "logo": "chivas_logo.png"},
        {"name": "尊尼获加", "first_letter": "Z", "logo": "johnniewalker_logo.png"},
        
        # 文具品牌
        {"name": "晨光", "first_letter": "C", "logo": "m&g_logo.png"},
        {"name": "得力", "first_letter": "D", "logo": "deli_logo.png"},
        {"name": "真彩", "first_letter": "Z", "logo": "truecolor_logo.png"},
        {"name": "百乐", "first_letter": "B", "logo": "pilot_logo.png"},
        {"name": "三菱", "first_letter": "S", "logo": "uni_logo.png"},
        {"name": "斑马", "first_letter": "B", "logo": "zebra_logo.png"},
        
        # 膨化食品品牌
        {"name": "上好佳", "first_letter": "S", "logo": "oishi_logo.png"},
        {"name": "奇多", "first_letter": "Q", "logo": "cheetos_logo.png"},
        
        # 护肤品品牌
        {"name": "大宝", "first_letter": "D", "logo": "dabao_logo.png"},
        {"name": "旁氏", "first_letter": "P", "logo": "ponds_logo.png"},
        
        # 白兰地品牌
        {"name": "马爹利", "first_letter": "M", "logo": "martell_logo.png"},
        {"name": "轩尼诗", "first_letter": "X", "logo": "hennessy_logo.png"},
        {"name": "人头马", "first_letter": "R", "logo": "remymartin_logo.png"},
        
        # 糕点品牌
        {"name": "好丽友", "first_letter": "H", "logo": "orion_logo.png"},
        
        # 咖啡品牌
        {"name": "雀巢", "first_letter": "Q", "logo": "nestle_logo.png"},
        {"name": "星巴克", "first_letter": "X", "logo": "starbucks_logo.png"},
        
        # 伏特加品牌
        {"name": "绝对", "first_letter": "J", "logo": "absolut_logo.png"},
        {"name": "斯米诺", "first_letter": "S", "logo": "smirnoff_logo.png"},
        
        # 计算器品牌
        {"name": "卡西欧", "first_letter": "K", "logo": "casio_logo.png"},
        
        # 糖果品牌
        {"name": "徐福记", "first_letter": "X", "logo": "hsufuchi_logo.png"},
        {"name": "金丝猴", "first_letter": "J", "logo": "goldenmonkey_logo.png"},
        
        # 洗手液品牌
        {"name": "威露士", "first_letter": "W", "logo": "walch_logo.png"},
        
        # 坚果品牌
        {"name": "三只松鼠", "first_letter": "S", "logo": "three_squirrels_logo.png"},
        {"name": "良品铺子", "first_letter": "L", "logo": "bestore_logo.png"},
        {"name": "百草味", "first_letter": "B", "logo": "becheery_logo.png"},
        
        # 饼干品牌
        {"name": "奥利奥", "first_letter": "A", "logo": "oreo_logo.png"},
        {"name": "乐事", "first_letter": "L", "logo": "lays_logo.png"},
        {"name": "盼盼", "first_letter": "P", "logo": "panpan_logo.png"},
        {"name": "旺旺", "first_letter": "W", "logo": "wantwant_logo.png"},
        
        # 洗衣液品牌
        {"name": "立白", "first_letter": "L", "logo": "liby_logo.png"},
        {"name": "雕牌", "first_letter": "D", "logo": "diaopai_logo.png"},
        {"name": "蓝月亮", "first_letter": "L", "logo": "bluemoon_logo.png"},
        
        # 牙膏品牌
        {"name": "高露洁", "first_letter": "G", "logo": "colgate_logo.png"},
        {"name": "佳洁士", "first_letter": "J", "logo": "crest_logo.png"},
        {"name": "黑人", "first_letter": "H", "logo": "darlie_logo.png"},
        
        # 牙刷品牌
        {"name": "欧乐B", "first_letter": "O", "logo": "oralb_logo.png"},
        {"name": "高露洁", "first_letter": "G", "logo": "colgate_logo.png"},
        
        # 果汁品牌
        {"name": "美汁源", "first_letter": "M", "logo": "minute_maid_logo.png"},
        {"name": "农夫果园", "first_letter": "N", "logo": "nongfu_orchard_logo.png"},
        {"name": "汇源", "first_letter": "H", "logo": "huiyuan_logo.png"},
        
        # 功能饮料品牌
        {"name": "红牛", "first_letter": "H", "logo": "red_bull_logo.png"},
        {"name": "东鹏特饮", "first_letter": "D", "logo": "dongpeng_logo.png"},
        {"name": "乐虎", "first_letter": "L", "logo": "lehu_logo.png"},
        
        # 啤酒品牌
        {"name": "青岛啤酒", "first_letter": "Q", "logo": "tsingtao_logo.png"},
        {"name": "雪花啤酒", "first_letter": "X", "logo": "snow_logo.png"},
        {"name": "燕京啤酒", "first_letter": "Y", "logo": "yanjing_logo.png"},
        {"name": "百威啤酒", "first_letter": "B", "logo": "budweiser_logo.png"},
        {"name": "喜力啤酒", "first_letter": "X", "logo": "heineken_logo.png"},
        
        # 红酒品牌
        {"name": "长城", "first_letter": "C", "logo": "greatwall_logo.png"},
        {"name": "张裕", "first_letter": "Z", "logo": "changyu_logo.png"},
        
        # 白酒品牌
        {"name": "茅台", "first_letter": "M", "logo": "moutai_logo.png"},
        {"name": "五粮液", "first_letter": "W", "logo": "wuliangye_logo.png"},
        {"name": "剑南春", "first_letter": "J", "logo": "jiannanchun_logo.png"},
        {"name": "泸州老窖", "first_letter": "L", "logo": "luzhoulaojiao_logo.png"},
    ],
    
    "products": [
        # 小米手机系列
        {
            "brand": "小米",
            "category1": "手机",
            "category2": "手机通讯",
            "category3": "智能手机",
            "spu_name": "小米14 Pro",
            "desc_detail": "小米14 Pro，徕卡光学镜头，骁龙8 Gen3处理器，2K超清屏幕，120W快充",
            "desc_pack": "包装清单：手机、充电器、数据线、保护壳、说明书",
            "desc_service": "7天无理由退货，15天换货，1年质保",
            "skus": [
                {
                    "name": "小米14 Pro 12GB+256GB 黑色",
                    "caption": "徕卡光学镜头｜骁龙8 Gen3｜2K超清屏",
                    "price": 4999.00,
                    "cost_price": 4200.00,
                    "market_price": 5999.00,
                    "stock": 100,
                    "specs": {"颜色": "黑色", "内存": "12GB+256GB"},
                    "barcode": "6941812701234"
                },
                {
                    "name": "小米14 Pro 16GB+512GB 白色",
                    "caption": "徕卡光学镜头｜骁龙8 Gen3｜2K超清屏",
                    "price": 5999.00,
                    "cost_price": 5000.00,
                    "market_price": 6999.00,
                    "stock": 80,
                    "specs": {"颜色": "白色", "内存": "16GB+512GB"},
                    "barcode": "6941812701235"
                },
            ]
        },
        {
            "brand": "小米",
            "category1": "手机",
            "category2": "手机通讯",
            "category3": "智能手机",
            "spu_name": "Redmi K70 Pro",
            "desc_detail": "Redmi K70 Pro，骁龙8 Gen3，2K高光屏，120W快充，5000mAh大电池",
            "desc_pack": "包装清单：手机、充电器、数据线、保护壳、说明书",
            "desc_service": "7天无理由退货，15天换货，1年质保",
            "skus": [
                {
                    "name": "Redmi K70 Pro 12GB+256GB 墨羽",
                    "caption": "骁龙8 Gen3｜2K高光屏｜120W快充",
                    "price": 3299.00,
                    "cost_price": 2800.00,
                    "market_price": 3899.00,
                    "stock": 150,
                    "specs": {"颜色": "墨羽", "内存": "12GB+256GB"},
                    "barcode": "6941812702345"
                },
                {
                    "name": "Redmi K70 Pro 16GB+512GB 晴雪",
                    "caption": "骁龙8 Gen3｜2K高光屏｜120W快充",
                    "price": 3699.00,
                    "cost_price": 3100.00,
                    "market_price": 4299.00,
                    "stock": 120,
                    "specs": {"颜色": "晴雪", "内存": "16GB+512GB"},
                    "barcode": "6941812702346"
                },
            ]
        },
        # OPPO手机系列
        {
            "brand": "OPPO",
            "category1": "手机",
            "category2": "手机通讯",
            "category3": "智能手机",
            "spu_name": "OPPO Find X7 Pro",
            "desc_detail": "OPPO Find X7 Pro，哈苏影像系统，骁龙8 Gen3，2K曲面屏，100W快充",
            "desc_pack": "包装清单：手机、充电器、数据线、保护壳、说明书",
            "desc_service": "7天无理由退货，15天换货，1年质保",
            "skus": [
                {
                    "name": "OPPO Find X7 Pro 16GB+512GB 银色",
                    "caption": "哈苏影像｜骁龙8 Gen3｜2K曲面屏",
                    "price": 5999.00,
                    "cost_price": 5100.00,
                    "market_price": 6999.00,
                    "stock": 90,
                    "specs": {"颜色": "银色", "内存": "16GB+512GB"},
                    "barcode": "6941812703456"
                },
            ]
        },
        # vivo手机系列
        {
            "brand": "vivo",
            "category1": "手机",
            "category2": "手机通讯",
            "category3": "智能手机",
            "spu_name": "vivo X100 Pro",
            "desc_detail": "vivo X100 Pro，蔡司影像，天玑9300，2K曲面屏，120W快充",
            "desc_pack": "包装清单：手机、充电器、数据线、保护壳、说明书",
            "desc_service": "7天无理由退货，15天换货，1年质保",
            "skus": [
                {
                    "name": "vivo X100 Pro 16GB+512GB 蓝色",
                    "caption": "蔡司影像｜天玑9300｜2K曲面屏",
                    "price": 5499.00,
                    "cost_price": 4600.00,
                    "market_price": 6499.00,
                    "stock": 85,
                    "specs": {"颜色": "蓝色", "内存": "16GB+512GB"},
                    "barcode": "6941812704567"
                },
            ]
        },
        # 联想笔记本
        {
            "brand": "联想",
            "category1": "电脑",
            "category2": "电脑",
            "category3": "笔记本",
            "spu_name": "联想ThinkPad X1 Carbon",
            "desc_detail": "联想ThinkPad X1 Carbon，Intel i7处理器，16GB内存，1TB SSD，14英寸2.8K OLED屏",
            "desc_pack": "包装清单：笔记本、电源适配器、说明书",
            "desc_service": "7天无理由退货，15天换坏，2年质保",
            "skus": [
                {
                    "name": "联想ThinkPad X1 Carbon i7/16GB/1TB 黑色",
                    "caption": "商务旗舰｜Intel i7｜2.8K OLED屏",
                    "price": 12999.00,
                    "cost_price": 11000.00,
                    "market_price": 14999.00,
                    "stock": 50,
                    "specs": {"颜色": "黑色", "配置": "i7/16GB/1TB"},
                    "barcode": "6941812705678"
                },
            ]
        },
        # 戴尔笔记本
        {
            "brand": "戴尔",
            "category1": "电脑",
            "category2": "电脑",
            "category3": "笔记本",
            "spu_name": "戴尔XPS 15",
            "desc_detail": "戴尔XPS 15，Intel i9处理器，32GB内存，1TB SSD，15.6英寸3.5K OLED触控屏",
            "desc_pack": "包装清单：笔记本、电源适配器、说明书",
            "desc_service": "7天无理由退货，15天换货，2年质保",
            "skus": [
                {
                    "name": "戴尔XPS 15 i9/32GB/1TB 银色",
                    "caption": "创作旗舰｜Intel i9｜3.5K OLED触控",
                    "price": 18999.00,
                    "cost_price": 16000.00,
                    "market_price": 21999.00,
                    "stock": 30,
                    "specs": {"颜色": "银色", "配置": "i9/32GB/1TB"},
                    "barcode": "6941812706789"
                },
            ]
        },
        # 美的空调
        {
            "brand": "美的",
            "category1": "家用电器",
            "category2": "空调",
            "category3": "变频空调",
            "spu_name": "美的1.5匹 变频空调",
            "desc_detail": "美的1.5匹变频空调，一级能效，智能控制，静音运行，自清洁功能",
            "desc_pack": "包装清单：室内机、室外机、遥控器、安装配件",
            "desc_service": "7天无理由退货，6年质保，免费安装",
            "skus": [
                {
                    "name": "美的1.5匹变频空调 KFR-35GW/N8MHA1 白色",
                    "caption": "一级能效｜智能控制｜自清洁",
                    "price": 2999.00,
                    "cost_price": 2400.00,
                    "market_price": 3599.00,
                    "stock": 200,
                    "specs": {"颜色": "白色", "匹数": "1.5匹"},
                    "barcode": "6941812707890"
                },
            ]
        },
        # 格力空调
        {
            "brand": "格力",
            "category1": "家用电器",
            "category2": "空调",
            "category3": "变频空调",
            "spu_name": "格力1.5匹 变频空调",
            "desc_detail": "格力1.5匹变频空调，一级能效，智能控制，静音运行，自清洁功能",
            "desc_pack": "包装清单：室内机、室外机、遥控器、安装配件",
            "desc_service": "7天无理由退货，6年质保，免费安装",
            "skus": [
                {
                    "name": "格力1.5匹变频空调 KFR-35GW/NhGc1B 白色",
                    "caption": "一级能效｜智能控制｜自清洁",
                    "price": 3299.00,
                    "cost_price": 2700.00,
                    "market_price": 3899.00,
                    "stock": 180,
                    "specs": {"颜色": "白色", "匹数": "1.5匹"},
                    "barcode": "6941812708901"
                },
            ]
        },
        # 海尔冰箱
        {
            "brand": "海尔",
            "category1": "家用电器",
            "category2": "冰箱",
            "category3": "多门冰箱",
            "spu_name": "海尔400L 多门冰箱",
            "desc_detail": "海尔400L多门冰箱，变频压缩机，智能控温，静音运行，无霜技术",
            "desc_pack": "包装清单：冰箱、说明书、保修卡",
            "desc_service": "7天无理由退货，3年质保，免费送货",
            "skus": [
                {
                    "name": "海尔400L多门冰箱 BCD-400WDPD 银色",
                    "caption": "变频压缩机｜智能控温｜无霜",
                    "price": 3999.00,
                    "cost_price": 3200.00,
                    "market_price": 4599.00,
                    "stock": 80,
                    "specs": {"颜色": "银色", "容量": "400L"},
                    "barcode": "6941812709012"
                },
            ]
        },
        # 耐克运动鞋
        {
            "brand": "耐克",
            "category1": "运动",
            "category2": "运动鞋",
            "category3": "跑步鞋",
            "spu_name": "耐克Air Max 270",
            "desc_detail": "耐克Air Max 270跑步鞋，气垫缓震，透气网面，轻量化设计",
            "desc_pack": "包装清单：鞋盒、鞋子",
            "desc_service": "7天无理由退货，30天质保",
            "skus": [
                {
                    "name": "耐克Air Max 270 42码 黑色",
                    "caption": "气垫缓震｜透气网面｜轻量化",
                    "price": 899.00,
                    "cost_price": 600.00,
                    "market_price": 1099.00,
                    "stock": 200,
                    "specs": {"颜色": "黑色", "尺码": "42码"},
                    "barcode": "6941812710123"
                },
                {
                    "name": "耐克Air Max 270 43码 白色",
                    "caption": "气垫缓震｜透气网面｜轻量化",
                    "price": 899.00,
                    "cost_price": 600.00,
                    "market_price": 1099.00,
                    "stock": 180,
                    "specs": {"颜色": "白色", "尺码": "43码"},
                    "barcode": "6941812710124"
                },
            ]
        },
        # 阿迪达斯运动鞋
        {
            "brand": "阿迪达斯",
            "category1": "运动",
            "category2": "运动鞋",
            "category3": "跑步鞋",
            "spu_name": "阿迪达斯Ultraboost",
            "desc_detail": "阿迪达斯Ultraboost跑步鞋，Boost缓震科技，Primeknit鞋面， Continental橡胶大底",
            "desc_pack": "包装清单：鞋盒、鞋子",
            "desc_service": "7天无理由退货，30天质保",
            "skus": [
                {
                    "name": "阿迪达斯Ultraboost 22 42码 黑色",
                    "caption": "Boost缓震｜Primeknit鞋面｜Continental大底",
                    "price": 1099.00,
                    "cost_price": 750.00,
                    "market_price": 1299.00,
                    "stock": 150,
                    "specs": {"颜色": "黑色", "尺码": "42码"},
                    "barcode": "6941812711234"
                },
            ]
        },
        # 三只松鼠零食
        {
            "brand": "三只松鼠",
            "category1": "食品",
            "category2": "零食",
            "category3": "坚果",
            "spu_name": "三只松鼠每日坚果",
            "desc_detail": "三只松鼠每日坚果，混合坚果礼盒，营养均衡，独立小包装",
            "desc_pack": "包装清单：坚果礼盒",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "三只松鼠每日坚果 750g 混合装",
                    "caption": "营养均衡｜独立小包装｜送礼首选",
                    "price": 128.00,
                    "cost_price": 80.00,
                    "market_price": 168.00,
                    "stock": 500,
                    "specs": {"规格": "750g", "类型": "混合装"},
                    "barcode": "6941812712345",
                    "shelf_life": 180,
                },
                {
                    "name": "三只松鼠每日坚果 1000g 混合装",
                    "caption": "营养均衡｜独立小包装｜送礼首选",
                    "price": 168.00,
                    "cost_price": 110.00,
                    "market_price": 208.00,
                    "stock": 400,
                    "specs": {"规格": "1000g", "类型": "混合装"},
                    "barcode": "6941812712346",
                    "shelf_life": 180,
                },
            ]
        },
        # 良品铺子零食
        {
            "brand": "良品铺子",
            "category1": "食品",
            "category2": "零食",
            "category3": "肉脯",
            "spu_name": "良品铺子猪肉脯",
            "desc_detail": "良品铺子猪肉脯，精选猪肉，传统工艺，口感鲜美",
            "desc_pack": "包装清单：猪肉脯礼盒",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "良品铺子猪肉脯 500g 原味",
                    "caption": "精选猪肉｜传统工艺｜口感鲜美",
                    "price": 68.00,
                    "cost_price": 40.00,
                    "market_price": 88.00,
                    "stock": 300,
                    "specs": {"规格": "500g", "口味": "原味"},
                    "barcode": "6941812713456",
                    "shelf_life": 90,
                },
            ]
        },
        # 欧莱雅化妆品
        {
            "brand": "欧莱雅",
            "category1": "美妆",
            "category2": "护肤品",
            "category3": "面霜",
            "spu_name": "欧莱雅复颜玻尿酸面霜",
            "desc_detail": "欧莱雅复颜玻尿酸面霜，含玻尿酸成分，保湿滋润，抗衰老",
            "desc_pack": "包装清单：面霜",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "欧莱雅复颜玻尿酸面霜 50ml",
                    "caption": "玻尿酸成分｜保湿滋润｜抗衰老",
                    "price": 299.00,
                    "cost_price": 180.00,
                    "market_price": 359.00,
                    "stock": 200,
                    "specs": {"规格": "50ml"},
                    "barcode": "6941812714567",
                    "shelf_life": 1095,
                },
            ]
        },
        # 雅诗兰黛化妆品
        {
            "brand": "雅诗兰黛",
            "category1": "美妆",
            "category2": "护肤品",
            "category3": "精华液",
            "spu_name": "雅诗兰黛小棕瓶精华",
            "desc_detail": "雅诗兰黛小棕瓶精华，修护肌肤，抗衰老，提亮肤色",
            "desc_pack": "包装清单：精华液",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "雅诗兰黛小棕瓶精华 30ml",
                    "caption": "修护肌肤｜抗衰老｜提亮肤色",
                    "price": 780.00,
                    "cost_price": 500.00,
                    "market_price": 880.00,
                    "stock": 100,
                    "specs": {"规格": "30ml"},
                    "barcode": "6941812715678",
                    "shelf_life": 1095,
                },
                {
                    "name": "雅诗兰黛小棕瓶精华 50ml",
                    "caption": "修护肌肤｜抗衰老｜提亮肤色",
                    "price": 1080.00,
                    "cost_price": 700.00,
                    "market_price": 1280.00,
                    "stock": 80,
                    "specs": {"规格": "50ml"},
                    "barcode": "6941812715679",
                    "shelf_life": 1095,
                },
            ]
        },
        # 李宁运动服
        {
            "brand": "李宁",
            "category1": "运动",
            "category2": "运动服",
            "category3": "T恤",
            "spu_name": "李宁运动T恤",
            "desc_detail": "李宁运动T恤，透气排汗，舒适面料，时尚设计",
            "desc_pack": "包装清单：T恤",
            "desc_service": "7天无理由退货，30天质保",
            "skus": [
                {
                    "name": "李宁运动T恤 L码 黑色",
                    "caption": "透气排汗｜舒适面料｜时尚设计",
                    "price": 199.00,
                    "cost_price": 120.00,
                    "market_price": 259.00,
                    "stock": 300,
                    "specs": {"颜色": "黑色", "尺码": "L码"},
                    "barcode": "6941812716789"
                },
                {
                    "name": "李宁运动T恤 XL码 白色",
                    "caption": "透气排汗｜舒适面料｜时尚设计",
                    "price": 199.00,
                    "cost_price": 120.00,
                    "market_price": 259.00,
                    "stock": 280,
                    "specs": {"颜色": "白色", "尺码": "XL码"},
                    "barcode": "6941812716790"
                },
            ]
        },
        # 优衣库服装
        {
            "brand": "优衣库",
            "category1": "男装",
            "category2": "T恤",
            "category3": "纯棉T恤",
            "spu_name": "优衣库纯棉T恤",
            "desc_detail": "优衣库纯棉T恤，100%纯棉，舒适透气，简约设计",
            "desc_pack": "包装清单：T恤",
            "desc_service": "7天无理由退货，30天质保",
            "skus": [
                {
                    "name": "优衣库纯棉T恤 L码 白色",
                    "caption": "100%纯棉｜舒适透气｜简约设计",
                    "price": 79.00,
                    "cost_price": 40.00,
                    "market_price": 99.00,
                    "stock": 400,
                    "specs": {"颜色": "白色", "尺码": "L码"},
                    "barcode": "6941812717890"
                },
                {
                    "name": "优衣库纯棉T恤 XL码 黑色",
                    "caption": "100%纯棉｜舒适透气｜简约设计",
                    "price": 79.00,
                    "cost_price": 40.00,
                    "market_price": 99.00,
                    "stock": 380,
                    "specs": {"颜色": "黑色", "尺码": "XL码"},
                    "barcode": "6941812717891"
                },
            ]
        },
        # 海信电视
        {
            "brand": "海信",
            "category1": "家用电器",
            "category2": "电视",
            "category3": "智能电视",
            "spu_name": "海信65英寸智能电视",
            "desc_detail": "海信65英寸4K智能电视，HDR画质，智能语音，超薄机身",
            "desc_pack": "包装清单：电视、遥控器、底座、说明书",
            "desc_service": "7天无理由退货，1年质保，免费安装",
            "skus": [
                {
                    "name": "海信65英寸4K智能电视 LED65E7F 黑色",
                    "caption": "4K画质｜HDR｜智能语音｜超薄",
                    "price": 3999.00,
                    "cost_price": 3200.00,
                    "market_price": 4599.00,
                    "stock": 60,
                    "specs": {"颜色": "黑色", "尺寸": "65英寸"},
                    "barcode": "6941812718901"
                },
            ]
        },
        
        # ==================== 食品类商品 ====================
        
        # 旺旺零食
        {
            "brand": "旺旺",
            "category1": "食品",
            "category2": "零食",
            "category3": "膨化食品",
            "spu_name": "旺旺仙贝",
            "desc_detail": "旺旺仙贝，经典米饼，香脆可口，怀旧零食",
            "desc_pack": "包装清单：旺旺仙贝",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "旺旺仙贝 400g 原味",
                    "caption": "经典米饼｜香脆可口｜怀旧零食",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 15.90,
                    "stock": 500,
                    "specs": {"规格": "400g", "口味": "原味"},
                    "barcode": "6901234567890",
                    "shelf_life": 180,
                },
                {
                    "name": "旺旺仙贝 800g 原味",
                    "caption": "经典米饼｜香脆可口｜怀旧零食",
                    "price": 23.90,
                    "cost_price": 15.00,
                    "market_price": 28.90,
                    "stock": 400,
                    "specs": {"规格": "800g", "口味": "原味"},
                    "barcode": "6901234567891",
                    "shelf_life": 180,
                },
            ]
        },
        {
            "brand": "旺旺",
            "category1": "食品",
            "category2": "零食",
            "category3": "膨化食品",
            "spu_name": "旺旺雪饼",
            "desc_detail": "旺旺雪饼，外脆内软，甜咸适中，经典零食",
            "desc_pack": "包装清单：旺旺雪饼",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "旺旺雪饼 400g 原味",
                    "caption": "外脆内软｜甜咸适中｜经典零食",
                    "price": 13.90,
                    "cost_price": 8.50,
                    "market_price": 16.90,
                    "stock": 450,
                    "specs": {"规格": "400g", "口味": "原味"},
                    "barcode": "6901234567892",
                    "shelf_life": 180,
                },
            ]
        },
        {
            "brand": "旺旺",
            "category1": "食品",
            "category2": "零食",
            "category3": "糖果",
            "spu_name": "旺仔牛奶糖",
            "desc_detail": "旺仔牛奶糖，浓郁奶香，口感丝滑，经典糖果",
            "desc_pack": "包装清单：旺仔牛奶糖",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "旺仔牛奶糖 200g",
                    "caption": "浓郁奶香｜口感丝滑｜经典糖果",
                    "price": 15.90,
                    "cost_price": 10.00,
                    "market_price": 19.90,
                    "stock": 600,
                    "specs": {"规格": "200g"},
                    "barcode": "6901234567893",
                    "shelf_life": 365,
                },
                {
                    "name": "旺仔牛奶糖 500g",
                    "caption": "浓郁奶香｜口感丝滑｜经典糖果",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 42.90,
                    "stock": 500,
                    "specs": {"规格": "500g"},
                    "barcode": "6901234567894",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 奥利奥饼干
        {
            "brand": "奥利奥",
            "category1": "食品",
            "category2": "零食",
            "category3": "饼干",
            "spu_name": "奥利奥饼干",
            "desc_detail": "奥利奥饼干，经典夹心饼干，扭一扭舔一舔泡一泡",
            "desc_pack": "包装清单：奥利奥饼干",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "奥利奥原味饼干 133g",
                    "caption": "经典夹心｜扭一扭舔一舔泡一泡",
                    "price": 8.90,
                    "cost_price": 5.50,
                    "market_price": 10.90,
                    "stock": 800,
                    "specs": {"规格": "133g", "口味": "原味"},
                    "barcode": "6901234567895",
                    "shelf_life": 365,
                },
                {
                    "name": "奥利奥原味饼干 299g",
                    "caption": "经典夹心｜扭一扭舔一舔泡一泡",
                    "price": 18.90,
                    "cost_price": 12.00,
                    "market_price": 22.90,
                    "stock": 700,
                    "specs": {"规格": "299g", "口味": "原味"},
                    "barcode": "6901234567896",
                    "shelf_life": 365,
                },
                {
                    "name": "奥利奥草莓味饼干 133g",
                    "caption": "草莓夹心｜甜而不腻｜经典美味",
                    "price": 9.90,
                    "cost_price": 6.00,
                    "market_price": 11.90,
                    "stock": 600,
                    "specs": {"规格": "133g", "口味": "草莓味"},
                    "barcode": "6901234567897",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 乐事薯片
        {
            "brand": "乐事",
            "category1": "食品",
            "category2": "零食",
            "category3": "薯片",
            "spu_name": "乐事薯片",
            "desc_detail": "乐事薯片，精选马铃薯，薄脆可口，多种口味",
            "desc_pack": "包装清单：乐事薯片",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "乐事原味薯片 70g",
                    "caption": "精选马铃薯｜薄脆可口｜经典原味",
                    "price": 8.50,
                    "cost_price": 5.00,
                    "market_price": 10.50,
                    "stock": 900,
                    "specs": {"规格": "70g", "口味": "原味"},
                    "barcode": "6901234567898",
                    "shelf_life": 180,
                },
                {
                    "name": "乐事黄瓜味薯片 70g",
                    "caption": "清爽黄瓜｜薄脆可口｜夏日必备",
                    "price": 8.50,
                    "cost_price": 5.00,
                    "market_price": 10.50,
                    "stock": 850,
                    "specs": {"规格": "70g", "口味": "黄瓜味"},
                    "barcode": "6901234567899",
                    "shelf_life": 180,
                },
                {
                    "name": "乐事番茄味薯片 70g",
                    "caption": "酸甜番茄｜薄脆可口｜经典美味",
                    "price": 8.50,
                    "cost_price": 5.00,
                    "market_price": 10.50,
                    "stock": 880,
                    "specs": {"规格": "70g", "口味": "番茄味"},
                    "barcode": "6901234567900",
                    "shelf_life": 180,
                },
                {
                    "name": "乐事烤肉味薯片 70g",
                    "caption": "香浓烤肉｜薄脆可口｜肉食爱好者",
                    "price": 9.50,
                    "cost_price": 5.50,
                    "market_price": 11.50,
                    "stock": 750,
                    "specs": {"规格": "70g", "口味": "烤肉味"},
                    "barcode": "6901234567901",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 康师傅方便面
        {
            "brand": "康师傅",
            "category1": "食品",
            "category2": "方便食品",
            "category3": "方便面",
            "spu_name": "康师傅红烧牛肉面",
            "desc_detail": "康师傅红烧牛肉面，经典口味，方便快捷，美味可口",
            "desc_pack": "包装清单：方便面",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "康师傅红烧牛肉面 105g",
                    "caption": "经典口味｜方便快捷｜美味可口",
                    "price": 3.50,
                    "cost_price": 2.00,
                    "market_price": 4.50,
                    "stock": 2000,
                    "specs": {"规格": "105g", "口味": "红烧牛肉"},
                    "barcode": "6901234567902",
                    "shelf_life": 180,
                },
                {
                    "name": "康师傅红烧牛肉面 5连包",
                    "caption": "经典口味｜家庭装｜实惠划算",
                    "price": 16.50,
                    "cost_price": 9.50,
                    "market_price": 20.50,
                    "stock": 1500,
                    "specs": {"规格": "5连包", "口味": "红烧牛肉"},
                    "barcode": "6901234567903",
                    "shelf_life": 180,
                },
            ]
        },
        {
            "brand": "康师傅",
            "category1": "食品",
            "category2": "方便食品",
            "category3": "方便面",
            "spu_name": "康师傅老坛酸菜牛肉面",
            "desc_detail": "康师傅老坛酸菜牛肉面，酸爽开胃，经典口味",
            "desc_pack": "包装清单：方便面",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "康师傅老坛酸菜牛肉面 105g",
                    "caption": "酸爽开胃｜经典口味｜美味可口",
                    "price": 3.50,
                    "cost_price": 2.00,
                    "market_price": 4.50,
                    "stock": 1800,
                    "specs": {"规格": "105g", "口味": "老坛酸菜"},
                    "barcode": "6901234567904",
                    "shelf_life": 180,
                },
                {
                    "name": "康师傅老坛酸菜牛肉面 5连包",
                    "caption": "酸爽开胃｜家庭装｜实惠划算",
                    "price": 16.50,
                    "cost_price": 9.50,
                    "market_price": 20.50,
                    "stock": 1300,
                    "specs": {"规格": "5连包", "口味": "老坛酸菜"},
                    "barcode": "6901234567905",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 统一方便面
        {
            "brand": "统一",
            "category1": "食品",
            "category2": "方便食品",
            "category3": "方便面",
            "spu_name": "统一老坛酸菜牛肉面",
            "desc_detail": "统一老坛酸菜牛肉面，酸爽开胃，经典口味",
            "desc_pack": "包装清单：方便面",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "统一老坛酸菜牛肉面 108g",
                    "caption": "酸爽开胃｜经典口味｜美味可口",
                    "price": 3.50,
                    "cost_price": 2.00,
                    "market_price": 4.50,
                    "stock": 1700,
                    "specs": {"规格": "108g", "口味": "老坛酸菜"},
                    "barcode": "6901234567906",
                    "shelf_life": 180,
                },
            ]
        },
        {
            "brand": "统一",
            "category1": "食品",
            "category2": "方便食品",
            "category3": "方便面",
            "spu_name": "统一红烧牛肉面",
            "desc_detail": "统一红烧牛肉面，经典口味，方便快捷",
            "desc_pack": "包装清单：方便面",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "统一红烧牛肉面 108g",
                    "caption": "经典口味｜方便快捷｜美味可口",
                    "price": 3.50,
                    "cost_price": 2.00,
                    "market_price": 4.50,
                    "stock": 1600,
                    "specs": {"规格": "108g", "口味": "红烧牛肉"},
                    "barcode": "6901234567907",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 卫龙辣条
        {
            "brand": "卫龙",
            "category1": "食品",
            "category2": "零食",
            "category3": "辣条",
            "spu_name": "卫龙大面筋",
            "desc_detail": "卫龙大面筋，香辣可口，面筋劲道，经典零食",
            "desc_pack": "包装清单：卫龙大面筋",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "卫龙大面筋 100g",
                    "caption": "香辣可口｜面筋劲道｜经典零食",
                    "price": 5.50,
                    "cost_price": 3.00,
                    "market_price": 7.50,
                    "stock": 1200,
                    "specs": {"规格": "100g", "口味": "香辣"},
                    "barcode": "6901234567908",
                    "shelf_life": 180,
                },
                {
                    "name": "卫龙大面筋 300g",
                    "caption": "香辣可口｜面筋劲道｜分享装",
                    "price": 15.50,
                    "cost_price": 8.50,
                    "market_price": 19.50,
                    "stock": 1000,
                    "specs": {"规格": "300g", "口味": "香辣"},
                    "barcode": "6901234567909",
                    "shelf_life": 180,
                },
            ]
        },
        {
            "brand": "卫龙",
            "category1": "食品",
            "category2": "零食",
            "category3": "辣条",
            "spu_name": "卫龙亲嘴烧",
            "desc_detail": "卫龙亲嘴烧，软糯香甜，口感独特，经典零食",
            "desc_pack": "包装清单：卫龙亲嘴烧",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "卫龙亲嘴烧 100g",
                    "caption": "软糯香甜｜口感独特｜经典零食",
                    "price": 5.50,
                    "cost_price": 3.00,
                    "market_price": 7.50,
                    "stock": 1100,
                    "specs": {"规格": "100g", "口味": "香甜"},
                    "barcode": "6901234567910",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 恰恰瓜子
        {
            "brand": "恰恰",
            "category1": "食品",
            "category2": "零食",
            "category3": "坚果炒货",
            "spu_name": "恰恰香瓜子",
            "desc_detail": "恰恰香瓜子，颗粒饱满，香脆可口，休闲零食",
            "desc_pack": "包装清单：恰恰香瓜子",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "恰恰香瓜子 200g",
                    "caption": "颗粒饱满｜香脆可口｜休闲零食",
                    "price": 9.90,
                    "cost_price": 6.00,
                    "market_price": 12.90,
                    "stock": 800,
                    "specs": {"规格": "200g", "口味": "原味"},
                    "barcode": "6901234567911",
                    "shelf_life": 180,
                },
                {
                    "name": "恰恰香瓜子 500g",
                    "caption": "颗粒饱满｜香脆可口｜家庭装",
                    "price": 22.90,
                    "cost_price": 14.00,
                    "market_price": 28.90,
                    "stock": 700,
                    "specs": {"规格": "500g", "口味": "原味"},
                    "barcode": "6901234567912",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 好想你枣
        {
            "brand": "好想你",
            "category1": "食品",
            "category2": "零食",
            "category3": "干果",
            "spu_name": "好想你红枣",
            "desc_detail": "好想你红枣，皮薄肉厚，香甜可口，营养健康",
            "desc_pack": "包装清单：好想你红枣",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "好想你红枣 500g",
                    "caption": "皮薄肉厚｜香甜可口｜营养健康",
                    "price": 29.90,
                    "cost_price": 18.00,
                    "market_price": 38.90,
                    "stock": 600,
                    "specs": {"规格": "500g"},
                    "barcode": "6901234567913",
                    "shelf_life": 365,
                },
                {
                    "name": "好想你红枣 1000g",
                    "caption": "皮薄肉厚｜香甜可口｜营养健康",
                    "price": 55.90,
                    "cost_price": 35.00,
                    "market_price": 68.90,
                    "stock": 500,
                    "specs": {"规格": "1000g"},
                    "barcode": "6901234567914",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 盐津铺子零食
        {
            "brand": "盐津铺子",
            "category1": "食品",
            "category2": "零食",
            "category3": "蜜饯",
            "spu_name": "盐津铺子芒果干",
            "desc_detail": "盐津铺子芒果干，酸甜可口，果肉厚实，休闲零食",
            "desc_pack": "包装清单：盐津铺子芒果干",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "盐津铺子芒果干 100g",
                    "caption": "酸甜可口｜果肉厚实｜休闲零食",
                    "price": 15.90,
                    "cost_price": 9.00,
                    "market_price": 19.90,
                    "stock": 700,
                    "specs": {"规格": "100g"},
                    "barcode": "6901234567915",
                    "shelf_life": 180,
                },
            ]
        },
        {
            "brand": "盐津铺子",
            "category1": "食品",
            "category2": "零食",
            "category3": "肉干",
            "spu_name": "盐津铺子猪肉干",
            "desc_detail": "盐津铺子猪肉干，香辣可口，肉质紧实，休闲零食",
            "desc_pack": "包装清单：盐津铺子猪肉干",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "盐津铺子猪肉干 100g",
                    "caption": "香辣可口｜肉质紧实｜休闲零食",
                    "price": 18.90,
                    "cost_price": 11.00,
                    "market_price": 23.90,
                    "stock": 650,
                    "specs": {"规格": "100g", "口味": "香辣"},
                    "barcode": "6901234567916",
                    "shelf_life": 90,
                },
            ]
        },
        
        # ==================== 牛奶饮料类商品 ====================
        
        # 蒙牛牛奶
        {
            "brand": "蒙牛",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "纯牛奶",
            "spu_name": "蒙牛纯牛奶",
            "desc_detail": "蒙牛纯牛奶，优质奶源，营养丰富，口感醇厚",
            "desc_pack": "包装清单：蒙牛纯牛奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "蒙牛纯牛奶 250ml*24盒",
                    "caption": "优质奶源｜营养丰富｜口感醇厚",
                    "price": 59.90,
                    "cost_price": 40.00,
                    "market_price": 72.90,
                    "stock": 800,
                    "specs": {"规格": "250ml*24盒"},
                    "barcode": "6901234567917",
                    "shelf_life": 180,
                },
                {
                    "name": "蒙牛纯牛奶 1L*6盒",
                    "caption": "优质奶源｜营养丰富｜家庭装",
                    "price": 65.90,
                    "cost_price": 45.00,
                    "market_price": 78.90,
                    "stock": 700,
                    "specs": {"规格": "1L*6盒"},
                    "barcode": "6901234567918",
                    "shelf_life": 180,
                },
            ]
        },
        {
            "brand": "蒙牛",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "酸奶",
            "spu_name": "蒙牛纯甄酸奶",
            "desc_detail": "蒙牛纯甄酸奶，无添加，口感纯正，营养健康",
            "desc_pack": "包装清单：蒙牛纯甄酸奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "蒙牛纯甄酸奶 200g*12杯",
                    "caption": "无添加｜口感纯正｜营养健康",
                    "price": 45.90,
                    "cost_price": 30.00,
                    "market_price": 55.90,
                    "stock": 750,
                    "specs": {"规格": "200g*12杯", "口味": "原味"},
                    "barcode": "6901234567919",
                    "shelf_life": 21,
                },
                {
                    "name": "蒙牛纯甄酸奶 200g*12杯 芒果味",
                    "caption": "无添加｜芒果风味｜营养健康",
                    "price": 47.90,
                    "cost_price": 32.00,
                    "market_price": 57.90,
                    "stock": 700,
                    "specs": {"规格": "200g*12杯", "口味": "芒果味"},
                    "barcode": "6901234567920",
                    "shelf_life": 21,
                },
            ]
        },
        
        # 伊利牛奶
        {
            "brand": "伊利",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "纯牛奶",
            "spu_name": "伊利纯牛奶",
            "desc_detail": "伊利纯牛奶，优质奶源，营养丰富，口感醇厚",
            "desc_pack": "包装清单：伊利纯牛奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "伊利纯牛奶 250ml*24盒",
                    "caption": "优质奶源｜营养丰富｜口感醇厚",
                    "price": 58.90,
                    "cost_price": 39.00,
                    "market_price": 71.90,
                    "stock": 850,
                    "specs": {"规格": "250ml*24盒"},
                    "barcode": "6901234567921",
                    "shelf_life": 180,
                },
                {
                    "name": "伊利纯牛奶 1L*6盒",
                    "caption": "优质奶源｜营养丰富｜家庭装",
                    "price": 64.90,
                    "cost_price": 44.00,
                    "market_price": 77.90,
                    "stock": 750,
                    "specs": {"规格": "1L*6盒"},
                    "barcode": "6901234567922",
                    "shelf_life": 180,
                },
            ]
        },
        {
            "brand": "伊利",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "酸奶",
            "spu_name": "伊利安慕希酸奶",
            "desc_detail": "伊利安慕希酸奶，希腊风味，口感浓郁，营养健康",
            "desc_pack": "包装清单：伊利安慕希酸奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "伊利安慕希酸奶 205g*12盒",
                    "caption": "希腊风味｜口感浓郁｜营养健康",
                    "price": 52.90,
                    "cost_price": 35.00,
                    "market_price": 63.90,
                    "stock": 800,
                    "specs": {"规格": "205g*12盒", "口味": "原味"},
                    "barcode": "6901234567923",
                    "shelf_life": 180,
                },
                {
                    "name": "伊利安慕希酸奶 205g*12盒 芒果味",
                    "caption": "希腊风味｜芒果口感｜营养健康",
                    "price": 54.90,
                    "cost_price": 36.00,
                    "market_price": 65.90,
                    "stock": 750,
                    "specs": {"规格": "205g*12盒", "口味": "芒果味"},
                    "barcode": "6901234567924",
                    "shelf_life": 180,
                },
                {
                    "name": "伊利安慕希酸奶 205g*12盒 草莓味",
                    "caption": "希腊风味｜草莓口感｜营养健康",
                    "price": 54.90,
                    "cost_price": 36.00,
                    "market_price": 65.90,
                    "stock": 720,
                    "specs": {"规格": "205g*12盒", "口味": "草莓味"},
                    "barcode": "6901234567925",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 光明牛奶
        {
            "brand": "光明",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "纯牛奶",
            "spu_name": "光明纯牛奶",
            "desc_detail": "光明纯牛奶，优质奶源，营养丰富，口感醇厚",
            "desc_pack": "包装清单：光明纯牛奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "光明纯牛奶 250ml*24盒",
                    "caption": "优质奶源｜营养丰富｜口感醇厚",
                    "price": 57.90,
                    "cost_price": 38.00,
                    "market_price": 70.90,
                    "stock": 700,
                    "specs": {"规格": "250ml*24盒"},
                    "barcode": "6901234567926",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 可口可乐
        {
            "brand": "可口可乐",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "碳酸饮料",
            "spu_name": "可口可乐",
            "desc_detail": "可口可乐，经典碳酸饮料，清爽解腻，畅爽口感",
            "desc_pack": "包装清单：可口可乐",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "可口可乐 330ml*24罐",
                    "caption": "经典碳酸｜清爽解腻｜畅爽口感",
                    "price": 45.90,
                    "cost_price": 30.00,
                    "market_price": 55.90,
                    "stock": 1500,
                    "specs": {"规格": "330ml*24罐"},
                    "barcode": "6901234567927",
                    "shelf_life": 365,
                },
                {
                    "name": "可口可乐 500ml*12瓶",
                    "caption": "经典碳酸｜清爽解腻｜畅爽口感",
                    "price": 38.90,
                    "cost_price": 25.00,
                    "market_price": 47.90,
                    "stock": 1400,
                    "specs": {"规格": "500ml*12瓶"},
                    "barcode": "6901234567928",
                    "shelf_life": 365,
                },
                {
                    "name": "可口可乐 2L*6瓶",
                    "caption": "经典碳酸｜家庭装｜畅爽口感",
                    "price": 42.90,
                    "cost_price": 28.00,
                    "market_price": 52.90,
                    "stock": 1200,
                    "specs": {"规格": "2L*6瓶"},
                    "barcode": "6901234567929",
                    "shelf_life": 365,
                },
            ]
        },
        {
            "brand": "可口可乐",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "碳酸饮料",
            "spu_name": "雪碧",
            "desc_detail": "雪碧，柠檬味碳酸饮料，清爽解腻，透心凉",
            "desc_pack": "包装清单：雪碧",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "雪碧 330ml*24罐",
                    "caption": "柠檬味碳酸｜清爽解腻｜透心凉",
                    "price": 45.90,
                    "cost_price": 30.00,
                    "market_price": 55.90,
                    "stock": 1450,
                    "specs": {"规格": "330ml*24罐"},
                    "barcode": "6901234567930",
                    "shelf_life": 365,
                },
                {
                    "name": "雪碧 500ml*12瓶",
                    "caption": "柠檬味碳酸｜清爽解腻｜透心凉",
                    "price": 38.90,
                    "cost_price": 25.00,
                    "market_price": 47.90,
                    "stock": 1350,
                    "specs": {"规格": "500ml*12瓶"},
                    "barcode": "6901234567931",
                    "shelf_life": 365,
                },
            ]
        },
        {
            "brand": "可口可乐",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "碳酸饮料",
            "spu_name": "芬达",
            "desc_detail": "芬达，橙味碳酸饮料，果香浓郁，清爽解腻",
            "desc_pack": "包装清单：芬达",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "芬达 330ml*24罐",
                    "caption": "橙味碳酸｜果香浓郁｜清爽解腻",
                    "price": 45.90,
                    "cost_price": 30.00,
                    "market_price": 55.90,
                    "stock": 1400,
                    "specs": {"规格": "330ml*24罐", "口味": "橙味"},
                    "barcode": "6901234567932",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 百事可乐
        {
            "brand": "百事可乐",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "碳酸饮料",
            "spu_name": "百事可乐",
            "desc_detail": "百事可乐，经典碳酸饮料，清爽解腻，年轻一代的选择",
            "desc_pack": "包装清单：百事可乐",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "百事可乐 330ml*24罐",
                    "caption": "经典碳酸｜清爽解腻｜年轻选择",
                    "price": 45.90,
                    "cost_price": 30.00,
                    "market_price": 55.90,
                    "stock": 1450,
                    "specs": {"规格": "330ml*24罐"},
                    "barcode": "6901234567933",
                    "shelf_life": 365,
                },
                {
                    "name": "百事可乐 500ml*12瓶",
                    "caption": "经典碳酸｜清爽解腻｜年轻选择",
                    "price": 38.90,
                    "cost_price": 25.00,
                    "market_price": 47.90,
                    "stock": 1350,
                    "specs": {"规格": "500ml*12瓶"},
                    "barcode": "6901234567934",
                    "shelf_life": 365,
                },
            ]
        },
        {
            "brand": "百事可乐",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "碳酸饮料",
            "spu_name": "美年达",
            "desc_detail": "美年达，橙味碳酸饮料，果香浓郁，清爽解腻",
            "desc_pack": "包装清单：美年达",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "美年达 330ml*24罐",
                    "caption": "橙味碳酸｜果香浓郁｜清爽解腻",
                    "price": 45.90,
                    "cost_price": 30.00,
                    "market_price": 55.90,
                    "stock": 1300,
                    "specs": {"规格": "330ml*24罐", "口味": "橙味"},
                    "barcode": "6901234567935",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 农夫山泉
        {
            "brand": "农夫山泉",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "矿泉水",
            "spu_name": "农夫山泉矿泉水",
            "desc_detail": "农夫山泉矿泉水，天然水源，甘甜清冽，健康饮水",
            "desc_pack": "包装清单：农夫山泉矿泉水",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "农夫山泉 550ml*24瓶",
                    "caption": "天然水源｜甘甜清冽｜健康饮水",
                    "price": 32.90,
                    "cost_price": 20.00,
                    "market_price": 40.90,
                    "stock": 2000,
                    "specs": {"规格": "550ml*24瓶"},
                    "barcode": "6901234567936",
                    "shelf_life": 730,
                },
                {
                    "name": "农夫山泉 4L*4桶",
                    "caption": "天然水源｜甘甜清冽｜家庭装",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 35.90,
                    "stock": 1500,
                    "specs": {"规格": "4L*4桶"},
                    "barcode": "6901234567937",
                    "shelf_life": 730,
                },
            ]
        },
        {
            "brand": "农夫山泉",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "茶饮料",
            "spu_name": "农夫山泉东方树叶",
            "desc_detail": "农夫山泉东方树叶，原味茶饮，0糖0卡，健康饮品",
            "desc_pack": "包装清单：农夫山泉东方树叶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "农夫山泉东方树叶 500ml*15瓶",
                    "caption": "原味茶饮｜0糖0卡｜健康饮品",
                    "price": 45.90,
                    "cost_price": 30.00,
                    "market_price": 55.90,
                    "stock": 1200,
                    "specs": {"规格": "500ml*15瓶", "口味": "茉莉花茶"},
                    "barcode": "6901234567938",
                    "shelf_life": 365,
                },
                {
                    "name": "农夫山泉东方树叶 500ml*15瓶 乌龙茶",
                    "caption": "原味茶饮｜0糖0卡｜健康饮品",
                    "price": 45.90,
                    "cost_price": 30.00,
                    "market_price": 55.90,
                    "stock": 1150,
                    "specs": {"规格": "500ml*15瓶", "口味": "乌龙茶"},
                    "barcode": "6901234567939",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 娃哈哈
        {
            "brand": "娃哈哈",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "果味饮料",
            "spu_name": "娃哈哈AD钙奶",
            "desc_detail": "娃哈哈AD钙奶，酸甜可口，营养补充，童年回忆",
            "desc_pack": "包装清单：娃哈哈AD钙奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "娃哈哈AD钙奶 220ml*24瓶",
                    "caption": "酸甜可口｜营养补充｜童年回忆",
                    "price": 42.90,
                    "cost_price": 28.00,
                    "market_price": 52.90,
                    "stock": 1800,
                    "specs": {"规格": "220ml*24瓶"},
                    "barcode": "6901234567940",
                    "shelf_life": 180,
                },
            ]
        },
        {
            "brand": "娃哈哈",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "纯净水",
            "spu_name": "娃哈哈纯净水",
            "desc_detail": "娃哈哈纯净水，纯净甘甜，安全健康，日常饮水",
            "desc_pack": "包装清单：娃哈哈纯净水",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "娃哈哈纯净水 596ml*24瓶",
                    "caption": "纯净甘甜｜安全健康｜日常饮水",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 35.90,
                    "stock": 1900,
                    "specs": {"规格": "596ml*24瓶"},
                    "barcode": "6901234567941",
                    "shelf_life": 730,
                },
            ]
        },
        
        # 汇源果汁
        {
            "brand": "汇源",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "果汁",
            "spu_name": "汇源100%果汁",
            "desc_detail": "汇源100%果汁，鲜果榨取，营养丰富，口感纯正",
            "desc_pack": "包装清单：汇源100%果汁",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "汇源100%橙汁 1L*6盒",
                    "caption": "鲜果榨取｜营养丰富｜口感纯正",
                    "price": 68.90,
                    "cost_price": 45.00,
                    "market_price": 82.90,
                    "stock": 800,
                    "specs": {"规格": "1L*6盒", "口味": "橙汁"},
                    "barcode": "6901234567942",
                    "shelf_life": 365,
                },
                {
                    "name": "汇源100%苹果汁 1L*6盒",
                    "caption": "鲜果榨取｜营养丰富｜口感纯正",
                    "price": 68.90,
                    "cost_price": 45.00,
                    "market_price": 82.90,
                    "stock": 750,
                    "specs": {"规格": "1L*6盒", "口味": "苹果汁"},
                    "barcode": "6901234567943",
                    "shelf_life": 365,
                },
                {
                    "name": "汇源100%葡萄汁 1L*6盒",
                    "caption": "鲜果榨取｜营养丰富｜口感纯正",
                    "price": 72.90,
                    "cost_price": 48.00,
                    "market_price": 88.90,
                    "stock": 700,
                    "specs": {"规格": "1L*6盒", "口味": "葡萄汁"},
                    "barcode": "6901234567944",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 加多宝凉茶
        {
            "brand": "加多宝",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "凉茶",
            "spu_name": "加多宝凉茶",
            "desc_detail": "加多宝凉茶，传统配方，清热降火，健康饮品",
            "desc_pack": "包装清单：加多宝凉茶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "加多宝凉茶 310ml*24罐",
                    "caption": "传统配方｜清热降火｜健康饮品",
                    "price": 52.90,
                    "cost_price": 35.00,
                    "market_price": 63.90,
                    "stock": 1400,
                    "specs": {"规格": "310ml*24罐"},
                    "barcode": "6901234567945",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 王老吉凉茶
        {
            "brand": "王老吉",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "凉茶",
            "spu_name": "王老吉凉茶",
            "desc_detail": "王老吉凉茶，传统配方，清热降火，健康饮品",
            "desc_pack": "包装清单：王老吉凉茶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "王老吉凉茶 310ml*24罐",
                    "caption": "传统配方｜清热降火｜健康饮品",
                    "price": 52.90,
                    "cost_price": 35.00,
                    "market_price": 63.90,
                    "stock": 1350,
                    "specs": {"规格": "310ml*24罐"},
                    "barcode": "6901234567946",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 红牛功能饮料
        {
            "brand": "红牛",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "功能饮料",
            "spu_name": "红牛功能饮料",
            "desc_detail": "红牛功能饮料，提神醒脑，补充能量，活力无限",
            "desc_pack": "包装清单：红牛功能饮料",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "红牛功能饮料 250ml*24罐",
                    "caption": "提神醒脑｜补充能量｜活力无限",
                    "price": 88.90,
                    "cost_price": 60.00,
                    "market_price": 108.90,
                    "stock": 1000,
                    "specs": {"规格": "250ml*24罐"},
                    "barcode": "6901234567947",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 雀巢咖啡
        {
            "brand": "雀巢",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "咖啡",
            "spu_name": "雀巢咖啡",
            "desc_detail": "雀巢咖啡，精选咖啡豆，香浓醇厚，提神醒脑",
            "desc_pack": "包装清单：雀巢咖啡",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "雀巢1+2原味咖啡 100g",
                    "caption": "精选咖啡豆｜香浓醇厚｜提神醒脑",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 35.90,
                    "stock": 900,
                    "specs": {"规格": "100g", "口味": "原味"},
                    "barcode": "6901234567948",
                    "shelf_life": 730,
                },
                {
                    "name": "雀巢1+2原味咖啡 200g",
                    "caption": "精选咖啡豆｜香浓醇厚｜提神醒脑",
                    "price": 52.90,
                    "cost_price": 34.00,
                    "market_price": 65.90,
                    "stock": 850,
                    "specs": {"规格": "200g", "口味": "原味"},
                    "barcode": "6901234567949",
                    "shelf_life": 730,
                },
            ]
        },
        
        # ==================== 日化类商品 ====================
        
        # 蓝月亮洗衣液
        {
            "brand": "蓝月亮",
            "category1": "日化",
            "category2": "清洁用品",
            "category3": "洗衣液",
            "spu_name": "蓝月亮洗衣液",
            "desc_detail": "蓝月亮洗衣液，深层洁净，护衣护色，温和无刺激",
            "desc_pack": "包装清单：蓝月亮洗衣液",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "蓝月亮洗衣液 1kg",
                    "caption": "深层洁净｜护衣护色｜温和无刺激",
                    "price": 19.90,
                    "cost_price": 12.00,
                    "market_price": 24.90,
                    "stock": 1000,
                    "specs": {"规格": "1kg", "类型": "深层洁净"},
                    "barcode": "6901234567950",
                    "shelf_life": 1825,
                },
                {
                    "name": "蓝月亮洗衣液 2kg",
                    "caption": "深层洁净｜护衣护色｜温和无刺激",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 44.90,
                    "stock": 900,
                    "specs": {"规格": "2kg", "类型": "深层洁净"},
                    "barcode": "6901234567951",
                    "shelf_life": 1825,
                },
                {
                    "name": "蓝月亮洗衣液 3kg",
                    "caption": "深层洁净｜护衣护色｜温和无刺激",
                    "price": 49.90,
                    "cost_price": 30.00,
                    "market_price": 62.90,
                    "stock": 800,
                    "specs": {"规格": "3kg", "类型": "深层洁净"},
                    "barcode": "6901234567952",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 立白洗衣液
        {
            "brand": "立白",
            "category1": "日化",
            "category2": "清洁用品",
            "category3": "洗衣液",
            "spu_name": "立白洗衣液",
            "desc_detail": "立白洗衣液，强力去污，护衣护色，清香怡人",
            "desc_pack": "包装清单：立白洗衣液",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "立白洗衣液 1kg",
                    "caption": "强力去污｜护衣护色｜清香怡人",
                    "price": 18.90,
                    "cost_price": 11.00,
                    "market_price": 23.90,
                    "stock": 1100,
                    "specs": {"规格": "1kg", "类型": "强力去污"},
                    "barcode": "6901234567953",
                    "shelf_life": 1825,
                },
                {
                    "name": "立白洗衣液 2kg",
                    "caption": "强力去污｜护衣护色｜清香怡人",
                    "price": 33.90,
                    "cost_price": 20.00,
                    "market_price": 42.90,
                    "stock": 1000,
                    "specs": {"规格": "2kg", "类型": "强力去污"},
                    "barcode": "6901234567954",
                    "shelf_life": 1825,
                },
                {
                    "name": "立白洗衣液 3kg",
                    "caption": "强力去污｜护衣护色｜清香怡人",
                    "price": 47.90,
                    "cost_price": 28.00,
                    "market_price": 60.90,
                    "stock": 900,
                    "specs": {"规格": "3kg", "类型": "强力去污"},
                    "barcode": "6901234567955",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 汰渍洗衣粉
        {
            "brand": "汰渍",
            "category1": "日化",
            "category2": "清洁用品",
            "category3": "洗衣粉",
            "spu_name": "汰渍洗衣粉",
            "desc_detail": "汰渍洗衣粉，强力去污，洁白如新，持久留香",
            "desc_pack": "包装清单：汰渍洗衣粉",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "汰渍洗衣粉 1.8kg",
                    "caption": "强力去污｜洁白如新｜持久留香",
                    "price": 22.90,
                    "cost_price": 14.00,
                    "market_price": 28.90,
                    "stock": 1200,
                    "specs": {"规格": "1.8kg", "类型": "强力去污"},
                    "barcode": "6901234567956",
                    "shelf_life": 1825,
                },
                {
                    "name": "汰渍洗衣粉 3.5kg",
                    "caption": "强力去污｜洁白如新｜持久留香",
                    "price": 42.90,
                    "cost_price": 26.00,
                    "market_price": 54.90,
                    "stock": 1000,
                    "specs": {"规格": "3.5kg", "类型": "强力去污"},
                    "barcode": "6901234567957",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 奥妙洗衣液
        {
            "brand": "奥妙",
            "category1": "日化",
            "category2": "清洁用品",
            "category3": "洗衣液",
            "spu_name": "奥妙洗衣液",
            "desc_detail": "奥妙洗衣液，深层洁净，除菌除螨，温和无刺激",
            "desc_pack": "包装清单：奥妙洗衣液",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "奥妙洗衣液 1kg",
                    "caption": "深层洁净｜除菌除螨｜温和无刺激",
                    "price": 18.90,
                    "cost_price": 11.00,
                    "market_price": 23.90,
                    "stock": 1100,
                    "specs": {"规格": "1kg", "类型": "除菌除螨"},
                    "barcode": "6901234567958",
                    "shelf_life": 1825,
                },
                {
                    "name": "奥妙洗衣液 2kg",
                    "caption": "深层洁净｜除菌除螨｜温和无刺激",
                    "price": 33.90,
                    "cost_price": 20.00,
                    "market_price": 42.90,
                    "stock": 1000,
                    "specs": {"规格": "2kg", "类型": "除菌除螨"},
                    "barcode": "6901234567959",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 海飞丝洗发水
        {
            "brand": "海飞丝",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "洗发水",
            "spu_name": "海飞丝洗发水",
            "desc_detail": "海飞丝洗发水，去屑止痒，清爽控油，秀发柔顺",
            "desc_pack": "包装清单：海飞丝洗发水",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "海飞丝去屑洗发水 400ml",
                    "caption": "去屑止痒｜清爽控油｜秀发柔顺",
                    "price": 38.90,
                    "cost_price": 24.00,
                    "market_price": 48.90,
                    "stock": 1500,
                    "specs": {"规格": "400ml", "类型": "去屑"},
                    "barcode": "6901234567960",
                    "shelf_life": 1825,
                },
                {
                    "name": "海飞丝去屑洗发水 800ml",
                    "caption": "去屑止痒｜清爽控油｜秀发柔顺",
                    "price": 68.90,
                    "cost_price": 42.00,
                    "market_price": 85.90,
                    "stock": 1300,
                    "specs": {"规格": "800ml", "类型": "去屑"},
                    "barcode": "6901234567961",
                    "shelf_life": 1825,
                },
                {
                    "name": "海飞丝丝质柔顺洗发水 400ml",
                    "caption": "丝质柔顺｜滋养修护｜秀发顺滑",
                    "price": 39.90,
                    "cost_price": 25.00,
                    "market_price": 49.90,
                    "stock": 1400,
                    "specs": {"规格": "400ml", "类型": "丝质柔顺"},
                    "barcode": "6901234567962",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 飘柔洗发水
        {
            "brand": "飘柔",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "洗发水",
            "spu_name": "飘柔洗发水",
            "desc_detail": "飘柔洗发水，柔顺秀发，清香怡人，易于梳理",
            "desc_pack": "包装清单：飘柔洗发水",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "飘柔柔顺洗发水 400ml",
                    "caption": "柔顺秀发｜清香怡人｜易于梳理",
                    "price": 32.90,
                    "cost_price": 20.00,
                    "market_price": 42.90,
                    "stock": 1600,
                    "specs": {"规格": "400ml", "类型": "柔顺"},
                    "barcode": "6901234567963",
                    "shelf_life": 1825,
                },
                {
                    "name": "飘柔柔顺洗发水 800ml",
                    "caption": "柔顺秀发｜清香怡人｜易于梳理",
                    "price": 58.90,
                    "cost_price": 36.00,
                    "market_price": 73.90,
                    "stock": 1400,
                    "specs": {"规格": "800ml", "类型": "柔顺"},
                    "barcode": "6901234567964",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 潘婷洗发水
        {
            "brand": "潘婷",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "洗发水",
            "spu_name": "潘婷洗发水",
            "desc_detail": "潘婷洗发水，强韧修护，滋养秀发，健康亮泽",
            "desc_pack": "包装清单：潘婷洗发水",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "潘婷修护洗发水 400ml",
                    "caption": "强韧修护｜滋养秀发｜健康亮泽",
                    "price": 42.90,
                    "cost_price": 26.00,
                    "market_price": 53.90,
                    "stock": 1400,
                    "specs": {"规格": "400ml", "类型": "修护"},
                    "barcode": "6901234567965",
                    "shelf_life": 1825,
                },
                {
                    "name": "潘婷修护洗发水 800ml",
                    "caption": "强韧修护｜滋养秀发｜健康亮泽",
                    "price": 75.90,
                    "cost_price": 46.00,
                    "market_price": 94.90,
                    "stock": 1200,
                    "specs": {"规格": "800ml", "类型": "修护"},
                    "barcode": "6901234567966",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 沙宣洗发水
        {
            "brand": "沙宣",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "洗发水",
            "spu_name": "沙宣洗发水",
            "desc_detail": "沙宣洗发水，专业造型，清爽控油，持久定型",
            "desc_pack": "包装清单：沙宣洗发水",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "沙宣专业洗发水 400ml",
                    "caption": "专业造型｜清爽控油｜持久定型",
                    "price": 45.90,
                    "cost_price": 28.00,
                    "market_price": 57.90,
                    "stock": 1300,
                    "specs": {"规格": "400ml", "类型": "专业造型"},
                    "barcode": "6901234567967",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 舒肤佳香皂
        {
            "brand": "舒肤佳",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "香皂",
            "spu_name": "舒肤佳香皂",
            "desc_detail": "舒肤佳香皂，抑菌除菌，温和清洁，全家适用",
            "desc_pack": "包装清单：舒肤佳香皂",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "舒肤佳香皂 115g*4块",
                    "caption": "抑菌除菌｜温和清洁｜全家适用",
                    "price": 18.90,
                    "cost_price": 11.00,
                    "market_price": 23.90,
                    "stock": 1800,
                    "specs": {"规格": "115g*4块"},
                    "barcode": "6901234567968",
                    "shelf_life": 1825,
                },
                {
                    "name": "舒肤佳香皂 115g*8块",
                    "caption": "抑菌除菌｜温和清洁｜家庭装",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 44.90,
                    "stock": 1600,
                    "specs": {"规格": "115g*8块"},
                    "barcode": "6901234567969",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 滴露消毒液
        {
            "brand": "滴露",
            "category1": "日化",
            "category2": "清洁用品",
            "category3": "消毒液",
            "spu_name": "滴露消毒液",
            "desc_detail": "滴露消毒液，强力杀菌，安全无毒，家居必备",
            "desc_pack": "包装清单：滴露消毒液",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "滴露消毒液 1.8L",
                    "caption": "强力杀菌｜安全无毒｜家居必备",
                    "price": 45.90,
                    "cost_price": 28.00,
                    "market_price": 57.90,
                    "stock": 1200,
                    "specs": {"规格": "1.8L"},
                    "barcode": "6901234567970",
                    "shelf_life": 1825,
                },
                {
                    "name": "滴露消毒液 3.5L",
                    "caption": "强力杀菌｜安全无毒｜家庭装",
                    "price": 78.90,
                    "cost_price": 48.00,
                    "market_price": 98.90,
                    "stock": 1000,
                    "specs": {"规格": "3.5L"},
                    "barcode": "6901234567971",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 维达纸巾
        {
            "brand": "维达",
            "category1": "日化",
            "category2": "纸品",
            "category3": "抽纸",
            "spu_name": "维达抽纸",
            "desc_detail": "维达抽纸，柔韧耐用，吸水性强，亲肤舒适",
            "desc_pack": "包装清单：维达抽纸",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "维达抽纸 3层*130抽*6包",
                    "caption": "柔韧耐用｜吸水性强｜亲肤舒适",
                    "price": 25.90,
                    "cost_price": 15.00,
                    "market_price": 32.90,
                    "stock": 2000,
                    "specs": {"规格": "3层*130抽*6包"},
                    "barcode": "6901234567972",
                    "shelf_life": 1825,
                },
                {
                    "name": "维达抽纸 3层*130抽*12包",
                    "caption": "柔韧耐用｜吸水性强｜家庭装",
                    "price": 48.90,
                    "cost_price": 28.00,
                    "market_price": 62.90,
                    "stock": 1800,
                    "specs": {"规格": "3层*130抽*12包"},
                    "barcode": "6901234567973",
                    "shelf_life": 1825,
                },
            ]
        },
        {
            "brand": "维达",
            "category1": "日化",
            "category2": "纸品",
            "category3": "卷纸",
            "spu_name": "维达卷纸",
            "desc_detail": "维达卷纸，柔韧耐用，吸水性强，经济实惠",
            "desc_pack": "包装清单：维达卷纸",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "维达卷纸 4层*140g*10卷",
                    "caption": "柔韧耐用｜吸水性强｜经济实惠",
                    "price": 32.90,
                    "cost_price": 20.00,
                    "market_price": 42.90,
                    "stock": 1900,
                    "specs": {"规格": "4层*140g*10卷"},
                    "barcode": "6901234567974",
                    "shelf_life": 1825,
                },
                {
                    "name": "维达卷纸 4层*140g*20卷",
                    "caption": "柔韧耐用｜吸水性强｜家庭装",
                    "price": 58.90,
                    "cost_price": 36.00,
                    "market_price": 75.90,
                    "stock": 1700,
                    "specs": {"规格": "4层*140g*20卷"},
                    "barcode": "6901234567975",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 清风纸巾
        {
            "brand": "清风",
            "category1": "日化",
            "category2": "纸品",
            "category3": "抽纸",
            "spu_name": "清风抽纸",
            "desc_detail": "清风抽纸，柔韧耐用，吸水性强，亲肤舒适",
            "desc_pack": "包装清单：清风抽纸",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "清风抽纸 3层*120抽*6包",
                    "caption": "柔韧耐用｜吸水性强｜亲肤舒适",
                    "price": 22.90,
                    "cost_price": 13.00,
                    "market_price": 29.90,
                    "stock": 2100,
                    "specs": {"规格": "3层*120抽*6包"},
                    "barcode": "6901234567976",
                    "shelf_life": 1825,
                },
                {
                    "name": "清风抽纸 3层*120抽*12包",
                    "caption": "柔韧耐用｜吸水性强｜家庭装",
                    "price": 42.90,
                    "cost_price": 25.00,
                    "market_price": 55.90,
                    "stock": 1900,
                    "specs": {"规格": "3层*120抽*12包"},
                    "barcode": "6901234567977",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 心相印纸巾
        {
            "brand": "心相印",
            "category1": "日化",
            "category2": "纸品",
            "category3": "抽纸",
            "spu_name": "心相印抽纸",
            "desc_detail": "心相印抽纸，柔韧耐用，吸水性强，亲肤舒适",
            "desc_pack": "包装清单：心相印抽纸",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "心相印抽纸 3层*130抽*6包",
                    "caption": "柔韧耐用｜吸水性强｜亲肤舒适",
                    "price": 24.90,
                    "cost_price": 15.00,
                    "market_price": 31.90,
                    "stock": 2000,
                    "specs": {"规格": "3层*130抽*6包"},
                    "barcode": "6901234567978",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 洁柔纸巾
        {
            "brand": "洁柔",
            "category1": "日化",
            "category2": "纸品",
            "category3": "抽纸",
            "spu_name": "洁柔抽纸",
            "desc_detail": "洁柔抽纸，柔韧耐用，吸水性强，亲肤舒适",
            "desc_pack": "包装清单：洁柔抽纸",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "洁柔抽纸 3层*130抽*6包",
                    "caption": "柔韧耐用｜吸水性强｜亲肤舒适",
                    "price": 23.90,
                    "cost_price": 14.00,
                    "market_price": 30.90,
                    "stock": 2050,
                    "specs": {"规格": "3层*130抽*6包"},
                    "barcode": "6901234567979",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 多芬沐浴露
        {
            "brand": "多芬",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "沐浴露",
            "spu_name": "多芬沐浴露",
            "desc_detail": "多芬沐浴露，温和清洁，滋润保湿，肌肤柔嫩",
            "desc_pack": "包装清单：多芬沐浴露",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "多芬沐浴露 550ml",
                    "caption": "温和清洁｜滋润保湿｜肌肤柔嫩",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 45.90,
                    "stock": 1400,
                    "specs": {"规格": "550ml", "类型": "滋润"},
                    "barcode": "6901234567980",
                    "shelf_life": 1825,
                },
                {
                    "name": "多芬沐浴露 720ml",
                    "caption": "温和清洁｜滋润保湿｜肌肤柔嫩",
                    "price": 45.90,
                    "cost_price": 28.00,
                    "market_price": 57.90,
                    "stock": 1200,
                    "specs": {"规格": "720ml", "类型": "滋润"},
                    "barcode": "6901234567981",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 力士沐浴露
        {
            "brand": "力士",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "沐浴露",
            "spu_name": "力士沐浴露",
            "desc_detail": "力士沐浴露，香氛怡人，温和清洁，持久留香",
            "desc_pack": "包装清单：力士沐浴露",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "力士沐浴露 550ml",
                    "caption": "香氛怡人｜温和清洁｜持久留香",
                    "price": 32.90,
                    "cost_price": 20.00,
                    "market_price": 42.90,
                    "stock": 1500,
                    "specs": {"规格": "550ml", "类型": "香氛"},
                    "barcode": "6901234567982",
                    "shelf_life": 1825,
                },
                {
                    "name": "力士沐浴露 720ml",
                    "caption": "香氛怡人｜温和清洁｜持久留香",
                    "price": 42.90,
                    "cost_price": 26.00,
                    "market_price": 54.90,
                    "stock": 1300,
                    "specs": {"规格": "720ml", "类型": "香氛"},
                    "barcode": "6901234567983",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 玉兰油沐浴露
        {
            "brand": "玉兰油",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "沐浴露",
            "spu_name": "玉兰油沐浴露",
            "desc_detail": "玉兰油沐浴露，滋养修护，温和清洁，肌肤水润",
            "desc_pack": "包装清单：玉兰油沐浴露",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "玉兰油沐浴露 550ml",
                    "caption": "滋养修护｜温和清洁｜肌肤水润",
                    "price": 45.90,
                    "cost_price": 28.00,
                    "market_price": 57.90,
                    "stock": 1200,
                    "specs": {"规格": "550ml", "类型": "滋养"},
                    "barcode": "6901234567984",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 酒水类商品 ====================
        
        # 茅台白酒
        {
            "brand": "茅台",
            "category1": "酒水",
            "category2": "白酒",
            "category3": "酱香型",
            "spu_name": "茅台飞天",
            "desc_detail": "茅台飞天，酱香突出，优雅细腻，回味悠长",
            "desc_pack": "包装清单：茅台飞天白酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "茅台飞天 53度 500ml",
                    "caption": "酱香突出｜优雅细腻｜回味悠长",
                    "price": 1499.00,
                    "cost_price": 1200.00,
                    "market_price": 1799.00,
                    "stock": 100,
                    "specs": {"规格": "500ml", "度数": "53度"},
                    "barcode": "6901234567985",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 五粮液白酒
        {
            "brand": "五粮液",
            "category1": "酒水",
            "category2": "白酒",
            "category3": "浓香型",
            "spu_name": "五粮液普五",
            "desc_detail": "五粮液普五，香气悠久，味醇厚，入口甘美",
            "desc_pack": "包装清单：五粮液普五白酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "五粮液普五 52度 500ml",
                    "caption": "香气悠久｜味醇厚｜入口甘美",
                    "price": 1099.00,
                    "cost_price": 880.00,
                    "market_price": 1299.00,
                    "stock": 150,
                    "specs": {"规格": "500ml", "度数": "52度"},
                    "barcode": "6901234567986",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 剑南春白酒
        {
            "brand": "剑南春",
            "category1": "酒水",
            "category2": "白酒",
            "category3": "浓香型",
            "spu_name": "剑南春水晶剑",
            "desc_detail": "剑南春水晶剑，香气浓郁，口感醇厚，回味悠长",
            "desc_pack": "包装清单：剑南春水晶剑白酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "剑南春水晶剑 52度 500ml",
                    "caption": "香气浓郁｜口感醇厚｜回味悠长",
                    "price": 459.00,
                    "cost_price": 360.00,
                    "market_price": 529.00,
                    "stock": 200,
                    "specs": {"规格": "500ml", "度数": "52度"},
                    "barcode": "6901234567987",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 泸州老窖白酒
        {
            "brand": "泸州老窖",
            "category1": "酒水",
            "category2": "白酒",
            "category3": "浓香型",
            "spu_name": "泸州老窖特曲",
            "desc_detail": "泸州老窖特曲，浓香正宗，窖香浓郁，口感醇厚",
            "desc_pack": "包装清单：泸州老窖特曲白酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "泸州老窖特曲 52度 500ml",
                    "caption": "浓香正宗｜窖香浓郁｜口感醇厚",
                    "price": 289.00,
                    "cost_price": 220.00,
                    "market_price": 329.00,
                    "stock": 250,
                    "specs": {"规格": "500ml", "度数": "52度"},
                    "barcode": "6901234567988",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 洋河白酒
        {
            "brand": "洋河",
            "category1": "酒水",
            "category2": "白酒",
            "category3": "绵柔型",
            "spu_name": "洋河海之蓝",
            "desc_detail": "洋河海之蓝，绵柔口感，香气幽雅，回味悠长",
            "desc_pack": "包装清单：洋河海之蓝白酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "洋河海之蓝 42度 480ml",
                    "caption": "绵柔口感｜香气幽雅｜回味悠长",
                    "price": 168.00,
                    "cost_price": 130.00,
                    "market_price": 198.00,
                    "stock": 300,
                    "specs": {"规格": "480ml", "度数": "42度"},
                    "barcode": "6901234567989",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 长城红酒
        {
            "brand": "长城",
            "category1": "酒水",
            "category2": "红酒",
            "category3": "干红",
            "spu_name": "长城干红葡萄酒",
            "desc_detail": "长城干红葡萄酒，果香浓郁，口感醇厚，余味悠长",
            "desc_pack": "包装清单：长城干红葡萄酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "长城干红葡萄酒 750ml",
                    "caption": "果香浓郁｜口感醇厚｜余味悠长",
                    "price": 68.00,
                    "cost_price": 45.00,
                    "market_price": 88.00,
                    "stock": 400,
                    "specs": {"规格": "750ml"},
                    "barcode": "6901234567990",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 张裕红酒
        {
            "brand": "张裕",
            "category1": "酒水",
            "category2": "红酒",
            "category3": "干红",
            "spu_name": "张裕解百纳",
            "desc_detail": "张裕解百纳，果香浓郁，口感醇厚，结构平衡",
            "desc_pack": "包装清单：张裕解百纳红酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "张裕解百纳 750ml",
                    "caption": "果香浓郁｜口感醇厚｜结构平衡",
                    "price": 88.00,
                    "cost_price": 60.00,
                    "market_price": 108.00,
                    "stock": 350,
                    "specs": {"规格": "750ml"},
                    "barcode": "6901234567991",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 青岛啤酒
        {
            "brand": "青岛啤酒",
            "category1": "酒水",
            "category2": "啤酒",
            "category3": "拉格",
            "spu_name": "青岛啤酒",
            "desc_detail": "青岛啤酒，经典口感，清爽纯正，百年传承",
            "desc_pack": "包装清单：青岛啤酒",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "青岛啤酒 330ml*24罐",
                    "caption": "经典口感｜清爽纯正｜百年传承",
                    "price": 58.90,
                    "cost_price": 40.00,
                    "market_price": 72.90,
                    "stock": 1800,
                    "specs": {"规格": "330ml*24罐"},
                    "barcode": "6901234567992",
                    "shelf_life": 365,
                },
                {
                    "name": "青岛啤酒 500ml*12罐",
                    "caption": "经典口感｜清爽纯正｜经典罐装",
                    "price": 48.90,
                    "cost_price": 33.00,
                    "market_price": 60.90,
                    "stock": 1700,
                    "specs": {"规格": "500ml*12罐"},
                    "barcode": "6901234567993",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 雪花啤酒
        {
            "brand": "雪花啤酒",
            "category1": "酒水",
            "category2": "啤酒",
            "category3": "拉格",
            "spu_name": "雪花啤酒",
            "desc_detail": "雪花啤酒，清爽纯正，口感醇厚，畅饮无忧",
            "desc_pack": "包装清单：雪花啤酒",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "雪花啤酒 330ml*24罐",
                    "caption": "清爽纯正｜口感醇厚｜畅饮无忧",
                    "price": 42.90,
                    "cost_price": 28.00,
                    "market_price": 52.90,
                    "stock": 2000,
                    "specs": {"规格": "330ml*24罐"},
                    "barcode": "6901234567994",
                    "shelf_life": 365,
                },
                {
                    "name": "雪花啤酒 500ml*12罐",
                    "caption": "清爽纯正｜口感醇厚｜经典罐装",
                    "price": 35.90,
                    "cost_price": 23.00,
                    "market_price": 44.90,
                    "stock": 1900,
                    "specs": {"规格": "500ml*12罐"},
                    "barcode": "6901234567995",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 哈尔滨啤酒
        {
            "brand": "哈尔滨啤酒",
            "category1": "酒水",
            "category2": "啤酒",
            "category3": "拉格",
            "spu_name": "哈尔滨啤酒",
            "desc_detail": "哈尔滨啤酒，纯正口感，清爽怡人，百年传承",
            "desc_pack": "包装清单：哈尔滨啤酒",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "哈尔滨啤酒 330ml*24罐",
                    "caption": "纯正口感｜清爽怡人｜百年传承",
                    "price": 45.90,
                    "cost_price": 30.00,
                    "market_price": 56.90,
                    "stock": 1700,
                    "specs": {"规格": "330ml*24罐"},
                    "barcode": "6901234567996",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 百威啤酒
        {
            "brand": "百威",
            "category1": "酒水",
            "category2": "啤酒",
            "category3": "拉格",
            "spu_name": "百威啤酒",
            "desc_detail": "百威啤酒，纯正口感，清爽怡人，国际品牌",
            "desc_pack": "包装清单：百威啤酒",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "百威啤酒 330ml*24罐",
                    "caption": "纯正口感｜清爽怡人｜国际品牌",
                    "price": 68.90,
                    "cost_price": 45.00,
                    "market_price": 85.90,
                    "stock": 1500,
                    "specs": {"规格": "330ml*24罐"},
                    "barcode": "6901234567997",
                    "shelf_life": 365,
                },
                {
                    "name": "百威啤酒 500ml*12罐",
                    "caption": "纯正口感｜清爽怡人｜经典罐装",
                    "price": 58.90,
                    "cost_price": 38.00,
                    "market_price": 72.90,
                    "stock": 1400,
                    "specs": {"规格": "500ml*12罐"},
                    "barcode": "6901234567998",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 喜力啤酒
        {
            "brand": "喜力",
            "category1": "酒水",
            "category2": "啤酒",
            "category3": "拉格",
            "spu_name": "喜力啤酒",
            "desc_detail": "喜力啤酒，纯正口感，清爽怡人，荷兰品牌",
            "desc_pack": "包装清单：喜力啤酒",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "喜力啤酒 330ml*24罐",
                    "caption": "纯正口感｜清爽怡人｜荷兰品牌",
                    "price": 72.90,
                    "cost_price": 48.00,
                    "market_price": 89.90,
                    "stock": 1200,
                    "specs": {"规格": "330ml*24罐"},
                    "barcode": "6901234567999",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 轩尼诗洋酒
        {
            "brand": "轩尼诗",
            "category1": "酒水",
            "category2": "洋酒",
            "category3": "干邑",
            "spu_name": "轩尼诗VSOP",
            "desc_detail": "轩尼诗VSOP，醇厚口感，香气浓郁，法国干邑",
            "desc_pack": "包装清单：轩尼诗VSOP",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "轩尼诗VSOP 700ml",
                    "caption": "醇厚口感｜香气浓郁｜法国干邑",
                    "price": 680.00,
                    "cost_price": 500.00,
                    "market_price": 820.00,
                    "stock": 200,
                    "specs": {"规格": "700ml"},
                    "barcode": "6901234568000",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 马爹利洋酒
        {
            "brand": "马爹利",
            "category1": "酒水",
            "category2": "洋酒",
            "category3": "干邑",
            "spu_name": "马爹利名士",
            "desc_detail": "马爹利名士，醇厚口感，香气浓郁，法国干邑",
            "desc_pack": "包装清单：马爹利名士",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "马爹利名士 700ml",
                    "caption": "醇厚口感｜香气浓郁｜法国干邑",
                    "price": 580.00,
                    "cost_price": 420.00,
                    "market_price": 700.00,
                    "stock": 180,
                    "specs": {"规格": "700ml"},
                    "barcode": "6901234568001",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 尊尼获加威士忌
        {
            "brand": "尊尼获加",
            "category1": "酒水",
            "category2": "洋酒",
            "category3": "威士忌",
            "spu_name": "尊尼获加黑方",
            "desc_detail": "尊尼获加黑方，醇厚口感，香气浓郁，苏格兰威士忌",
            "desc_pack": "包装清单：尊尼获加黑方",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "尊尼获加黑方 700ml",
                    "caption": "醇厚口感｜香气浓郁｜苏格兰威士忌",
                    "price": 280.00,
                    "cost_price": 200.00,
                    "market_price": 340.00,
                    "stock": 250,
                    "specs": {"规格": "700ml"},
                    "barcode": "6901234568002",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 芝华士威士忌
        {
            "brand": "芝华士",
            "category1": "酒水",
            "category2": "洋酒",
            "category3": "威士忌",
            "spu_name": "芝华士12年",
            "desc_detail": "芝华士12年，醇厚口感，香气浓郁，苏格兰威士忌",
            "desc_pack": "包装清单：芝华士12年",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "芝华士12年 700ml",
                    "caption": "醇厚口感｜香气浓郁｜苏格兰威士忌",
                    "price": 320.00,
                    "cost_price": 230.00,
                    "market_price": 390.00,
                    "stock": 220,
                    "specs": {"规格": "700ml"},
                    "barcode": "6901234568003",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 杰克丹尼威士忌
        {
            "brand": "杰克丹尼",
            "category1": "酒水",
            "category2": "洋酒",
            "category3": "威士忌",
            "spu_name": "杰克丹尼",
            "desc_detail": "杰克丹尼，醇厚口感，香气浓郁，美国田纳西威士忌",
            "desc_pack": "包装清单：杰克丹尼",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "杰克丹尼 700ml",
                    "caption": "醇厚口感｜香气浓郁｜美国威士忌",
                    "price": 260.00,
                    "cost_price": 180.00,
                    "market_price": 320.00,
                    "stock": 240,
                    "specs": {"规格": "700ml"},
                    "barcode": "6901234568004",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # ==================== 更多食品类商品 ====================
        
        # 盼盼食品
        {
            "brand": "盼盼",
            "category1": "食品",
            "category2": "零食",
            "category3": "膨化食品",
            "spu_name": "盼盼麦香鸡味块",
            "desc_detail": "盼盼麦香鸡味块，香脆可口，经典零食，童年回忆",
            "desc_pack": "包装清单：盼盼麦香鸡味块",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "盼盼麦香鸡味块 80g",
                    "caption": "香脆可口｜经典零食｜童年回忆",
                    "price": 5.90,
                    "cost_price": 3.50,
                    "market_price": 7.90,
                    "stock": 1500,
                    "specs": {"规格": "80g", "口味": "鸡味"},
                    "barcode": "6901234568005",
                    "shelf_life": 180,
                },
                {
                    "name": "盼盼麦香鸡味块 160g",
                    "caption": "香脆可口｜经典零食｜分享装",
                    "price": 10.90,
                    "cost_price": 6.50,
                    "market_price": 14.90,
                    "stock": 1300,
                    "specs": {"规格": "160g", "口味": "鸡味"},
                    "barcode": "6901234568006",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 达利园食品
        {
            "brand": "达利园",
            "category1": "食品",
            "category2": "零食",
            "category3": "糕点",
            "spu_name": "达利园蛋黄派",
            "desc_detail": "达利园蛋黄派，松软香甜，口感细腻，经典糕点",
            "desc_pack": "包装清单：达利园蛋黄派",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "达利园蛋黄派 300g",
                    "caption": "松软香甜｜口感细腻｜经典糕点",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 1400,
                    "specs": {"规格": "300g"},
                    "barcode": "6901234568007",
                    "shelf_life": 90,
                },
                {
                    "name": "达利园蛋黄派 600g",
                    "caption": "松软香甜｜口感细腻｜家庭装",
                    "price": 23.90,
                    "cost_price": 15.00,
                    "market_price": 30.90,
                    "stock": 1200,
                    "specs": {"规格": "600g"},
                    "barcode": "6901234568008",
                    "shelf_life": 90,
                },
            ]
        },
        {
            "brand": "达利园",
            "category1": "食品",
            "category2": "零食",
            "category3": "糕点",
            "spu_name": "达利园面包",
            "desc_detail": "达利园面包，松软香甜，营养早餐，方便快捷",
            "desc_pack": "包装清单：达利园面包",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "达利园面包 400g",
                    "caption": "松软香甜｜营养早餐｜方便快捷",
                    "price": 8.90,
                    "cost_price": 5.50,
                    "market_price": 11.90,
                    "stock": 1600,
                    "specs": {"规格": "400g", "口味": "原味"},
                    "barcode": "6901234568009",
                    "shelf_life": 30,
                },
            ]
        },
        
        # 来伊份零食
        {
            "brand": "来伊份",
            "category1": "食品",
            "category2": "零食",
            "category3": "坚果",
            "spu_name": "来伊份混合坚果",
            "desc_detail": "来伊份混合坚果，营养均衡，口感丰富，休闲零食",
            "desc_pack": "包装清单：来伊份混合坚果",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "来伊份混合坚果 500g",
                    "caption": "营养均衡｜口感丰富｜休闲零食",
                    "price": 58.90,
                    "cost_price": 38.00,
                    "market_price": 72.90,
                    "stock": 600,
                    "specs": {"规格": "500g"},
                    "barcode": "6901234568010",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 稻香村糕点
        {
            "brand": "稻香村",
            "category1": "食品",
            "category2": "零食",
            "category3": "糕点",
            "spu_name": "稻香村月饼",
            "desc_detail": "稻香村月饼，传统工艺，口感香甜，中秋佳品",
            "desc_pack": "包装清单：稻香村月饼",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "稻香村月饼 500g",
                    "caption": "传统工艺｜口感香甜｜中秋佳品",
                    "price": 68.90,
                    "cost_price": 45.00,
                    "market_price": 85.90,
                    "stock": 500,
                    "specs": {"规格": "500g", "口味": "五仁"},
                    "barcode": "6901234568011",
                    "shelf_life": 60,
                },
                {
                    "name": "稻香村月饼 500g 莲蓉",
                    "caption": "传统工艺｜口感香甜｜中秋佳品",
                    "price": 68.90,
                    "cost_price": 45.00,
                    "market_price": 85.90,
                    "stock": 500,
                    "specs": {"规格": "500g", "口味": "莲蓉"},
                    "barcode": "6901234568012",
                    "shelf_life": 60,
                },
            ]
        },
        
        # 好利来蛋糕
        {
            "brand": "好利来",
            "category1": "食品",
            "category2": "零食",
            "category3": "蛋糕",
            "spu_name": "好利来半熟芝士",
            "desc_detail": "好利来半熟芝士，口感绵密，芝士浓郁，美味蛋糕",
            "desc_pack": "包装清单：好利来半熟芝士",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "好利来半熟芝士 6枚装",
                    "caption": "口感绵密｜芝士浓郁｜美味蛋糕",
                    "price": 45.90,
                    "cost_price": 30.00,
                    "market_price": 58.90,
                    "stock": 800,
                    "specs": {"规格": "6枚装"},
                    "barcode": "6901234568013",
                    "shelf_life": 7,
                },
            ]
        },
        
        # 味多美面包
        {
            "brand": "味多美",
            "category1": "食品",
            "category2": "零食",
            "category3": "面包",
            "spu_name": "味多美法棍",
            "desc_detail": "味多美法棍，外脆内软，麦香浓郁，经典面包",
            "desc_pack": "包装清单：味多美法棍",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "味多美法棍 300g",
                    "caption": "外脆内软｜麦香浓郁｜经典面包",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 1000,
                    "specs": {"规格": "300g"},
                    "barcode": "6901234568014",
                    "shelf_life": 3,
                },
            ]
        },
        
        # 巴黎贝甜面包
        {
            "brand": "巴黎贝甜",
            "category1": "食品",
            "category2": "零食",
            "category3": "面包",
            "spu_name": "巴黎贝甜牛角包",
            "desc_detail": "巴黎贝甜牛角包，层次丰富，口感酥脆，法式面包",
            "desc_pack": "包装清单：巴黎贝甜牛角包",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "巴黎贝甜牛角包 100g",
                    "caption": "层次丰富｜口感酥脆｜法式面包",
                    "price": 15.90,
                    "cost_price": 10.00,
                    "market_price": 20.90,
                    "stock": 900,
                    "specs": {"规格": "100g"},
                    "barcode": "6901234568015",
                    "shelf_life": 3,
                },
            ]
        },
        
        # 85度C面包
        {
            "brand": "85度C",
            "category1": "食品",
            "category2": "零食",
            "category3": "面包",
            "spu_name": "85度C凯撒大帝",
            "desc_detail": "85度C凯撒大帝，香脆可口，营养丰富，经典面包",
            "desc_pack": "包装清单：85度C凯撒大帝",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "85度C凯撒大帝 200g",
                    "caption": "香脆可口｜营养丰富｜经典面包",
                    "price": 18.90,
                    "cost_price": 12.00,
                    "market_price": 24.90,
                    "stock": 850,
                    "specs": {"规格": "200g"},
                    "barcode": "6901234568016",
                    "shelf_life": 3,
                },
            ]
        },
        
        # 元祖蛋糕
        {
            "brand": "元祖",
            "category1": "食品",
            "category2": "零食",
            "category3": "蛋糕",
            "spu_name": "元祖雪月饼",
            "desc_detail": "元祖雪月饼，冰皮月饼，口感独特，中秋佳品",
            "desc_pack": "包装清单：元祖雪月饼",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "元祖雪月饼 6枚装",
                    "caption": "冰皮月饼｜口感独特｜中秋佳品",
                    "price": 128.00,
                    "cost_price": 85.00,
                    "market_price": 158.00,
                    "stock": 400,
                    "specs": {"规格": "6枚装"},
                    "barcode": "6901234568017",
                    "shelf_life": 30,
                },
            ]
        },
        
        # 可颂坊面包
        {
            "brand": "可颂坊",
            "category1": "食品",
            "category2": "零食",
            "category3": "面包",
            "spu_name": "可颂坊丹麦酥",
            "desc_detail": "可颂坊丹麦酥，层次丰富，口感酥脆，法式糕点",
            "desc_pack": "包装清单：可颂坊丹麦酥",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "可颂坊丹麦酥 150g",
                    "caption": "层次丰富｜口感酥脆｜法式糕点",
                    "price": 16.90,
                    "cost_price": 11.00,
                    "market_price": 21.90,
                    "stock": 800,
                    "specs": {"规格": "150g"},
                    "barcode": "6901234568018",
                    "shelf_life": 5,
                },
            ]
        },
        
        # 面包新语面包
        {
            "brand": "面包新语",
            "category1": "食品",
            "category2": "零食",
            "category3": "面包",
            "spu_name": "面包新语松松",
            "desc_detail": "面包新语松松，松软香甜，口感丰富，新加坡品牌",
            "desc_pack": "包装清单：面包新语松松",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "面包新语松松 180g",
                    "caption": "松软香甜｜口感丰富｜新加坡品牌",
                    "price": 19.90,
                    "cost_price": 13.00,
                    "market_price": 25.90,
                    "stock": 750,
                    "specs": {"规格": "180g"},
                    "barcode": "6901234568019",
                    "shelf_life": 3,
                },
            ]
        },
        
        # ==================== 更多日化类商品 ====================
        
        # 威露士消毒液
        {
            "brand": "威露士",
            "category1": "日化",
            "category2": "清洁用品",
            "category3": "消毒液",
            "spu_name": "威露士消毒液",
            "desc_detail": "威露士消毒液，强力杀菌，安全无毒，家居必备",
            "desc_pack": "包装清单：威露士消毒液",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "威露士消毒液 1.8L",
                    "caption": "强力杀菌｜安全无毒｜家居必备",
                    "price": 42.90,
                    "cost_price": 26.00,
                    "market_price": 54.90,
                    "stock": 1100,
                    "specs": {"规格": "1.8L"},
                    "barcode": "6901234568020",
                    "shelf_life": 1825,
                },
                {
                    "name": "威露士消毒液 3L",
                    "caption": "强力杀菌｜安全无毒｜家庭装",
                    "price": 68.90,
                    "cost_price": 42.00,
                    "market_price": 85.90,
                    "stock": 900,
                    "specs": {"规格": "3L"},
                    "barcode": "6901234568021",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 宝洁旗下产品
        {
            "brand": "宝洁",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "洗发水",
            "spu_name": "海飞丝去屑洗发水",
            "desc_detail": "海飞丝去屑洗发水，去屑止痒，清爽控油，秀发柔顺",
            "desc_pack": "包装清单：海飞丝去屑洗发水",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "海飞丝去屑洗发水 200ml",
                    "caption": "去屑止痒｜清爽控油｜秀发柔顺",
                    "price": 22.90,
                    "cost_price": 14.00,
                    "market_price": 28.90,
                    "stock": 1600,
                    "specs": {"规格": "200ml", "类型": "去屑"},
                    "barcode": "6901234568022",
                    "shelf_life": 1825,
                },
            ]
        },
        {
            "brand": "宝洁",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "沐浴露",
            "spu_name": "舒肤佳沐浴露",
            "desc_detail": "舒肤佳沐浴露，抑菌除菌，温和清洁，全家适用",
            "desc_pack": "包装清单：舒肤佳沐浴露",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "舒肤佳沐浴露 720ml",
                    "caption": "抑菌除菌｜温和清洁｜全家适用",
                    "price": 38.90,
                    "cost_price": 24.00,
                    "market_price": 48.90,
                    "stock": 1400,
                    "specs": {"规格": "720ml"},
                    "barcode": "6901234568023",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 联合利华旗下产品
        {
            "brand": "联合利华",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "洗发水",
            "spu_name": "清扬洗发水",
            "desc_detail": "清扬洗发水，去屑止痒，清爽控油，秀发柔顺",
            "desc_pack": "包装清单：清扬洗发水",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "清扬洗发水 400ml",
                    "caption": "去屑止痒｜清爽控油｜秀发柔顺",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 45.90,
                    "stock": 1500,
                    "specs": {"规格": "400ml", "类型": "去屑"},
                    "barcode": "6901234568024",
                    "shelf_life": 1825,
                },
            ]
        },
        {
            "brand": "联合利华",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "沐浴露",
            "spu_name": "多芬沐浴露",
            "desc_detail": "多芬沐浴露，温和清洁，滋润保湿，肌肤柔嫩",
            "desc_pack": "包装清单：多芬沐浴露",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "多芬沐浴露 300ml",
                    "caption": "温和清洁｜滋润保湿｜肌肤柔嫩",
                    "price": 22.90,
                    "cost_price": 14.00,
                    "market_price": 28.90,
                    "stock": 1600,
                    "specs": {"规格": "300ml", "类型": "滋润"},
                    "barcode": "6901234568025",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多牛奶饮料类商品 ====================
        
        # 星巴克咖啡
        {
            "brand": "星巴克",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "咖啡",
            "spu_name": "星巴克咖啡豆",
            "desc_detail": "星巴克咖啡豆，精选阿拉比卡豆，香浓醇厚，提神醒脑",
            "desc_pack": "包装清单：星巴克咖啡豆",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "星巴克咖啡豆 250g",
                    "caption": "精选阿拉比卡豆｜香浓醇厚｜提神醒脑",
                    "price": 88.00,
                    "cost_price": 60.00,
                    "market_price": 108.00,
                    "stock": 600,
                    "specs": {"规格": "250g", "口味": "中度烘焙"},
                    "barcode": "6901234568026",
                    "shelf_life": 365,
                },
                {
                    "name": "星巴克咖啡豆 500g",
                    "caption": "精选阿拉比卡豆｜香浓醇厚｜家庭装",
                    "price": 158.00,
                    "cost_price": 110.00,
                    "market_price": 198.00,
                    "stock": 500,
                    "specs": {"规格": "500g", "口味": "中度烘焙"},
                    "barcode": "6901234568027",
                    "shelf_life": 365,
                },
            ]
        },
        {
            "brand": "星巴克",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "咖啡",
            "spu_name": "星巴克即饮咖啡",
            "desc_detail": "星巴克即饮咖啡，方便快捷，香浓醇厚，提神醒脑",
            "desc_pack": "包装清单：星巴克即饮咖啡",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "星巴克即饮咖啡 270ml*6瓶",
                    "caption": "方便快捷｜香浓醇厚｜提神醒脑",
                    "price": 68.90,
                    "cost_price": 45.00,
                    "market_price": 85.90,
                    "stock": 800,
                    "specs": {"规格": "270ml*6瓶", "口味": "拿铁"},
                    "barcode": "6901234568028",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 喜茶饮品
        {
            "brand": "喜茶",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "茶饮",
            "spu_name": "喜茶水果茶",
            "desc_detail": "喜茶水果茶，新鲜水果，茶香浓郁，健康饮品",
            "desc_pack": "包装清单：喜茶水果茶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "喜茶水果茶 500ml",
                    "caption": "新鲜水果｜茶香浓郁｜健康饮品",
                    "price": 28.00,
                    "cost_price": 18.00,
                    "market_price": 35.00,
                    "stock": 1000,
                    "specs": {"规格": "500ml", "口味": "多肉葡萄"},
                    "barcode": "6901234568029",
                    "shelf_life": 7,
                },
            ]
        },
        
        # ==================== 更多酒水类商品 ====================
        
        # 汾酒白酒
        {
            "brand": "汾酒",
            "category1": "酒水",
            "category2": "白酒",
            "category3": "清香型",
            "spu_name": "汾酒青花",
            "desc_detail": "汾酒青花，清香纯正，口感醇厚，回味悠长",
            "desc_pack": "包装清单：汾酒青花",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "汾酒青花 53度 500ml",
                    "caption": "清香纯正｜口感醇厚｜回味悠长",
                    "price": 388.00,
                    "cost_price": 300.00,
                    "market_price": 468.00,
                    "stock": 200,
                    "specs": {"规格": "500ml", "度数": "53度"},
                    "barcode": "6901234568030",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 王朝红酒
        {
            "brand": "王朝",
            "category1": "酒水",
            "category2": "红酒",
            "category3": "干红",
            "spu_name": "王朝干红葡萄酒",
            "desc_detail": "王朝干红葡萄酒，果香浓郁，口感醇厚，余味悠长",
            "desc_pack": "包装清单：王朝干红葡萄酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "王朝干红葡萄酒 750ml",
                    "caption": "果香浓郁｜口感醇厚｜余味悠长",
                    "price": 58.00,
                    "cost_price": 38.00,
                    "market_price": 72.00,
                    "stock": 350,
                    "specs": {"规格": "750ml"},
                    "barcode": "6901234568031",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 人头马洋酒
        {
            "brand": "人头马",
            "category1": "酒水",
            "category2": "洋酒",
            "category3": "干邑",
            "spu_name": "人头马VSOP",
            "desc_detail": "人头马VSOP，醇厚口感，香气浓郁，法国干邑",
            "desc_pack": "包装清单：人头马VSOP",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "人头马VSOP 700ml",
                    "caption": "醇厚口感｜香气浓郁｜法国干邑",
                    "price": 620.00,
                    "cost_price": 450.00,
                    "market_price": 750.00,
                    "stock": 180,
                    "specs": {"规格": "700ml"},
                    "barcode": "6901234568032",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # ==================== 更多食品类商品 - 粮油调味 ====================
        
        # 金龙鱼食用油
        {
            "brand": "金龙鱼",
            "category1": "食品",
            "category2": "粮油",
            "category3": "食用油",
            "spu_name": "金龙鱼调和油",
            "desc_detail": "金龙鱼调和油，营养均衡，健康烹饪，家庭必备",
            "desc_pack": "包装清单：金龙鱼调和油",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "金龙鱼调和油 1.8L",
                    "caption": "营养均衡｜健康烹饪｜家庭必备",
                    "price": 25.90,
                    "cost_price": 16.00,
                    "market_price": 32.90,
                    "stock": 1500,
                    "specs": {"规格": "1.8L"},
                    "barcode": "6901234568033",
                    "shelf_life": 730,
                },
                {
                    "name": "金龙鱼调和油 5L",
                    "caption": "营养均衡｜健康烹饪｜家庭装",
                    "price": 65.90,
                    "cost_price": 42.00,
                    "market_price": 82.90,
                    "stock": 1200,
                    "specs": {"规格": "5L"},
                    "barcode": "6901234568034",
                    "shelf_life": 730,
                },
            ]
        },
        {
            "brand": "金龙鱼",
            "category1": "食品",
            "category2": "粮油",
            "category3": "食用油",
            "spu_name": "金龙鱼花生油",
            "desc_detail": "金龙鱼花生油，香浓纯正，健康烹饪，美味佳肴",
            "desc_pack": "包装清单：金龙鱼花生油",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "金龙鱼花生油 1.8L",
                    "caption": "香浓纯正｜健康烹饪｜美味佳肴",
                    "price": 35.90,
                    "cost_price": 23.00,
                    "market_price": 45.90,
                    "stock": 1300,
                    "specs": {"规格": "1.8L"},
                    "barcode": "6901234568035",
                    "shelf_life": 730,
                },
                {
                    "name": "金龙鱼花生油 5L",
                    "caption": "香浓纯正｜健康烹饪｜家庭装",
                    "price": 95.90,
                    "cost_price": 62.00,
                    "market_price": 118.90,
                    "stock": 1000,
                    "specs": {"规格": "5L"},
                    "barcode": "6901234568036",
                    "shelf_life": 730,
                },
            ]
        },
        
        # 福临门食用油
        {
            "brand": "福临门",
            "category1": "食品",
            "category2": "粮油",
            "category3": "食用油",
            "spu_name": "福临门玉米油",
            "desc_detail": "福临门玉米油，清香纯正，健康烹饪，营养美味",
            "desc_pack": "包装清单：福临门玉米油",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "福临门玉米油 1.8L",
                    "caption": "清香纯正｜健康烹饪｜营养美味",
                    "price": 32.90,
                    "cost_price": 21.00,
                    "market_price": 42.90,
                    "stock": 1400,
                    "specs": {"规格": "1.8L"},
                    "barcode": "6901234568037",
                    "shelf_life": 730,
                },
                {
                    "name": "福临门玉米油 5L",
                    "caption": "清香纯正｜健康烹饪｜家庭装",
                    "price": 88.90,
                    "cost_price": 58.00,
                    "market_price": 110.90,
                    "stock": 1100,
                    "specs": {"规格": "5L"},
                    "barcode": "6901234568038",
                    "shelf_life": 730,
                },
            ]
        },
        
        # 鲁花花生油
        {
            "brand": "鲁花",
            "category1": "食品",
            "category2": "粮油",
            "category3": "食用油",
            "spu_name": "鲁花花生油",
            "desc_detail": "鲁花花生油，物理压榨，香浓纯正，健康烹饪",
            "desc_pack": "包装清单：鲁花花生油",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "鲁花花生油 1.8L",
                    "caption": "物理压榨｜香浓纯正｜健康烹饪",
                    "price": 42.90,
                    "cost_price": 28.00,
                    "market_price": 55.90,
                    "stock": 1200,
                    "specs": {"规格": "1.8L"},
                    "barcode": "6901234568039",
                    "shelf_life": 730,
                },
                {
                    "name": "鲁花花生油 5L",
                    "caption": "物理压榨｜香浓纯正｜家庭装",
                    "price": 115.90,
                    "cost_price": 75.00,
                    "market_price": 145.90,
                    "stock": 900,
                    "specs": {"规格": "5L"},
                    "barcode": "6901234568040",
                    "shelf_life": 730,
                },
            ]
        },
        
        # 海天酱油
        {
            "brand": "海天",
            "category1": "食品",
            "category2": "调味品",
            "category3": "酱油",
            "spu_name": "海天酱油",
            "desc_detail": "海天酱油，酿造工艺，鲜味浓郁，烹饪必备",
            "desc_pack": "包装清单：海天酱油",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "海天酱油 500ml",
                    "caption": "酿造工艺｜鲜味浓郁｜烹饪必备",
                    "price": 8.90,
                    "cost_price": 5.50,
                    "market_price": 11.90,
                    "stock": 2000,
                    "specs": {"规格": "500ml", "类型": "生抽"},
                    "barcode": "6901234568041",
                    "shelf_life": 730,
                },
                {
                    "name": "海天酱油 1.75L",
                    "caption": "酿造工艺｜鲜味浓郁｜家庭装",
                    "price": 22.90,
                    "cost_price": 14.00,
                    "market_price": 28.90,
                    "stock": 1800,
                    "specs": {"规格": "1.75L", "类型": "生抽"},
                    "barcode": "6901234568042",
                    "shelf_life": 730,
                },
                {
                    "name": "海天酱油 500ml 老抽",
                    "caption": "酿造工艺｜色泽红亮｜烹饪必备",
                    "price": 9.90,
                    "cost_price": 6.00,
                    "market_price": 12.90,
                    "stock": 1900,
                    "specs": {"规格": "500ml", "类型": "老抽"},
                    "barcode": "6901234568043",
                    "shelf_life": 730,
                },
            ]
        },
        
        # 李锦记酱油
        {
            "brand": "李锦记",
            "category1": "食品",
            "category2": "调味品",
            "category3": "酱油",
            "spu_name": "李锦记酱油",
            "desc_detail": "李锦记酱油，百年传承，鲜味浓郁，烹饪佳品",
            "desc_pack": "包装清单：李锦记酱油",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "李锦记酱油 500ml",
                    "caption": "百年传承｜鲜味浓郁｜烹饪佳品",
                    "price": 15.90,
                    "cost_price": 10.00,
                    "market_price": 20.90,
                    "stock": 1500,
                    "specs": {"规格": "500ml", "类型": "生抽"},
                    "barcode": "6901234568044",
                    "shelf_life": 730,
                },
                {
                    "name": "李锦记酱油 1.8L",
                    "caption": "百年传承｜鲜味浓郁｜家庭装",
                    "price": 45.90,
                    "cost_price": 30.00,
                    "market_price": 58.90,
                    "stock": 1300,
                    "specs": {"规格": "1.8L", "类型": "生抽"},
                    "barcode": "6901234568045",
                    "shelf_life": 730,
                },
            ]
        },
        
        # 老干妈辣椒酱
        {
            "brand": "老干妈",
            "category1": "食品",
            "category2": "调味品",
            "category3": "辣椒酱",
            "spu_name": "老干妈辣椒酱",
            "desc_detail": "老干妈辣椒酱，香辣可口，下饭神器，经典调味",
            "desc_pack": "包装清单：老干妈辣椒酱",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "老干妈辣椒酱 280g",
                    "caption": "香辣可口｜下饭神器｜经典调味",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 2500,
                    "specs": {"规格": "280g", "口味": "风味豆豉"},
                    "barcode": "6901234568046",
                    "shelf_life": 730,
                },
                {
                    "name": "老干妈辣椒酱 475g",
                    "caption": "香辣可口｜下饭神器｜家庭装",
                    "price": 18.90,
                    "cost_price": 12.00,
                    "market_price": 24.90,
                    "stock": 2200,
                    "specs": {"规格": "475g", "口味": "风味豆豉"},
                    "barcode": "6901234568047",
                    "shelf_life": 730,
                },
            ]
        },
        
        # 太太乐鸡精
        {
            "brand": "太太乐",
            "category1": "食品",
            "category2": "调味品",
            "category3": "鸡精",
            "spu_name": "太太乐鸡精",
            "desc_detail": "太太乐鸡精，鲜味浓郁，提鲜增香，烹饪必备",
            "desc_pack": "包装清单：太太乐鸡精",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "太太乐鸡精 200g",
                    "caption": "鲜味浓郁｜提鲜增香｜烹饪必备",
                    "price": 8.90,
                    "cost_price": 5.50,
                    "market_price": 11.90,
                    "stock": 2000,
                    "specs": {"规格": "200g"},
                    "barcode": "6901234568048",
                    "shelf_life": 730,
                },
                {
                    "name": "太太乐鸡精 454g",
                    "caption": "鲜味浓郁｜提鲜增香｜家庭装",
                    "price": 18.90,
                    "cost_price": 12.00,
                    "market_price": 24.90,
                    "stock": 1800,
                    "specs": {"规格": "454g"},
                    "barcode": "6901234568049",
                    "shelf_life": 730,
                },
                {
                    "name": "太太乐鸡精 900g",
                    "caption": "鲜味浓郁｜提鲜增香｜实惠装",
                    "price": 35.90,
                    "cost_price": 23.00,
                    "market_price": 45.90,
                    "stock": 1500,
                    "specs": {"规格": "900g"},
                    "barcode": "6901234568050",
                    "shelf_life": 730,
                },
            ]
        },
        
        # 厨邦酱油
        {
            "brand": "厨邦",
            "category1": "食品",
            "category2": "调味品",
            "category3": "酱油",
            "spu_name": "厨邦酱油",
            "desc_detail": "厨邦酱油，阳光酿造，鲜味浓郁，烹饪佳品",
            "desc_pack": "包装清单：厨邦酱油",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "厨邦酱油 500ml",
                    "caption": "阳光酿造｜鲜味浓郁｜烹饪佳品",
                    "price": 9.90,
                    "cost_price": 6.00,
                    "market_price": 12.90,
                    "stock": 1900,
                    "specs": {"规格": "500ml", "类型": "生抽"},
                    "barcode": "6901234568051",
                    "shelf_life": 730,
                },
                {
                    "name": "厨邦酱油 1.6L",
                    "caption": "阳光酿造｜鲜味浓郁｜家庭装",
                    "price": 24.90,
                    "cost_price": 16.00,
                    "market_price": 32.90,
                    "stock": 1700,
                    "specs": {"规格": "1.6L", "类型": "生抽"},
                    "barcode": "6901234568052",
                    "shelf_life": 730,
                },
            ]
        },
        
        # 恒顺醋
        {
            "brand": "恒顺",
            "category1": "食品",
            "category2": "调味品",
            "category3": "醋",
            "spu_name": "恒顺香醋",
            "desc_detail": "恒顺香醋，传统工艺，酸味纯正，烹饪佳品",
            "desc_pack": "包装清单：恒顺香醋",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "恒顺香醋 500ml",
                    "caption": "传统工艺｜酸味纯正｜烹饪佳品",
                    "price": 8.90,
                    "cost_price": 5.50,
                    "market_price": 11.90,
                    "stock": 1800,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568053",
                    "shelf_life": 730,
                },
                {
                    "name": "恒顺香醋 550ml",
                    "caption": "传统工艺｜酸味纯正｜经典装",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 1600,
                    "specs": {"规格": "550ml"},
                    "barcode": "6901234568054",
                    "shelf_life": 730,
                },
            ]
        },
        
        # ==================== 更多食品类商品 - 方便速食 ====================
        
        # 统一方便面
        {
            "brand": "统一",
            "category1": "食品",
            "category2": "方便食品",
            "category3": "方便面",
            "spu_name": "统一汤达人",
            "desc_detail": "统一汤达人，浓郁汤底，劲道面条，美味方便",
            "desc_pack": "包装清单：统一汤达人",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "统一汤达人 105g",
                    "caption": "浓郁汤底｜劲道面条｜美味方便",
                    "price": 5.50,
                    "cost_price": 3.50,
                    "market_price": 7.50,
                    "stock": 1800,
                    "specs": {"规格": "105g", "口味": "豚骨拉面"},
                    "barcode": "6901234568055",
                    "shelf_life": 180,
                },
                {
                    "name": "统一汤达人 5连包",
                    "caption": "浓郁汤底｜劲道面条｜家庭装",
                    "price": 25.50,
                    "cost_price": 16.00,
                    "market_price": 32.50,
                    "stock": 1500,
                    "specs": {"规格": "5连包", "口味": "豚骨拉面"},
                    "barcode": "6901234568056",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 康师傅方便面
        {
            "brand": "康师傅",
            "category1": "食品",
            "category2": "方便食品",
            "category3": "方便面",
            "spu_name": "康师傅鲜虾鱼板面",
            "desc_detail": "康师傅鲜虾鱼板面，海鲜风味，鲜美可口，经典方便",
            "desc_pack": "包装清单：康师傅鲜虾鱼板面",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "康师傅鲜虾鱼板面 105g",
                    "caption": "海鲜风味｜鲜美可口｜经典方便",
                    "price": 3.50,
                    "cost_price": 2.00,
                    "market_price": 4.50,
                    "stock": 1900,
                    "specs": {"规格": "105g", "口味": "鲜虾鱼板"},
                    "barcode": "6901234568057",
                    "shelf_life": 180,
                },
                {
                    "name": "康师傅鲜虾鱼板面 5连包",
                    "caption": "海鲜风味｜鲜美可口｜家庭装",
                    "price": 16.50,
                    "cost_price": 9.50,
                    "market_price": 20.50,
                    "stock": 1600,
                    "specs": {"规格": "5连包", "口味": "鲜虾鱼板"},
                    "barcode": "6901234568058",
                    "shelf_life": 180,
                },
            ]
        },
        
        # ==================== 更多食品类商品 - 罐头食品 ====================
        
        # 梅林午餐肉
        {
            "brand": "梅林",
            "category1": "食品",
            "category2": "罐头",
            "category3": "肉罐头",
            "spu_name": "梅林午餐肉",
            "desc_detail": "梅林午餐肉，肉质鲜嫩，口感丰富，方便快捷",
            "desc_pack": "包装清单：梅林午餐肉",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "梅林午餐肉 340g",
                    "caption": "肉质鲜嫩｜口感丰富｜方便快捷",
                    "price": 18.90,
                    "cost_price": 12.00,
                    "market_price": 24.90,
                    "stock": 1200,
                    "specs": {"规格": "340g"},
                    "barcode": "6901234568059",
                    "shelf_life": 1095,
                },
            ]
        },
        
        # 古龙香菇猪脚
        {
            "brand": "古龙",
            "category1": "食品",
            "category2": "罐头",
            "category3": "肉罐头",
            "spu_name": "古龙香菇猪脚",
            "desc_detail": "古龙香菇猪脚，传统工艺，肉质酥烂，美味佳肴",
            "desc_pack": "包装清单：古龙香菇猪脚",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "古龙香菇猪脚 340g",
                    "caption": "传统工艺｜肉质酥烂｜美味佳肴",
                    "price": 22.90,
                    "cost_price": 15.00,
                    "market_price": 28.90,
                    "stock": 1000,
                    "specs": {"规格": "340g"},
                    "barcode": "6901234568060",
                    "shelf_life": 1095,
                },
            ]
        },
        
        # 鹰金钱豆豉鲮鱼
        {
            "brand": "鹰金钱",
            "category1": "食品",
            "category2": "罐头",
            "category3": "鱼罐头",
            "spu_name": "鹰金钱豆豉鲮鱼",
            "desc_detail": "鹰金钱豆豉鲮鱼，传统工艺，鱼肉鲜美，经典罐头",
            "desc_pack": "包装清单：鹰金钱豆豉鲮鱼",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "鹰金钱豆豉鲮鱼 227g",
                    "caption": "传统工艺｜鱼肉鲜美｜经典罐头",
                    "price": 15.90,
                    "cost_price": 10.00,
                    "market_price": 20.90,
                    "stock": 1100,
                    "specs": {"规格": "227g"},
                    "barcode": "6901234568061",
                    "shelf_life": 1095,
                },
            ]
        },
        
        # ==================== 更多食品类商品 - 休闲零食 ====================
        
        # 旺旺更多产品
        {
            "brand": "旺旺",
            "category1": "食品",
            "category2": "零食",
            "category3": "膨化食品",
            "spu_name": "旺旺浪味仙",
            "desc_detail": "旺旺浪味仙，香脆可口，多种口味，经典零食",
            "desc_pack": "包装清单：旺旺浪味仙",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "旺旺浪味仙 70g",
                    "caption": "香脆可口｜多种口味｜经典零食",
                    "price": 6.90,
                    "cost_price": 4.50,
                    "market_price": 8.90,
                    "stock": 1400,
                    "specs": {"规格": "70g", "口味": "蔬菜"},
                    "barcode": "6901234568062",
                    "shelf_life": 180,
                },
                {
                    "name": "旺旺浪味仙 140g",
                    "caption": "香脆可口｜多种口味｜分享装",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 1200,
                    "specs": {"规格": "140g", "口味": "蔬菜"},
                    "barcode": "6901234568063",
                    "shelf_life": 180,
                },
            ]
        },
        {
            "brand": "旺旺",
            "category1": "食品",
            "category2": "零食",
            "category3": "糖果",
            "spu_name": "旺旺QQ糖",
            "desc_detail": "旺旺QQ糖，Q弹口感，多种口味，儿童喜爱",
            "desc_pack": "包装清单：旺旺QQ糖",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "旺旺QQ糖 50g",
                    "caption": "Q弹口感｜多种口味｜儿童喜爱",
                    "price": 5.90,
                    "cost_price": 3.50,
                    "market_price": 7.90,
                    "stock": 1600,
                    "specs": {"规格": "50g", "口味": "荔枝"},
                    "barcode": "6901234568064",
                    "shelf_life": 365,
                },
                {
                    "name": "旺旺QQ糖 120g",
                    "caption": "Q弹口感｜多种口味｜分享装",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 1400,
                    "specs": {"规格": "120g", "口味": "荔枝"},
                    "barcode": "6901234568065",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 奥利奥更多产品
        {
            "brand": "奥利奥",
            "category1": "食品",
            "category2": "零食",
            "category3": "饼干",
            "spu_name": "奥利奥巧克力棒",
            "desc_detail": "奥利奥巧克力棒，巧克力涂层，香脆可口，经典零食",
            "desc_pack": "包装清单：奥利奥巧克力棒",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "奥利奥巧克力棒 124g",
                    "caption": "巧克力涂层｜香脆可口｜经典零食",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 1300,
                    "specs": {"规格": "124g"},
                    "barcode": "6901234568066",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 乐事更多产品
        {
            "brand": "乐事",
            "category1": "食品",
            "category2": "零食",
            "category3": "薯片",
            "spu_name": "乐事波浪薯片",
            "desc_detail": "乐事波浪薯片，波浪口感，香脆可口，独特体验",
            "desc_pack": "包装清单：乐事波浪薯片",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "乐事波浪薯片 70g",
                    "caption": "波浪口感｜香脆可口｜独特体验",
                    "price": 9.50,
                    "cost_price": 6.00,
                    "market_price": 12.50,
                    "stock": 1200,
                    "specs": {"规格": "70g", "口味": "原味"},
                    "barcode": "6901234568067",
                    "shelf_life": 180,
                },
                {
                    "name": "乐事波浪薯片 145g",
                    "caption": "波浪口感｜香脆可口｜分享装",
                    "price": 18.50,
                    "cost_price": 12.00,
                    "market_price": 23.50,
                    "stock": 1000,
                    "specs": {"规格": "145g", "口味": "原味"},
                    "barcode": "6901234568068",
                    "shelf_life": 180,
                },
            ]
        },
        
        # ==================== 更多日化类商品 - 口腔护理 ====================
        
        # 高露洁牙膏
        {
            "brand": "高露洁",
            "category1": "日化",
            "category2": "口腔护理",
            "category3": "牙膏",
            "spu_name": "高露洁牙膏",
            "desc_detail": "高露洁牙膏，专业护理，清新口气，健齿护龈",
            "desc_pack": "包装清单：高露洁牙膏",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "高露洁牙膏 120g",
                    "caption": "专业护理｜清新口气｜健齿护龈",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 1800,
                    "specs": {"规格": "120g", "类型": "全效"},
                    "barcode": "6901234568069",
                    "shelf_life": 1825,
                },
                {
                    "name": "高露洁牙膏 200g",
                    "caption": "专业护理｜清新口气｜家庭装",
                    "price": 22.90,
                    "cost_price": 14.00,
                    "market_price": 28.90,
                    "stock": 1600,
                    "specs": {"规格": "200g", "类型": "全效"},
                    "barcode": "6901234568070",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 佳洁士牙膏
        {
            "brand": "佳洁士",
            "category1": "日化",
            "category2": "口腔护理",
            "category3": "牙膏",
            "spu_name": "佳洁士牙膏",
            "desc_detail": "佳洁士牙膏，专业美白，清新口气，健齿护龈",
            "desc_pack": "包装清单：佳洁士牙膏",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "佳洁士牙膏 120g",
                    "caption": "专业美白｜清新口气｜健齿护龈",
                    "price": 15.90,
                    "cost_price": 10.00,
                    "market_price": 20.90,
                    "stock": 1700,
                    "specs": {"规格": "120g", "类型": "3D美白"},
                    "barcode": "6901234568071",
                    "shelf_life": 1825,
                },
                {
                    "name": "佳洁士牙膏 200g",
                    "caption": "专业美白｜清新口气｜家庭装",
                    "price": 25.90,
                    "cost_price": 16.00,
                    "market_price": 32.90,
                    "stock": 1500,
                    "specs": {"规格": "200g", "类型": "3D美白"},
                    "barcode": "6901234568072",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 黑人牙膏
        {
            "brand": "黑人牙膏",
            "category1": "日化",
            "category2": "口腔护理",
            "category3": "牙膏",
            "spu_name": "黑人牙膏",
            "desc_detail": "黑人牙膏，清新口气，美白健齿，经典品牌",
            "desc_pack": "包装清单：黑人牙膏",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "黑人牙膏 120g",
                    "caption": "清新口气｜美白健齿｜经典品牌",
                    "price": 13.90,
                    "cost_price": 8.50,
                    "market_price": 17.90,
                    "stock": 1900,
                    "specs": {"规格": "120g", "类型": "超白"},
                    "barcode": "6901234568073",
                    "shelf_life": 1825,
                },
                {
                    "name": "黑人牙膏 170g",
                    "caption": "清新口气｜美白健齿｜家庭装",
                    "price": 22.90,
                    "cost_price": 14.00,
                    "market_price": 28.90,
                    "stock": 1700,
                    "specs": {"规格": "170g", "类型": "超白"},
                    "barcode": "6901234568074",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 云南白药牙膏
        {
            "brand": "云南白药",
            "category1": "日化",
            "category2": "口腔护理",
            "category3": "牙膏",
            "spu_name": "云南白药牙膏",
            "desc_detail": "云南白药牙膏，养护牙龈，止血止痛，专业护理",
            "desc_pack": "包装清单：云南白药牙膏",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "云南白药牙膏 100g",
                    "caption": "养护牙龈｜止血止痛｜专业护理",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 36.90,
                    "stock": 1400,
                    "specs": {"规格": "100g"},
                    "barcode": "6901234568075",
                    "shelf_life": 1825,
                },
                {
                    "name": "云南白药牙膏 155g",
                    "caption": "养护牙龈｜止血止痛｜家庭装",
                    "price": 42.90,
                    "cost_price": 27.00,
                    "market_price": 54.90,
                    "stock": 1200,
                    "specs": {"规格": "155g"},
                    "barcode": "6901234568076",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多日化类商品 - 牙刷 ====================
        
        # 欧乐B牙刷
        {
            "brand": "欧乐B",
            "category1": "日化",
            "category2": "口腔护理",
            "category3": "牙刷",
            "spu_name": "欧乐B牙刷",
            "desc_detail": "欧乐B牙刷，专业设计，清洁彻底，护齿健龈",
            "desc_pack": "包装清单：欧乐B牙刷",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "欧乐B牙刷 4支装",
                    "caption": "专业设计｜清洁彻底｜护齿健龈",
                    "price": 25.90,
                    "cost_price": 16.00,
                    "market_price": 32.90,
                    "stock": 1500,
                    "specs": {"规格": "4支装", "类型": "软毛"},
                    "barcode": "6901234568077",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多日化类商品 - 洗护用品 ====================
        
        # 资生堂洗发水
        {
            "brand": "资生堂",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "洗发水",
            "spu_name": "资生堂洗发水",
            "desc_detail": "资生堂洗发水，专业护理，滋润修护，秀发柔顺",
            "desc_pack": "包装清单：资生堂洗发水",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "资生堂洗发水 400ml",
                    "caption": "专业护理｜滋润修护｜秀发柔顺",
                    "price": 68.90,
                    "cost_price": 42.00,
                    "market_price": 85.90,
                    "stock": 1000,
                    "specs": {"规格": "400ml", "类型": "滋润"},
                    "barcode": "6901234568078",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 施华蔻洗发水
        {
            "brand": "施华蔻",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "洗发水",
            "spu_name": "施华蔻洗发水",
            "desc_detail": "施华蔻洗发水，专业护理，染烫修护，秀发健康",
            "desc_pack": "包装清单：施华蔻洗发水",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "施华蔻洗发水 400ml",
                    "caption": "专业护理｜染烫修护｜秀发健康",
                    "price": 58.90,
                    "cost_price": 36.00,
                    "market_price": 73.90,
                    "stock": 1100,
                    "specs": {"规格": "400ml", "类型": "修护"},
                    "barcode": "6901234568079",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多牛奶饮料类商品 - 功能饮料 ====================
        
        # 东鹏特饮
        {
            "brand": "东鹏特饮",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "功能饮料",
            "spu_name": "东鹏特饮",
            "desc_detail": "东鹏特饮，提神醒脑，补充能量，运动必备",
            "desc_pack": "包装清单：东鹏特饮",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "东鹏特饮 250ml",
                    "caption": "提神醒脑｜补充能量｜运动必备",
                    "price": 5.50,
                    "cost_price": 3.50,
                    "market_price": 7.50,
                    "stock": 2000,
                    "specs": {"规格": "250ml"},
                    "barcode": "6901234568080",
                    "shelf_life": 365,
                },
                {
                    "name": "东鹏特饮 250ml*6罐",
                    "caption": "提神醒脑｜补充能量｜整箱装",
                    "price": 32.50,
                    "cost_price": 20.00,
                    "market_price": 42.50,
                    "stock": 1500,
                    "specs": {"规格": "250ml*6罐"},
                    "barcode": "6901234568081",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 乐虎功能饮料
        {
            "brand": "乐虎",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "功能饮料",
            "spu_name": "乐虎功能饮料",
            "desc_detail": "乐虎功能饮料，提神醒脑，补充能量，运动必备",
            "desc_pack": "包装清单：乐虎功能饮料",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "乐虎功能饮料 380ml",
                    "caption": "提神醒脑｜补充能量｜运动必备",
                    "price": 6.00,
                    "cost_price": 3.80,
                    "market_price": 8.00,
                    "stock": 1900,
                    "specs": {"规格": "380ml"},
                    "barcode": "6901234568082",
                    "shelf_life": 365,
                },
                {
                    "name": "乐虎功能饮料 380ml*6罐",
                    "caption": "提神醒脑｜补充能量｜整箱装",
                    "price": 35.00,
                    "cost_price": 22.00,
                    "market_price": 45.00,
                    "stock": 1400,
                    "specs": {"规格": "380ml*6罐"},
                    "barcode": "6901234568083",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 脉动维生素饮料
        {
            "brand": "脉动",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "维生素饮料",
            "spu_name": "脉动维生素饮料",
            "desc_detail": "脉动维生素饮料，补充维生素，清爽解渴，健康饮品",
            "desc_pack": "包装清单：脉动维生素饮料",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "脉动维生素饮料 500ml",
                    "caption": "补充维生素｜清爽解渴｜健康饮品",
                    "price": 5.00,
                    "cost_price": 3.00,
                    "market_price": 6.50,
                    "stock": 2100,
                    "specs": {"规格": "500ml", "口味": "青柠"},
                    "barcode": "6901234568084",
                    "shelf_life": 365,
                },
                {
                    "name": "脉动维生素饮料 500ml*6瓶",
                    "caption": "补充维生素｜清爽解渴｜整箱装",
                    "price": 28.00,
                    "cost_price": 17.00,
                    "market_price": 36.00,
                    "stock": 1600,
                    "specs": {"规格": "500ml*6瓶", "口味": "青柠"},
                    "barcode": "6901234568085",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 尖叫运动饮料
        {
            "brand": "尖叫",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "运动饮料",
            "spu_name": "尖叫运动饮料",
            "desc_detail": "尖叫运动饮料，补充电解质，运动必备，健康饮品",
            "desc_pack": "包装清单：尖叫运动饮料",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "尖叫运动饮料 550ml",
                    "caption": "补充电解质｜运动必备｜健康饮品",
                    "price": 5.50,
                    "cost_price": 3.50,
                    "market_price": 7.50,
                    "stock": 2000,
                    "specs": {"规格": "550ml", "口味": "纤维"},
                    "barcode": "6901234568086",
                    "shelf_life": 365,
                },
                {
                    "name": "尖叫运动饮料 550ml*6瓶",
                    "caption": "补充电解质｜运动必备｜整箱装",
                    "price": 32.00,
                    "cost_price": 20.00,
                    "market_price": 42.00,
                    "stock": 1500,
                    "specs": {"规格": "550ml*6瓶", "口味": "纤维"},
                    "barcode": "6901234568087",
                    "shelf_life": 365,
                },
            ]
        },
        
        # ==================== 更多牛奶饮料类商品 - 茶饮 ====================
        
        # 康师傅冰红茶
        {
            "brand": "康师傅",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "茶饮",
            "spu_name": "康师傅冰红茶",
            "desc_detail": "康师傅冰红茶，清爽解渴，经典茶饮，夏日必备",
            "desc_pack": "包装清单：康师傅冰红茶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "康师傅冰红茶 500ml",
                    "caption": "清爽解渴｜经典茶饮｜夏日必备",
                    "price": 3.50,
                    "cost_price": 2.00,
                    "market_price": 4.50,
                    "stock": 2500,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568088",
                    "shelf_life": 365,
                },
                {
                    "name": "康师傅冰红茶 500ml*15瓶",
                    "caption": "清爽解渴｜经典茶饮｜整箱装",
                    "price": 48.00,
                    "cost_price": 28.00,
                    "market_price": 60.00,
                    "stock": 1800,
                    "specs": {"规格": "500ml*15瓶"},
                    "barcode": "6901234568089",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 统一冰红茶
        {
            "brand": "统一",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "茶饮",
            "spu_name": "统一冰红茶",
            "desc_detail": "统一冰红茶，清爽解渴，经典茶饮，夏日必备",
            "desc_pack": "包装清单：统一冰红茶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "统一冰红茶 500ml",
                    "caption": "清爽解渴｜经典茶饮｜夏日必备",
                    "price": 3.50,
                    "cost_price": 2.00,
                    "market_price": 4.50,
                    "stock": 2400,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568090",
                    "shelf_life": 365,
                },
                {
                    "name": "统一冰红茶 500ml*15瓶",
                    "caption": "清爽解渴｜经典茶饮｜整箱装",
                    "price": 48.00,
                    "cost_price": 28.00,
                    "market_price": 60.00,
                    "stock": 1700,
                    "specs": {"规格": "500ml*15瓶"},
                    "barcode": "6901234568091",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 三得利乌龙茶
        {
            "brand": "三得利",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "茶饮",
            "spu_name": "三得利乌龙茶",
            "desc_detail": "三得利乌龙茶，清香醇厚，健康茶饮，零糖零卡",
            "desc_pack": "包装清单：三得利乌龙茶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "三得利乌龙茶 500ml",
                    "caption": "清香醇厚｜健康茶饮｜零糖零卡",
                    "price": 4.50,
                    "cost_price": 2.80,
                    "market_price": 6.00,
                    "stock": 2200,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568092",
                    "shelf_life": 365,
                },
                {
                    "name": "三得利乌龙茶 500ml*15瓶",
                    "caption": "清香醇厚｜健康茶饮｜整箱装",
                    "price": 62.00,
                    "cost_price": 38.00,
                    "market_price": 78.00,
                    "stock": 1600,
                    "specs": {"规格": "500ml*15瓶"},
                    "barcode": "6901234568093",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 东方树叶
        {
            "brand": "东方树叶",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "茶饮",
            "spu_name": "东方树叶",
            "desc_detail": "东方树叶，传统工艺，清香醇厚，健康茶饮",
            "desc_pack": "包装清单：东方树叶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "东方树叶 500ml",
                    "caption": "传统工艺｜清香醇厚｜健康茶饮",
                    "price": 5.00,
                    "cost_price": 3.00,
                    "market_price": 6.50,
                    "stock": 2100,
                    "specs": {"规格": "500ml", "口味": "茉莉花茶"},
                    "barcode": "6901234568094",
                    "shelf_life": 365,
                },
                {
                    "name": "东方树叶 500ml*12瓶",
                    "caption": "传统工艺｜清香醇厚｜整箱装",
                    "price": 55.00,
                    "cost_price": 34.00,
                    "market_price": 70.00,
                    "stock": 1500,
                    "specs": {"规格": "500ml*12瓶", "口味": "茉莉花茶"},
                    "barcode": "6901234568095",
                    "shelf_life": 365,
                },
            ]
        },
        
        # ==================== 更多牛奶饮料类商品 - 果汁 ====================
        
        # 美汁源果粒橙
        {
            "brand": "美汁源",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "果汁",
            "spu_name": "美汁源果粒橙",
            "desc_detail": "美汁源果粒橙，真实果粒，鲜榨口感，健康果汁",
            "desc_pack": "包装清单：美汁源果粒橙",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "美汁源果粒橙 450ml",
                    "caption": "真实果粒｜鲜榨口感｜健康果汁",
                    "price": 5.50,
                    "cost_price": 3.50,
                    "market_price": 7.50,
                    "stock": 2300,
                    "specs": {"规格": "450ml"},
                    "barcode": "6901234568096",
                    "shelf_life": 365,
                },
                {
                    "name": "美汁源果粒橙 450ml*12瓶",
                    "caption": "真实果粒｜鲜榨口感｜整箱装",
                    "price": 62.00,
                    "cost_price": 38.00,
                    "market_price": 78.00,
                    "stock": 1600,
                    "specs": {"规格": "450ml*12瓶"},
                    "barcode": "6901234568097",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 农夫果园
        {
            "brand": "农夫果园",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "果汁",
            "spu_name": "农夫果园",
            "desc_detail": "农夫果园，混合果汁，营养均衡，健康饮品",
            "desc_pack": "包装清单：农夫果园",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "农夫果园 380ml",
                    "caption": "混合果汁｜营养均衡｜健康饮品",
                    "price": 6.00,
                    "cost_price": 3.80,
                    "market_price": 8.00,
                    "stock": 2200,
                    "specs": {"规格": "380ml", "口味": "30%混合果汁"},
                    "barcode": "6901234568098",
                    "shelf_life": 365,
                },
                {
                    "name": "农夫果园 380ml*12瓶",
                    "caption": "混合果汁｜营养均衡｜整箱装",
                    "price": 68.00,
                    "cost_price": 42.00,
                    "market_price": 85.00,
                    "stock": 1500,
                    "specs": {"规格": "380ml*12瓶", "口味": "30%混合果汁"},
                    "barcode": "6901234568099",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 统一鲜橙多
        {
            "brand": "统一",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "果汁",
            "spu_name": "统一鲜橙多",
            "desc_detail": "统一鲜橙多，鲜橙榨取，维生素C，健康果汁",
            "desc_pack": "包装清单：统一鲜橙多",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "统一鲜橙多 500ml",
                    "caption": "鲜橙榨取｜维生素C｜健康果汁",
                    "price": 5.00,
                    "cost_price": 3.00,
                    "market_price": 6.50,
                    "stock": 2400,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568100",
                    "shelf_life": 365,
                },
                {
                    "name": "统一鲜橙多 500ml*15瓶",
                    "caption": "鲜橙榨取｜维生素C｜整箱装",
                    "price": 68.00,
                    "cost_price": 42.00,
                    "market_price": 85.00,
                    "stock": 1700,
                    "specs": {"规格": "500ml*15瓶"},
                    "barcode": "6901234568101",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 酷儿果汁
        {
            "brand": "酷儿",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "果汁",
            "spu_name": "酷儿果汁",
            "desc_detail": "酷儿果汁，儿童喜爱，营养健康，美味果汁",
            "desc_pack": "包装清单：酷儿果汁",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "酷儿果汁 200ml",
                    "caption": "儿童喜爱｜营养健康｜美味果汁",
                    "price": 3.50,
                    "cost_price": 2.00,
                    "market_price": 4.50,
                    "stock": 2500,
                    "specs": {"规格": "200ml", "口味": "橙汁"},
                    "barcode": "6901234568102",
                    "shelf_life": 365,
                },
                {
                    "name": "酷儿果汁 200ml*12瓶",
                    "caption": "儿童喜爱｜营养健康｜整箱装",
                    "price": 38.00,
                    "cost_price": 22.00,
                    "market_price": 48.00,
                    "stock": 1800,
                    "specs": {"规格": "200ml*12瓶", "口味": "橙汁"},
                    "barcode": "6901234568103",
                    "shelf_life": 365,
                },
            ]
        },
        
        # ==================== 更多酒水类商品 - 啤酒 ====================
        
        # 燕京啤酒
        {
            "brand": "燕京",
            "category1": "酒水",
            "category2": "啤酒",
            "category3": "拉格",
            "spu_name": "燕京啤酒",
            "desc_detail": "燕京啤酒，清爽口感，麦香浓郁，经典啤酒",
            "desc_pack": "包装清单：燕京啤酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "燕京啤酒 500ml",
                    "caption": "清爽口感｜麦香浓郁｜经典啤酒",
                    "price": 4.50,
                    "cost_price": 2.80,
                    "market_price": 6.00,
                    "stock": 2000,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568104",
                    "shelf_life": 365,
                },
                {
                    "name": "燕京啤酒 500ml*12罐",
                    "caption": "清爽口感｜麦香浓郁｜整箱装",
                    "price": 52.00,
                    "cost_price": 32.00,
                    "market_price": 65.00,
                    "stock": 1500,
                    "specs": {"规格": "500ml*12罐"},
                    "barcode": "6901234568105",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 百威啤酒
        {
            "brand": "百威",
            "category1": "酒水",
            "category2": "啤酒",
            "category3": "拉格",
            "spu_name": "百威啤酒",
            "desc_detail": "百威啤酒，醇厚口感，麦香浓郁，国际品牌",
            "desc_pack": "包装清单：百威啤酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "百威啤酒 500ml",
                    "caption": "醇厚口感｜麦香浓郁｜国际品牌",
                    "price": 8.50,
                    "cost_price": 5.50,
                    "market_price": 11.00,
                    "stock": 1800,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568106",
                    "shelf_life": 365,
                },
                {
                    "name": "百威啤酒 500ml*12罐",
                    "caption": "醇厚口感｜麦香浓郁｜整箱装",
                    "price": 98.00,
                    "cost_price": 62.00,
                    "market_price": 125.00,
                    "stock": 1300,
                    "specs": {"规格": "500ml*12罐"},
                    "barcode": "6901234568107",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 喜力啤酒
        {
            "brand": "喜力",
            "category1": "酒水",
            "category2": "啤酒",
            "category3": "拉格",
            "spu_name": "喜力啤酒",
            "desc_detail": "喜力啤酒，清爽口感，麦香浓郁，荷兰品牌",
            "desc_pack": "包装清单：喜力啤酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "喜力啤酒 330ml",
                    "caption": "清爽口感｜麦香浓郁｜荷兰品牌",
                    "price": 9.50,
                    "cost_price": 6.00,
                    "market_price": 12.00,
                    "stock": 1600,
                    "specs": {"规格": "330ml"},
                    "barcode": "6901234568108",
                    "shelf_life": 365,
                },
                {
                    "name": "喜力啤酒 330ml*24罐",
                    "caption": "清爽口感｜麦香浓郁｜整箱装",
                    "price": 220.00,
                    "cost_price": 140.00,
                    "market_price": 280.00,
                    "stock": 1000,
                    "specs": {"规格": "330ml*24罐"},
                    "barcode": "6901234568109",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 科罗娜啤酒
        {
            "brand": "科罗娜",
            "category1": "酒水",
            "category2": "啤酒",
            "category3": "拉格",
            "spu_name": "科罗娜啤酒",
            "desc_detail": "科罗娜啤酒，清爽口感，配青柠，墨西哥品牌",
            "desc_pack": "包装清单：科罗娜啤酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "科罗娜啤酒 330ml",
                    "caption": "清爽口感｜配青柠｜墨西哥品牌",
                    "price": 12.00,
                    "cost_price": 7.50,
                    "market_price": 15.00,
                    "stock": 1400,
                    "specs": {"规格": "330ml"},
                    "barcode": "6901234568110",
                    "shelf_life": 365,
                },
                {
                    "name": "科罗娜啤酒 330ml*24罐",
                    "caption": "清爽口感｜配青柠｜整箱装",
                    "price": 280.00,
                    "cost_price": 175.00,
                    "market_price": 350.00,
                    "stock": 900,
                    "specs": {"规格": "330ml*24罐"},
                    "barcode": "6901234568111",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 福佳白啤酒
        {
            "brand": "福佳白",
            "category1": "酒水",
            "category2": "啤酒",
            "category3": "小麦啤酒",
            "spu_name": "福佳白啤酒",
            "desc_detail": "福佳白啤酒，小麦酿造，口感清爽，比利时品牌",
            "desc_pack": "包装清单：福佳白啤酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "福佳白啤酒 330ml",
                    "caption": "小麦酿造｜口感清爽｜比利时品牌",
                    "price": 11.00,
                    "cost_price": 7.00,
                    "market_price": 14.00,
                    "stock": 1500,
                    "specs": {"规格": "330ml"},
                    "barcode": "6901234568112",
                    "shelf_life": 365,
                },
                {
                    "name": "福佳白啤酒 330ml*24罐",
                    "caption": "小麦酿造｜口感清爽｜整箱装",
                    "price": 250.00,
                    "cost_price": 160.00,
                    "market_price": 320.00,
                    "stock": 950,
                    "specs": {"规格": "330ml*24罐"},
                    "barcode": "6901234568113",
                    "shelf_life": 365,
                },
            ]
        },
        
        # ==================== 更多酒水类商品 - 红酒 ====================
        
        # 奔富红酒
        {
            "brand": "奔富",
            "category1": "酒水",
            "category2": "红酒",
            "category3": "干红",
            "spu_name": "奔富干红葡萄酒",
            "desc_detail": "奔富干红葡萄酒，澳洲名酒，果香浓郁，口感醇厚",
            "desc_pack": "包装清单：奔富干红葡萄酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "奔富干红葡萄酒 750ml",
                    "caption": "澳洲名酒｜果香浓郁｜口感醇厚",
                    "price": 188.00,
                    "cost_price": 120.00,
                    "market_price": 235.00,
                    "stock": 300,
                    "specs": {"规格": "750ml"},
                    "barcode": "6901234568114",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 拉菲红酒
        {
            "brand": "拉菲",
            "category1": "酒水",
            "category2": "红酒",
            "category3": "干红",
            "spu_name": "拉菲干红葡萄酒",
            "desc_detail": "拉菲干红葡萄酒，法国名酒，果香浓郁，口感醇厚",
            "desc_pack": "包装清单：拉菲干红葡萄酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "拉菲干红葡萄酒 750ml",
                    "caption": "法国名酒｜果香浓郁｜口感醇厚",
                    "price": 388.00,
                    "cost_price": 250.00,
                    "market_price": 488.00,
                    "stock": 200,
                    "specs": {"规格": "750ml"},
                    "barcode": "6901234568115",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 黄尾袋鼠红酒
        {
            "brand": "黄尾袋鼠",
            "category1": "酒水",
            "category2": "红酒",
            "category3": "干红",
            "spu_name": "黄尾袋鼠干红葡萄酒",
            "desc_detail": "黄尾袋鼠干红葡萄酒，澳洲品牌，果香浓郁，口感醇厚",
            "desc_pack": "包装清单：黄尾袋鼠干红葡萄酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "黄尾袋鼠干红葡萄酒 750ml",
                    "caption": "澳洲品牌｜果香浓郁｜口感醇厚",
                    "price": 68.00,
                    "cost_price": 45.00,
                    "market_price": 85.00,
                    "stock": 400,
                    "specs": {"规格": "750ml", "口味": "梅洛"},
                    "barcode": "6901234568116",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 蒙特斯红酒
        {
            "brand": "蒙特斯",
            "category1": "酒水",
            "category2": "红酒",
            "category3": "干红",
            "spu_name": "蒙特斯干红葡萄酒",
            "desc_detail": "蒙特斯干红葡萄酒，智利品牌，果香浓郁，口感醇厚",
            "desc_pack": "包装清单：蒙特斯干红葡萄酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "蒙特斯干红葡萄酒 750ml",
                    "caption": "智利品牌｜果香浓郁｜口感醇厚",
                    "price": 78.00,
                    "cost_price": 50.00,
                    "market_price": 98.00,
                    "stock": 350,
                    "specs": {"规格": "750ml"},
                    "barcode": "6901234568117",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # ==================== 更多日化类商品 - 洗衣用品 ====================
        
        # 立白洗衣液
        {
            "brand": "立白",
            "category1": "日化",
            "category2": "清洁用品",
            "category3": "洗衣液",
            "spu_name": "立白洗衣液",
            "desc_detail": "立白洗衣液，深层洁净，温和护衣，家庭必备",
            "desc_pack": "包装清单：立白洗衣液",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "立白洗衣液 2kg",
                    "caption": "深层洁净｜温和护衣｜家庭必备",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 36.90,
                    "stock": 1600,
                    "specs": {"规格": "2kg"},
                    "barcode": "6901234568118",
                    "shelf_life": 1825,
                },
                {
                    "name": "立白洗衣液 3kg",
                    "caption": "深层洁净｜温和护衣｜家庭装",
                    "price": 42.90,
                    "cost_price": 27.00,
                    "market_price": 54.90,
                    "stock": 1400,
                    "specs": {"规格": "3kg"},
                    "barcode": "6901234568119",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 蓝月亮洗衣液
        {
            "brand": "蓝月亮",
            "category1": "日化",
            "category2": "清洁用品",
            "category3": "洗衣液",
            "spu_name": "蓝月亮洗衣液",
            "desc_detail": "蓝月亮洗衣液，深层洁净，温和护衣，专业护理",
            "desc_pack": "包装清单：蓝月亮洗衣液",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "蓝月亮洗衣液 1kg",
                    "caption": "深层洁净｜温和护衣｜专业护理",
                    "price": 25.90,
                    "cost_price": 16.00,
                    "market_price": 32.90,
                    "stock": 1700,
                    "specs": {"规格": "1kg"},
                    "barcode": "6901234568120",
                    "shelf_life": 1825,
                },
                {
                    "name": "蓝月亮洗衣液 3kg",
                    "caption": "深层洁净｜温和护衣｜家庭装",
                    "price": 68.90,
                    "cost_price": 42.00,
                    "market_price": 85.90,
                    "stock": 1300,
                    "specs": {"规格": "3kg"},
                    "barcode": "6901234568121",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 汰渍洗衣液
        {
            "brand": "汰渍",
            "category1": "日化",
            "category2": "清洁用品",
            "category3": "洗衣液",
            "spu_name": "汰渍洗衣液",
            "desc_detail": "汰渍洗衣液，强力去污，洁净护色，国际品牌",
            "desc_pack": "包装清单：汰渍洗衣液",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "汰渍洗衣液 2kg",
                    "caption": "强力去污｜洁净护色｜国际品牌",
                    "price": 32.90,
                    "cost_price": 20.00,
                    "market_price": 42.90,
                    "stock": 1500,
                    "specs": {"规格": "2kg"},
                    "barcode": "6901234568122",
                    "shelf_life": 1825,
                },
                {
                    "name": "汰渍洗衣液 3kg",
                    "caption": "强力去污｜洁净护色｜家庭装",
                    "price": 48.90,
                    "cost_price": 30.00,
                    "market_price": 62.90,
                    "stock": 1300,
                    "specs": {"规格": "3kg"},
                    "barcode": "6901234568123",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 奥妙洗衣液
        {
            "brand": "奥妙",
            "category1": "日化",
            "category2": "清洁用品",
            "category3": "洗衣液",
            "spu_name": "奥妙洗衣液",
            "desc_detail": "奥妙洗衣液，深层洁净，温和护衣，国际品牌",
            "desc_pack": "包装清单：奥妙洗衣液",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "奥妙洗衣液 2kg",
                    "caption": "深层洁净｜温和护衣｜国际品牌",
                    "price": 29.90,
                    "cost_price": 18.00,
                    "market_price": 38.90,
                    "stock": 1550,
                    "specs": {"规格": "2kg"},
                    "barcode": "6901234568124",
                    "shelf_life": 1825,
                },
                {
                    "name": "奥妙洗衣液 3kg",
                    "caption": "深层洁净｜温和护衣｜家庭装",
                    "price": 45.90,
                    "cost_price": 28.00,
                    "market_price": 58.90,
                    "stock": 1350,
                    "specs": {"规格": "3kg"},
                    "barcode": "6901234568125",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 超能洗衣液
        {
            "brand": "超能",
            "category1": "日化",
            "category2": "清洁用品",
            "category3": "洗衣液",
            "spu_name": "超能洗衣液",
            "desc_detail": "超能洗衣液，天然椰油，温和护衣，环保配方",
            "desc_pack": "包装清单：超能洗衣液",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "超能洗衣液 2kg",
                    "caption": "天然椰油｜温和护衣｜环保配方",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 45.90,
                    "stock": 1450,
                    "specs": {"规格": "2kg"},
                    "barcode": "6901234568126",
                    "shelf_life": 1825,
                },
                {
                    "name": "超能洗衣液 3kg",
                    "caption": "天然椰油｜温和护衣｜家庭装",
                    "price": 52.90,
                    "cost_price": 32.00,
                    "market_price": 68.90,
                    "stock": 1250,
                    "specs": {"规格": "3kg"},
                    "barcode": "6901234568127",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多日化类商品 - 纸品 ====================
        
        # 维达纸巾
        {
            "brand": "维达",
            "category1": "日化",
            "category2": "纸品",
            "category3": "面巾纸",
            "spu_name": "维达面巾纸",
            "desc_detail": "维达面巾纸，柔韧舒适，吸水性强，品质保证",
            "desc_pack": "包装清单：维达面巾纸",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "维达面巾纸 3层*130抽*6包",
                    "caption": "柔韧舒适｜吸水性强｜品质保证",
                    "price": 18.90,
                    "cost_price": 12.00,
                    "market_price": 24.90,
                    "stock": 2000,
                    "specs": {"规格": "3层*130抽*6包"},
                    "barcode": "6901234568128",
                    "shelf_life": 1825,
                },
                {
                    "name": "维达面巾纸 3层*130抽*12包",
                    "caption": "柔韧舒适｜吸水性强｜家庭装",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 45.90,
                    "stock": 1800,
                    "specs": {"规格": "3层*130抽*12包"},
                    "barcode": "6901234568129",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 清风纸巾
        {
            "brand": "清风",
            "category1": "日化",
            "category2": "纸品",
            "category3": "面巾纸",
            "spu_name": "清风面巾纸",
            "desc_detail": "清风面巾纸，柔韧舒适，吸水性强，品质保证",
            "desc_pack": "包装清单：清风面巾纸",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "清风面巾纸 3层*130抽*6包",
                    "caption": "柔韧舒适｜吸水性强｜品质保证",
                    "price": 16.90,
                    "cost_price": 10.50,
                    "market_price": 22.90,
                    "stock": 2100,
                    "specs": {"规格": "3层*130抽*6包"},
                    "barcode": "6901234568130",
                    "shelf_life": 1825,
                },
                {
                    "name": "清风面巾纸 3层*130抽*12包",
                    "caption": "柔韧舒适｜吸水性强｜家庭装",
                    "price": 32.90,
                    "cost_price": 20.00,
                    "market_price": 42.90,
                    "stock": 1900,
                    "specs": {"规格": "3层*130抽*12包"},
                    "barcode": "6901234568131",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 心相印纸巾
        {
            "brand": "心相印",
            "category1": "日化",
            "category2": "纸品",
            "category3": "面巾纸",
            "spu_name": "心相印面巾纸",
            "desc_detail": "心相印面巾纸，柔韧舒适，吸水性强，品质保证",
            "desc_pack": "包装清单：心相印面巾纸",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "心相印面巾纸 3层*130抽*6包",
                    "caption": "柔韧舒适｜吸水性强｜品质保证",
                    "price": 17.90,
                    "cost_price": 11.00,
                    "market_price": 23.90,
                    "stock": 2050,
                    "specs": {"规格": "3层*130抽*6包"},
                    "barcode": "6901234568132",
                    "shelf_life": 1825,
                },
                {
                    "name": "心相印面巾纸 3层*130抽*12包",
                    "caption": "柔韧舒适｜吸水性强｜家庭装",
                    "price": 34.90,
                    "cost_price": 21.00,
                    "market_price": 44.90,
                    "stock": 1850,
                    "specs": {"规格": "3层*130抽*12包"},
                    "barcode": "6901234568133",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 洁柔纸巾
        {
            "brand": "洁柔",
            "category1": "日化",
            "category2": "纸品",
            "category3": "面巾纸",
            "spu_name": "洁柔面巾纸",
            "desc_detail": "洁柔面巾纸，柔韧舒适，吸水性强，品质保证",
            "desc_pack": "包装清单：洁柔面巾纸",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "洁柔面巾纸 3层*130抽*6包",
                    "caption": "柔韧舒适｜吸水性强｜品质保证",
                    "price": 18.90,
                    "cost_price": 11.50,
                    "market_price": 24.90,
                    "stock": 1950,
                    "specs": {"规格": "3层*130抽*6包"},
                    "barcode": "6901234568134",
                    "shelf_life": 1825,
                },
                {
                    "name": "洁柔面巾纸 3层*130抽*12包",
                    "caption": "柔韧舒适｜吸水性强｜家庭装",
                    "price": 36.90,
                    "cost_price": 22.00,
                    "market_price": 46.90,
                    "stock": 1750,
                    "specs": {"规格": "3层*130抽*12包"},
                    "barcode": "6901234568135",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 得宝纸巾
        {
            "brand": "得宝",
            "category1": "日化",
            "category2": "纸品",
            "category3": "面巾纸",
            "spu_name": "得宝面巾纸",
            "desc_detail": "得宝面巾纸，柔韧舒适，吸水性强，品质保证",
            "desc_pack": "包装清单：得宝面巾纸",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "得宝面巾纸 4层*90抽*6包",
                    "caption": "柔韧舒适｜吸水性强｜品质保证",
                    "price": 25.90,
                    "cost_price": 16.00,
                    "market_price": 32.90,
                    "stock": 1800,
                    "specs": {"规格": "4层*90抽*6包"},
                    "barcode": "6901234568136",
                    "shelf_life": 1825,
                },
                {
                    "name": "得宝面巾纸 4层*90抽*12包",
                    "caption": "柔韧舒适｜吸水性强｜家庭装",
                    "price": 48.90,
                    "cost_price": 30.00,
                    "market_price": 62.90,
                    "stock": 1600,
                    "specs": {"规格": "4层*90抽*12包"},
                    "barcode": "6901234568137",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多食品类商品 - 乳制品 ====================
        
        # 蒙牛纯牛奶
        {
            "brand": "蒙牛",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "牛奶",
            "spu_name": "蒙牛纯牛奶",
            "desc_detail": "蒙牛纯牛奶，营养丰富，口感香醇，健康饮品",
            "desc_pack": "包装清单：蒙牛纯牛奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "蒙牛纯牛奶 250ml*24盒",
                    "caption": "营养丰富｜口感香醇｜健康饮品",
                    "price": 58.90,
                    "cost_price": 38.00,
                    "market_price": 73.90,
                    "stock": 1500,
                    "specs": {"规格": "250ml*24盒"},
                    "barcode": "6901234568138",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 伊利纯牛奶
        {
            "brand": "伊利",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "牛奶",
            "spu_name": "伊利纯牛奶",
            "desc_detail": "伊利纯牛奶，营养丰富，口感香醇，健康饮品",
            "desc_pack": "包装清单：伊利纯牛奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "伊利纯牛奶 250ml*24盒",
                    "caption": "营养丰富｜口感香醇｜健康饮品",
                    "price": 58.90,
                    "cost_price": 38.00,
                    "market_price": 73.90,
                    "stock": 1500,
                    "specs": {"规格": "250ml*24盒"},
                    "barcode": "6901234568139",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 光明纯牛奶
        {
            "brand": "光明",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "牛奶",
            "spu_name": "光明纯牛奶",
            "desc_detail": "光明纯牛奶，营养丰富，口感香醇，健康饮品",
            "desc_pack": "包装清单：光明纯牛奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "光明纯牛奶 250ml*24盒",
                    "caption": "营养丰富｜口感香醇｜健康饮品",
                    "price": 58.90,
                    "cost_price": 38.00,
                    "market_price": 73.90,
                    "stock": 1500,
                    "specs": {"规格": "250ml*24盒"},
                    "barcode": "6901234568140",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 三元纯牛奶
        {
            "brand": "三元",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "牛奶",
            "spu_name": "三元纯牛奶",
            "desc_detail": "三元纯牛奶，营养丰富，口感香醇，健康饮品",
            "desc_pack": "包装清单：三元纯牛奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "三元纯牛奶 250ml*24盒",
                    "caption": "营养丰富｜口感香醇｜健康饮品",
                    "price": 58.90,
                    "cost_price": 38.00,
                    "market_price": 73.90,
                    "stock": 1500,
                    "specs": {"规格": "250ml*24盒"},
                    "barcode": "6901234568141",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 君乐宝纯牛奶
        {
            "brand": "君乐宝",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "牛奶",
            "spu_name": "君乐宝纯牛奶",
            "desc_detail": "君乐宝纯牛奶，营养丰富，口感香醇，健康饮品",
            "desc_pack": "包装清单：君乐宝纯牛奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "君乐宝纯牛奶 250ml*24盒",
                    "caption": "营养丰富｜口感香醇｜健康饮品",
                    "price": 58.90,
                    "cost_price": 38.00,
                    "market_price": 73.90,
                    "stock": 1500,
                    "specs": {"规格": "250ml*24盒"},
                    "barcode": "6901234568142",
                    "shelf_life": 180,
                },
            ]
        },
        
        # ==================== 更多食品类商品 - 酸奶 ====================
        
        # 蒙牛酸奶
        {
            "brand": "蒙牛",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "酸奶",
            "spu_name": "蒙牛酸奶",
            "desc_detail": "蒙牛酸奶，酸甜可口，营养丰富，健康饮品",
            "desc_pack": "包装清单：蒙牛酸奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "蒙牛酸奶 200g*12杯",
                    "caption": "酸甜可口｜营养丰富｜健康饮品",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 45.90,
                    "stock": 1400,
                    "specs": {"规格": "200g*12杯", "口味": "原味"},
                    "barcode": "6901234568143",
                    "shelf_life": 21,
                },
            ]
        },
        
        # 伊利酸奶
        {
            "brand": "伊利",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "酸奶",
            "spu_name": "伊利酸奶",
            "desc_detail": "伊利酸奶，酸甜可口，营养丰富，健康饮品",
            "desc_pack": "包装清单：伊利酸奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "伊利酸奶 200g*12杯",
                    "caption": "酸甜可口｜营养丰富｜健康饮品",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 45.90,
                    "stock": 1400,
                    "specs": {"规格": "200g*12杯", "口味": "原味"},
                    "barcode": "6901234568144",
                    "shelf_life": 21,
                },
            ]
        },
        
        # 光明酸奶
        {
            "brand": "光明",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "酸奶",
            "spu_name": "光明酸奶",
            "desc_detail": "光明酸奶，酸甜可口，营养丰富，健康饮品",
            "desc_pack": "包装清单：光明酸奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "光明酸奶 200g*12杯",
                    "caption": "酸甜可口｜营养丰富｜健康饮品",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 45.90,
                    "stock": 1400,
                    "specs": {"规格": "200g*12杯", "口味": "原味"},
                    "barcode": "6901234568145",
                    "shelf_life": 21,
                },
            ]
        },
        
        # 君乐宝酸奶
        {
            "brand": "君乐宝",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "酸奶",
            "spu_name": "君乐宝酸奶",
            "desc_detail": "君乐宝酸奶，酸甜可口，营养丰富，健康饮品",
            "desc_pack": "包装清单：君乐宝酸奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "君乐宝酸奶 200g*12杯",
                    "caption": "酸甜可口｜营养丰富｜健康饮品",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 45.90,
                    "stock": 1400,
                    "specs": {"规格": "200g*12杯", "口味": "原味"},
                    "barcode": "6901234568146",
                    "shelf_life": 21,
                },
            ]
        },
        
        # ==================== 更多食品类商品 - 坚果 ====================
        
        # 三只松鼠碧根果
        {
            "brand": "三只松鼠",
            "category1": "食品",
            "category2": "零食",
            "category3": "坚果",
            "spu_name": "三只松鼠碧根果",
            "desc_detail": "三只松鼠碧根果，香脆可口，营养丰富，休闲零食",
            "desc_pack": "包装清单：三只松鼠碧根果",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "三只松鼠碧根果 210g",
                    "caption": "香脆可口｜营养丰富｜休闲零食",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 36.90,
                    "stock": 1200,
                    "specs": {"规格": "210g"},
                    "barcode": "6901234568147",
                    "shelf_life": 180,
                },
                {
                    "name": "三只松鼠碧根果 500g",
                    "caption": "香脆可口｜营养丰富｜家庭装",
                    "price": 58.90,
                    "cost_price": 38.00,
                    "market_price": 73.90,
                    "stock": 1000,
                    "specs": {"规格": "500g"},
                    "barcode": "6901234568148",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 百草味腰果
        {
            "brand": "百草味",
            "category1": "食品",
            "category2": "零食",
            "category3": "坚果",
            "spu_name": "百草味腰果",
            "desc_detail": "百草味腰果，香脆可口，营养丰富，休闲零食",
            "desc_pack": "包装清单：百草味腰果",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "百草味腰果 200g",
                    "caption": "香脆可口｜营养丰富｜休闲零食",
                    "price": 25.90,
                    "cost_price": 16.00,
                    "market_price": 32.90,
                    "stock": 1300,
                    "specs": {"规格": "200g"},
                    "barcode": "6901234568149",
                    "shelf_life": 180,
                },
                {
                    "name": "百草味腰果 500g",
                    "caption": "香脆可口｜营养丰富｜家庭装",
                    "price": 58.90,
                    "cost_price": 38.00,
                    "market_price": 73.90,
                    "stock": 1100,
                    "specs": {"规格": "500g"},
                    "barcode": "6901234568150",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 良品铺子开心果
        {
            "brand": "良品铺子",
            "category1": "食品",
            "category2": "零食",
            "category3": "坚果",
            "spu_name": "良品铺子开心果",
            "desc_detail": "良品铺子开心果，香脆可口，营养丰富，休闲零食",
            "desc_pack": "包装清单：良品铺子开心果",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "良品铺子开心果 200g",
                    "caption": "香脆可口｜营养丰富｜休闲零食",
                    "price": 32.90,
                    "cost_price": 21.00,
                    "market_price": 42.90,
                    "stock": 1100,
                    "specs": {"规格": "200g"},
                    "barcode": "6901234568151",
                    "shelf_life": 180,
                },
                {
                    "name": "良品铺子开心果 500g",
                    "caption": "香脆可口｜营养丰富｜家庭装",
                    "price": 78.90,
                    "cost_price": 50.00,
                    "market_price": 98.90,
                    "stock": 900,
                    "specs": {"规格": "500g"},
                    "barcode": "6901234568152",
                    "shelf_life": 180,
                },
            ]
        },
        
        # ==================== 更多日化类商品 - 洗洁精 ====================
        
        # 立白洗洁精
        {
            "brand": "立白",
            "category1": "日化",
            "category2": "清洁用品",
            "category3": "洗洁精",
            "spu_name": "立白洗洁精",
            "desc_detail": "立白洗洁精，强力去油，温和护手，厨房必备",
            "desc_pack": "包装清单：立白洗洁精",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "立白洗洁精 1kg",
                    "caption": "强力去油｜温和护手｜厨房必备",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 2000,
                    "specs": {"规格": "1kg"},
                    "barcode": "6901234568153",
                    "shelf_life": 1825,
                },
                {
                    "name": "立白洗洁精 2kg",
                    "caption": "强力去油｜温和护手｜家庭装",
                    "price": 22.90,
                    "cost_price": 14.00,
                    "market_price": 28.90,
                    "stock": 1800,
                    "specs": {"规格": "2kg"},
                    "barcode": "6901234568154",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 雕牌洗洁精
        {
            "brand": "雕牌",
            "category1": "日化",
            "category2": "清洁用品",
            "category3": "洗洁精",
            "spu_name": "雕牌洗洁精",
            "desc_detail": "雕牌洗洁精，强力去油，温和护手，厨房必备",
            "desc_pack": "包装清单：雕牌洗洁精",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "雕牌洗洁精 1kg",
                    "caption": "强力去油｜温和护手｜厨房必备",
                    "price": 10.90,
                    "cost_price": 6.50,
                    "market_price": 14.90,
                    "stock": 2100,
                    "specs": {"规格": "1kg"},
                    "barcode": "6901234568155",
                    "shelf_life": 1825,
                },
                {
                    "name": "雕牌洗洁精 2kg",
                    "caption": "强力去油｜温和护手｜家庭装",
                    "price": 19.90,
                    "cost_price": 12.00,
                    "market_price": 25.90,
                    "stock": 1900,
                    "specs": {"规格": "2kg"},
                    "barcode": "6901234568156",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 威猛先生洗洁精
        {
            "brand": "威猛先生",
            "category1": "日化",
            "category2": "清洁用品",
            "category3": "洗洁精",
            "spu_name": "威猛先生洗洁精",
            "desc_detail": "威猛先生洗洁精，强力去油，温和护手，国际品牌",
            "desc_pack": "包装清单：威猛先生洗洁精",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "威猛先生洗洁精 1kg",
                    "caption": "强力去油｜温和护手｜国际品牌",
                    "price": 15.90,
                    "cost_price": 10.00,
                    "market_price": 20.90,
                    "stock": 1900,
                    "specs": {"规格": "1kg"},
                    "barcode": "6901234568157",
                    "shelf_life": 1825,
                },
                {
                    "name": "威猛先生洗洁精 2kg",
                    "caption": "强力去油｜温和护手｜家庭装",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 36.90,
                    "stock": 1700,
                    "specs": {"规格": "2kg"},
                    "barcode": "6901234568158",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 白猫洗洁精
        {
            "brand": "白猫",
            "category1": "日化",
            "category2": "清洁用品",
            "category3": "洗洁精",
            "spu_name": "白猫洗洁精",
            "desc_detail": "白猫洗洁精，强力去油，温和护手，经典品牌",
            "desc_pack": "包装清单：白猫洗洁精",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "白猫洗洁精 1kg",
                    "caption": "强力去油｜温和护手｜经典品牌",
                    "price": 11.90,
                    "cost_price": 7.00,
                    "market_price": 15.90,
                    "stock": 2000,
                    "specs": {"规格": "1kg"},
                    "barcode": "6901234568159",
                    "shelf_life": 1825,
                },
                {
                    "name": "白猫洗洁精 2kg",
                    "caption": "强力去油｜温和护手｜家庭装",
                    "price": 21.90,
                    "cost_price": 13.00,
                    "market_price": 28.90,
                    "stock": 1800,
                    "specs": {"规格": "2kg"},
                    "barcode": "6901234568160",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多酒水类商品 - 白酒 ====================
        
        # 古井贡酒
        {
            "brand": "古井贡",
            "category1": "酒水",
            "category2": "白酒",
            "category3": "浓香型",
            "spu_name": "古井贡酒",
            "desc_detail": "古井贡酒，浓香型白酒，口感醇厚，回味悠长",
            "desc_pack": "包装清单：古井贡酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "古井贡酒 50度 500ml",
                    "caption": "浓香型白酒｜口感醇厚｜回味悠长",
                    "price": 288.00,
                    "cost_price": 200.00,
                    "market_price": 358.00,
                    "stock": 250,
                    "specs": {"规格": "500ml", "度数": "50度"},
                    "barcode": "6901234568161",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 水井坊
        {
            "brand": "水井坊",
            "category1": "酒水",
            "category2": "白酒",
            "category3": "浓香型",
            "spu_name": "水井坊",
            "desc_detail": "水井坊，浓香型白酒，口感醇厚，历史悠久",
            "desc_pack": "包装清单：水井坊",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "水井坊 52度 500ml",
                    "caption": "浓香型白酒｜口感醇厚｜历史悠久",
                    "price": 588.00,
                    "cost_price": 400.00,
                    "market_price": 728.00,
                    "stock": 180,
                    "specs": {"规格": "500ml", "度数": "52度"},
                    "barcode": "6901234568162",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 舍得酒
        {
            "brand": "舍得",
            "category1": "酒水",
            "category2": "白酒",
            "category3": "浓香型",
            "spu_name": "舍得酒",
            "desc_detail": "舍得酒，浓香型白酒，口感醇厚，智慧人生",
            "desc_pack": "包装清单：舍得酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "舍得酒 52度 500ml",
                    "caption": "浓香型白酒｜口感醇厚｜智慧人生",
                    "price": 488.00,
                    "cost_price": 330.00,
                    "market_price": 608.00,
                    "stock": 200,
                    "specs": {"规格": "500ml", "度数": "52度"},
                    "barcode": "6901234568163",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 酒鬼酒
        {
            "brand": "酒鬼",
            "category1": "酒水",
            "category2": "白酒",
            "category3": "馥郁香型",
            "spu_name": "酒鬼酒",
            "desc_detail": "酒鬼酒，馥郁香型白酒，口感独特，湘西名酒",
            "desc_pack": "包装清单：酒鬼酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "酒鬼酒 52度 500ml",
                    "caption": "馥郁香型白酒｜口感独特｜湘西名酒",
                    "price": 388.00,
                    "cost_price": 260.00,
                    "market_price": 488.00,
                    "stock": 220,
                    "specs": {"规格": "500ml", "度数": "52度"},
                    "barcode": "6901234568164",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # ==================== 更多食品类商品 - 饼干糕点 ====================
        
        # 奥利奥饼干
        {
            "brand": "奥利奥",
            "category1": "食品",
            "category2": "零食",
            "category3": "饼干",
            "spu_name": "奥利奥饼干",
            "desc_detail": "奥利奥饼干，经典夹心，酥脆可口，休闲零食",
            "desc_pack": "包装清单：奥利奥饼干",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "奥利奥原味饼干 133g",
                    "caption": "经典夹心｜酥脆可口｜休闲零食",
                    "price": 9.90,
                    "cost_price": 6.00,
                    "market_price": 12.90,
                    "stock": 2000,
                    "specs": {"规格": "133g", "口味": "原味"},
                    "barcode": "6901234568165",
                    "shelf_life": 365,
                },
                {
                    "name": "奥利奥原味饼干 454g",
                    "caption": "经典夹心｜酥脆可口｜家庭装",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 36.90,
                    "stock": 1500,
                    "specs": {"规格": "454g", "口味": "原味"},
                    "barcode": "6901234568166",
                    "shelf_life": 365,
                },
                {
                    "name": "奥利奥草莓味饼干 133g",
                    "caption": "草莓夹心｜酥脆可口｜休闲零食",
                    "price": 10.90,
                    "cost_price": 6.50,
                    "market_price": 13.90,
                    "stock": 1800,
                    "specs": {"规格": "133g", "口味": "草莓味"},
                    "barcode": "6901234568167",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 乐事薯片
        {
            "brand": "乐事",
            "category1": "食品",
            "category2": "零食",
            "category3": "薯片",
            "spu_name": "乐事薯片",
            "desc_detail": "乐事薯片，薄脆香浓，多种口味，休闲零食",
            "desc_pack": "包装清单：乐事薯片",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "乐事原味薯片 70g",
                    "caption": "薄脆香浓｜经典原味｜休闲零食",
                    "price": 8.90,
                    "cost_price": 5.50,
                    "market_price": 11.90,
                    "stock": 2200,
                    "specs": {"规格": "70g", "口味": "原味"},
                    "barcode": "6901234568168",
                    "shelf_life": 365,
                },
                {
                    "name": "乐事原味薯片 145g",
                    "caption": "薄脆香浓｜经典原味｜家庭装",
                    "price": 17.90,
                    "cost_price": 11.00,
                    "market_price": 22.90,
                    "stock": 1700,
                    "specs": {"规格": "145g", "口味": "原味"},
                    "barcode": "6901234568169",
                    "shelf_life": 365,
                },
                {
                    "name": "乐事番茄味薯片 70g",
                    "caption": "薄脆香浓｜番茄味｜休闲零食",
                    "price": 8.90,
                    "cost_price": 5.50,
                    "market_price": 11.90,
                    "stock": 2100,
                    "specs": {"规格": "70g", "口味": "番茄味"},
                    "barcode": "6901234568170",
                    "shelf_life": 365,
                },
                {
                    "name": "乐事烧烤味薯片 70g",
                    "caption": "薄脆香浓｜烧烤味｜休闲零食",
                    "price": 8.90,
                    "cost_price": 5.50,
                    "market_price": 11.90,
                    "stock": 2000,
                    "specs": {"规格": "70g", "口味": "烧烤味"},
                    "barcode": "6901234568171",
                    "shelf_life": 365,
                },
                {
                    "name": "乐事黄瓜味薯片 70g",
                    "caption": "薄脆香浓｜黄瓜味｜休闲零食",
                    "price": 8.90,
                    "cost_price": 5.50,
                    "market_price": 11.90,
                    "stock": 1900,
                    "specs": {"规格": "70g", "口味": "黄瓜味"},
                    "barcode": "6901234568172",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 盼盼薯片
        {
            "brand": "盼盼",
            "category1": "食品",
            "category2": "零食",
            "category3": "薯片",
            "spu_name": "盼盼薯片",
            "desc_detail": "盼盼薯片，香脆可口，多种口味，休闲零食",
            "desc_pack": "包装清单：盼盼薯片",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "盼盼薯片 80g",
                    "caption": "香脆可口｜多种口味｜休闲零食",
                    "price": 6.90,
                    "cost_price": 4.00,
                    "market_price": 9.90,
                    "stock": 2500,
                    "specs": {"规格": "80g", "口味": "原味"},
                    "barcode": "6901234568173",
                    "shelf_life": 365,
                },
                {
                    "name": "盼盼薯片 160g",
                    "caption": "香脆可口｜多种口味｜家庭装",
                    "price": 12.90,
                    "cost_price": 7.50,
                    "market_price": 16.90,
                    "stock": 2000,
                    "specs": {"规格": "160g", "口味": "原味"},
                    "barcode": "6901234568174",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 旺旺雪饼
        {
            "brand": "旺旺",
            "category1": "食品",
            "category2": "零食",
            "category3": "饼干",
            "spu_name": "旺旺雪饼",
            "desc_detail": "旺旺雪饼，香甜酥脆，经典口味，休闲零食",
            "desc_pack": "包装清单：旺旺雪饼",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "旺旺雪饼 400g",
                    "caption": "香甜酥脆｜经典口味｜休闲零食",
                    "price": 15.90,
                    "cost_price": 10.00,
                    "market_price": 20.90,
                    "stock": 1800,
                    "specs": {"规格": "400g"},
                    "barcode": "6901234568175",
                    "shelf_life": 365,
                },
                {
                    "name": "旺旺雪饼 800g",
                    "caption": "香甜酥脆｜经典口味｜家庭装",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 36.90,
                    "stock": 1500,
                    "specs": {"规格": "800g"},
                    "barcode": "6901234568176",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 旺旺仙贝
        {
            "brand": "旺旺",
            "category1": "食品",
            "category2": "零食",
            "category3": "饼干",
            "spu_name": "旺旺仙贝",
            "desc_detail": "旺旺仙贝，咸香酥脆，经典口味，休闲零食",
            "desc_pack": "包装清单：旺旺仙贝",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "旺旺仙贝 400g",
                    "caption": "咸香酥脆｜经典口味｜休闲零食",
                    "price": 15.90,
                    "cost_price": 10.00,
                    "market_price": 20.90,
                    "stock": 1700,
                    "specs": {"规格": "400g"},
                    "barcode": "6901234568177",
                    "shelf_life": 365,
                },
                {
                    "name": "旺旺仙贝 800g",
                    "caption": "咸香酥脆｜经典口味｜家庭装",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 36.90,
                    "stock": 1400,
                    "specs": {"规格": "800g"},
                    "barcode": "6901234568178",
                    "shelf_life": 365,
                },
            ]
        },
        
        # ==================== 更多食品类商品 - 糖果 ====================
        
        # 阿尔卑斯糖果
        {
            "brand": "阿尔卑斯",
            "category1": "食品",
            "category2": "零食",
            "category3": "糖果",
            "spu_name": "阿尔卑斯糖果",
            "desc_detail": "阿尔卑斯糖果，香甜可口，多种口味，休闲零食",
            "desc_pack": "包装清单：阿尔卑斯糖果",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "阿尔卑斯硬糖 500g",
                    "caption": "香甜可口｜多种口味｜休闲零食",
                    "price": 18.90,
                    "cost_price": 12.00,
                    "market_price": 24.90,
                    "stock": 1600,
                    "specs": {"规格": "500g", "口味": "混合装"},
                    "barcode": "6901234568179",
                    "shelf_life": 730,
                },
                {
                    "name": "阿尔卑斯软糖 400g",
                    "caption": "香甜可口｜多种口味｜休闲零食",
                    "price": 22.90,
                    "cost_price": 14.00,
                    "market_price": 28.90,
                    "stock": 1400,
                    "specs": {"规格": "400g", "口味": "混合装"},
                    "barcode": "6901234568180",
                    "shelf_life": 730,
                },
            ]
        },
        
        # 德芙巧克力
        {
            "brand": "德芙",
            "category1": "食品",
            "category2": "零食",
            "category3": "巧克力",
            "spu_name": "德芙巧克力",
            "desc_detail": "德芙巧克力，丝滑口感，浓郁香甜，休闲零食",
            "desc_pack": "包装清单：德芙巧克力",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "德芙丝滑牛奶巧克力 80g",
                    "caption": "丝滑口感｜浓郁香甜｜休闲零食",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 1800,
                    "specs": {"规格": "80g", "口味": "牛奶"},
                    "barcode": "6901234568181",
                    "shelf_life": 730,
                },
                {
                    "name": "德芙丝滑牛奶巧克力 227g",
                    "caption": "丝滑口感｜浓郁香甜｜家庭装",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 45.90,
                    "stock": 1300,
                    "specs": {"规格": "227g", "口味": "牛奶"},
                    "barcode": "6901234568182",
                    "shelf_life": 730,
                },
                {
                    "name": "德芙黑巧克力 80g",
                    "caption": "丝滑口感｜浓郁香甜｜休闲零食",
                    "price": 13.90,
                    "cost_price": 8.50,
                    "market_price": 17.90,
                    "stock": 1700,
                    "specs": {"规格": "80g", "口味": "黑巧克力"},
                    "barcode": "6901234568183",
                    "shelf_life": 730,
                },
            ]
        },
        
        # 费列罗巧克力
        {
            "brand": "费列罗",
            "category1": "食品",
            "category2": "零食",
            "category3": "巧克力",
            "spu_name": "费列罗巧克力",
            "desc_detail": "费列罗巧克力，榛子夹心，丝滑口感，高端礼品",
            "desc_pack": "包装清单：费列罗巧克力",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "费列罗榛果威化巧克力 200g",
                    "caption": "榛子夹心｜丝滑口感｜高端礼品",
                    "price": 68.90,
                    "cost_price": 45.00,
                    "market_price": 88.90,
                    "stock": 800,
                    "specs": {"规格": "200g"},
                    "barcode": "6901234568184",
                    "shelf_life": 730,
                },
                {
                    "name": "费列罗榛果威化巧克力 300g",
                    "caption": "榛子夹心｜丝滑口感｜高端礼品",
                    "price": 98.90,
                    "cost_price": 65.00,
                    "market_price": 128.90,
                    "stock": 600,
                    "specs": {"规格": "300g"},
                    "barcode": "6901234568185",
                    "shelf_life": 730,
                },
            ]
        },
        
        # ==================== 更多日化类商品 - 洗发水 ====================
        
        # 飘柔洗发水
        {
            "brand": "飘柔",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "洗发水",
            "spu_name": "飘柔洗发水",
            "desc_detail": "飘柔洗发水，柔顺护发，清香怡人，日常护理",
            "desc_pack": "包装清单：飘柔洗发水",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "飘柔柔顺洗发水 200ml",
                    "caption": "柔顺护发｜清香怡人｜日常护理",
                    "price": 18.90,
                    "cost_price": 12.00,
                    "market_price": 24.90,
                    "stock": 2000,
                    "specs": {"规格": "200ml", "类型": "柔顺"},
                    "barcode": "6901234568186",
                    "shelf_life": 1825,
                },
                {
                    "name": "飘柔柔顺洗发水 400ml",
                    "caption": "柔顺护发｜清香怡人｜日常护理",
                    "price": 32.90,
                    "cost_price": 21.00,
                    "market_price": 42.90,
                    "stock": 1800,
                    "specs": {"规格": "400ml", "类型": "柔顺"},
                    "barcode": "6901234568187",
                    "shelf_life": 1825,
                },
                {
                    "name": "飘柔去屑洗发水 400ml",
                    "caption": "去屑止痒｜清香怡人｜日常护理",
                    "price": 35.90,
                    "cost_price": 23.00,
                    "market_price": 45.90,
                    "stock": 1700,
                    "specs": {"规格": "400ml", "类型": "去屑"},
                    "barcode": "6901234568188",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 潘婷洗发水
        {
            "brand": "潘婷",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "洗发水",
            "spu_name": "潘婷洗发水",
            "desc_detail": "潘婷洗发水，强韧修护，健康秀发，专业护理",
            "desc_pack": "包装清单：潘婷洗发水",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "潘婷修护洗发水 200ml",
                    "caption": "强韧修护｜健康秀发｜专业护理",
                    "price": 25.90,
                    "cost_price": 16.00,
                    "market_price": 32.90,
                    "stock": 1900,
                    "specs": {"规格": "200ml", "类型": "修护"},
                    "barcode": "6901234568189",
                    "shelf_life": 1825,
                },
                {
                    "name": "潘婷修护洗发水 400ml",
                    "caption": "强韧修护｜健康秀发｜专业护理",
                    "price": 42.90,
                    "cost_price": 27.00,
                    "market_price": 55.90,
                    "stock": 1600,
                    "specs": {"规格": "400ml", "类型": "修护"},
                    "barcode": "6901234568190",
                    "shelf_life": 1825,
                },
                {
                    "name": "潘婷丝质顺滑洗发水 400ml",
                    "caption": "丝质顺滑｜健康秀发｜专业护理",
                    "price": 45.90,
                    "cost_price": 29.00,
                    "market_price": 58.90,
                    "stock": 1500,
                    "specs": {"规格": "400ml", "类型": "丝质顺滑"},
                    "barcode": "6901234568191",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多牛奶饮料类商品 - 酸奶 ====================
        
        # 蒙牛酸奶
        {
            "brand": "蒙牛",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "酸奶",
            "spu_name": "蒙牛酸奶",
            "desc_detail": "蒙牛酸奶，酸甜可口，营养丰富，健康饮品",
            "desc_pack": "包装清单：蒙牛酸奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "蒙牛酸奶 200g*12杯",
                    "caption": "酸甜可口｜营养丰富｜健康饮品",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 45.90,
                    "stock": 1400,
                    "specs": {"规格": "200g*12杯", "口味": "原味"},
                    "barcode": "6901234568192",
                    "shelf_life": 21,
                },
                {
                    "name": "蒙牛酸奶 200g*12杯 草莓味",
                    "caption": "酸甜可口｜营养丰富｜健康饮品",
                    "price": 37.90,
                    "cost_price": 23.00,
                    "market_price": 47.90,
                    "stock": 1300,
                    "specs": {"规格": "200g*12杯", "口味": "草莓味"},
                    "barcode": "6901234568193",
                    "shelf_life": 21,
                },
                {
                    "name": "蒙牛酸奶 200g*12杯 黄桃味",
                    "caption": "酸甜可口｜营养丰富｜健康饮品",
                    "price": 37.90,
                    "cost_price": 23.00,
                    "market_price": 47.90,
                    "stock": 1200,
                    "specs": {"规格": "200g*12杯", "口味": "黄桃味"},
                    "barcode": "6901234568194",
                    "shelf_life": 21,
                },
            ]
        },
        
        # 伊利酸奶
        {
            "brand": "伊利",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "酸奶",
            "spu_name": "伊利酸奶",
            "desc_detail": "伊利酸奶，酸甜可口，营养丰富，健康饮品",
            "desc_pack": "包装清单：伊利酸奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "伊利酸奶 200g*12杯",
                    "caption": "酸甜可口｜营养丰富｜健康饮品",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 45.90,
                    "stock": 1350,
                    "specs": {"规格": "200g*12杯", "口味": "原味"},
                    "barcode": "6901234568195",
                    "shelf_life": 21,
                },
                {
                    "name": "伊利酸奶 200g*12杯 蓝莓味",
                    "caption": "酸甜可口｜营养丰富｜健康饮品",
                    "price": 37.90,
                    "cost_price": 23.00,
                    "market_price": 47.90,
                    "stock": 1250,
                    "specs": {"规格": "200g*12杯", "口味": "蓝莓味"},
                    "barcode": "6901234568196",
                    "shelf_life": 21,
                },
            ]
        },
        
        # 光明酸奶
        {
            "brand": "光明",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "酸奶",
            "spu_name": "光明酸奶",
            "desc_detail": "光明酸奶，酸甜可口，营养丰富，健康饮品",
            "desc_pack": "包装清单：光明酸奶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "光明酸奶 200g*12杯",
                    "caption": "酸甜可口｜营养丰富｜健康饮品",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 45.90,
                    "stock": 1300,
                    "specs": {"规格": "200g*12杯", "口味": "原味"},
                    "barcode": "6901234568197",
                    "shelf_life": 21,
                },
                {
                    "name": "光明酸奶 200g*12杯 芦荟味",
                    "caption": "酸甜可口｜营养丰富｜健康饮品",
                    "price": 37.90,
                    "cost_price": 23.00,
                    "market_price": 47.90,
                    "stock": 1200,
                    "specs": {"规格": "200g*12杯", "口味": "芦荟味"},
                    "barcode": "6901234568198",
                    "shelf_life": 21,
                },
            ]
        },
        
        # ==================== 更多酒水类商品 - 黄酒 ====================
        
        # 古越龙山黄酒
        {
            "brand": "古越龙山",
            "category1": "酒水",
            "category2": "黄酒",
            "category3": "绍兴黄酒",
            "spu_name": "古越龙山黄酒",
            "desc_detail": "古越龙山黄酒，传统工艺，醇香浓郁，绍兴名酒",
            "desc_pack": "包装清单：古越龙山黄酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "古越龙山黄酒 500ml",
                    "caption": "传统工艺｜醇香浓郁｜绍兴名酒",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 36.90,
                    "stock": 800,
                    "specs": {"规格": "500ml", "度数": "15度"},
                    "barcode": "6901234568199",
                    "shelf_life": 3650,
                },
                {
                    "name": "古越龙山黄酒 1L",
                    "caption": "传统工艺｜醇香浓郁｜家庭装",
                    "price": 48.90,
                    "cost_price": 30.00,
                    "market_price": 62.90,
                    "stock": 600,
                    "specs": {"规格": "1L", "度数": "15度"},
                    "barcode": "6901234568200",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 会稽山黄酒
        {
            "brand": "会稽山",
            "category1": "酒水",
            "category2": "黄酒",
            "category3": "绍兴黄酒",
            "spu_name": "会稽山黄酒",
            "desc_detail": "会稽山黄酒，传统工艺，醇香浓郁，绍兴名酒",
            "desc_pack": "包装清单：会稽山黄酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "会稽山黄酒 500ml",
                    "caption": "传统工艺｜醇香浓郁｜绍兴名酒",
                    "price": 32.90,
                    "cost_price": 20.00,
                    "market_price": 42.90,
                    "stock": 750,
                    "specs": {"规格": "500ml", "度数": "15度"},
                    "barcode": "6901234568201",
                    "shelf_life": 3650,
                },
                {
                    "name": "会稽山黄酒 1L",
                    "caption": "传统工艺｜醇香浓郁｜家庭装",
                    "price": 55.90,
                    "cost_price": 35.00,
                    "market_price": 72.90,
                    "stock": 550,
                    "specs": {"规格": "1L", "度数": "15度"},
                    "barcode": "6901234568202",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # ==================== 更多食品类商品 - 方便面 ====================
        
        # 康师傅红烧牛肉面
        {
            "brand": "康师傅",
            "category1": "食品",
            "category2": "方便食品",
            "category3": "方便面",
            "spu_name": "康师傅红烧牛肉面",
            "desc_detail": "康师傅红烧牛肉面，经典口味，方便快捷，休闲食品",
            "desc_pack": "包装清单：康师傅红烧牛肉面",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "康师傅红烧牛肉面 105g",
                    "caption": "经典口味｜方便快捷｜休闲食品",
                    "price": 3.50,
                    "cost_price": 2.00,
                    "market_price": 4.50,
                    "stock": 3000,
                    "specs": {"规格": "105g", "口味": "红烧牛肉"},
                    "barcode": "6901234568203",
                    "shelf_life": 180,
                },
                {
                    "name": "康师傅红烧牛肉面 5连包",
                    "caption": "经典口味｜方便快捷｜家庭装",
                    "price": 16.50,
                    "cost_price": 10.00,
                    "market_price": 21.50,
                    "stock": 2500,
                    "specs": {"规格": "5连包", "口味": "红烧牛肉"},
                    "barcode": "6901234568204",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 统一来一桶
        {
            "brand": "统一",
            "category1": "食品",
            "category2": "方便食品",
            "category3": "方便面",
            "spu_name": "统一来一桶",
            "desc_detail": "统一来一桶，经典口味，方便快捷，休闲食品",
            "desc_pack": "包装清单：统一来一桶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "统一来一桶红烧牛肉 108g",
                    "caption": "经典口味｜方便快捷｜休闲食品",
                    "price": 4.00,
                    "cost_price": 2.50,
                    "market_price": 5.00,
                    "stock": 2800,
                    "specs": {"规格": "108g", "口味": "红烧牛肉"},
                    "barcode": "6901234568205",
                    "shelf_life": 180,
                },
                {
                    "name": "统一来一桶老坛酸菜 108g",
                    "caption": "经典口味｜方便快捷｜休闲食品",
                    "price": 4.00,
                    "cost_price": 2.50,
                    "market_price": 5.00,
                    "stock": 2700,
                    "specs": {"规格": "108g", "口味": "老坛酸菜"},
                    "barcode": "6901234568206",
                    "shelf_life": 180,
                },
            ]
        },
        
        # ==================== 更多食品类商品 - 火腿肠 ====================
        
        # 双汇火腿肠
        {
            "brand": "双汇",
            "category1": "食品",
            "category2": "肉制品",
            "category3": "火腿肠",
            "spu_name": "双汇火腿肠",
            "desc_detail": "双汇火腿肠，肉质鲜嫩，口感丰富，方便食品",
            "desc_pack": "包装清单：双汇火腿肠",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "双汇火腿肠 50g*10根",
                    "caption": "肉质鲜嫩｜口感丰富｜方便食品",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 2000,
                    "specs": {"规格": "50g*10根", "口味": "原味"},
                    "barcode": "6901234568207",
                    "shelf_life": 180,
                },
                {
                    "name": "双汇火腿肠 70g*10根",
                    "caption": "肉质鲜嫩｜口感丰富｜家庭装",
                    "price": 18.90,
                    "cost_price": 12.00,
                    "market_price": 24.90,
                    "stock": 1800,
                    "specs": {"规格": "70g*10根", "口味": "原味"},
                    "barcode": "6901234568208",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 金锣火腿肠
        {
            "brand": "金锣",
            "category1": "食品",
            "category2": "肉制品",
            "category3": "火腿肠",
            "spu_name": "金锣火腿肠",
            "desc_detail": "金锣火腿肠，肉质鲜嫩，口感丰富，方便食品",
            "desc_pack": "包装清单：金锣火腿肠",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "金锣火腿肠 50g*10根",
                    "caption": "肉质鲜嫩｜口感丰富｜方便食品",
                    "price": 11.90,
                    "cost_price": 7.50,
                    "market_price": 15.90,
                    "stock": 1900,
                    "specs": {"规格": "50g*10根", "口味": "原味"},
                    "barcode": "6901234568209",
                    "shelf_life": 180,
                },
                {
                    "name": "金锣火腿肠 70g*10根",
                    "caption": "肉质鲜嫩｜口感丰富｜家庭装",
                    "price": 17.90,
                    "cost_price": 11.00,
                    "market_price": 23.90,
                    "stock": 1700,
                    "specs": {"规格": "70g*10根", "口味": "原味"},
                    "barcode": "6901234568210",
                    "shelf_life": 180,
                },
            ]
        },
        
        # ==================== 更多日化类商品 - 沐浴露 ====================
        
        # 六神沐浴露
        {
            "brand": "六神",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "沐浴露",
            "spu_name": "六神沐浴露",
            "desc_detail": "六神沐浴露，草本清香，清爽舒适，日常护理",
            "desc_pack": "包装清单：六神沐浴露",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "六神沐浴露 300ml",
                    "caption": "草本清香｜清爽舒适｜日常护理",
                    "price": 22.90,
                    "cost_price": 14.00,
                    "market_price": 28.90,
                    "stock": 1800,
                    "specs": {"规格": "300ml", "口味": "经典"},
                    "barcode": "6901234568211",
                    "shelf_life": 1825,
                },
                {
                    "name": "六神沐浴露 700ml",
                    "caption": "草本清香｜清爽舒适｜家庭装",
                    "price": 42.90,
                    "cost_price": 27.00,
                    "market_price": 55.90,
                    "stock": 1500,
                    "specs": {"规格": "700ml", "口味": "经典"},
                    "barcode": "6901234568212",
                    "shelf_life": 1825,
                },
                {
                    "name": "六神沐浴露 300ml 冰凉",
                    "caption": "草本清香｜清爽舒适｜日常护理",
                    "price": 24.90,
                    "cost_price": 15.00,
                    "market_price": 32.90,
                    "stock": 1700,
                    "specs": {"规格": "300ml", "口味": "冰凉"},
                    "barcode": "6901234568213",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 舒肤佳沐浴露
        {
            "brand": "舒肤佳",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "沐浴露",
            "spu_name": "舒肤佳沐浴露",
            "desc_detail": "舒肤佳沐浴露，抑菌护肤，清香怡人，日常护理",
            "desc_pack": "包装清单：舒肤佳沐浴露",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "舒肤佳沐浴露 300ml",
                    "caption": "抑菌护肤｜清香怡人｜日常护理",
                    "price": 25.90,
                    "cost_price": 16.00,
                    "market_price": 32.90,
                    "stock": 1700,
                    "specs": {"规格": "300ml", "类型": "纯白"},
                    "barcode": "6901234568214",
                    "shelf_life": 1825,
                },
                {
                    "name": "舒肤佳沐浴露 720ml",
                    "caption": "抑菌护肤｜清香怡人｜家庭装",
                    "price": 48.90,
                    "cost_price": 30.00,
                    "market_price": 62.90,
                    "stock": 1400,
                    "specs": {"规格": "720ml", "类型": "纯白"},
                    "barcode": "6901234568215",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多牛奶饮料类商品 - 碳酸饮料 ====================
        
        # 可口可乐
        {
            "brand": "可口可乐",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "碳酸饮料",
            "spu_name": "可口可乐",
            "desc_detail": "可口可乐，经典口味，清爽解渴，休闲饮品",
            "desc_pack": "包装清单：可口可乐",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "可口可乐 330ml",
                    "caption": "经典口味｜清爽解渴｜休闲饮品",
                    "price": 3.00,
                    "cost_price": 1.80,
                    "market_price": 4.00,
                    "stock": 3000,
                    "specs": {"规格": "330ml"},
                    "barcode": "6901234568216",
                    "shelf_life": 365,
                },
                {
                    "name": "可口可乐 500ml",
                    "caption": "经典口味｜清爽解渴｜休闲饮品",
                    "price": 3.50,
                    "cost_price": 2.20,
                    "market_price": 4.50,
                    "stock": 2800,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568217",
                    "shelf_life": 365,
                },
                {
                    "name": "可口可乐 330ml*24罐",
                    "caption": "经典口味｜清爽解渴｜整箱装",
                    "price": 68.90,
                    "cost_price": 42.00,
                    "market_price": 88.90,
                    "stock": 1500,
                    "specs": {"规格": "330ml*24罐"},
                    "barcode": "6901234568218",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 百事可乐
        {
            "brand": "百事",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "碳酸饮料",
            "spu_name": "百事可乐",
            "desc_detail": "百事可乐，经典口味，清爽解渴，休闲饮品",
            "desc_pack": "包装清单：百事可乐",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "百事可乐 330ml",
                    "caption": "经典口味｜清爽解渴｜休闲饮品",
                    "price": 3.00,
                    "cost_price": 1.80,
                    "market_price": 4.00,
                    "stock": 2900,
                    "specs": {"规格": "330ml"},
                    "barcode": "6901234568219",
                    "shelf_life": 365,
                },
                {
                    "name": "百事可乐 500ml",
                    "caption": "经典口味｜清爽解渴｜休闲饮品",
                    "price": 3.50,
                    "cost_price": 2.20,
                    "market_price": 4.50,
                    "stock": 2700,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568220",
                    "shelf_life": 365,
                },
                {
                    "name": "百事可乐 330ml*24罐",
                    "caption": "经典口味｜清爽解渴｜整箱装",
                    "price": 68.90,
                    "cost_price": 42.00,
                    "market_price": 88.90,
                    "stock": 1400,
                    "specs": {"规格": "330ml*24罐"},
                    "barcode": "6901234568221",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 雪碧
        {
            "brand": "雪碧",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "碳酸饮料",
            "spu_name": "雪碧",
            "desc_detail": "雪碧，柠檬口味，清爽解渴，休闲饮品",
            "desc_pack": "包装清单：雪碧",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "雪碧 330ml",
                    "caption": "柠檬口味｜清爽解渴｜休闲饮品",
                    "price": 3.00,
                    "cost_price": 1.80,
                    "market_price": 4.00,
                    "stock": 2800,
                    "specs": {"规格": "330ml"},
                    "barcode": "6901234568222",
                    "shelf_life": 365,
                },
                {
                    "name": "雪碧 500ml",
                    "caption": "柠檬口味｜清爽解渴｜休闲饮品",
                    "price": 3.50,
                    "cost_price": 2.20,
                    "market_price": 4.50,
                    "stock": 2600,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568223",
                    "shelf_life": 365,
                },
                {
                    "name": "雪碧 330ml*24罐",
                    "caption": "柠檬口味｜清爽解渴｜整箱装",
                    "price": 68.90,
                    "cost_price": 42.00,
                    "market_price": 88.90,
                    "stock": 1300,
                    "specs": {"规格": "330ml*24罐"},
                    "barcode": "6901234568224",
                    "shelf_life": 365,
                },
            ]
        },
        
        # ==================== 更多酒水类商品 - 威士忌 ====================
        
        # 芝华士威士忌
        {
            "brand": "芝华士",
            "category1": "酒水",
            "category2": "威士忌",
            "category3": "苏格兰威士忌",
            "spu_name": "芝华士威士忌",
            "desc_detail": "芝华士威士忌，苏格兰名酒，醇厚口感，高端礼品",
            "desc_pack": "包装清单：芝华士威士忌",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "芝华士12年 700ml",
                    "caption": "苏格兰名酒｜醇厚口感｜高端礼品",
                    "price": 320.00,
                    "cost_price": 220.00,
                    "market_price": 400.00,
                    "stock": 400,
                    "specs": {"规格": "700ml", "年份": "12年"},
                    "barcode": "6901234568225",
                    "shelf_life": 3650,
                },
                {
                    "name": "芝华士18年 700ml",
                    "caption": "苏格兰名酒｜醇厚口感｜高端礼品",
                    "price": 580.00,
                    "cost_price": 400.00,
                    "market_price": 720.00,
                    "stock": 300,
                    "specs": {"规格": "700ml", "年份": "18年"},
                    "barcode": "6901234568226",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 尊尼获加威士忌
        {
            "brand": "尊尼获加",
            "category1": "酒水",
            "category2": "威士忌",
            "category3": "苏格兰威士忌",
            "spu_name": "尊尼获加威士忌",
            "desc_detail": "尊尼获加威士忌，苏格兰名酒，醇厚口感，高端礼品",
            "desc_pack": "包装清单：尊尼获加威士忌",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "尊尼获加黑方 700ml",
                    "caption": "苏格兰名酒｜醇厚口感｜高端礼品",
                    "price": 280.00,
                    "cost_price": 190.00,
                    "market_price": 350.00,
                    "stock": 450,
                    "specs": {"规格": "700ml", "系列": "黑方"},
                    "barcode": "6901234568227",
                    "shelf_life": 3650,
                },
                {
                    "name": "尊尼获加红方 700ml",
                    "caption": "苏格兰名酒｜醇厚口感｜高端礼品",
                    "price": 180.00,
                    "cost_price": 120.00,
                    "market_price": 225.00,
                    "stock": 500,
                    "specs": {"规格": "700ml", "系列": "红方"},
                    "barcode": "6901234568228",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # ==================== 更多食品类商品 - 饼干 ====================
        
        # 达利园饼干
        {
            "brand": "达利园",
            "category1": "食品",
            "category2": "零食",
            "category3": "饼干",
            "spu_name": "达利园饼干",
            "desc_detail": "达利园饼干，香甜酥脆，多种口味，休闲零食",
            "desc_pack": "包装清单：达利园饼干",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "达利园饼干 400g",
                    "caption": "香甜酥脆｜多种口味｜休闲零食",
                    "price": 8.90,
                    "cost_price": 5.50,
                    "market_price": 11.90,
                    "stock": 2200,
                    "specs": {"规格": "400g", "口味": "原味"},
                    "barcode": "6901234568229",
                    "shelf_life": 365,
                },
                {
                    "name": "达利园饼干 800g",
                    "caption": "香甜酥脆｜多种口味｜家庭装",
                    "price": 16.90,
                    "cost_price": 10.00,
                    "market_price": 22.90,
                    "stock": 1800,
                    "specs": {"规格": "800g", "口味": "原味"},
                    "barcode": "6901234568230",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 盼盼法式小面包
        {
            "brand": "盼盼",
            "category1": "食品",
            "category2": "零食",
            "category3": "面包",
            "spu_name": "盼盼法式小面包",
            "desc_detail": "盼盼法式小面包，香甜松软，营养早餐，休闲零食",
            "desc_pack": "包装清单：盼盼法式小面包",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "盼盼法式小面包 400g",
                    "caption": "香甜松软｜营养早餐｜休闲零食",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 2000,
                    "specs": {"规格": "400g"},
                    "barcode": "6901234568231",
                    "shelf_life": 180,
                },
                {
                    "name": "盼盼法式小面包 800g",
                    "caption": "香甜松软｜营养早餐｜家庭装",
                    "price": 23.90,
                    "cost_price": 15.00,
                    "market_price": 30.90,
                    "stock": 1600,
                    "specs": {"规格": "800g"},
                    "barcode": "6901234568232",
                    "shelf_life": 180,
                },
            ]
        },
        
        # ==================== 更多日化类商品 - 洗衣粉 ====================
        
        # 立白洗衣粉
        {
            "brand": "立白",
            "category1": "日化",
            "category2": "清洁用品",
            "category3": "洗衣粉",
            "spu_name": "立白洗衣粉",
            "desc_detail": "立白洗衣粉，强力去污，温和护衣，家庭必备",
            "desc_pack": "包装清单：立白洗衣粉",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "立白洗衣粉 1.8kg",
                    "caption": "强力去污｜温和护衣｜家庭必备",
                    "price": 18.90,
                    "cost_price": 12.00,
                    "market_price": 24.90,
                    "stock": 1800,
                    "specs": {"规格": "1.8kg"},
                    "barcode": "6901234568233",
                    "shelf_life": 1825,
                },
                {
                    "name": "立白洗衣粉 3.5kg",
                    "caption": "强力去污｜温和护衣｜家庭装",
                    "price": 35.90,
                    "cost_price": 23.00,
                    "market_price": 45.90,
                    "stock": 1400,
                    "specs": {"规格": "3.5kg"},
                    "barcode": "6901234568234",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 雕牌洗衣粉
        {
            "brand": "雕牌",
            "category1": "日化",
            "category2": "清洁用品",
            "category3": "洗衣粉",
            "spu_name": "雕牌洗衣粉",
            "desc_detail": "雕牌洗衣粉，强力去污，温和护衣，家庭必备",
            "desc_pack": "包装清单：雕牌洗衣粉",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "雕牌洗衣粉 1.8kg",
                    "caption": "强力去污｜温和护衣｜家庭必备",
                    "price": 15.90,
                    "cost_price": 10.00,
                    "market_price": 20.90,
                    "stock": 1700,
                    "specs": {"规格": "1.8kg"},
                    "barcode": "6901234568235",
                    "shelf_life": 1825,
                },
                {
                    "name": "雕牌洗衣粉 3.5kg",
                    "caption": "强力去污｜温和护衣｜家庭装",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 36.90,
                    "stock": 1300,
                    "specs": {"规格": "3.5kg"},
                    "barcode": "6901234568236",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多食品类商品 - 蜜饯果干 ====================
        
        # 良品铺子蜜饯
        {
            "brand": "良品铺子",
            "category1": "食品",
            "category2": "零食",
            "category3": "蜜饯",
            "spu_name": "良品铺子蜜饯",
            "desc_detail": "良品铺子蜜饯，酸甜可口，营养丰富，休闲零食",
            "desc_pack": "包装清单：良品铺子蜜饯",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "良品铺子话梅 200g",
                    "caption": "酸甜可口｜营养丰富｜休闲零食",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 36.90,
                    "stock": 1200,
                    "specs": {"规格": "200g", "口味": "话梅"},
                    "barcode": "6901234568237",
                    "shelf_life": 365,
                },
                {
                    "name": "良品铺子山楂片 200g",
                    "caption": "酸甜可口｜营养丰富｜休闲零食",
                    "price": 25.90,
                    "cost_price": 16.00,
                    "market_price": 32.90,
                    "stock": 1100,
                    "specs": {"规格": "200g", "口味": "山楂"},
                    "barcode": "6901234568238",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 三只松鼠蜜饯
        {
            "brand": "三只松鼠",
            "category1": "食品",
            "category2": "零食",
            "category3": "蜜饯",
            "spu_name": "三只松鼠蜜饯",
            "desc_detail": "三只松鼠蜜饯，酸甜可口，营养丰富，休闲零食",
            "desc_pack": "包装清单：三只松鼠蜜饯",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "三只松鼠芒果干 200g",
                    "caption": "酸甜可口｜营养丰富｜休闲零食",
                    "price": 32.90,
                    "cost_price": 20.00,
                    "market_price": 42.90,
                    "stock": 1000,
                    "specs": {"规格": "200g", "口味": "芒果"},
                    "barcode": "6901234568239",
                    "shelf_life": 365,
                },
                {
                    "name": "三只松鼠草莓干 200g",
                    "caption": "酸甜可口｜营养丰富｜休闲零食",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 45.90,
                    "stock": 900,
                    "specs": {"规格": "200g", "口味": "草莓"},
                    "barcode": "6901234568240",
                    "shelf_life": 365,
                },
            ]
        },
        
        # ==================== 文具类商品 - 笔类 ====================
        
        # 晨光中性笔
        {
            "brand": "晨光",
            "category1": "文具",
            "category2": "笔类",
            "category3": "中性笔",
            "spu_name": "晨光中性笔",
            "desc_detail": "晨光中性笔，书写流畅，持久耐用，办公学习必备",
            "desc_pack": "包装清单：晨光中性笔",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "晨光中性笔 0.5mm 黑色 12支装",
                    "caption": "书写流畅｜持久耐用｜办公学习必备",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 3000,
                    "specs": {"规格": "0.5mm", "颜色": "黑色", "数量": "12支"},
                    "barcode": "6901234568241",
                    "shelf_life": 1825,
                },
                {
                    "name": "晨光中性笔 0.5mm 蓝色 12支装",
                    "caption": "书写流畅｜持久耐用｜办公学习必备",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 2800,
                    "specs": {"规格": "0.5mm", "颜色": "蓝色", "数量": "12支"},
                    "barcode": "6901234568242",
                    "shelf_life": 1825,
                },
                {
                    "name": "晨光中性笔 0.5mm 红色 12支装",
                    "caption": "书写流畅｜持久耐用｜办公学习必备",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 2600,
                    "specs": {"规格": "0.5mm", "颜色": "红色", "数量": "12支"},
                    "barcode": "6901234568243",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 得力圆珠笔
        {
            "brand": "得力",
            "category1": "文具",
            "category2": "笔类",
            "category3": "圆珠笔",
            "spu_name": "得力圆珠笔",
            "desc_detail": "得力圆珠笔，书写流畅，持久耐用，办公学习必备",
            "desc_pack": "包装清单：得力圆珠笔",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "得力圆珠笔 1.0mm 黑色 12支装",
                    "caption": "书写流畅｜持久耐用｜办公学习必备",
                    "price": 9.90,
                    "cost_price": 6.00,
                    "market_price": 12.90,
                    "stock": 3200,
                    "specs": {"规格": "1.0mm", "颜色": "黑色", "数量": "12支"},
                    "barcode": "6901234568244",
                    "shelf_life": 1825,
                },
                {
                    "name": "得力圆珠笔 1.0mm 蓝色 12支装",
                    "caption": "书写流畅｜持久耐用｜办公学习必备",
                    "price": 9.90,
                    "cost_price": 6.00,
                    "market_price": 12.90,
                    "stock": 3000,
                    "specs": {"规格": "1.0mm", "颜色": "蓝色", "数量": "12支"},
                    "barcode": "6901234568245",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 百乐中性笔
        {
            "brand": "百乐",
            "category1": "文具",
            "category2": "笔类",
            "category3": "中性笔",
            "spu_name": "百乐中性笔",
            "desc_detail": "百乐中性笔，日本进口，书写流畅，高端品质",
            "desc_pack": "包装清单：百乐中性笔",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "百乐中性笔 0.5mm 黑色 10支装",
                    "caption": "日本进口｜书写流畅｜高端品质",
                    "price": 25.90,
                    "cost_price": 16.00,
                    "market_price": 32.90,
                    "stock": 2000,
                    "specs": {"规格": "0.5mm", "颜色": "黑色", "数量": "10支"},
                    "barcode": "6901234568246",
                    "shelf_life": 1825,
                },
                {
                    "name": "百乐中性笔 0.5mm 蓝色 10支装",
                    "caption": "日本进口｜书写流畅｜高端品质",
                    "price": 25.90,
                    "cost_price": 16.00,
                    "market_price": 32.90,
                    "stock": 1800,
                    "specs": {"规格": "0.5mm", "颜色": "蓝色", "数量": "10支"},
                    "barcode": "6901234568247",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 三菱中性笔
        {
            "brand": "三菱",
            "category1": "文具",
            "category2": "笔类",
            "category3": "中性笔",
            "spu_name": "三菱中性笔",
            "desc_detail": "三菱中性笔，日本进口，书写流畅，高端品质",
            "desc_pack": "包装清单：三菱中性笔",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "三菱中性笔 0.5mm 黑色 10支装",
                    "caption": "日本进口｜书写流畅｜高端品质",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 45.90,
                    "stock": 1500,
                    "specs": {"规格": "0.5mm", "颜色": "黑色", "数量": "10支"},
                    "barcode": "6901234568248",
                    "shelf_life": 1825,
                },
                {
                    "name": "三菱中性笔 0.5mm 蓝色 10支装",
                    "caption": "日本进口｜书写流畅｜高端品质",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 45.90,
                    "stock": 1400,
                    "specs": {"规格": "0.5mm", "颜色": "蓝色", "数量": "10支"},
                    "barcode": "6901234568249",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 文具类商品 - 笔记本 ====================
        
        # 晨光笔记本
        {
            "brand": "晨光",
            "category1": "文具",
            "category2": "本册",
            "category3": "笔记本",
            "spu_name": "晨光笔记本",
            "desc_detail": "晨光笔记本，纸张优质，书写舒适，办公学习必备",
            "desc_pack": "包装清单：晨光笔记本",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "晨光笔记本 B5 100页",
                    "caption": "纸张优质｜书写舒适｜办公学习必备",
                    "price": 8.90,
                    "cost_price": 5.50,
                    "market_price": 11.90,
                    "stock": 2500,
                    "specs": {"规格": "B5", "页数": "100页"},
                    "barcode": "6901234568250",
                    "shelf_life": 1825,
                },
                {
                    "name": "晨光笔记本 A4 100页",
                    "caption": "纸张优质｜书写舒适｜办公学习必备",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 2200,
                    "specs": {"规格": "A4", "页数": "100页"},
                    "barcode": "6901234568251",
                    "shelf_life": 1825,
                },
                {
                    "name": "晨光笔记本 A5 80页",
                    "caption": "纸张优质｜书写舒适｜便携实用",
                    "price": 6.90,
                    "cost_price": 4.00,
                    "market_price": 9.90,
                    "stock": 2800,
                    "specs": {"规格": "A5", "页数": "80页"},
                    "barcode": "6901234568252",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 得力笔记本
        {
            "brand": "得力",
            "category1": "文具",
            "category2": "本册",
            "category3": "笔记本",
            "spu_name": "得力笔记本",
            "desc_detail": "得力笔记本，纸张优质，书写舒适，办公学习必备",
            "desc_pack": "包装清单：得力笔记本",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "得力笔记本 B5 100页",
                    "caption": "纸张优质｜书写舒适｜办公学习必备",
                    "price": 7.90,
                    "cost_price": 5.00,
                    "market_price": 10.90,
                    "stock": 2400,
                    "specs": {"规格": "B5", "页数": "100页"},
                    "barcode": "6901234568253",
                    "shelf_life": 1825,
                },
                {
                    "name": "得力笔记本 A4 100页",
                    "caption": "纸张优质｜书写舒适｜办公学习必备",
                    "price": 11.90,
                    "cost_price": 7.50,
                    "market_price": 15.90,
                    "stock": 2100,
                    "specs": {"规格": "A4", "页数": "100页"},
                    "barcode": "6901234568254",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 文具类商品 - 文具套装 ====================
        
        # 晨光文具套装
        {
            "brand": "晨光",
            "category1": "文具",
            "category2": "文具套装",
            "category3": "学生文具套装",
            "spu_name": "晨光文具套装",
            "desc_detail": "晨光文具套装，齐全实用，性价比高，学生必备",
            "desc_pack": "包装清单：晨光文具套装",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "晨光文具套装 20件套",
                    "caption": "齐全实用｜性价比高｜学生必备",
                    "price": 45.90,
                    "cost_price": 28.00,
                    "market_price": 58.90,
                    "stock": 1500,
                    "specs": {"规格": "20件套"},
                    "barcode": "6901234568255",
                    "shelf_life": 1825,
                },
                {
                    "name": "晨光文具套装 30件套",
                    "caption": "齐全实用｜性价比高｜学生必备",
                    "price": 68.90,
                    "cost_price": 42.00,
                    "market_price": 88.90,
                    "stock": 1200,
                    "specs": {"规格": "30件套"},
                    "barcode": "6901234568256",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 得力文具套装
        {
            "brand": "得力",
            "category1": "文具",
            "category2": "文具套装",
            "category3": "办公文具套装",
            "spu_name": "得力文具套装",
            "desc_detail": "得力文具套装，齐全实用，性价比高，办公必备",
            "desc_pack": "包装清单：得力文具套装",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "得力文具套装 15件套",
                    "caption": "齐全实用｜性价比高｜办公必备",
                    "price": 38.90,
                    "cost_price": 24.00,
                    "market_price": 49.90,
                    "stock": 1400,
                    "specs": {"规格": "15件套"},
                    "barcode": "6901234568257",
                    "shelf_life": 1825,
                },
                {
                    "name": "得力文具套装 25件套",
                    "caption": "齐全实用｜性价比高｜办公必备",
                    "price": 58.90,
                    "cost_price": 36.00,
                    "market_price": 75.90,
                    "stock": 1100,
                    "specs": {"规格": "25件套"},
                    "barcode": "6901234568258",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多零食和食品类商品 - 膨化食品 ====================
        
        # 上好佳膨化食品
        {
            "brand": "上好佳",
            "category1": "食品",
            "category2": "零食",
            "category3": "膨化食品",
            "spu_name": "上好佳膨化食品",
            "desc_detail": "上好佳膨化食品，香脆可口，多种口味，休闲零食",
            "desc_pack": "包装清单：上好佳膨化食品",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "上好佳鲜虾片 80g",
                    "caption": "香脆可口｜多种口味｜休闲零食",
                    "price": 6.90,
                    "cost_price": 4.00,
                    "market_price": 9.90,
                    "stock": 2200,
                    "specs": {"规格": "80g", "口味": "鲜虾"},
                    "barcode": "6901234568259",
                    "shelf_life": 365,
                },
                {
                    "name": "上好佳田园薯片 80g",
                    "caption": "香脆可口｜多种口味｜休闲零食",
                    "price": 6.90,
                    "cost_price": 4.00,
                    "market_price": 9.90,
                    "stock": 2100,
                    "specs": {"规格": "80g", "口味": "田园"},
                    "barcode": "6901234568260",
                    "shelf_life": 365,
                },
                {
                    "name": "上好佳洋葱圈 80g",
                    "caption": "香脆可口｜多种口味｜休闲零食",
                    "price": 6.90,
                    "cost_price": 4.00,
                    "market_price": 9.90,
                    "stock": 2000,
                    "specs": {"规格": "80g", "口味": "洋葱"},
                    "barcode": "6901234568261",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 奇多膨化食品
        {
            "brand": "奇多",
            "category1": "食品",
            "category2": "零食",
            "category3": "膨化食品",
            "spu_name": "奇多膨化食品",
            "desc_detail": "奇多膨化食品，香脆可口，多种口味，休闲零食",
            "desc_pack": "包装清单：奇多膨化食品",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "奇多玉米棒 70g",
                    "caption": "香脆可口｜多种口味｜休闲零食",
                    "price": 7.90,
                    "cost_price": 4.50,
                    "market_price": 10.90,
                    "stock": 1900,
                    "specs": {"规格": "70g", "口味": "原味"},
                    "barcode": "6901234568262",
                    "shelf_life": 365,
                },
                {
                    "name": "奇多玉米棒 70g 烧烤味",
                    "caption": "香脆可口｜多种口味｜休闲零食",
                    "price": 7.90,
                    "cost_price": 4.50,
                    "market_price": 10.90,
                    "stock": 1800,
                    "specs": {"规格": "70g", "口味": "烧烤味"},
                    "barcode": "6901234568263",
                    "shelf_life": 365,
                },
            ]
        },
        
        # ==================== 更多日化类商品 - 护肤品 ====================
        
        # 大宝护肤品
        {
            "brand": "大宝",
            "category1": "日化",
            "category2": "护肤品",
            "category3": "面霜",
            "spu_name": "大宝护肤品",
            "desc_detail": "大宝护肤品，温和保湿，滋润肌肤，日常护理",
            "desc_pack": "包装清单：大宝护肤品",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "大宝SOD蜜 50g",
                    "caption": "温和保湿｜滋润肌肤｜日常护理",
                    "price": 18.90,
                    "cost_price": 12.00,
                    "market_price": 24.90,
                    "stock": 2000,
                    "specs": {"规格": "50g"},
                    "barcode": "6901234568264",
                    "shelf_life": 1825,
                },
                {
                    "name": "大宝SOD蜜 100g",
                    "caption": "温和保湿｜滋润肌肤｜家庭装",
                    "price": 32.90,
                    "cost_price": 21.00,
                    "market_price": 42.90,
                    "stock": 1700,
                    "specs": {"规格": "100g"},
                    "barcode": "6901234568265",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 旁氏护肤品
        {
            "brand": "旁氏",
            "category1": "日化",
            "category2": "护肤品",
            "category3": "洗面奶",
            "spu_name": "旁氏洗面奶",
            "desc_detail": "旁氏洗面奶，深层清洁，温和不刺激，日常护理",
            "desc_pack": "包装清单：旁氏洗面奶",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "旁氏洗面奶 100g",
                    "caption": "深层清洁｜温和不刺激｜日常护理",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 36.90,
                    "stock": 1800,
                    "specs": {"规格": "100g"},
                    "barcode": "6901234568266",
                    "shelf_life": 1825,
                },
                {
                    "name": "旁氏洗面奶 150g",
                    "caption": "深层清洁｜温和不刺激｜家庭装",
                    "price": 42.90,
                    "cost_price": 27.00,
                    "market_price": 55.90,
                    "stock": 1500,
                    "specs": {"规格": "150g"},
                    "barcode": "6901234568267",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多牛奶饮料类商品 - 茶饮料 ====================
        
        # 康师傅绿茶
        {
            "brand": "康师傅",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "茶饮料",
            "spu_name": "康师傅绿茶",
            "desc_detail": "康师傅绿茶，清香怡人，清爽解渴，休闲饮品",
            "desc_pack": "包装清单：康师傅绿茶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "康师傅绿茶 500ml",
                    "caption": "清香怡人｜清爽解渴｜休闲饮品",
                    "price": 3.50,
                    "cost_price": 2.20,
                    "market_price": 4.50,
                    "stock": 3000,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568268",
                    "shelf_life": 365,
                },
                {
                    "name": "康师傅绿茶 500ml*15瓶",
                    "caption": "清香怡人｜清爽解渴｜整箱装",
                    "price": 48.00,
                    "cost_price": 30.00,
                    "market_price": 62.00,
                    "stock": 1500,
                    "specs": {"规格": "500ml*15瓶"},
                    "barcode": "6901234568269",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 统一绿茶
        {
            "brand": "统一",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "茶饮料",
            "spu_name": "统一绿茶",
            "desc_detail": "统一绿茶，清香怡人，清爽解渴，休闲饮品",
            "desc_pack": "包装清单：统一绿茶",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "统一绿茶 500ml",
                    "caption": "清香怡人｜清爽解渴｜休闲饮品",
                    "price": 3.50,
                    "cost_price": 2.20,
                    "market_price": 4.50,
                    "stock": 2900,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568270",
                    "shelf_life": 365,
                },
                {
                    "name": "统一绿茶 500ml*15瓶",
                    "caption": "清香怡人｜清爽解渴｜整箱装",
                    "price": 48.00,
                    "cost_price": 30.00,
                    "market_price": 62.00,
                    "stock": 1400,
                    "specs": {"规格": "500ml*15瓶"},
                    "barcode": "6901234568271",
                    "shelf_life": 365,
                },
            ]
        },
        
        # ==================== 更多酒水类商品 - 白兰地 ====================
        
        # 马爹利白兰地
        {
            "brand": "马爹利",
            "category1": "酒水",
            "category2": "白兰地",
            "category3": "干邑",
            "spu_name": "马爹利白兰地",
            "desc_detail": "马爹利白兰地，法国名酒，醇厚口感，高端礼品",
            "desc_pack": "包装清单：马爹利白兰地",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "马爹利名士 700ml",
                    "caption": "法国名酒｜醇厚口感｜高端礼品",
                    "price": 580.00,
                    "cost_price": 400.00,
                    "market_price": 720.00,
                    "stock": 300,
                    "specs": {"规格": "700ml"},
                    "barcode": "6901234568272",
                    "shelf_life": 3650,
                },
                {
                    "name": "马爹利蓝带 700ml",
                    "caption": "法国名酒｜醇厚口感｜高端礼品",
                    "price": 880.00,
                    "cost_price": 600.00,
                    "market_price": 1100.00,
                    "stock": 200,
                    "specs": {"规格": "700ml"},
                    "barcode": "6901234568273",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 轩尼诗白兰地
        {
            "brand": "轩尼诗",
            "category1": "酒水",
            "category2": "白兰地",
            "category3": "干邑",
            "spu_name": "轩尼诗白兰地",
            "desc_detail": "轩尼诗白兰地，法国名酒，醇厚口感，高端礼品",
            "desc_pack": "包装清单：轩尼诗白兰地",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "轩尼诗VSOP 700ml",
                    "caption": "法国名酒｜醇厚口感｜高端礼品",
                    "price": 680.00,
                    "cost_price": 470.00,
                    "market_price": 850.00,
                    "stock": 350,
                    "specs": {"规格": "700ml"},
                    "barcode": "6901234568274",
                    "shelf_life": 3650,
                },
                {
                    "name": "轩尼诗XO 700ml",
                    "caption": "法国名酒｜醇厚口感｜高端礼品",
                    "price": 1280.00,
                    "cost_price": 880.00,
                    "market_price": 1600.00,
                    "stock": 150,
                    "specs": {"规格": "700ml"},
                    "barcode": "6901234568275",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 人头马白兰地
        {
            "brand": "人头马",
            "category1": "酒水",
            "category2": "白兰地",
            "category3": "干邑",
            "spu_name": "人头马白兰地",
            "desc_detail": "人头马白兰地，法国名酒，醇厚口感，高端礼品",
            "desc_pack": "包装清单：人头马白兰地",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "人头马VSOP 700ml",
                    "caption": "法国名酒｜醇厚口感｜高端礼品",
                    "price": 620.00,
                    "cost_price": 430.00,
                    "market_price": 780.00,
                    "stock": 320,
                    "specs": {"规格": "700ml"},
                    "barcode": "6901234568276",
                    "shelf_life": 3650,
                },
                {
                    "name": "人头马XO 700ml",
                    "caption": "法国名酒｜醇厚口感｜高端礼品",
                    "price": 1180.00,
                    "cost_price": 810.00,
                    "market_price": 1480.00,
                    "stock": 180,
                    "specs": {"规格": "700ml"},
                    "barcode": "6901234568277",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # ==================== 更多文具类商品 - 修正带 ====================
        
        # 晨光修正带
        {
            "brand": "晨光",
            "category1": "文具",
            "category2": "修正用品",
            "category3": "修正带",
            "spu_name": "晨光修正带",
            "desc_detail": "晨光修正带，修正清晰，使用方便，办公学习必备",
            "desc_pack": "包装清单：晨光修正带",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "晨光修正带 5mm*12m",
                    "caption": "修正清晰｜使用方便｜办公学习必备",
                    "price": 3.90,
                    "cost_price": 2.50,
                    "market_price": 5.90,
                    "stock": 3000,
                    "specs": {"规格": "5mm*12m"},
                    "barcode": "6901234568278",
                    "shelf_life": 1825,
                },
                {
                    "name": "晨光修正带 5mm*12m 3支装",
                    "caption": "修正清晰｜使用方便｜办公学习必备",
                    "price": 10.90,
                    "cost_price": 7.00,
                    "market_price": 14.90,
                    "stock": 2500,
                    "specs": {"规格": "5mm*12m", "数量": "3支"},
                    "barcode": "6901234568279",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 得力修正带
        {
            "brand": "得力",
            "category1": "文具",
            "category2": "修正用品",
            "category3": "修正带",
            "spu_name": "得力修正带",
            "desc_detail": "得力修正带，修正清晰，使用方便，办公学习必备",
            "desc_pack": "包装清单：得力修正带",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "得力修正带 5mm*12m",
                    "caption": "修正清晰｜使用方便｜办公学习必备",
                    "price": 3.50,
                    "cost_price": 2.20,
                    "market_price": 5.50,
                    "stock": 2800,
                    "specs": {"规格": "5mm*12m"},
                    "barcode": "6901234568280",
                    "shelf_life": 1825,
                },
                {
                    "name": "得力修正带 5mm*12m 3支装",
                    "caption": "修正清晰｜使用方便｜办公学习必备",
                    "price": 9.90,
                    "cost_price": 6.00,
                    "market_price": 13.90,
                    "stock": 2300,
                    "specs": {"规格": "5mm*12m", "数量": "3支"},
                    "barcode": "6901234568281",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多零食和食品类商品 - 糕点 ====================
        
        # 好丽友派
        {
            "brand": "好丽友",
            "category1": "食品",
            "category2": "零食",
            "category3": "糕点",
            "spu_name": "好丽友派",
            "desc_detail": "好丽友派，香甜松软，巧克力涂层，休闲零食",
            "desc_pack": "包装清单：好丽友派",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "好丽友派 216g",
                    "caption": "香甜松软｜巧克力涂层｜休闲零食",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 2000,
                    "specs": {"规格": "216g", "口味": "巧克力"},
                    "barcode": "6901234568282",
                    "shelf_life": 180,
                },
                {
                    "name": "好丽友派 432g",
                    "caption": "香甜松软｜巧克力涂层｜家庭装",
                    "price": 23.90,
                    "cost_price": 15.00,
                    "market_price": 30.90,
                    "stock": 1700,
                    "specs": {"规格": "432g", "口味": "巧克力"},
                    "barcode": "6901234568283",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 达利园蛋黄派
        {
            "brand": "达利园",
            "category1": "食品",
            "category2": "零食",
            "category3": "糕点",
            "spu_name": "达利园蛋黄派",
            "desc_detail": "达利园蛋黄派，香甜松软，营养丰富，休闲零食",
            "desc_pack": "包装清单：达利园蛋黄派",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "达利园蛋黄派 240g",
                    "caption": "香甜松软｜营养丰富｜休闲零食",
                    "price": 11.90,
                    "cost_price": 7.50,
                    "market_price": 15.90,
                    "stock": 1900,
                    "specs": {"规格": "240g"},
                    "barcode": "6901234568284",
                    "shelf_life": 180,
                },
                {
                    "name": "达利园蛋黄派 480g",
                    "caption": "香甜松软｜营养丰富｜家庭装",
                    "price": 22.90,
                    "cost_price": 14.00,
                    "market_price": 29.90,
                    "stock": 1600,
                    "specs": {"规格": "480g"},
                    "barcode": "6901234568285",
                    "shelf_life": 180,
                },
            ]
        },
        
        # ==================== 更多日化类商品 - 洗手液 ====================
        
        # 蓝月亮洗手液
        {
            "brand": "蓝月亮",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "洗手液",
            "spu_name": "蓝月亮洗手液",
            "desc_detail": "蓝月亮洗手液，温和抑菌，清香怡人，日常护理",
            "desc_pack": "包装清单：蓝月亮洗手液",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "蓝月亮洗手液 300ml",
                    "caption": "温和抑菌｜清香怡人｜日常护理",
                    "price": 15.90,
                    "cost_price": 10.00,
                    "market_price": 20.90,
                    "stock": 2000,
                    "specs": {"规格": "300ml"},
                    "barcode": "6901234568286",
                    "shelf_life": 1825,
                },
                {
                    "name": "蓝月亮洗手液 500ml",
                    "caption": "温和抑菌｜清香怡人｜家庭装",
                    "price": 25.90,
                    "cost_price": 16.00,
                    "market_price": 32.90,
                    "stock": 1700,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568287",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 威露士洗手液
        {
            "brand": "威露士",
            "category1": "日化",
            "category2": "个人护理",
            "category3": "洗手液",
            "spu_name": "威露士洗手液",
            "desc_detail": "威露士洗手液，温和抑菌，清香怡人，日常护理",
            "desc_pack": "包装清单：威露士洗手液",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "威露士洗手液 300ml",
                    "caption": "温和抑菌｜清香怡人｜日常护理",
                    "price": 18.90,
                    "cost_price": 12.00,
                    "market_price": 24.90,
                    "stock": 1800,
                    "specs": {"规格": "300ml"},
                    "barcode": "6901234568288",
                    "shelf_life": 1825,
                },
                {
                    "name": "威露士洗手液 500ml",
                    "caption": "温和抑菌｜清香怡人｜家庭装",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 36.90,
                    "stock": 1500,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568289",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多牛奶饮料类商品 - 咖啡饮料 ====================
        
        # 雀巢咖啡
        {
            "brand": "雀巢",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "咖啡饮料",
            "spu_name": "雀巢咖啡",
            "desc_detail": "雀巢咖啡，香浓醇厚，提神醒脑，休闲饮品",
            "desc_pack": "包装清单：雀巢咖啡",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "雀巢咖啡 268ml",
                    "caption": "香浓醇厚｜提神醒脑｜休闲饮品",
                    "price": 6.90,
                    "cost_price": 4.50,
                    "market_price": 8.90,
                    "stock": 2500,
                    "specs": {"规格": "268ml", "口味": "原味"},
                    "barcode": "6901234568290",
                    "shelf_life": 365,
                },
                {
                    "name": "雀巢咖啡 268ml*6瓶",
                    "caption": "香浓醇厚｜提神醒脑｜整箱装",
                    "price": 38.90,
                    "cost_price": 25.00,
                    "market_price": 50.90,
                    "stock": 1200,
                    "specs": {"规格": "268ml*6瓶", "口味": "原味"},
                    "barcode": "6901234568291",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 星巴克咖啡
        {
            "brand": "星巴克",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "咖啡饮料",
            "spu_name": "星巴克咖啡",
            "desc_detail": "星巴克咖啡，香浓醇厚，提神醒脑，高端饮品",
            "desc_pack": "包装清单：星巴克咖啡",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "星巴克咖啡 270ml",
                    "caption": "香浓醇厚｜提神醒脑｜高端饮品",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 1500,
                    "specs": {"规格": "270ml", "口味": "拿铁"},
                    "barcode": "6901234568292",
                    "shelf_life": 365,
                },
                {
                    "name": "星巴克咖啡 270ml*6瓶",
                    "caption": "香浓醇厚｜提神醒脑｜整箱装",
                    "price": 72.90,
                    "cost_price": 45.00,
                    "market_price": 95.90,
                    "stock": 800,
                    "specs": {"规格": "270ml*6瓶", "口味": "拿铁"},
                    "barcode": "6901234568293",
                    "shelf_life": 365,
                },
            ]
        },
        
        # ==================== 更多酒水类商品 - 伏特加 ====================
        
        # 绝对伏特加
        {
            "brand": "绝对",
            "category1": "酒水",
            "category2": "伏特加",
            "category3": "瑞典伏特加",
            "spu_name": "绝对伏特加",
            "desc_detail": "绝对伏特加，瑞典名酒，纯净口感，高端礼品",
            "desc_pack": "包装清单：绝对伏特加",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "绝对伏特加 700ml",
                    "caption": "瑞典名酒｜纯净口感｜高端礼品",
                    "price": 280.00,
                    "cost_price": 190.00,
                    "market_price": 350.00,
                    "stock": 400,
                    "specs": {"规格": "700ml"},
                    "barcode": "6901234568294",
                    "shelf_life": 3650,
                },
                {
                    "name": "绝对伏特加 1L",
                    "caption": "瑞典名酒｜纯净口感｜家庭装",
                    "price": 380.00,
                    "cost_price": 260.00,
                    "market_price": 480.00,
                    "stock": 300,
                    "specs": {"规格": "1L"},
                    "barcode": "6901234568295",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 斯米诺伏特加
        {
            "brand": "斯米诺",
            "category1": "酒水",
            "category2": "伏特加",
            "category3": "俄罗斯伏特加",
            "spu_name": "斯米诺伏特加",
            "desc_detail": "斯米诺伏特加，俄罗斯名酒，纯净口感，高端礼品",
            "desc_pack": "包装清单：斯米诺伏特加",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "斯米诺伏特加 700ml",
                    "caption": "俄罗斯名酒｜纯净口感｜高端礼品",
                    "price": 220.00,
                    "cost_price": 150.00,
                    "market_price": 280.00,
                    "stock": 450,
                    "specs": {"规格": "700ml"},
                    "barcode": "6901234568296",
                    "shelf_life": 3650,
                },
                {
                    "name": "斯米诺伏特加 1L",
                    "caption": "俄罗斯名酒｜纯净口感｜家庭装",
                    "price": 300.00,
                    "cost_price": 200.00,
                    "market_price": 380.00,
                    "stock": 350,
                    "specs": {"规格": "1L"},
                    "barcode": "6901234568297",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # ==================== 更多文具类商品 - 计算器 ====================
        
        # 卡西欧计算器
        {
            "brand": "卡西欧",
            "category1": "文具",
            "category2": "计算器",
            "category3": "科学计算器",
            "spu_name": "卡西欧计算器",
            "desc_detail": "卡西欧计算器，功能强大，精准计算，办公学习必备",
            "desc_pack": "包装清单：卡西欧计算器",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "卡西欧科学计算器 FX-991",
                    "caption": "功能强大｜精准计算｜办公学习必备",
                    "price": 128.00,
                    "cost_price": 85.00,
                    "market_price": 160.00,
                    "stock": 1000,
                    "specs": {"规格": "FX-991"},
                    "barcode": "6901234568298",
                    "shelf_life": 1825,
                },
                {
                    "name": "卡西欧科学计算器 FX-82",
                    "caption": "功能强大｜精准计算｜办公学习必备",
                    "price": 88.00,
                    "cost_price": 58.00,
                    "market_price": 110.00,
                    "stock": 1200,
                    "specs": {"规格": "FX-82"},
                    "barcode": "6901234568299",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 得力计算器
        {
            "brand": "得力",
            "category1": "文具",
            "category2": "计算器",
            "category3": "普通计算器",
            "spu_name": "得力计算器",
            "desc_detail": "得力计算器，功能实用，精准计算，办公学习必备",
            "desc_pack": "包装清单：得力计算器",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "得力计算器 12位",
                    "caption": "功能实用｜精准计算｜办公学习必备",
                    "price": 25.90,
                    "cost_price": 16.00,
                    "market_price": 32.90,
                    "stock": 1800,
                    "specs": {"规格": "12位"},
                    "barcode": "6901234568300",
                    "shelf_life": 1825,
                },
                {
                    "name": "得力计算器 8位",
                    "caption": "功能实用｜精准计算｜办公学习必备",
                    "price": 15.90,
                    "cost_price": 10.00,
                    "market_price": 20.90,
                    "stock": 2000,
                    "specs": {"规格": "8位"},
                    "barcode": "6901234568301",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多零食和食品类商品 - 糖果 ====================
        
        # 徐福记糖果
        {
            "brand": "徐福记",
            "category1": "食品",
            "category2": "零食",
            "category3": "糖果",
            "spu_name": "徐福记糖果",
            "desc_detail": "徐福记糖果，香甜可口，多种口味，休闲零食",
            "desc_pack": "包装清单：徐福记糖果",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "徐福记酥糖 400g",
                    "caption": "香甜可口｜多种口味｜休闲零食",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 36.90,
                    "stock": 1500,
                    "specs": {"规格": "400g", "口味": "酥糖"},
                    "barcode": "6901234568302",
                    "shelf_life": 365,
                },
                {
                    "name": "徐福记牛奶糖 400g",
                    "caption": "香甜可口｜多种口味｜休闲零食",
                    "price": 25.90,
                    "cost_price": 16.00,
                    "market_price": 32.90,
                    "stock": 1400,
                    "specs": {"规格": "400g", "口味": "牛奶糖"},
                    "barcode": "6901234568303",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 金丝猴糖果
        {
            "brand": "金丝猴",
            "category1": "食品",
            "category2": "零食",
            "category3": "糖果",
            "spu_name": "金丝猴糖果",
            "desc_detail": "金丝猴糖果，香甜可口，多种口味，休闲零食",
            "desc_pack": "包装清单：金丝猴糖果",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "金丝猴奶糖 400g",
                    "caption": "香甜可口｜多种口味｜休闲零食",
                    "price": 22.90,
                    "cost_price": 14.00,
                    "market_price": 28.90,
                    "stock": 1300,
                    "specs": {"规格": "400g", "口味": "奶糖"},
                    "barcode": "6901234568304",
                    "shelf_life": 365,
                },
                {
                    "name": "金丝猴麦芽糖 400g",
                    "caption": "香甜可口｜多种口味｜休闲零食",
                    "price": 20.90,
                    "cost_price": 13.00,
                    "market_price": 26.90,
                    "stock": 1200,
                    "specs": {"规格": "400g", "口味": "麦芽糖"},
                    "barcode": "6901234568305",
                    "shelf_life": 365,
                },
            ]
        },
        
        # ==================== 更多文具类商品 - 尺子 ====================
        
        # 晨光尺子
        {
            "brand": "晨光",
            "category1": "文具",
            "category2": "尺子",
            "category3": "直尺",
            "spu_name": "晨光尺子",
            "desc_detail": "晨光尺子，精准刻度，坚固耐用，办公学习必备",
            "desc_pack": "包装清单：晨光尺子",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "晨光直尺 15cm",
                    "caption": "精准刻度｜坚固耐用｜办公学习必备",
                    "price": 2.50,
                    "cost_price": 1.50,
                    "market_price": 3.50,
                    "stock": 5000,
                    "specs": {"规格": "15cm"},
                    "barcode": "6901234568306",
                    "shelf_life": 1825,
                },
                {
                    "name": "晨光直尺 20cm",
                    "caption": "精准刻度｜坚固耐用｜办公学习必备",
                    "price": 3.50,
                    "cost_price": 2.00,
                    "market_price": 4.50,
                    "stock": 4500,
                    "specs": {"规格": "20cm"},
                    "barcode": "6901234568307",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 得力尺子
        {
            "brand": "得力",
            "category1": "文具",
            "category2": "尺子",
            "category3": "直尺",
            "spu_name": "得力尺子",
            "desc_detail": "得力尺子，精准刻度，坚固耐用，办公学习必备",
            "desc_pack": "包装清单：得力尺子",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "得力直尺 15cm",
                    "caption": "精准刻度｜坚固耐用｜办公学习必备",
                    "price": 2.00,
                    "cost_price": 1.20,
                    "market_price": 3.00,
                    "stock": 4800,
                    "specs": {"规格": "15cm"},
                    "barcode": "6901234568308",
                    "shelf_life": 1825,
                },
                {
                    "name": "得力直尺 30cm",
                    "caption": "精准刻度｜坚固耐用｜办公学习必备",
                    "price": 4.50,
                    "cost_price": 2.80,
                    "market_price": 5.50,
                    "stock": 4200,
                    "specs": {"规格": "30cm"},
                    "barcode": "6901234568309",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多文具类商品 - 橡皮 ====================
        
        # 晨光橡皮
        {
            "brand": "晨光",
            "category1": "文具",
            "category2": "橡皮",
            "category3": "橡皮擦",
            "spu_name": "晨光橡皮",
            "desc_detail": "晨光橡皮，擦除干净，不伤纸张，办公学习必备",
            "desc_pack": "包装清单：晨光橡皮",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "晨光橡皮 4B",
                    "caption": "擦除干净｜不伤纸张｜办公学习必备",
                    "price": 1.50,
                    "cost_price": 0.80,
                    "market_price": 2.50,
                    "stock": 6000,
                    "specs": {"规格": "4B"},
                    "barcode": "6901234568310",
                    "shelf_life": 1825,
                },
                {
                    "name": "晨光橡皮 2B",
                    "caption": "擦除干净｜不伤纸张｜办公学习必备",
                    "price": 1.00,
                    "cost_price": 0.60,
                    "market_price": 1.80,
                    "stock": 5500,
                    "specs": {"规格": "2B"},
                    "barcode": "6901234568311",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 得力橡皮
        {
            "brand": "得力",
            "category1": "文具",
            "category2": "橡皮",
            "category3": "橡皮擦",
            "spu_name": "得力橡皮",
            "desc_detail": "得力橡皮，擦除干净，不伤纸张，办公学习必备",
            "desc_pack": "包装清单：得力橡皮",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "得力橡皮 4B",
                    "caption": "擦除干净｜不伤纸张｜办公学习必备",
                    "price": 1.20,
                    "cost_price": 0.70,
                    "market_price": 2.00,
                    "stock": 5800,
                    "specs": {"规格": "4B"},
                    "barcode": "6901234568312",
                    "shelf_life": 1825,
                },
                {
                    "name": "得力橡皮 2B 5块装",
                    "caption": "擦除干净｜不伤纸张｜办公学习必备",
                    "price": 4.50,
                    "cost_price": 2.80,
                    "market_price": 6.50,
                    "stock": 4000,
                    "specs": {"规格": "2B", "数量": "5块"},
                    "barcode": "6901234568313",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多文具类商品 - 文件夹 ====================
        
        # 晨光文件夹
        {
            "brand": "晨光",
            "category1": "文具",
            "category2": "文件夹",
            "category3": "资料夹",
            "spu_name": "晨光文件夹",
            "desc_detail": "晨光文件夹，坚固耐用，容量大，办公学习必备",
            "desc_pack": "包装清单：晨光文件夹",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "晨光文件夹 A4 蓝色",
                    "caption": "坚固耐用｜容量大｜办公学习必备",
                    "price": 5.90,
                    "cost_price": 3.50,
                    "market_price": 7.90,
                    "stock": 3000,
                    "specs": {"规格": "A4", "颜色": "蓝色"},
                    "barcode": "6901234568314",
                    "shelf_life": 1825,
                },
                {
                    "name": "晨光文件夹 A4 黑色",
                    "caption": "坚固耐用｜容量大｜办公学习必备",
                    "price": 5.90,
                    "cost_price": 3.50,
                    "market_price": 7.90,
                    "stock": 3000,
                    "specs": {"规格": "A4", "颜色": "黑色"},
                    "barcode": "6901234568315",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 得力文件夹
        {
            "brand": "得力",
            "category1": "文具",
            "category2": "文件夹",
            "category3": "资料夹",
            "spu_name": "得力文件夹",
            "desc_detail": "得力文件夹，坚固耐用，容量大，办公学习必备",
            "desc_pack": "包装清单：得力文件夹",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "得力文件夹 A4 蓝色",
                    "caption": "坚固耐用｜容量大｜办公学习必备",
                    "price": 4.90,
                    "cost_price": 3.00,
                    "market_price": 6.90,
                    "stock": 2800,
                    "specs": {"规格": "A4", "颜色": "蓝色"},
                    "barcode": "6901234568316",
                    "shelf_life": 1825,
                },
                {
                    "name": "得力文件夹 A5 蓝色",
                    "caption": "坚固耐用｜容量大｜办公学习必备",
                    "price": 3.90,
                    "cost_price": 2.50,
                    "market_price": 5.90,
                    "stock": 2600,
                    "specs": {"规格": "A5", "颜色": "蓝色"},
                    "barcode": "6901234568317",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多零食类商品 - 坚果 ====================
        
        # 三只松鼠坚果
        {
            "brand": "三只松鼠",
            "category1": "食品",
            "category2": "零食",
            "category3": "坚果",
            "spu_name": "三只松鼠坚果",
            "desc_detail": "三只松鼠坚果，香脆可口，营养丰富，休闲零食",
            "desc_pack": "包装清单：三只松鼠坚果",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "三只松鼠每日坚果 25g*7包",
                    "caption": "香脆可口｜营养丰富｜休闲零食",
                    "price": 39.90,
                    "cost_price": 25.00,
                    "market_price": 49.90,
                    "stock": 1500,
                    "specs": {"规格": "25g*7包"},
                    "barcode": "6901234568318",
                    "shelf_life": 180,
                },
                {
                    "name": "三只松鼠腰果 500g",
                    "caption": "香脆可口｜营养丰富｜休闲零食",
                    "price": 45.90,
                    "cost_price": 28.00,
                    "market_price": 58.90,
                    "stock": 1200,
                    "specs": {"规格": "500g"},
                    "barcode": "6901234568319",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 良品铺子坚果
        {
            "brand": "良品铺子",
            "category1": "食品",
            "category2": "零食",
            "category3": "坚果",
            "spu_name": "良品铺子坚果",
            "desc_detail": "良品铺子坚果，香脆可口，营养丰富，休闲零食",
            "desc_pack": "包装清单：良品铺子坚果",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "良品铺子每日坚果 25g*7包",
                    "caption": "香脆可口｜营养丰富｜休闲零食",
                    "price": 42.90,
                    "cost_price": 27.00,
                    "market_price": 52.90,
                    "stock": 1400,
                    "specs": {"规格": "25g*7包"},
                    "barcode": "6901234568320",
                    "shelf_life": 180,
                },
                {
                    "name": "良品铺子开心果 500g",
                    "caption": "香脆可口｜营养丰富｜休闲零食",
                    "price": 58.90,
                    "cost_price": 36.00,
                    "market_price": 72.90,
                    "stock": 1000,
                    "specs": {"规格": "500g"},
                    "barcode": "6901234568321",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 百草味坚果
        {
            "brand": "百草味",
            "category1": "食品",
            "category2": "零食",
            "category3": "坚果",
            "spu_name": "百草味坚果",
            "desc_detail": "百草味坚果，香脆可口，营养丰富，休闲零食",
            "desc_pack": "包装清单：百草味坚果",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "百草味每日坚果 25g*7包",
                    "caption": "香脆可口｜营养丰富｜休闲零食",
                    "price": 38.90,
                    "cost_price": 24.00,
                    "market_price": 48.90,
                    "stock": 1300,
                    "specs": {"规格": "25g*7包"},
                    "barcode": "6901234568322",
                    "shelf_life": 180,
                },
                {
                    "name": "百草味夏威夷果 500g",
                    "caption": "香脆可口｜营养丰富｜休闲零食",
                    "price": 52.90,
                    "cost_price": 32.00,
                    "market_price": 65.90,
                    "stock": 1100,
                    "specs": {"规格": "500g"},
                    "barcode": "6901234568323",
                    "shelf_life": 365,
                },
            ]
        },
        
        # ==================== 更多零食类商品 - 饼干 ====================
        
        # 奥利奥饼干
        {
            "brand": "奥利奥",
            "category1": "食品",
            "category2": "零食",
            "category3": "饼干",
            "spu_name": "奥利奥饼干",
            "desc_detail": "奥利奥饼干，香甜可口，夹心美味，休闲零食",
            "desc_pack": "包装清单：奥利奥饼干",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "奥利奥原味饼干 133g",
                    "caption": "香甜可口｜夹心美味｜休闲零食",
                    "price": 9.90,
                    "cost_price": 6.00,
                    "market_price": 12.90,
                    "stock": 2500,
                    "specs": {"规格": "133g", "口味": "原味"},
                    "barcode": "6901234568324",
                    "shelf_life": 365,
                },
                {
                    "name": "奥利奥草莓味饼干 133g",
                    "caption": "香甜可口｜夹心美味｜休闲零食",
                    "price": 10.90,
                    "cost_price": 6.50,
                    "market_price": 13.90,
                    "stock": 2300,
                    "specs": {"规格": "133g", "口味": "草莓味"},
                    "barcode": "6901234568325",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 乐事薯片
        {
            "brand": "乐事",
            "category1": "食品",
            "category2": "零食",
            "category3": "薯片",
            "spu_name": "乐事薯片",
            "desc_detail": "乐事薯片，香脆可口，多种口味，休闲零食",
            "desc_pack": "包装清单：乐事薯片",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "乐事原味薯片 70g",
                    "caption": "香脆可口｜多种口味｜休闲零食",
                    "price": 8.90,
                    "cost_price": 5.50,
                    "market_price": 11.90,
                    "stock": 2800,
                    "specs": {"规格": "70g", "口味": "原味"},
                    "barcode": "6901234568326",
                    "shelf_life": 180,
                },
                {
                    "name": "乐事番茄味薯片 70g",
                    "caption": "香脆可口｜多种口味｜休闲零食",
                    "price": 8.90,
                    "cost_price": 5.50,
                    "market_price": 11.90,
                    "stock": 2700,
                    "specs": {"规格": "70g", "口味": "番茄味"},
                    "barcode": "6901234568327",
                    "shelf_life": 180,
                },
            ]
        },
        
        # ==================== 更多日化类商品 - 洗衣液 ====================
        
        # 立白洗衣液
        {
            "brand": "立白",
            "category1": "日化",
            "category2": "洗涤用品",
            "category3": "洗衣液",
            "spu_name": "立白洗衣液",
            "desc_detail": "立白洗衣液，去污强，护色护衣，家庭必备",
            "desc_pack": "包装清单：立白洗衣液",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "立白洗衣液 2kg",
                    "caption": "去污强｜护色护衣｜家庭必备",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 36.90,
                    "stock": 2000,
                    "specs": {"规格": "2kg"},
                    "barcode": "6901234568328",
                    "shelf_life": 1825,
                },
                {
                    "name": "立白洗衣液 3kg",
                    "caption": "去污强｜护色护衣｜家庭必备",
                    "price": 42.90,
                    "cost_price": 27.00,
                    "market_price": 52.90,
                    "stock": 1700,
                    "specs": {"规格": "3kg"},
                    "barcode": "6901234568329",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 雕牌洗衣液
        {
            "brand": "雕牌",
            "category1": "日化",
            "category2": "洗涤用品",
            "category3": "洗衣液",
            "spu_name": "雕牌洗衣液",
            "desc_detail": "雕牌洗衣液，去污强，护色护衣，家庭必备",
            "desc_pack": "包装清单：雕牌洗衣液",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "雕牌洗衣液 2kg",
                    "caption": "去污强｜护色护衣｜家庭必备",
                    "price": 25.90,
                    "cost_price": 16.00,
                    "market_price": 32.90,
                    "stock": 1900,
                    "specs": {"规格": "2kg"},
                    "barcode": "6901234568330",
                    "shelf_life": 1825,
                },
                {
                    "name": "雕牌洗衣液 3kg",
                    "caption": "去污强｜护色护衣｜家庭必备",
                    "price": 38.90,
                    "cost_price": 24.00,
                    "market_price": 48.90,
                    "stock": 1600,
                    "specs": {"规格": "3kg"},
                    "barcode": "6901234568331",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 蓝月亮洗衣液
        {
            "brand": "蓝月亮",
            "category1": "日化",
            "category2": "洗涤用品",
            "category3": "洗衣液",
            "spu_name": "蓝月亮洗衣液",
            "desc_detail": "蓝月亮洗衣液，去污强，护色护衣，家庭必备",
            "desc_pack": "包装清单：蓝月亮洗衣液",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "蓝月亮洗衣液 1kg",
                    "caption": "去污强｜护色护衣｜家庭必备",
                    "price": 22.90,
                    "cost_price": 14.00,
                    "market_price": 28.90,
                    "stock": 2100,
                    "specs": {"规格": "1kg"},
                    "barcode": "6901234568332",
                    "shelf_life": 1825,
                },
                {
                    "name": "蓝月亮洗衣液 3kg",
                    "caption": "去污强｜护色护衣｜家庭必备",
                    "price": 58.90,
                    "cost_price": 36.00,
                    "market_price": 72.90,
                    "stock": 1500,
                    "specs": {"规格": "3kg"},
                    "barcode": "6901234568333",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多日化类商品 - 牙膏 ====================
        
        # 高露洁牙膏
        {
            "brand": "高露洁",
            "category1": "日化",
            "category2": "口腔护理",
            "category3": "牙膏",
            "spu_name": "高露洁牙膏",
            "desc_detail": "高露洁牙膏，清新口气，保护牙齿，日常护理",
            "desc_pack": "包装清单：高露洁牙膏",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "高露洁牙膏 120g",
                    "caption": "清新口气｜保护牙齿｜日常护理",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 3000,
                    "specs": {"规格": "120g"},
                    "barcode": "6901234568334",
                    "shelf_life": 1825,
                },
                {
                    "name": "高露洁牙膏 200g",
                    "caption": "清新口气｜保护牙齿｜日常护理",
                    "price": 18.90,
                    "cost_price": 12.00,
                    "market_price": 23.90,
                    "stock": 2500,
                    "specs": {"规格": "200g"},
                    "barcode": "6901234568335",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 佳洁士牙膏
        {
            "brand": "佳洁士",
            "category1": "日化",
            "category2": "口腔护理",
            "category3": "牙膏",
            "spu_name": "佳洁士牙膏",
            "desc_detail": "佳洁士牙膏，清新口气，保护牙齿，日常护理",
            "desc_pack": "包装清单：佳洁士牙膏",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "佳洁士牙膏 120g",
                    "caption": "清新口气｜保护牙齿｜日常护理",
                    "price": 13.90,
                    "cost_price": 8.50,
                    "market_price": 17.90,
                    "stock": 2800,
                    "specs": {"规格": "120g"},
                    "barcode": "6901234568336",
                    "shelf_life": 1825,
                },
                {
                    "name": "佳洁士牙膏 200g",
                    "caption": "清新口气｜保护牙齿｜日常护理",
                    "price": 19.90,
                    "cost_price": 12.50,
                    "market_price": 24.90,
                    "stock": 2300,
                    "specs": {"规格": "200g"},
                    "barcode": "6901234568337",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 黑人牙膏
        {
            "brand": "黑人",
            "category1": "日化",
            "category2": "口腔护理",
            "category3": "牙膏",
            "spu_name": "黑人牙膏",
            "desc_detail": "黑人牙膏，清新口气，美白牙齿，日常护理",
            "desc_pack": "包装清单：黑人牙膏",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "黑人牙膏 120g",
                    "caption": "清新口气｜美白牙齿｜日常护理",
                    "price": 14.90,
                    "cost_price": 9.00,
                    "market_price": 18.90,
                    "stock": 2700,
                    "specs": {"规格": "120g"},
                    "barcode": "6901234568338",
                    "shelf_life": 1825,
                },
                {
                    "name": "黑人牙膏 200g",
                    "caption": "清新口气｜美白牙齿｜日常护理",
                    "price": 20.90,
                    "cost_price": 13.00,
                    "market_price": 25.90,
                    "stock": 2200,
                    "specs": {"规格": "200g"},
                    "barcode": "6901234568339",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多日化类商品 - 牙刷 ====================
        
        # 欧乐B牙刷
        {
            "brand": "欧乐B",
            "category1": "日化",
            "category2": "口腔护理",
            "category3": "牙刷",
            "spu_name": "欧乐B牙刷",
            "desc_detail": "欧乐B牙刷，刷毛柔软，清洁彻底，日常护理",
            "desc_pack": "包装清单：欧乐B牙刷",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "欧乐B牙刷 2支装",
                    "caption": "刷毛柔软｜清洁彻底｜日常护理",
                    "price": 18.90,
                    "cost_price": 12.00,
                    "market_price": 23.90,
                    "stock": 2500,
                    "specs": {"规格": "2支装"},
                    "barcode": "6901234568340",
                    "shelf_life": 1825,
                },
                {
                    "name": "欧乐B牙刷 4支装",
                    "caption": "刷毛柔软｜清洁彻底｜日常护理",
                    "price": 35.90,
                    "cost_price": 22.00,
                    "market_price": 45.90,
                    "stock": 2000,
                    "specs": {"规格": "4支装"},
                    "barcode": "6901234568341",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # 高露洁牙刷
        {
            "brand": "高露洁",
            "category1": "日化",
            "category2": "口腔护理",
            "category3": "牙刷",
            "spu_name": "高露洁牙刷",
            "desc_detail": "高露洁牙刷，刷毛柔软，清洁彻底，日常护理",
            "desc_pack": "包装清单：高露洁牙刷",
            "desc_service": "7天无理由退货",
            "skus": [
                {
                    "name": "高露洁牙刷 2支装",
                    "caption": "刷毛柔软｜清洁彻底｜日常护理",
                    "price": 15.90,
                    "cost_price": 10.00,
                    "market_price": 20.90,
                    "stock": 2400,
                    "specs": {"规格": "2支装"},
                    "barcode": "6901234568342",
                    "shelf_life": 1825,
                },
                {
                    "name": "高露洁牙刷 4支装",
                    "caption": "刷毛柔软｜清洁彻底｜日常护理",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 36.90,
                    "stock": 1900,
                    "specs": {"规格": "4支装"},
                    "barcode": "6901234568343",
                    "shelf_life": 1825,
                },
            ]
        },
        
        # ==================== 更多饮料类商品 - 果汁 ====================
        
        # 美汁源果汁
        {
            "brand": "美汁源",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "果汁",
            "spu_name": "美汁源果汁",
            "desc_detail": "美汁源果汁，鲜榨口感，营养丰富，健康饮品",
            "desc_pack": "包装清单：美汁源果汁",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "美汁源橙汁 450ml",
                    "caption": "鲜榨口感｜营养丰富｜健康饮品",
                    "price": 6.90,
                    "cost_price": 4.50,
                    "market_price": 8.90,
                    "stock": 3000,
                    "specs": {"规格": "450ml", "口味": "橙汁"},
                    "barcode": "6901234568344",
                    "shelf_life": 180,
                },
                {
                    "name": "美汁源橙汁 1.25L",
                    "caption": "鲜榨口感｜营养丰富｜家庭装",
                    "price": 12.90,
                    "cost_price": 8.00,
                    "market_price": 16.90,
                    "stock": 2000,
                    "specs": {"规格": "1.25L", "口味": "橙汁"},
                    "barcode": "6901234568345",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 农夫果园果汁
        {
            "brand": "农夫果园",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "果汁",
            "spu_name": "农夫果园果汁",
            "desc_detail": "农夫果园果汁，鲜榨口感，营养丰富，健康饮品",
            "desc_pack": "包装清单：农夫果园果汁",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "农夫果园混合果汁 500ml",
                    "caption": "鲜榨口感｜营养丰富｜健康饮品",
                    "price": 7.90,
                    "cost_price": 5.00,
                    "market_price": 9.90,
                    "stock": 2800,
                    "specs": {"规格": "500ml", "口味": "混合"},
                    "barcode": "6901234568346",
                    "shelf_life": 180,
                },
                {
                    "name": "农夫果园混合果汁 1L",
                    "caption": "鲜榨口感｜营养丰富｜家庭装",
                    "price": 13.90,
                    "cost_price": 8.50,
                    "market_price": 17.90,
                    "stock": 1900,
                    "specs": {"规格": "1L", "口味": "混合"},
                    "barcode": "6901234568347",
                    "shelf_life": 180,
                },
            ]
        },
        
        # 汇源果汁
        {
            "brand": "汇源",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "果汁",
            "spu_name": "汇源果汁",
            "desc_detail": "汇源果汁，鲜榨口感，营养丰富，健康饮品",
            "desc_pack": "包装清单：汇源果汁",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "汇源100%果汁 1L",
                    "caption": "鲜榨口感｜营养丰富｜健康饮品",
                    "price": 15.90,
                    "cost_price": 10.00,
                    "market_price": 19.90,
                    "stock": 1800,
                    "specs": {"规格": "1L", "口味": "橙汁"},
                    "barcode": "6901234568348",
                    "shelf_life": 365,
                },
                {
                    "name": "汇源100%果汁 2L",
                    "caption": "鲜榨口感｜营养丰富｜家庭装",
                    "price": 28.90,
                    "cost_price": 18.00,
                    "market_price": 36.90,
                    "stock": 1200,
                    "specs": {"规格": "2L", "口味": "橙汁"},
                    "barcode": "6901234568349",
                    "shelf_life": 365,
                },
            ]
        },
        
        # ==================== 更多饮料类商品 - 功能饮料 ====================
        
        # 红牛功能饮料
        {
            "brand": "红牛",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "功能饮料",
            "spu_name": "红牛功能饮料",
            "desc_detail": "红牛功能饮料，提神醒脑，补充能量，运动必备",
            "desc_pack": "包装清单：红牛功能饮料",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "红牛功能饮料 250ml",
                    "caption": "提神醒脑｜补充能量｜运动必备",
                    "price": 6.50,
                    "cost_price": 4.00,
                    "market_price": 8.50,
                    "stock": 4000,
                    "specs": {"规格": "250ml"},
                    "barcode": "6901234568350",
                    "shelf_life": 365,
                },
                {
                    "name": "红牛功能饮料 250ml*24罐",
                    "caption": "提神醒脑｜补充能量｜整箱装",
                    "price": 145.90,
                    "cost_price": 90.00,
                    "market_price": 185.90,
                    "stock": 800,
                    "specs": {"规格": "250ml*24罐"},
                    "barcode": "6901234568351",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 东鹏特饮
        {
            "brand": "东鹏特饮",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "功能饮料",
            "spu_name": "东鹏特饮",
            "desc_detail": "东鹏特饮，提神醒脑，补充能量，运动必备",
            "desc_pack": "包装清单：东鹏特饮",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "东鹏特饮 250ml",
                    "caption": "提神醒脑｜补充能量｜运动必备",
                    "price": 5.50,
                    "cost_price": 3.50,
                    "market_price": 7.50,
                    "stock": 3800,
                    "specs": {"规格": "250ml"},
                    "barcode": "6901234568352",
                    "shelf_life": 365,
                },
                {
                    "name": "东鹏特饮 250ml*24罐",
                    "caption": "提神醒脑｜补充能量｜整箱装",
                    "price": 125.90,
                    "cost_price": 78.00,
                    "market_price": 160.90,
                    "stock": 750,
                    "specs": {"规格": "250ml*24罐"},
                    "barcode": "6901234568353",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 乐虎功能饮料
        {
            "brand": "乐虎",
            "category1": "食品",
            "category2": "牛奶饮料",
            "category3": "功能饮料",
            "spu_name": "乐虎功能饮料",
            "desc_detail": "乐虎功能饮料，提神醒脑，补充能量，运动必备",
            "desc_pack": "包装清单：乐虎功能饮料",
            "desc_service": "7天无理由退货，过期包赔",
            "skus": [
                {
                    "name": "乐虎功能饮料 380ml",
                    "caption": "提神醒脑｜补充能量｜运动必备",
                    "price": 6.00,
                    "cost_price": 3.80,
                    "market_price": 8.00,
                    "stock": 3500,
                    "specs": {"规格": "380ml"},
                    "barcode": "6901234568354",
                    "shelf_life": 365,
                },
                {
                    "name": "乐虎功能饮料 380ml*15瓶",
                    "caption": "提神醒脑｜补充能量｜整箱装",
                    "price": 85.90,
                    "cost_price": 53.00,
                    "market_price": 110.90,
                    "stock": 700,
                    "specs": {"规格": "380ml*15瓶"},
                    "barcode": "6901234568355",
                    "shelf_life": 365,
                },
            ]
        },
        
        # ==================== 更多酒水类商品 - 啤酒 ====================
        
        # 青岛啤酒
        {
            "brand": "青岛啤酒",
            "category1": "酒水",
            "category2": "啤酒",
            "category3": "拉格啤酒",
            "spu_name": "青岛啤酒",
            "desc_detail": "青岛啤酒，清爽口感，经典品质，聚会必备",
            "desc_pack": "包装清单：青岛啤酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "青岛啤酒 500ml",
                    "caption": "清爽口感｜经典品质｜聚会必备",
                    "price": 5.90,
                    "cost_price": 3.50,
                    "market_price": 7.90,
                    "stock": 5000,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568356",
                    "shelf_life": 365,
                },
                {
                    "name": "青岛啤酒 500ml*12罐",
                    "caption": "清爽口感｜经典品质｜整箱装",
                    "price": 68.90,
                    "cost_price": 40.00,
                    "market_price": 88.90,
                    "stock": 1500,
                    "specs": {"规格": "500ml*12罐"},
                    "barcode": "6901234568357",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 雪花啤酒
        {
            "brand": "雪花啤酒",
            "category1": "酒水",
            "category2": "啤酒",
            "category3": "拉格啤酒",
            "spu_name": "雪花啤酒",
            "desc_detail": "雪花啤酒，清爽口感，经典品质，聚会必备",
            "desc_pack": "包装清单：雪花啤酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "雪花啤酒 500ml",
                    "caption": "清爽口感｜经典品质｜聚会必备",
                    "price": 4.90,
                    "cost_price": 3.00,
                    "market_price": 6.90,
                    "stock": 4800,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568358",
                    "shelf_life": 365,
                },
                {
                    "name": "雪花啤酒 500ml*12罐",
                    "caption": "清爽口感｜经典品质｜整箱装",
                    "price": 58.90,
                    "cost_price": 35.00,
                    "market_price": 75.90,
                    "stock": 1400,
                    "specs": {"规格": "500ml*12罐"},
                    "barcode": "6901234568359",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 燕京啤酒
        {
            "brand": "燕京啤酒",
            "category1": "酒水",
            "category2": "啤酒",
            "category3": "拉格啤酒",
            "spu_name": "燕京啤酒",
            "desc_detail": "燕京啤酒，清爽口感，经典品质，聚会必备",
            "desc_pack": "包装清单：燕京啤酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "燕京啤酒 500ml",
                    "caption": "清爽口感｜经典品质｜聚会必备",
                    "price": 5.50,
                    "cost_price": 3.30,
                    "market_price": 7.50,
                    "stock": 4600,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568360",
                    "shelf_life": 365,
                },
                {
                    "name": "燕京啤酒 500ml*12罐",
                    "caption": "清爽口感｜经典品质｜整箱装",
                    "price": 63.90,
                    "cost_price": 38.00,
                    "market_price": 82.90,
                    "stock": 1300,
                    "specs": {"规格": "500ml*12罐"},
                    "barcode": "6901234568361",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 百威啤酒
        {
            "brand": "百威啤酒",
            "category1": "酒水",
            "category2": "啤酒",
            "category3": "拉格啤酒",
            "spu_name": "百威啤酒",
            "desc_detail": "百威啤酒，清爽口感，国际品质，聚会必备",
            "desc_pack": "包装清单：百威啤酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "百威啤酒 330ml",
                    "caption": "清爽口感｜国际品质｜聚会必备",
                    "price": 6.90,
                    "cost_price": 4.20,
                    "market_price": 9.90,
                    "stock": 4000,
                    "specs": {"规格": "330ml"},
                    "barcode": "6901234568362",
                    "shelf_life": 365,
                },
                {
                    "name": "百威啤酒 330ml*24罐",
                    "caption": "清爽口感｜国际品质｜整箱装",
                    "price": 158.90,
                    "cost_price": 95.00,
                    "market_price": 205.90,
                    "stock": 1000,
                    "specs": {"规格": "330ml*24罐"},
                    "barcode": "6901234568363",
                    "shelf_life": 365,
                },
            ]
        },
        
        # 喜力啤酒
        {
            "brand": "喜力啤酒",
            "category1": "酒水",
            "category2": "啤酒",
            "category3": "拉格啤酒",
            "spu_name": "喜力啤酒",
            "desc_detail": "喜力啤酒，清爽口感，国际品质，聚会必备",
            "desc_pack": "包装清单：喜力啤酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "喜力啤酒 330ml",
                    "caption": "清爽口感｜国际品质｜聚会必备",
                    "price": 8.90,
                    "cost_price": 5.50,
                    "market_price": 11.90,
                    "stock": 3500,
                    "specs": {"规格": "330ml"},
                    "barcode": "6901234568364",
                    "shelf_life": 365,
                },
                {
                    "name": "喜力啤酒 330ml*24罐",
                    "caption": "清爽口感｜国际品质｜整箱装",
                    "price": 205.90,
                    "cost_price": 125.00,
                    "market_price": 265.90,
                    "stock": 800,
                    "specs": {"规格": "330ml*24罐"},
                    "barcode": "6901234568365",
                    "shelf_life": 365,
                },
            ]
        },
        
        # ==================== 更多酒水类商品 - 红酒 ====================
        
        # 长城红酒
        {
            "brand": "长城",
            "category1": "酒水",
            "category2": "红酒",
            "category3": "干红",
            "spu_name": "长城红酒",
            "desc_detail": "长城红酒，醇厚口感，中国名酒，高端礼品",
            "desc_pack": "包装清单：长城红酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "长城干红 750ml",
                    "caption": "醇厚口感｜中国名酒｜高端礼品",
                    "price": 88.00,
                    "cost_price": 55.00,
                    "market_price": 110.00,
                    "stock": 800,
                    "specs": {"规格": "750ml"},
                    "barcode": "6901234568366",
                    "shelf_life": 3650,
                },
                {
                    "name": "长城干红 750ml*2瓶",
                    "caption": "醇厚口感｜中国名酒｜礼盒装",
                    "price": 168.00,
                    "cost_price": 105.00,
                    "market_price": 210.00,
                    "stock": 500,
                    "specs": {"规格": "750ml*2瓶"},
                    "barcode": "6901234568367",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 张裕红酒
        {
            "brand": "张裕",
            "category1": "酒水",
            "category2": "红酒",
            "category3": "干红",
            "spu_name": "张裕红酒",
            "desc_detail": "张裕红酒，醇厚口感，中国名酒，高端礼品",
            "desc_pack": "包装清单：张裕红酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "张裕干红 750ml",
                    "caption": "醇厚口感｜中国名酒｜高端礼品",
                    "price": 98.00,
                    "cost_price": 60.00,
                    "market_price": 125.00,
                    "stock": 750,
                    "specs": {"规格": "750ml"},
                    "barcode": "6901234568368",
                    "shelf_life": 3650,
                },
                {
                    "name": "张裕干红 750ml*2瓶",
                    "caption": "醇厚口感｜中国名酒｜礼盒装",
                    "price": 188.00,
                    "cost_price": 115.00,
                    "market_price": 235.00,
                    "stock": 450,
                    "specs": {"规格": "750ml*2瓶"},
                    "barcode": "6901234568369",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # ==================== 更多酒水类商品 - 白酒 ====================
        
        # 茅台白酒
        {
            "brand": "茅台",
            "category1": "酒水",
            "category2": "白酒",
            "category3": "酱香型",
            "spu_name": "茅台白酒",
            "desc_detail": "茅台白酒，酱香浓郁，中国国酒，高端礼品",
            "desc_pack": "包装清单：茅台白酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "茅台飞天 500ml",
                    "caption": "酱香浓郁｜中国国酒｜高端礼品",
                    "price": 1499.00,
                    "cost_price": 950.00,
                    "market_price": 1880.00,
                    "stock": 200,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568370",
                    "shelf_life": 3650,
                },
                {
                    "name": "茅台王子酒 500ml",
                    "caption": "酱香浓郁｜中国名酒｜中端礼品",
                    "price": 288.00,
                    "cost_price": 180.00,
                    "market_price": 360.00,
                    "stock": 500,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568371",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 五粮液白酒
        {
            "brand": "五粮液",
            "category1": "酒水",
            "category2": "白酒",
            "category3": "浓香型",
            "spu_name": "五粮液白酒",
            "desc_detail": "五粮液白酒，浓香醇厚，中国名酒，高端礼品",
            "desc_pack": "包装清单：五粮液白酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "五粮液普五 500ml",
                    "caption": "浓香醇厚｜中国名酒｜高端礼品",
                    "price": 1099.00,
                    "cost_price": 700.00,
                    "market_price": 1380.00,
                    "stock": 250,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568372",
                    "shelf_life": 3650,
                },
                {
                    "name": "五粮液1618 500ml",
                    "caption": "浓香醇厚｜中国名酒｜高端礼品",
                    "price": 1299.00,
                    "cost_price": 830.00,
                    "market_price": 1630.00,
                    "stock": 200,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568373",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 剑南春白酒
        {
            "brand": "剑南春",
            "category1": "酒水",
            "category2": "白酒",
            "category3": "浓香型",
            "spu_name": "剑南春白酒",
            "desc_detail": "剑南春白酒，浓香醇厚，中国名酒，高端礼品",
            "desc_pack": "包装清单：剑南春白酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "剑南春水晶剑 500ml",
                    "caption": "浓香醇厚｜中国名酒｜高端礼品",
                    "price": 458.00,
                    "cost_price": 290.00,
                    "market_price": 575.00,
                    "stock": 400,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568374",
                    "shelf_life": 3650,
                },
                {
                    "name": "剑南春珍藏级 500ml",
                    "caption": "浓香醇厚｜中国名酒｜高端礼品",
                    "price": 588.00,
                    "cost_price": 375.00,
                    "market_price": 735.00,
                    "stock": 350,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568375",
                    "shelf_life": 3650,
                },
            ]
        },
        
        # 泸州老窖白酒
        {
            "brand": "泸州老窖",
            "category1": "酒水",
            "category2": "白酒",
            "category3": "浓香型",
            "spu_name": "泸州老窖白酒",
            "desc_detail": "泸州老窖白酒，浓香醇厚，中国名酒，高端礼品",
            "desc_pack": "包装清单：泸州老窖白酒",
            "desc_service": "7天无理由退货，正品保证",
            "skus": [
                {
                    "name": "泸州老窖特曲 500ml",
                    "caption": "浓香醇厚｜中国名酒｜高端礼品",
                    "price": 388.00,
                    "cost_price": 245.00,
                    "market_price": 485.00,
                    "stock": 450,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568376",
                    "shelf_life": 3650,
                },
                {
                    "name": "泸州老窖国窖1573 500ml",
                    "caption": "浓香醇厚｜中国名酒｜高端礼品",
                    "price": 899.00,
                    "cost_price": 570.00,
                    "market_price": 1125.00,
                    "stock": 300,
                    "specs": {"规格": "500ml"},
                    "barcode": "6901234568377",
                    "shelf_life": 3650,
                },
            ]
        },
    ]
}


def get_or_create_category(name, parent=None):
    """获取或创建商品类别"""
    try:
        category = GoodsCategory.objects.get(name=name, parent=parent)
        return category
    except GoodsCategory.DoesNotExist:
        category = GoodsCategory.objects.create(name=name, parent=parent)
        return category


def get_or_create_brand(brand_data):
    """获取或创建品牌"""
    try:
        brand = Brand.objects.get(name=brand_data["name"])
        return brand
    except Brand.DoesNotExist:
        # 创建品牌（暂时不设置logo，因为没有实际图片文件）
        brand = Brand.objects.create(
            name=brand_data["name"],
            first_letter=brand_data["first_letter"]
        )
        return brand


def import_goods():
    """导入商品数据"""
    print("开始导入京东风格商品数据...")
    
    with transaction.atomic():
        # 导入品牌
        print("导入品牌...")
        brand_map = {}
        for brand_data in JD_GOODS_DATA["brands"]:
            brand = get_or_create_brand(brand_data)
            brand_map[brand.name] = brand
            print(f"  品牌: {brand.name}")
        
        # 导入商品
        print("导入商品SPU和SKU...")
        for product_data in JD_GOODS_DATA["products"]:
            brand = brand_map[product_data["brand"]]
            
            # 获取或创建类别
            category1 = get_or_create_category(product_data["category1"])
            category2 = get_or_create_category(product_data["category2"], category1)
            category3 = get_or_create_category(product_data["category3"], category2)
            
            # 检查SPU是否已存在（处理重复数据）
            existing_spus = SPU.objects.filter(
                name=product_data["spu_name"],
                brand=brand,
                category1=category1,
                category2=category2,
                category3=category3
            )
            
            if existing_spus.exists():
                # 如果存在多个，取第一个并跳过其他重复的
                spu = existing_spus.first()
                if existing_spus.count() > 1:
                    print(f"  SPU: {spu.name} (跳过{existing_spus.count()-1}个重复)")
                
                # 更新已存在的SPU
                spu.desc_detail = product_data["desc_detail"]
                spu.desc_pack = product_data["desc_pack"]
                spu.desc_service = product_data["desc_service"]
                spu.save()
                print(f"  SPU: {spu.name} (更新)")
                spu_created = False
            else:
                # 创建新的SPU
                spu = SPU.objects.create(
                    name=product_data["spu_name"],
                    brand=brand,
                    category1=category1,
                    category2=category2,
                    category3=category3,
                    sales=random.randint(100, 10000),
                    comments=random.randint(50, 500),
                    desc_detail=product_data["desc_detail"],
                    desc_pack=product_data["desc_pack"],
                    desc_service=product_data["desc_service"]
                )
                print(f"  SPU: {spu.name} (新建)")
                spu_created = True
            
            # 创建或更新规格
            spec_map = {}
            for sku_data in product_data["skus"]:
                for spec_name, spec_value in sku_data["specs"].items():
                    # 获取或创建SPU规格
                    if spec_name not in spec_map:
                        spu_spec, created = SPUSpecification.objects.get_or_create(
                            spu=spu,
                            name=spec_name
                        )
                        spec_map[spec_name] = spu_spec
                    
                    # 获取或创建规格选项
                    spec_option, created = SpecificationOption.objects.get_or_create(
                        spec=spec_map[spec_name],
                        value=spec_value
                    )
            
            # 创建或更新SKU
            for sku_data in product_data["skus"]:
                # 设置生产日期和保质期
                production_date = datetime.now().date() - timedelta(days=random.randint(30, 180))
                shelf_life = sku_data.get("shelf_life", 0)
                expiration_date = None
                if shelf_life > 0:
                    expiration_date = production_date + timedelta(days=shelf_life)
                
                barcode = sku_data.get("barcode", "")
                
                # 检查SKU是否已存在（通过SPU和名称或条码）
                sku_filters = {'spu': spu, 'name': sku_data["name"]}
                if barcode:
                    sku_filters['barcode'] = barcode
                
                existing_skus = SKU.objects.filter(**sku_filters)
                
                if existing_skus.exists():
                    # 如果存在多个，取第一个并跳过其他重复的
                    sku = existing_skus.first()
                    if existing_skus.count() > 1:
                        print(f"    SKU: {sku.name} - ¥{sku.price} (跳过{existing_skus.count()-1}个重复)")
                    
                    # 更新已存在的SKU
                    sku.caption = sku_data["caption"]
                    sku.category = category3
                    sku.price = sku_data["price"]
                    sku.cost_price = sku_data["cost_price"]
                    sku.market_price = sku_data["market_price"]
                    sku.stock = sku_data["stock"]
                    sku.production_date = production_date
                    sku.shelf_life = shelf_life
                    sku.expiration_date = expiration_date
                    if barcode:
                        sku.barcode = barcode
                    sku.save()
                    print(f"    SKU: {sku.name} - ¥{sku.price} (更新)")
                    sku_created = False
                else:
                    # 创建新的SKU
                    sku = SKU.objects.create(
                        name=sku_data["name"],
                        caption=sku_data["caption"],
                        spu=spu,
                        category=category3,
                        price=sku_data["price"],
                        cost_price=sku_data["cost_price"],
                        market_price=sku_data["market_price"],
                        stock=sku_data["stock"],
                        sales=random.randint(10, 1000),
                        comments=random.randint(5, 200),
                        is_launched=True,
                        production_date=production_date,
                        shelf_life=shelf_life,
                        expiration_date=expiration_date,
                        barcode=barcode
                    )
                    print(f"    SKU: {sku.name} - ¥{sku.price} (新建)")
                    sku_created = True
                
                # 创建SKU规格关联（先删除旧的，再创建新的）
                SKUSpecification.objects.filter(sku=sku).delete()
                for spec_name, spec_value in sku_data["specs"].items():
                    spu_spec = spec_map[spec_name]
                    spec_option = SpecificationOption.objects.get(
                        spec=spu_spec,
                        value=spec_value
                    )
                    SKUSpecification.objects.create(
                        sku=sku,
                        spec=spu_spec,
                        option=spec_option
                    )
    
    print("京东风格商品数据导入完成！")
    print(f"品牌总数: {Brand.objects.count()}")
    print(f"SPU总数: {SPU.objects.count()}")
    print(f"SKU总数: {SKU.objects.count()}")


# 自动执行导入
import_goods()
