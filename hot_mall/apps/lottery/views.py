from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.db import IntegrityError
from django.middleware.csrf import get_token
from .models import PrizeLevel, Prize, LotteryRecord
from goods.models import SKU
import json
import random
from django.db import IntegrityError


class PrizeLevelListView(LoginRequiredMixin, View):
    """中奖等级列表【页面】"""

    def get(self, request):
        prize_levels = PrizeLevel.objects.all().order_by('level')
        context = {
            'prize_levels': prize_levels,
            'csrf_token': get_token(request),
            'left_menu_active': 'lottery-prize-level',
            'is_superuser': request.user.is_superuser
        }
        return render(request, 'lottery/prize_level_list.html', context)


class PrizeLevelAddView(LoginRequiredMixin, View):
    """添加中奖等级【页面表单】"""

    def get(self, request):
        context = {
            'prize_level': None,
            'csrf_token': get_token(request),
            'left_menu_active': 'lottery-prize-level',
            'is_superuser': request.user.is_superuser
        }
        return render(request, 'lottery/prize_level_form.html', context)

    def post(self, request):
        name = request.POST.get('name', '').strip()
        level = request.POST.get('level', '')
        probability = request.POST.get('probability', '')
        color = request.POST.get('color', '#FF6B6B').strip()
        form_errors = []

        # 参数校验
        if not name:
            form_errors.append("等级名称不能为空")
        try:
            level = int(level)
            if level < 1:
                form_errors.append("等级序号必须大于0")
        except (ValueError, TypeError):
            form_errors.append("等级序号必须为有效数字")

        try:
            probability = float(probability)
            if not (0 <= probability <= 100):
                form_errors.append("中奖概率范围：0 ~ 100")
        except (ValueError, TypeError):
            form_errors.append("中奖概率格式错误")

        if form_errors:
            # ✅ 修复：构建临时模型对象，不再传递字典，前端模板正常取值回填
            temp_obj = PrizeLevel()
            temp_obj.name = name
            temp_obj.level = level
            temp_obj.probability = probability
            temp_obj.color = color
            context = {
                'form_errors': form_errors,
                'prize_level': temp_obj,
                'csrf_token': get_token(request),
                'left_menu_active': 'lottery-prize-level',
                'is_superuser': request.user.is_superuser
            }
            return render(request, 'lottery/prize_level_form.html', context)

        try:
            PrizeLevel.objects.create(name=name, level=level, probability=probability, color=color)
        except IntegrityError:
            form_errors.append("等级序号不能重复！")
            # ✅ 唯一索引冲突时同样使用临时对象回填表单
            temp_obj = PrizeLevel()
            temp_obj.name = name
            temp_obj.level = level
            temp_obj.probability = probability
            temp_obj.color = color
            context = {
                'form_errors': form_errors,
                'prize_level': temp_obj,
                'csrf_token': get_token(request),
                'left_menu_active': 'lottery-prize-level',
                'is_superuser': request.user.is_superuser
            }
            return render(request, 'lottery/prize_level_form.html', context)
        return redirect('lottery:prize_level_list')


