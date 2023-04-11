import json
import platform
import os
import time

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from trading.models import AccountInfo, OrderInfo, Strategy, PlaceAlgo
from trading.strategy.okx.AccountAndTradeApi import AccountAndTradeApi
from trading.task import *
from trading.tradingviews.login_views import islogin


trading_status = {
    -2: "强制退出",
    -1: '出现错误',
    0: '空闲中',
    1:  '等待信号1',
    2:  '等待信号2',
    3:  '等待信号3',
    4:  '准备开仓',
    5:  '开仓成功',
    6:  '有账户异常',
    7:  '止盈',
    8:  '止损',
    9:  '已停止运行',
}


# gt 大于某个值
# gte 大于或等于某个值
# lt  小于某个值
# lte 小于或等于某个值


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
    clOrdId = "123"
    # result = obj_api.tradeAPI.get_orders(instId, clOrdId)

    if order_lst:
        obj_api.close_positions_all_(order_lst, clOrdId)

    # 更新收益
    time.sleep(0.3)
    result = obj_api.tradeAPI.get_orders_history('SWAP', limit='2')
    result = result.get("data")
    # 第一个是平仓，第二个是开仓的订单
    open_order_id = result[1].get('ordId')
    orderinfos = OrderInfo.objects.filter(ordid=open_order_id)
    for orderinfo in orderinfos:
        if orderinfo.pnl is None:
            orderinfo.pnl = result[0].get("pnl")
            orderinfo.closeavgpx = "%.2f" % float(result[0].get('avgPx'))
            orderinfo.closeordid = result[0].get('ordId')
            orderinfo.close_position = 1
            orderinfo.save()

    return redirect(reverse('trading:account_info'))


@islogin
def close_positions_all(request):
    if request.method == 'POST':
        trade_code = request.POST.get('trade_code', '').strip()
        strategy_id = request.POST.get('algo_number', '').strip()
        if trade_code != '123456':
            return HttpResponse('Who are you!!!')
        try:
            account_id_list = []
            strategyinfo = Strategy.objects.get(pk=int(strategy_id))
            for account_id in eval(strategyinfo.accountinfo):
                account_id_list.append(int(account_id))
            accountinfo_all = AccountInfo.objects.filter(id__in=account_id_list).filter(status__gte=2)
        except Exception as e:
            print(e)
            return HttpResponse('委托单设置错误')

        if not accountinfo_all:
            return HttpResponse('未查询到之前的委托信息')

        status_list = []
        for accountinfo in accountinfo_all:
            obj_api = AccountAndTradeApi(accountinfo.api_key, accountinfo.secret_key, accountinfo.passphrase, False,
                                         accountinfo.flag)

            status = accountinfo.status
            result = obj_api.accountAPI.get_positions('SWAP')
            order_lst = result.get('data', [])
            if not order_lst:
                status = 0
            for item in order_lst:
                if item:
                    para = {
                        "instId": item.get("instId"),
                        'mgnMode': item.get('mgnMode'),
                        "ccy": item.get('ccy'),
                        "posSide": item.get('posSide'),
                        'autoCxl': True
                    }

                    try:
                        result = obj_api.tradeAPI.close_positions(**para)
                        if result.get("code") == '0':
                            status = 0
                        else:
                            status = -1
                    except Exception as e:
                        print(e)
                        status = -1
            status_list.append({'obj': accountinfo, "status": status})

        # 手动平仓之后，更新收益情况
        orderinfos = OrderInfo.objects.filter(strategyid=int(strategy_id))
        for orderinfo in orderinfos:
            close_positions_update_pnl(orderinfo)

        # 更新数据库状态
        for item in status_list:
            obj = item['obj']
            obj.status = item['status']
            obj.save()

        strategyinfo.status = 0
        strategyinfo.is_active = 0
        strategyinfo.save()

        return redirect(reverse('trading:account_info'))


