import json
import time

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from .strategy.main import MyTrade
from .models import Trader, AccountInfo
from django.contrib import auth
from django.contrib.auth.decorators import login_required
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
}

def maalarm(request):
    if request.method == 'GET':
        return render(request, 'trading/matrade.html')
    ma = request.POST.get('ma', '')
    currency = request.POST.get('currency', '')
    bar = request.POST.getlist('bar', [])
    return HttpResponse('提交成功')


def matrade(request):
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


def login(request):
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

    trader = Trader.objects.filter(pk=1)[0]
    return render(request, 'trading/matrade.html', {'trader': trader})


def stop_processing_strategy(request):
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

    account_all = AccountInfo.objects.filter(status__gte=5)
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
        account_all = AccountInfo.objects.all()
        for obj in account_all:
            show_data = {}
            try:
                obj_api = AccountAndTradeApi(obj.api_key, obj.secret_key, obj.passphrase, False, obj.flag)
                result = obj_api.accountAPI.get_positions('SWAP')
                balance = obj_api.get_my_balance('eq')
                show_data['balance'] = balance
                order_lst = result.get('data', [])
            except Exception as e:
                order_lst = []
            show_data['account_text'] = obj.account_text
            show_data['id'] = obj.id
            show_data['status'] = trading_status.get(obj.status, '出现错误')
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