class PrizeLevelEditView(LoginRequiredMixin, View):
    """编辑中奖等级【页面表单】"""

    def get(self, request, pk):
        try:
            prize_level = PrizeLevel.objects.get(pk=pk)
        except PrizeLevel.DoesNotExist:
            return redirect('lottery:prize_level_list')
        context = {
            'prize_level': prize_level,
            'csrf_token': get_token(request),
            'left_menu_active': 'lottery-prize-level',
            'is_superuser': request.user.is_superuser
        }
        return render(request, 'lottery/prize_level_form.html', context)

    def post(self, request, pk):
        try:
            prize_level = PrizeLevel.objects.get(pk=pk)
        except PrizeLevel.DoesNotExist:
            return redirect('lottery:prize_level_list')

        name = request.POST.get('name', '').strip()
        level = request.POST.get('level', '')
        probability = request.POST.get('probability', '')
        color = request.POST.get('color', '#FF6B6B').strip()
        form_errors = []

        if not name:
            form_errors.append("等级名称不能为空")
        try:
            level = int(level)
            if level < 1:
                form_errors.append("等级序号必须大于0")
        except (ValueError, TypeError):
            form_errors.append("等级序号必须为有效数字")

        try:
            probability = float(probability)
            if not (0 <= probability <= 100):
                form_errors.append("中奖概率范围：0 ~ 100")
        except (ValueError, TypeError):
            form_errors.append("中奖概率格式错误")

        if form_errors:
            prize_level.name = name
            prize_level.level = level
            prize_level.probability = probability
            prize_level.color = color
            context = {
                'form_errors': form_errors,
                'prize_level': prize_level,
                'csrf_token': get_token(request),
                'left_menu_active': 'lottery-prize-level',
                'is_superuser': request.user.is_superuser
            }
            return render(request, 'lottery/prize_level_form.html', context)
        prize_level.name = name
        prize_level.level = level
        prize_level.probability = probability
        prize_level.color = color
        try:
            prize_level.save()
        except IntegrityError:
            form_errors.append("等级序号不能与其他等级重复！")
            context = {
                'form_errors': form_errors,
                'prize_level': prize_level,
                'csrf_token': get_token(request),
                'left_menu_active': 'lottery-prize-level',
                'is_superuser': request.user.is_superuser
            }
            return render(request, 'lottery/prize_level_form.html', context)
        return redirect('lottery:prize_level_list')


# ===================== AJAX 异步删除接口（前端JS调用） =====================
class PrizeLevelDeleteAjaxView(LoginRequiredMixin, View):
    """AJAX删除中奖等级，返回JSON"""

    def post(self, request):
        level_id = request.POST.get("id")
        try:
            level_id = int(level_id)
            level_obj = PrizeLevel.objects.get(pk=level_id)
        except (ValueError, PrizeLevel.DoesNotExist):
            return JsonResponse({"code": 1, "msg": "数据不存在"})

        # 业务约束：存在绑定奖品禁止删除
        if Prize.objects.filter(prize_level=level_obj).exists():
            return JsonResponse({"code": 1, "msg": "该等级已绑定奖品，禁止删除！"})

        level_obj.delete()
        return JsonResponse({"code": 0, "msg": "ok"})


class PrizeDeleteAjaxView(LoginRequiredMixin, View):
    """AJAX删除奖品，返回JSON"""

    def post(self, request):
        prize_id = request.POST.get("id")
        try:
            prize_id = int(prize_id)
            prize_obj = Prize.objects.get(pk=prize_id)
        except (ValueError, Prize.DoesNotExist):
            return JsonResponse({"code": 1, "msg": "奖品不存在"})

        # 【后续扩展】这里可以增加判断：存在中奖记录则禁止删除
        # if LotteryRecord.objects.filter(prize=prize_obj).exists():
        #     return JsonResponse({"code":1,"msg":"已有用户中奖，禁止删除"})

        prize_obj.delete()
        return JsonResponse({"code": 0, "msg": "ok"})


# ===================== 奖品管理页面视图 =====================
class PrizeListView(LoginRequiredMixin, View):
    """奖品列表页面"""

    def get(self, request):
        prizes = Prize.objects.select_related('prize_level', 'sku').all()
        context = {
            'prizes': prizes,
            'csrf_token': get_token(request),
            'left_menu_active': 'lottery-prize',
            'is_superuser': request.user.is_superuser
        }
        return render(request, 'lottery/prize_list.html', context)