def close_positions_update_pnl(orderinfo):
    if orderinfo.pnl is None:
        accountinfo = orderinfo.accountinfo
        obj_api = AccountAndTradeApi(accountinfo.api_key, accountinfo.secret_key, accountinfo.passphrase, False,
                                     accountinfo.flag)
        # 更新收益
        time.sleep(0.5)
        result = obj_api.tradeAPI.get_orders_history('SWAP', limit='2')
        result = result.get("data")
        # 第一个是平仓，第二个是开仓的订单
        open_order_id = result[1].get('ordId')
        orderinfos = OrderInfo.objects.filter(ordid=open_order_id)
        for orderinfo in orderinfos:
            if orderinfo.pnl is None:
                orderinfo.pnl = result[0].get("pnl")
                orderinfo.closeavgpx = "%.2f" % float(result[0].get('avgPx'))
                orderinfo.closeordid = result[0].get('ordId')
                orderinfo.close_position = 1
                orderinfo.save()


@islogin
def trading_index(request):
    return render(request, 'trading/trade.html')


def trading_index_no_login(request):
    return render(request, 'trading/trade_no_login.html')


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


def orderinfo_show_no_login(request):
    if request.method == 'GET':
        accountinfo_id = request.GET.get('accountinfo_id', None)
        if accountinfo_id is None:
            all_accountinfo = AccountInfo.objects.filter(is_active=1)
            return render(request, 'trading/orderinfo_no_login.html', {'all_accountinfo': all_accountinfo})
    else:
        accountinfo_id = request.POST.get('accountinfo_id', '')
    try:
        orderinfos = OrderInfo.objects.filter(accountinfo_id=int(accountinfo_id))
    except:
        return HttpResponse("ERROR")
    return render(request, 'trading/orderinfo1_no_login.html', {'orderinfos': orderinfos})


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
    filename = request.FILES.get("args_file")
    if filename:
        result = save_args_file(filename)
        if not result:
            return HttpResponse('配置文件错误')

    strategy_name = 'MaTrade'

    kw = {
        'instId': instId,
        "ma": ma,
        "bar2": bar,
        "accountinfo": all_accountinfo,
        "trader": request.session.get('username'),
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
                accountinfos_obj = AccountInfo.objects.filter(id__in=accountinfos)
                strategyinfo.accountinfo = [accountinfo.account_text for accountinfo in accountinfos_obj]
                strategyinfo.status = trading_status.get(strategyinfo.status)

        except Exception as e:
            strategyinfos = None
        return render(request, 'trading/strategy.html', {'strategyinfos': strategyinfos})


def strategyinfo_no_login(request):
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
        return render(request, 'trading/strategy_no_login.html', {'strategyinfos': strategyinfos})


@islogin
def matrade_open_order(request):
    accountinfos = AccountInfo.objects.filter(is_active=1).filter(status__in=(-2, 0))
    if request.method == 'GET':
        return render(request, 'trading/matrade_open_order.html', {'accountinfos': accountinfos})
    trade_code = request.POST.get('trade_code', '')
    if not trade_code.strip().lower() == '123456':
        return HttpResponse('验证码错误')
    ma = request.POST.get('ma', '')
    instId = request.POST.get('instId', '')
    bar = request.POST.get('bar', '')
    posside = request.POST.get('posside', '')
    if posside not in ('short', 'long'):
        return HttpResponse('方向错误')
    if not all([ma, instId, bar, posside]):
        return HttpResponse('参数设置错误---[均线: %s]---[货币: %s]---[周期: %s]----[方向: %s]' % (ma, instId, bar, posside))
    all_accountinfo = request.POST.getlist('select2')
    if not all_accountinfo:
        return HttpResponse('未选择账户')
    strategy_name = 'MaTrade'

    kw = {
        'instId': instId,
        "ma": ma,
        "bar2": bar,
        "posside": posside,
        "accountinfo": all_accountinfo,
        "trader": request.session.get('username'),
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


def save_args_file(file):
    result = True
    try:
        if file.name == '参数信息.txt':
            cur_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ma_trade_args = os.path.join(cur_dir, 'strategy', 'conf', 'ma_trade_args.py')
            with open(ma_trade_args, 'wb') as f:
                for chunk in file.chunks():
                    if not chunk:
                        result = False
                    f.write(chunk)
        else:
            result = False
    except Exception as e:
        print(e)
        result = False

    return result
