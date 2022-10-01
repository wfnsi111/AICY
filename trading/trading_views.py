import json
import time

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from .strategy.main import MyTrade
from .models import Trader, AccountInfo, OrderInfo, Strategy
from requests.exceptions import ConnectionError
from .strategy.okx.AccountAndTradeApi import AccountAndTradeApi

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


def matrade_bak(request):
    if request.method == 'GET':
        return render(request, 'trading/matrade.html')
    ma = request.POST.get('ma', '')
    instId = request.POST.get('instId', '')
    bar = request.POST.getlist('bar')
    if not bar:
        return HttpResponse('bar error')
    accountinfo_id = request.POST.get('accountinfo')
    try:
        one_accountinfo = AccountInfo.objects.get(pk=accountinfo_id)
    except:
        return HttpResponse('没有账户')
    if one_accountinfo.status == -1:
        return HttpResponse('交易出现未知错误')
    if one_accountinfo.status > 0:
        return HttpResponse('正在交易中')
    api_key = one_accountinfo.api_key
    secret_key = one_accountinfo.secret_key
    passphrase = one_accountinfo.passphrase
    flag = one_accountinfo.flag
    use_server_time = False
    strategy = 'MaTrade'
    kw = {
        'instId': instId,
        "ma": ma,
        "bar2": bar[0],
        "accountinfo": one_accountinfo
    }

    try:
        one_accountinfo.status = 1
        one_accountinfo.msg = ''
        one_accountinfo.save()
        my_trade = MyTrade(api_key, secret_key, passphrase, use_server_time, flag)
        my_trade.start_tarde(strategy, **kw)
    except ConnectionError as e:
        one_accountinfo.msg = e
        one_accountinfo.status = 0
        one_accountinfo.save()
        return HttpResponse('网络错误')
    except Exception as e:
        if one_accountinfo.status == -2:
            one_accountinfo.status = 0
            one_accountinfo.save()
        return HttpResponse('ok')

    return HttpResponse('OK')


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


def stop_processing_strategy(request):
    if request.method == 'GET':
        strategyinfo_id = request.GET.get("strategyinfo_id")
        data = {}
        try:
            strategyinfo = Strategy.objects.get(pk=strategyinfo_id)
        except:
            data['status'] = trading_status.get(-1)
            return HttpResponse(json.dumps(data))
        strategyinfo.status = -2
        strategyinfo.is_active = 0
        strategyinfo.save()
        return redirect(reverse('trading:strategyinfo'))


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


def trading_index(request):
    return render(request, 'trading/trade.html')


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
    strategy = 'MaTrade'
    strategy_obj = Strategy(name=strategy, ma=ma, instid=instId, bar2=bar, accountinfo=all_accountinfo)
    # 选择一个账户作为模板
    accountinfo_id = all_accountinfo[0]
    try:
        one_accountinfo = AccountInfo.objects.get(pk=accountinfo_id)
        # all_accountinfo = AccountInfo.objects.filter(pk__in=all_accountinfo)
    except:
        return HttpResponse('没有账户')
    api_key = one_accountinfo.api_key
    secret_key = one_accountinfo.secret_key
    passphrase = one_accountinfo.passphrase
    flag = one_accountinfo.flag
    use_server_time = False

    kw = {
        'instId': instId,
        "ma": ma,
        "bar2": bar,
        "accountinfo": one_accountinfo,
        "strategy_obj": strategy_obj,
    }

    try:
        strategy_obj.is_active = 1
        strategy_obj.status = 1
        strategy_obj.msg = ''
        strategy_obj.save()
        my_trade = MyTrade(api_key, secret_key, passphrase, use_server_time, flag)
        my_trade.start_tarde(strategy, **kw)
    except ConnectionError as e:
        strategy_obj.msg = e
    except Exception as e:
        if strategy_obj.status == -2:
            strategy_obj.msg = e
            print(e)
    strategy_obj.status = 0
    strategy_obj.is_active = 0
    strategy_obj.save()
    return HttpResponse('OK')


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