class PrizeAddView(LoginRequiredMixin, View):
    """添加奖品页面"""

    def get(self, request):
        prize_levels = PrizeLevel.objects.all().order_by("level")
        skus = SKU.objects.all()
        context = {
            'prize_levels': prize_levels,
            'skus': skus,
            'csrf_token': get_token(request),
            'left_menu_active': 'lottery-prize',
            'is_superuser': request.user.is_superuser
        }
        return render(request, 'lottery/prize_form.html', context)

    def post(self, request):
        prize_level_id = request.POST.get('prize_level')
        sku_id = request.POST.get('sku')
        quantity = request.POST.get('quantity')
        form_errors = []

        try:
            quantity = int(quantity)
            if quantity < 1:
                form_errors.append("奖品数量不能小于1")
        except (ValueError, TypeError):
            form_errors.append("奖品数量必须是正整数")

        try:
            PrizeLevel.objects.get(pk=prize_level_id)
        except PrizeLevel.DoesNotExist:
            form_errors.append("选中的中奖等级不存在")

        try:
            SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            form_errors.append("选中商品不存在")

        if form_errors:
            prize_levels = PrizeLevel.objects.all()
            skus = SKU.objects.all()
            context = {
                'form_errors': form_errors,
                'prize_levels': prize_levels,
                'skus': skus,
                'prize': {
                    "prize_level_id": prize_level_id,
                    "sku_id": sku_id,
                    "quantity": quantity
                },
                'csrf_token': get_token(request),
                'left_menu_active': 'lottery-prize',
                'is_superuser': request.user.is_superuser
            }
            return render(request, 'lottery/prize_form.html', context)

        Prize.objects.create(prize_level_id=prize_level_id, sku_id=sku_id, quantity=quantity)
        return redirect('lottery:prize_list')


class PrizeEditView(LoginRequiredMixin, View):
    """编辑奖品页面"""

    def get(self, request, pk):
        try:
            prize = Prize.objects.select_related('prize_level', 'sku').get(pk=pk)
        except Prize.DoesNotExist:
            return redirect('lottery:prize_list')
        prize_levels = PrizeLevel.objects.all().order_by("level")
        skus = SKU.objects.all()
        context = {
            'prize': prize,
            'prize_levels': prize_levels,
            'skus': skus,
            'csrf_token': get_token(request),
            'left_menu_active': 'lottery-prize',
            'is_superuser': request.user.is_superuser
        }
        return render(request, 'lottery/prize_form.html', context)

    def post(self, request, pk):
        try:
            prize = Prize.objects.get(pk=pk)
        except Prize.DoesNotExist:
            return redirect('lottery:prize_list')

        prize_level_id = request.POST.get('prize_level')
        sku_id = request.POST.get('sku')
        quantity = request.POST.get('quantity')
        form_errors = []

        try:
            quantity = int(quantity)
            if quantity < 1:
                form_errors.append("奖品数量不能小于1")
        except (ValueError, TypeError):
            form_errors.append("奖品数量必须是正整数")

        try:
            PrizeLevel.objects.get(pk=prize_level_id)
        except PrizeLevel.DoesNotExist:
            form_errors.append("选中的中奖等级不存在")
        try:
            SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            form_errors.append("选中商品不存在")

        if form_errors:
            prize_levels = PrizeLevel.objects.all()
            skus = SKU.objects.all()
            context = {
                'form_errors': form_errors,
                'prize': prize,
                'prize_levels': prize_levels,
                'skus': skus,
                'csrf_token': get_token(request),
                'left_menu_active': 'lottery-prize',
                'is_superuser': request.user.is_superuser
            }
            return render(request, 'lottery/prize_form.html', context)

        prize.prize_level_id = prize_level_id
        prize.sku_id = sku_id
        prize.quantity = quantity
        prize.save()
        return redirect('lottery:prize_list')


# ===================== 用户端转盘页面 + 抽奖接口 =====================
class LotteryWheelView(LoginRequiredMixin, View):
    """幸运大转盘页面（用户前端）"""

    def get(self, request):
        prize_levels = PrizeLevel.objects.all().order_by('level')
        prizes_data = []
        for level in prize_levels:
            prizes = Prize.objects.filter(prize_level=level).select_related('sku')
            prize_list = []
            for prize in prizes:
                prize_list.append({
                    'sku_name': prize.sku.name,
                    'quantity': prize.quantity
                })
            prizes_data.append({
                'level': level.level,
                'name': level.name,
                'color': level.color,
                'probability': float(level.probability),
                'prizes': prize_list
            })
        context = {
            'prizes_data': json.dumps(prizes_data, ensure_ascii=False),
            'csrf_token': get_token(request),
            'left_menu_active': 'lottery-wheel',
            'is_superuser': request.user.is_superuser
        }
        return render(request, 'lottery/lottery_wheel.html', context)


