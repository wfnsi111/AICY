import json
import time
import platform

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from .strategy.main import start_my_strategy
from .models import Trader, AccountInfo, OrderInfo, Strategy
from .strategy.okx.AccountAndTradeApi import AccountAndTradeApi
from .task import *
from .login_views import islogin


"""
status 状态：
    -2：强制退出
    -1：出现错误
    0： 空闲中
    1： 等待信号1
    2： 等待信号2
    3： 等待信号3
    4： 准备开仓
    5： 开仓成功
    6： 止损止盈设置成功
    
"""
trading_status = {
    -2: "强制退出",
    -1: '出现错误',
    0: '空闲中',
    1:  '等待信号1',
    2:  '等待信号2',
    3:  '等待信号3',
    4:  '准备开仓',
    5:  '开仓成功',
    6:  '止损止盈设置成功',
    7:  '止盈',
    8:  '止损',
}

account_status = {
    -2: "强制退出",
    -1: '出现错误',
    0: '空闲中',
    1:  '策略运行中',

}


def maalarm(request):
    if request.method == 'GET':
        return render(request, 'trading/matrade.html')
    ma = request.POST.get('ma', '')
    currency = request.POST.get('currency', '')
    bar = request.POST.getlist('bar', [])
    return HttpResponse('提交成功')


@islogin
def trade(request):
    # if request.method == 'GET':
    #     return render(request, 'trading/login.html')
    # username = request.POST.get('username')
    # password = request.POST.get('password')
    # try:
    #     user = auth.authenticate(account=username, password=password)
    #     trader = Trader.objects.filter(account=username).filter(password=password)[0]
    # except:
    #     return HttpResponse('error')
    # # selected_accountinfo = trader.accountinfo_set.all()

    # accountinfos = AccountInfo.objects.filter(is_active=1).filter(status__in=(-2, 0)).filter(flag=0)
    accountinfos = AccountInfo.objects.filter(is_active=1).filter(status__in=(-2, 0))
    return render(request, 'trading/matrade.html', {'accountinfos': accountinfos})


@islogin
def stop_processing_account(request):
    if request.method == 'POST':
        accountinfo_id = request.POST.get("accountinfo_id")
        data = {}
        try:
            accountinfo = AccountInfo.objects.get(pk=accountinfo_id)
        except:
            data['trading_status'] = trading_status.get(-1)
            return HttpResponse(json.dumps(data))
        accountinfo.status = -2
        accountinfo.save()
        data['trading_status'] = trading_status.get(-2)
        return HttpResponse(json.dumps(data))


@islogin
def stop_processing_strategy(request):
    if request.method == 'GET':
        strategyinfo_id = request.GET.get("strategyinfo_id")
        data = {}
        try:
            # 更新策略状态
            strategyinfo = Strategy.objects.get(pk=strategyinfo_id)
            strategyinfo.status = -2
            strategyinfo.is_active = 0
            strategyinfo.save()
            # 更新账户状态
            accountinfos = strategyinfo.accountinfo
            accountinfos = eval(accountinfos)
            # update 更改数据 不会改变有auto_now和自增的字段的值
            AccountInfo.objects.filter(pk__in=accountinfos).update(status=0)
        except Exception as e:
            data['status'] = trading_status.get(-1)
            return HttpResponse(json.dumps(data))

        return redirect(reverse('trading:strategyinfo'))


@islogin
def close_positions_one(request):
    accountinfo_id = request.GET.get('accountinfo_id', None)
    if accountinfo_id is None:
        return HttpResponse('error')
    try:
        accountinfo = AccountInfo.objects.get(pk=accountinfo_id)
    except:
        return HttpResponse('no account info')
    obj_api = AccountAndTradeApi(accountinfo.api_key, accountinfo.secret_key, accountinfo.passphrase, False,
                                 accountinfo.flag)
    accountinfo.status = 0
    accountinfo.save()
    result = obj_api.accountAPI.get_positions('SWAP')
    order_lst = result.get('data', [])
    if order_lst:
        obj_api.close_positions_all(order_lst)
    return redirect(reverse('trading:account_info'))