class LotteryDrawView(LoginRequiredMixin, View):
    """【核心抽奖接口】服务端概率随机开奖！"""

    def post(self, request):
        # 1. 这里可以扩展：校验用户今日抽奖次数
        # user = request.user
        # if 次数不足: return JsonResponse({"code":1,"msg":"今日抽奖次数已用完"})

        # 2. 获取所有中奖等级
        levels = list(PrizeLevel.objects.all())
        if not levels:
            return JsonResponse({"code": 1, "msg": "抽奖活动配置未完成"})

        # 3. 概率随机算法
        rand_val = random.uniform(0, 100)
        current = 0
        win_index = 0
        win_level = None
        
        # 添加调试日志
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"抽奖随机值: {rand_val}")
        
        for idx, lv in enumerate(levels):
            current += lv.probability
            logger.info(f"等级{idx}: {lv.name}, 概率: {lv.probability}, 累积概率: {current}")
            if rand_val <= current:
                win_index = idx
                win_level = lv
                logger.info(f"中奖: {lv.name} (索引: {win_index})")
                break
        
        # 如果没有匹配到任何等级（概率总和小于100%），选择最后一个等级
        if win_level is None:
            win_level = levels[-1]
            win_index = len(levels) - 1
            logger.info(f"概率总和不足，选择最后一个等级: {win_level.name} (索引: {win_index})")

        # 4. 记录抽奖历史
        try:
            # 获取该等级对应的奖品
            prize = Prize.objects.filter(prize_level=win_level).first()
            
            # 创建抽奖记录
            LotteryRecord.objects.create(
                user=request.user,
                prize_level=win_level,
                prize=prize,
                is_won=(prize is not None),
                ip_address=self.get_client_ip(request)
            )
        except Exception as e:
            # 记录失败不影响抽奖结果，但打印错误日志
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"记录抽奖历史失败: {str(e)}", exc_info=True)

        # 5. 返回中奖等级下标，前端控制转盘动画
        return JsonResponse({
            "code": 0,
            "msg": "success",
            "data": {
                "index": win_index
            }
        })

    def get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LotteryRecordListView(LoginRequiredMixin, View):
    """中奖历史记录列表页面"""

    def get(self, request):
        context = {
            'csrf_token': get_token(request),
            'left_menu_active': 'lottery-record',
            'is_superuser': request.user.is_superuser
        }
        return render(request, 'lottery/lottery_record_list.html', context)


class LotteryRecordAPIView(LoginRequiredMixin, View):
    """中奖历史记录API接口"""

    def get(self, request):
        from django.core.paginator import Paginator
        
        page = int(request.GET.get('page', 1))
        username = request.GET.get('username', '').strip()
        is_won = request.GET.get('is_won', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        
        # 构建查询
        records = LotteryRecord.objects.select_related('user', 'prize_level', 'prize__sku')
        
        if username:
            records = records.filter(user__username__icontains=username)
        
        if is_won:
            records = records.filter(is_won=(is_won == '1'))
        
        if start_date:
            records = records.filter(create_time__gte=start_date)
        
        if end_date:
            records = records.filter(create_time__lte=end_date)
        
        # 分页
        paginator = Paginator(records, 10)
        page_obj = paginator.get_page(page)
        
        # 序列化数据
        items = []
        for record in page_obj:
            items.append({
                'id': record.id,
                'username': record.user.username,
                'prize_level': record.prize_level.name if record.prize_level else '-',
                'prize': f"{record.prize.sku.name} x{record.prize.quantity}" if record.prize else '-',
                'is_won': '中奖' if record.is_won else '未中奖',
                'is_won_status': record.is_won,
                'ip_address': record.ip_address or '-',
                'create_time': record.create_time.strftime('%Y-%m-%d %H:%M:%S') if record.create_time else '-'
            })
        
        return JsonResponse({
            'success': True,
            'items': items,
            'current_page': page_obj.number,
            'total_pages': page_obj.paginator.num_pages,
            'total_count': page_obj.paginator.count
        })