@islogin
def close_positions_all(request):
    if request.method == 'GET':
        return render(request, 'trading/close_positions_all.html')

    code = request.POST.get('code', '').strip()
    if code != '123456':
        return HttpResponse('Who are you!!!')

    # gt 大于某个值
    # gte 大于或等于某个值
    # lt  小于某个值
    # lte 小于或等于某个值
    account_all = AccountInfo.objects.filter(status__gte=1)
    for obj in account_all:
        obj.status = 0
        obj.save()
        obj_api = AccountAndTradeApi(obj.api_key, obj.secret_key, obj.passphrase, False, obj.flag)
        result = obj_api.accountAPI.get_positions('SWAP')
        order_lst = result.get('data', [])
        for item in order_lst:
            if item:
                para = {
                    "instId": item.get("instId"),
                    'mgnMode': item.get('mgnMode'),
                    "ccy": item.get('ccy'),
                    "posSide": item.get('posSide'),
                    'autoCxl': True
                }
                # self.posSide = {"buy": "long", "sell": "short"}.get(self.side, '')
                # 检测是否有委托 ，如果有委托， 先撤销委托，在平仓
                # self.algo = self.cancel_algo_order_(algoid)
                try:
                    result = obj_api.tradeAPI.close_positions(**para)
                    obj.status = 0
                    obj.save()
                except:
                    obj.status = -1
                    obj.save()

    return HttpResponse('OK!!!')


@islogin
def trading_index(request):
    return render(request, 'trading/trade.html')


@islogin
def account_info(request):
    if request.method == 'GET':
        show_lst = []
        account_all = AccountInfo.objects.filter(is_active=1)
        for obj in account_all:
            show_data = {}
            try:
                obj_api = AccountAndTradeApi(obj.api_key, obj.secret_key, obj.passphrase, False, obj.flag)
                result = obj_api.accountAPI.get_positions('SWAP')
                balance = obj_api.get_my_balance('availEq')
                order_algos_info = obj_api.get_order_tp_and_sl_info()
                show_data['balance'] = balance
                order_lst = result.get('data', [])
                if order_algos_info:
                    show_data['tpTriggerPx'] = order_algos_info.get('tpTriggerPx')
                    show_data['slTriggerPx'] = order_algos_info.get('slTriggerPx')
            except Exception as e:
                order_lst = []
            show_data['account_text'] = obj.account_text
            show_data['id'] = obj.id
            show_data['status'] = account_status.get(obj.status, '无状态')
            show_data['strategy_name'] = obj.strategy_name
            show_data['bar2'] = obj.bar2
            if order_lst:
                for item in order_lst:
                    show_data.update(item)
                    show_data['upl'] = "%.2f" % float(item['upl'])

            else:
                pass

            show_lst.append(show_data)

        return render(request, 'trading/accountinfo.html', {"accountinfo": show_lst})


def test(request):
    if request.method == 'POST':
        time.sleep(5)
        return HttpResponse('post')
    return render(request, 'trading/test.html')


@islogin
def orderinfo_show(request):
    if request.method == 'GET':
        accountinfo_id = request.GET.get('accountinfo_id', None)
        if accountinfo_id is None:
            all_accountinfo = AccountInfo.objects.filter(is_active=1)
            return render(request, 'trading/orderinfo.html', {'all_accountinfo': all_accountinfo})
    else:
        accountinfo_id = request.POST.get('accountinfo_id', '')
    try:
        orderinfos = OrderInfo.objects.filter(accountinfo_id=int(accountinfo_id))
    except:
        return HttpResponse("ERROR")
    return render(request, 'trading/orderinfo1.html', {'orderinfos': orderinfos})


@islogin
def matrade(request):
    if request.method == 'GET':
        return render(request, 'trading/matrade.html')
    ma = request.POST.get('ma', '')
    instId = request.POST.get('instId', '')
    bar = request.POST.get('bar', '')
    if not bar or not instId or not bar:
        return HttpResponse('参数设置错误---[均线: %s]---[货币: %s]---[周期: %s]' % (ma, instId, bar))
    all_accountinfo = request.POST.getlist('select2')
    if not all_accountinfo:
        return HttpResponse('未选择账户')
    strategy_name = 'MaTrade'

    kw = {
        'instId': instId,
        "ma": ma,
        "bar2": bar,
        "accountinfo": all_accountinfo,
    }

    try:
        plat = platform.system().lower()
        if plat == 'windows':
            start_my_strategy(strategy_name, kw)
        else:
            # celery 管理任务
            result = start_my_strategy_by_celery.delay(strategy_name, kw)
    except Exception as e:
        print(e)
    return HttpResponse('策略启动成功')


@islogin
def strategyinfo(request):
    if request.method == 'GET':
        try:
            strategyinfos = Strategy.objects.filter(is_active=1)
            for strategyinfo in strategyinfos:
                account_name_list = []
                accountinfos = strategyinfo.accountinfo
                accountinfos = eval(accountinfos)
                accountinfos = AccountInfo.objects.filter(id__in=accountinfos)
                for accountinfo in accountinfos:
                    account_name_list.append(accountinfo.account_text)
                strategyinfo.accountinfo = ', '.join(account_name_list)
                strategyinfo.status = trading_status.get(strategyinfo.status)

        except Exception as e:
            strategyinfos = None
        return render(request, 'trading/strategy.html', {'strategyinfos': strategyinfos})
